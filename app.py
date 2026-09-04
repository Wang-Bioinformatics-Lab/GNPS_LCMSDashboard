# -*- coding: utf-8 -*-

"""
GNPS LCMS Dashboard - maintenance shim.

The interactive dashboard has been retired in favor of the rewritten service at
dashboard2.gnps2.org. This process keeps exactly one piece of the old server
alive - the ``/downloadlink`` USI resolver, which other tools call directly -
and forwards every other path onward.

Deliberately kept small: no Dash, no Celery workers, no Redis, no file
downloads, no conversion, no subprocess execution.
"""

import os
import urllib.parse

from flask import Flask, Response, redirect, request
from werkzeug.middleware.proxy_fix import ProxyFix

import download

# Where everything that is no longer served here gets forwarded.
FORWARD_BASE = os.environ.get("FORWARD_BASE", "https://dashboard2.gnps2.org").rstrip("/")

# Longest USI we will even attempt to resolve.
MAX_USI_LENGTH = 2000

server = Flask(__name__)
server.wsgi_app = ProxyFix(server.wsgi_app, x_for=1, x_host=1)

# Optional throttle for the one endpoint that makes outbound requests. Unset by
# default so existing programmatic consumers are not broken by the cutover; set
# e.g. DOWNLOADLINK_RATELIMIT="120 per minute" if it gets abused.
_ratelimit = os.environ.get("DOWNLOADLINK_RATELIMIT", "").strip()
if _ratelimit:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(get_remote_address, app=server, default_limits=[])
else:
    limiter = None


def _text(body, status=200):
    return Response(body, status=status, mimetype="text/plain")


def _validate_usi(usi):
    """Returns an error string if the USI is not worth trying to resolve, else None."""

    if not usi:
        return "Missing required 'usi' parameter"

    if len(usi) > MAX_USI_LENGTH:
        return "USI too long"

    # A USI is mzspec:<collection>:<path>[:...]. Everything downstream indexes
    # into those splits, so reject short input here rather than raising later.
    splits = usi.split(":")
    if splits[0] != "mzspec" or len(splits) < 3:
        return "Malformed USI, expected mzspec:<collection>:<path>"

    return None


@server.route("/downloadlink")
def downloadlink():
    """Resolve a USI to the remote URL its data can be fetched from.

    Kept on this host because external tooling depends on it. Response body is
    the bare URL, as it has always been.
    """

    usi = request.args.get("usi", "")

    error = _validate_usi(usi)
    if error is not None:
        return _text(error, 400)

    try:
        remote_link, _resource = download._resolve_usi_remotelink(usi)
    except Exception:
        # Upstream repository lookups fail routinely (MassIVE TLS, PX outages).
        # Do not leak a traceback for it.
        return _text("Unable to resolve USI", 502)

    if not remote_link:
        return _text("USI could not be resolved to a remote link", 404)

    return _text(remote_link)


@server.route("/health")
def health():
    return _text("ok")


@server.route("/", defaults={"path": ""})
@server.route("/<path:path>")
def forward(path):
    """Forward everything else to the replacement service.

    302, not 301: a permanent redirect would be cached by browsers indefinitely
    and could not be walked back if the new service needs to be rolled back.
    """

    # Flask has already URL-decoded `path`. Re-encoding it - and keeping only
    # "/" safe - means a crafted path cannot inject a host, query, or fragment
    # into the target and turn this into an open redirect.
    safe_path = urllib.parse.quote(path.lstrip("/"), safe="/")

    target = "{}/{}".format(FORWARD_BASE, safe_path)

    # Deep links carry all their state in the query string (usi, xicmz,
    # xic_tolerance, ...) and are cited in published papers. Preserve verbatim.
    query_string = request.query_string.decode("utf-8", "ignore")
    if query_string:
        target = "{}?{}".format(target, query_string)

    return redirect(target, code=302)


if _ratelimit:
    # Applied after the view exists so the decorator order stays readable.
    limiter.limit(_ratelimit)(server.view_functions["downloadlink"])


if __name__ == "__main__":
    server.run(port=5000, host="0.0.0.0")
