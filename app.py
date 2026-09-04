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

import ipaddress
import os
import urllib.parse

from flask import Flask, Response, redirect, request
from werkzeug.middleware.proxy_fix import ProxyFix

import download

# Where everything that is no longer served here gets forwarded.
FORWARD_BASE = os.environ.get("FORWARD_BASE", "https://dashboard2.gnps2.org").rstrip("/")

# Longest USI we will even attempt to resolve.
MAX_USI_LENGTH = 2000


def _parse_cidrs(raw):
    """Parse a comma-separated CIDR list, ignoring anything unparseable.

    A typo here must not take the service down, and must not silently widen the
    exemption either - bad entries are dropped, not treated as match-all.
    """

    networks = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        try:
            networks.append(ipaddress.ip_network(entry, strict=False))
        except ValueError:
            print("Ignoring unparseable exempt CIDR: {!r}".format(entry))
    return networks


# Networks that bypass the rate limit entirely - our own infrastructure and lab
# machines, which legitimately make bulk resolution requests.
EXEMPT_NETWORKS = _parse_cidrs(os.environ.get("RATELIMIT_EXEMPT_CIDRS", ""))


def _is_exempt(address):
    if not address:
        return False
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return any(ip in network for network in EXEMPT_NETWORKS)


server = Flask(__name__)
# x_for=1 trusts exactly one proxy hop, so request.remote_addr is the real client
# rather than nginx. The exemption check depends on that being right - if another
# proxy is ever put in front, this count has to go up or every client looks like
# the proxy.
server.wsgi_app = ProxyFix(server.wsgi_app, x_for=1, x_host=1)

# Optional throttle for the one endpoint that makes outbound requests. Unset by
# default so existing programmatic consumers are not broken by the cutover; set
# e.g. DOWNLOADLINK_RATELIMIT="120 per minute" if it gets abused.
_ratelimit = os.environ.get("DOWNLOADLINK_RATELIMIT", "").strip()
if _ratelimit:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(get_remote_address, app=server, default_limits=[])

    @limiter.request_filter
    def _exempt_known_networks():
        return _is_exempt(get_remote_address())

    # Must decorate the view at definition time. Calling limiter.limit() on an
    # already-registered view does nothing, and does it silently.
    ratelimit = limiter.limit(_ratelimit)
else:
    limiter = None

    def ratelimit(view):
        return view


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
@ratelimit
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


if __name__ == "__main__":
    server.run(port=5000, host="0.0.0.0")
