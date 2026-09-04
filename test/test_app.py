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
