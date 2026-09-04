"""Offline tests for the shim: routing, redirect behavior, and input validation.

Nothing here touches the network - resolution itself is covered by
test_usi_resolution.py.
"""

import sys

import pytest

sys.path.insert(0, "..")

import app as app_module


@pytest.fixture
def client():
    app_module.server.config["TESTING"] = True
    with app_module.server.test_client() as c:
        yield c


BASE = app_module.FORWARD_BASE


def test_root_redirects(client):
    r = client.get("/")
    assert r.status_code == 302
    assert r.headers["Location"] == BASE + "/"


def test_redirect_is_temporary_not_permanent(client):
    # A 301 would be cached by browsers indefinitely and could not be rolled back.
    assert client.get("/").status_code == 302
    assert client.get("/mspreview?usi=mzspec:MSV000084951:AH22").status_code == 302


def test_redirect_preserves_query_string(client):
    # Deep links are cited in published papers; every param must survive.
    query = "usi=mzspec%3AMSV000084951%3AAH22&xicmz=870.95&xic_tolerance=0.5&xic_norm=False"
    r = client.get("/?" + query)
    assert r.headers["Location"] == "{}/?{}".format(BASE, query)


def test_retired_endpoints_forward(client):
    for path in ["/mspreview", "/shorturl", "/settingsdownload", "/overlayresolve", "/logo.png"]:
        r = client.get(path)
        assert r.status_code == 302, path
        assert r.headers["Location"].startswith(BASE + "/"), path


def test_forward_cannot_be_turned_into_open_redirect(client):
    # A crafted path must not be able to inject a different host into the target.
    for path in ["//evil.example.com/x", "/x/../../evil.example.com", "/https://evil.example.com"]:
        r = client.get(path)
        if r.status_code == 404:
            # Werkzeug normalized it away before routing; also acceptable.
            continue
        assert r.status_code == 302, path
        assert r.headers["Location"].startswith(BASE + "/"), path


@pytest.mark.parametrize("query", [
    "",                                  # no usi at all
    "usi=",                              # empty usi
    "usi=notausi",                       # wrong scheme
    "usi=mzspec:MSV000084951",           # too few components
])
def test_downloadlink_rejects_bad_input(client, query):
    r = client.get("/downloadlink?" + query)
    assert r.status_code == 400
    assert r.mimetype == "text/plain"


def test_downloadlink_rejects_overlong_usi(client):
    r = client.get("/downloadlink?usi=mzspec:MSV000084951:" + "A" * app_module.MAX_USI_LENGTH)
    assert r.status_code == 400


def test_downloadlink_returns_bare_url(client, monkeypatch):
    monkeypatch.setattr(
        app_module.download, "_resolve_usi_remotelink",
        lambda usi: ("https://example.org/file.mzML", "MASSIVEDATASET"),
    )
    r = client.get("/downloadlink?usi=mzspec:MSV000084951:AH22")
    assert r.status_code == 200
    # Response body has always been the bare URL - consumers parse it directly.
    assert r.get_data(as_text=True) == "https://example.org/file.mzML"


def test_downloadlink_unresolvable_is_404(client, monkeypatch):
    monkeypatch.setattr(app_module.download, "_resolve_usi_remotelink", lambda usi: ("", ""))
    r = client.get("/downloadlink?usi=mzspec:NOPE:file.mzML")
    assert r.status_code == 404


def test_downloadlink_upstream_failure_does_not_leak_traceback(client, monkeypatch):
    def boom(usi):
        raise RuntimeError("massive.ucsd.edu TLS handshake failed")

    monkeypatch.setattr(app_module.download, "_resolve_usi_remotelink", boom)
    r = client.get("/downloadlink?usi=mzspec:MSV000084951:AH22")
    assert r.status_code == 502
    assert "TLS" not in r.get_data(as_text=True)
    assert "Traceback" not in r.get_data(as_text=True)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_data(as_text=True) == "ok"


def test_ratelimit_actually_enforces(monkeypatch):
    """The limiter is opt-in, so it is easy for it to be wired up but inert.

    Applying limiter.limit() to an already-registered view silently does
    nothing; this catches that regression.
    """
    import importlib

    monkeypatch.setenv("DOWNLOADLINK_RATELIMIT", "3 per minute")
    limited = importlib.reload(app_module)
    try:
        with limited.server.test_client() as c:
            codes = [c.get("/downloadlink?usi=garbage").status_code for _ in range(6)]
        assert 429 in codes, codes
    finally:
        # Restore the unlimited module for the rest of the session.
        monkeypatch.delenv("DOWNLOADLINK_RATELIMIT")
        importlib.reload(app_module)


def test_no_ratelimit_by_default(client):
    # Default must not throttle - existing consumers were never rate limited.
    codes = [client.get("/downloadlink?usi=garbage").status_code for _ in range(15)]
    assert set(codes) == {400}, codes


def _reload_with(monkeypatch, **env):
    import importlib

    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return importlib.reload(app_module)


def test_exempt_network_bypasses_ratelimit(monkeypatch):
    import importlib

    limited = _reload_with(
        monkeypatch,
        DOWNLOADLINK_RATELIMIT="3 per minute",
        RATELIMIT_EXEMPT_CIDRS="137.110.0.0/16, 10.0.0.0/8",
    )
    try:
        with limited.server.test_client() as c:
            def hit(ip):
                return [
                    c.get("/downloadlink?usi=garbage",
                          headers={"X-Forwarded-For": ip}).status_code
                    for _ in range(6)
                ]

            assert 429 not in hit("137.110.5.9")
            assert 429 not in hit("10.1.2.3")
            # A host outside the exempt space must still be limited.
            assert 429 in hit("8.8.8.8")
    finally:
        monkeypatch.delenv("DOWNLOADLINK_RATELIMIT")
        monkeypatch.delenv("RATELIMIT_EXEMPT_CIDRS")
        importlib.reload(app_module)


def test_bad_cidr_is_dropped_not_treated_as_match_all(monkeypatch):
    # A typo must never widen the exemption to everyone.
    nets = app_module._parse_cidrs("137.110.0.0/16, not-a-cidr, , 999.999.0.0/16")
    assert [str(n) for n in nets] == ["137.110.0.0/16"]

    monkeypatch.setattr(app_module, "EXEMPT_NETWORKS", nets)
    assert app_module._is_exempt("137.110.5.9") is True
    assert app_module._is_exempt("8.8.8.8") is False


def test_empty_exempt_config_exempts_nobody(monkeypatch):
    monkeypatch.setattr(app_module, "EXEMPT_NETWORKS", app_module._parse_cidrs(""))
    assert app_module._is_exempt("137.110.5.9") is False


@pytest.mark.parametrize("address,expected", [
    ("137.110.5.9", True),
    ("8.8.8.8", False),
    ("", False),
    ("not-an-ip", False),
    (None, False),
])
def test_is_exempt(monkeypatch, address, expected):
    monkeypatch.setattr(app_module, "EXEMPT_NETWORKS",
                        app_module._parse_cidrs("137.110.0.0/16"))
    assert app_module._is_exempt(address) is expected
