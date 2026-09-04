# GNPS LCMS Dashboard — Agent Notes

## What this is now

A maintenance shim, not the dashboard. The interactive app was retired in favor
of the rewrite at `dashboard2.gnps2.org`. This branch keeps exactly one endpoint
alive and forwards everything else.

- `app.py` — the whole server (~140 lines). Flask only; no Dash, no Celery, no Redis.
- `download.py` + `download_msv.py`, `download_workbench.py`, `download_norman.py`,
  `download_zenodo.py` — USI → remote URL resolution, and nothing else.

## Constraints

The point of this branch is a small attack surface. Keep it that way:

- **No subprocess execution.** The old code shelled out to `wget`, `msaccess`
  and `msconvert` with USI-derived strings interpolated into `os.system`. None of
  that survives here; do not reintroduce it.
- **No file download or conversion.** Resolution returns a URL; the caller fetches it.
- **No filesystem writes.** The container runs `read_only: true` with no volumes.
- **Dependencies stay at five** (`requirements.txt`). Anything needing pandas,
  numpy, a converter binary, or a compiler belongs in the rewrite, not here.
- **Every outbound `requests` call needs a timeout** — they run on a request path
  and upstream repositories hang. Use `HTTP_TIMEOUT`.

## Behavior that must not drift

- `/downloadlink` returns the **bare URL** as the response body. External tools
  parse it directly; do not wrap it in JSON.
- The catch-all forward is **302, not 301**. A permanent redirect gets cached by
  browsers and cannot be walked back if the rewrite needs a rollback.
- The forward **preserves the full query string**. Deep links of the form
  `/?usi=...&xicmz=...&xic_tolerance=...` appear in published papers.
- The forward re-encodes the path with `quote(..., safe="/")` so a crafted path
  cannot inject a host and turn it into an open redirect. `test_app.py` covers this.

## Testing

```shell
cd test
make app        # offline; this is what CI gates on
make resolve    # hits live upstream repositories; allowed to fail in CI
```

`usi_list.tsv` is the resolution corpus — one USI per supported repository.

## Deploying

Single container, fronted by **Cloudflare** — the nginx-proxy / letsencrypt
companion and the external `nginx-net` network are gone, and the port is
published directly (`HOST_PORT`, default 6548).

The origin speaks plain HTTP. If it is publicly reachable, firewall it to
Cloudflare's published IP ranges, or it can be hit directly and Cloudflare
bypassed. For a cloudflared tunnel, set `BIND_ADDRESS=127.0.0.1`.

`ProxyFix(x_for=1)` trusts exactly one proxy hop. That is correct for Cloudflare
alone; if another proxy is ever added in front, the count must go up or every
request appears to come from the proxy.

On a host that previously ran the full stack, the old worker and Redis
containers are *not* removed by `docker compose up`; run
`make server-compose-down` there first, or they keep running with their old
`/data/datasets` mounts.

## Deferred: rate limiting on /downloadlink

Removed for now (2026-09-03) to keep the surface minimal — it was never enabled
in production. **To restore: `git revert 5f69df7` then `git revert df8432d`'s
limiter hunks**, or just re-read commit `5f69df7`, which has the full working
implementation plus tests.

What it provided:

- `DOWNLOADLINK_RATELIMIT` (e.g. `120 per minute`), off when unset.
- `RATELIMIT_EXEMPT_CIDRS` — comma-separated CIDRs bypassing the limit, for lab
  and infrastructure ranges that legitimately make bulk requests. **The actual
  lab ranges were never filled in**; `137.110.0.0/16` appeared only as a test
  fixture. Get the real ranges before enabling, and check whether lab traffic
  arrives from off-campus or VPN addresses that a campus CIDR would miss.
- Dependency: `flask_limiter` (dropped from `requirements.txt`).

Two traps if it is re-added:

1. **Decorate the view at definition time.** Calling `limiter.limit()` on an
   already-registered view registers nothing and raises no error — the endpoint
   looks protected and is not. This shipped once already; it needs a test that
   asserts a 429 actually happens.
2. **In-memory storage is per-worker.** With multiple gunicorn workers the
   effective limit is N times the configured one. Fine for a coarse abuse
   ceiling, wrong if a precise limit is ever needed.

Also worth doing before enabling: Cloudflare can rate limit at the edge, which
may be the better place for this now that it fronts the origin.
