## GNPS LCMS Dashboard — maintenance shim

The interactive GNPS LCMS Dashboard has been retired. It is replaced by a
rewritten service at **https://dashboard2.gnps2.org**.

What remains in this repository is a small Flask app whose only jobs are:

1. Keep serving `/downloadlink`, the USI → remote URL resolver that other tools
   call directly.
2. Forward every other request to the replacement service.

Everything else — the Dash UI, XIC/TIC/2D-map computation, MS2 rendering, feature
finding, MassQL, overlays, collaborative sync, file download and conversion, the
Celery workers, Redis, and the bundled ProteoWizard binaries — has been removed.

### API

#### Resolve a USI to a download URL

```
GET /downloadlink?usi=<usi>
```

Returns the bare URL as `text/plain`. This is unchanged from the previous
implementation.

```
$ curl 'https://dashboard.gnps2.org/downloadlink?usi=mzspec:MSV000084951:AH22'
https://massiveproxy.gnps2.org/massiveproxy/MSV000084951/ccms_peak/AH22.mzML
```

| Status | Meaning |
| --- | --- |
| `200` | Body is the remote URL |
| `400` | Missing or malformed `usi` |
| `404` | Well-formed USI that resolves to nothing |
| `502` | Upstream repository lookup failed |

Supported collections: MassIVE (`MSV`), GNPS/GNPS2 tasks, MetaboLights
(`MTBLS`), Metabolomics Workbench (`ST`), GlycoPost (`GPST`), Zenodo
(`ZENODO-`), NORMAN (`NORMAN-`), ProteomeXchange (`PXD`).

#### Health

```
GET /health   ->   200 "ok"
```

### Everything else

Any other path is answered with a **302** to `dashboard2.gnps2.org`, preserving
the path and the full query string, so existing deep links
(`/?usi=...&xicmz=...&xic_tolerance=...`) keep working as long as the
replacement accepts the same parameters.

The redirect is deliberately temporary rather than permanent — a `301` would be
cached by browsers indefinitely and could not be rolled back.

### Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `FORWARD_BASE` | `https://dashboard2.gnps2.org` | Redirect target |
| `DOWNLOADLINK_RATELIMIT` | unset (no limit) | e.g. `120 per minute` |
| `HOSTNAME` | `dashboard.gnps2.org` | Virtual host for the nginx proxy |

### Running

```shell
make server-compose-production     # single container, port 6548 -> 5000
```

Or without Docker:

```shell
pip install -r requirements.txt
./run_server.sh                    # http://localhost:5000
```

Note that `docker compose up` will not remove the retired worker and Redis
containers on a host that previously ran the full stack. Run
`make server-compose-down` there once before bringing this up.

### Testing

```shell
cd test
make app        # offline: routing, redirects, input validation
make resolve    # hits live upstream repositories
```
