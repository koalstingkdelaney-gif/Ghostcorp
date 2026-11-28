import time

from fastapi.testclient import TestClient

from app import main, owner_auth


def configure_owner(monkeypatch):
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("OWNER_GITHUB_LOGIN", "koalstingkdelaney-gif")
    monkeypatch.setenv("GHOSTCORP_OWNER_EMAIL", "owner@example.com")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "test-session-secret-that-is-long-enough")
    monkeypatch.setenv("GITHUB_OAUTH_REDIRECT_URI", "https://api.ghostcorpnet.com/auth/github/callback")
    monkeypatch.setenv("GHOSTCORP_SITE_ORIGIN", "https://ghostcorpnet.com")
    monkeypatch.setattr(main, "FEDERATION_ADMIN_TOKEN", "")


def make_session():
    csrf = "csrf-test-token"
    token = owner_auth._sign({
        "sub": "koalstingkdelaney-gif",
        "csrf": csrf,
        "exp": int(time.time()) + 600,
    }, "test-session-secret-that-is-long-enough")
    return token, csrf


def test_owner_oauth_is_locked_until_provider_configuration(monkeypatch):
    for key in ("GITHUB_OAUTH_CLIENT_ID", "GITHUB_OAUTH_CLIENT_SECRET",
                "OWNER_GITHUB_LOGIN", "GHOSTCORP_OWNER_EMAIL", "OWNER_SESSION_SECRET",
                "GITHUB_OAUTH_REDIRECT_URI", "GHOSTCORP_SITE_ORIGIN"):
        monkeypatch.delenv(key, raising=False)
    client = TestClient(main.app)
    assert client.get("/auth/status").json()["configured"] is False
    assert client.get("/auth/github/start").status_code == 503


def test_owner_session_allows_private_reads(monkeypatch):
    configure_owner(monkeypatch)
    token, _ = make_session()
    client = TestClient(main.app, base_url="https://testserver")
    response = client.get("/api/leads", headers={"Cookie": f"{owner_auth.SESSION_COOKIE}={token}"})
    assert response.status_code == 200


def test_owner_session_requires_csrf_and_same_origin_for_mutations(monkeypatch):
    configure_owner(monkeypatch)
    token, csrf = make_session()
    client = TestClient(main.app, base_url="https://testserver")
    cookie = f"{owner_auth.SESSION_COOKIE}={token}"
    payload = {"name": "Owner Auth Test", "email": "owner-auth-test@example.invalid",
               "service": "AI Website"}

    missing_csrf = client.post("/api/leads", json=payload,
                               headers={"Cookie": cookie, "Origin": "https://ghostcorpnet.com"})
    assert missing_csrf.status_code == 403

    wrong_origin = client.post("/api/leads", json=payload,
                               headers={"Cookie": cookie, "Origin": "https://evil.example",
                                        "X-CSRF-Token": csrf})
    assert wrong_origin.status_code == 403


def test_owner_session_rejects_expired_or_wrong_identity(monkeypatch):
    configure_owner(monkeypatch)
    expired = owner_auth._sign({"sub": "koalstingkdelaney-gif", "csrf": "x",
                                "exp": int(time.time()) - 1},
                               "test-session-secret-that-is-long-enough")
    assert owner_auth.read_session(expired) is None
    wrong_user = owner_auth._sign({"sub": "someone-else", "csrf": "x",
                                   "exp": int(time.time()) + 600},
                                  "test-session-secret-that-is-long-enough")
    assert owner_auth.read_session(wrong_user) is None

class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeGitHubClient:
    email_payload = [{"email": "owner@example.com", "verified": True, "primary": True}]

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, **kwargs):
        return FakeResponse({"access_token": "short-lived-test-token"})

    def get(self, url, **kwargs):
        if url.endswith("/user/emails"):
            return FakeResponse(self.email_payload)
        return FakeResponse({"login": "koalstingkdelaney-gif"})


def test_github_oauth_requires_matching_verified_owner_email(monkeypatch):
    from urllib.parse import parse_qs, urlsplit

    configure_owner(monkeypatch)
    monkeypatch.setattr(owner_auth.httpx, "Client", FakeGitHubClient)
    _, state_cookie = owner_auth.issue_state()
    state = parse_qs(urlsplit(owner_auth.issue_state()[0]).query)["state"][0]
    session, csrf = owner_auth.complete_login("authorization-code", state, state_cookie)
    parsed = owner_auth.read_session(session)
    assert parsed["sub"] == "koalstingkdelaney-gif"
    assert parsed["csrf"] == csrf


def test_github_oauth_rejects_unverified_owner_email(monkeypatch):
    from urllib.parse import parse_qs, urlsplit

    configure_owner(monkeypatch)
    FakeGitHubClient.email_payload = [
        {"email": "owner@example.com", "verified": False, "primary": True}
    ]
    monkeypatch.setattr(owner_auth.httpx, "Client", FakeGitHubClient)
    authorize_url, state_cookie = owner_auth.issue_state()
    state = parse_qs(urlsplit(authorize_url).query)["state"][0]
    with pytest.raises(PermissionError, match="verified owner email"):
        owner_auth.complete_login("authorization-code", state, state_cookie)
    FakeGitHubClient.email_payload = [
        {"email": "owner@example.com", "verified": True, "primary": True}
    ]
