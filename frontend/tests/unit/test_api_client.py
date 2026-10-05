import json

import httpx
import pytest

from shared.lib.api_client import ApiClient, ApiError, TokenPair


def make(handler, tokens=None, on_expired=None):
    return ApiClient("http://b.test", 5, tokens or TokenPair("old", "r1"),
                     transport=httpx.MockTransport(handler), on_session_expired=on_expired)


def test_base_url_and_bearer_header():
    seen = {}

    def handler(req):
        seen["url"], seen["auth"] = str(req.url), req.headers.get("authorization")
        return httpx.Response(200, json={"ok": 1})

    assert make(handler).request_json("GET", "/x") == {"ok": 1}
    assert seen == {"url": "http://b.test/x", "auth": "Bearer old"}


def test_refresh_once_then_retry_succeeds():
    calls = []

    def handler(req):
        calls.append((req.url.path, req.headers.get("authorization")))
        if req.url.path == "/users/refresh_token":
            assert json.loads(req.content) == {"token": "r1"}
            return httpx.Response(200, json={"access_token": "new", "refresh_token": "r2", "token_type": "bearer"})
        if req.headers.get("authorization") == "Bearer old":
            return httpx.Response(401, json={"detail": "expired"})
        return httpx.Response(200, json={"ok": True})

    tokens = TokenPair("old", "r1")
    assert make(handler, tokens).request_json("GET", "/data") == {"ok": True}
    assert tokens.access == "new" and tokens.refresh == "r2"
    assert [c[0] for c in calls] == ["/data", "/users/refresh_token", "/data"]
    assert calls[-1][1] == "Bearer new"


def test_failed_refresh_expires_session_and_calls_back():
    expired = []

    def handler(req):
        return httpx.Response(401, json={"detail": "x"})

    tokens = TokenPair("old", "r1")
    with pytest.raises(ApiError) as exc:
        make(handler, tokens, lambda: expired.append(1)).request("GET", "/data")
    assert exc.value.kind == "session_expired" and exc.value.status_code == 401
    assert tokens.access is None and tokens.refresh is None and expired == [1]


def test_retry_happens_only_once():
    count = {"data": 0}

    def handler(req):
        if req.url.path == "/users/refresh_token":
            return httpx.Response(200, json={"access_token": "new", "refresh_token": "r2"})
        count["data"] += 1
        return httpx.Response(401, json={"detail": "still no"})

    with pytest.raises(ApiError):
        make(handler).request("GET", "/data")
    assert count["data"] == 2


def test_auth_false_requests_never_refresh_and_surface_backend_message():
    def handler(req):
        assert "authorization" not in req.headers
        return httpx.Response(401, json={"error": True, "status_code": 401, "detail": "Invalid credentials"})

    with pytest.raises(ApiError) as exc:
        make(handler).request_json("POST", "/users/login", auth=False, json={})
    assert exc.value.message == "Invalid credentials" and exc.value.kind == "error"


@pytest.mark.parametrize("status,expected", [
    (403, "permission"), (404, "could not find"), (413, "too large"), (429, "Too many"),
    (500, "temporarily unavailable"), (503, "temporarily unavailable"),
])
def test_status_mapping_is_friendly(status, expected):
    def handler(req):
        return httpx.Response(status, json={"detail": "Traceback (most recent call last) internal secret"})

    with pytest.raises(ApiError) as exc:
        make(handler).request("GET", "/x")
    assert expected in exc.value.message and "Traceback" not in exc.value.message


def test_validation_list_detail_is_flattened():
    def handler(req):
        return httpx.Response(422, json={"detail": [
            {"loc": ["body", "email"], "msg": "Value error, bad email"}, {"loc": ["body"], "msg": "other"}]})

    with pytest.raises(ApiError) as exc:
        make(handler).request("POST", "/x", json={})
    assert exc.value.message == "email: bad email; other"


def test_non_json_error_and_success_bodies_do_not_crash():
    def html_500(req):
        return httpx.Response(502, text="<html>bad gateway</html>")

    with pytest.raises(ApiError) as exc:
        make(html_500).request("GET", "/x")
    assert "temporarily unavailable" in exc.value.message

    def html_200(req):
        return httpx.Response(200, text="<html>ok</html>")

    with pytest.raises(ApiError):
        make(html_200).request_json("GET", "/x")
    assert make(html_200).request("GET", "/x").text.startswith("<html>")


def test_network_and_timeout_errors_are_mapped():
    def boom(req):
        raise httpx.ConnectError("refused")

    def slow(req):
        raise httpx.ReadTimeout("slow")

    with pytest.raises(ApiError) as e1:
        make(boom).request("GET", "/x")
    assert e1.value.kind == "network" and "Cannot reach" in e1.value.message
    with pytest.raises(ApiError) as e2:
        make(slow).request("GET", "/x")
    assert e2.value.kind == "timeout"


def test_long_or_odd_detail_falls_back_to_generic():
    def handler(req):
        return httpx.Response(400, json={"detail": "x" * 500})

    with pytest.raises(ApiError) as exc:
        make(handler).request("GET", "/x")
    assert exc.value.message == "Something went wrong. Please try again."


def test_401_without_refresh_token_expires_session():
    def handler(req):
        return httpx.Response(401, json={"detail": "x"})

    with pytest.raises(ApiError) as exc:
        make(handler, TokenPair("a", None)).request("GET", "/x")
    assert exc.value.kind == "session_expired"
