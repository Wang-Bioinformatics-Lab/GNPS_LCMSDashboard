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

Single container. On a host that previously ran the full stack, the old worker
and Redis containers are *not* removed by `docker compose up`; run
`make server-compose-down` there first, or they keep running with their old
`/data/datasets` mounts.
