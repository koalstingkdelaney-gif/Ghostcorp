"""Optional GitHub OAuth owner sessions.

The OAuth application and owner allowlist are configured only in the hosting
secret manager. Sessions are signed, short-lived, HttpOnly cookies. Browser
mutations require a matching CSRF header and same-origin request.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from urllib.parse import urlencode

import httpx

SESSION_COOKIE = "ghostcorp_owner_session"
CSRF_COOKIE = "ghostcorp_owner_csrf"
SESSION_TTL = 8 * 60 * 60
STATE_TTL = 10 * 60


class OwnerAuthUnavailable(RuntimeError):
    pass


def _settings():
    return {
        "client_id": os.environ.get("GITHUB_OAUTH_CLIENT_ID", ""),
        "client_secret": os.environ.get("GITHUB_OAUTH_CLIENT_SECRET", ""),
        "owner_login": os.environ.get("OWNER_GITHUB_LOGIN", "").strip().lower(),
        "owner_email": os.environ.get("GHOSTCORP_OWNER_EMAIL", "").strip().lower(),
        "session_secret": os.environ.get("OWNER_SESSION_SECRET", ""),
        "redirect_uri": os.environ.get("GITHUB_OAUTH_REDIRECT_URI", ""),
        "site_origin": os.environ.get("GHOSTCORP_SITE_ORIGIN", "").rstrip("/"),
    }


def configured() -> bool:
    s = _settings()
    return all(s[k] for k in ("client_id", "client_secret", "owner_login", "owner_email",
                               "session_secret", "redirect_uri", "site_origin"))


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _sign(payload: dict, secret: str) -> str:
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    return body + "." + signature


def _verify(token: str, secret: str) -> dict | None:
    try:
        body, signature = token.split(".", 1)
        expected = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(_unb64(body))
        if not isinstance(payload, dict) or int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def issue_state() -> tuple[str, str]:
    s = _settings()
    if not configured():
        raise OwnerAuthUnavailable("GitHub OAuth owner sign-in is not configured")
    state = secrets.token_urlsafe(32)
    cookie = _sign({"state": state, "exp": int(time.time()) + STATE_TTL}, s["session_secret"])
    params = {
        "client_id": s["client_id"],
        "redirect_uri": s["redirect_uri"],
        "scope": "read:user user:email",
        "state": state,
        "allow_signup": "false",
    }
    return "https://github.com/login/oauth/authorize?" + urlencode(params), cookie


def complete_login(code: str, state: str, state_cookie: str) -> tuple[str, str]:
    s = _settings()
    if not configured():
        raise OwnerAuthUnavailable("GitHub OAuth owner sign-in is not configured")
    state_data = _verify(state_cookie, s["session_secret"])
    if not state_data or not hmac.compare_digest(str(state_data.get("state", "")), state):
        raise ValueError("OAuth state validation failed")
    if not code or len(code) > 2048:
        raise ValueError("invalid OAuth authorization code")
    with httpx.Client(timeout=12.0, follow_redirects=False) as client:
        token_response = client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={"client_id": s["client_id"], "client_secret": s["client_secret"],
                  "code": code, "redirect_uri": s["redirect_uri"], "state": state},
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise ValueError("GitHub did not issue an access token")
        user_response = client.get(
            "https://api.github.com/user",
            headers={"Authorization": "Bearer " + access_token,
                     "Accept": "application/vnd.github+json"},
        )
        user_response.raise_for_status()
        user = user_response.json()
        emails_response = client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": "Bearer " + access_token,
                     "Accept": "application/vnd.github+json"},
        )
        emails_response.raise_for_status()
        emails = emails_response.json()
    login = str(user.get("login", "")).lower()
    verified_owner_email = any(
        isinstance(item, dict)
        and str(item.get("email", "")).lower() == s["owner_email"]
        and item.get("verified") is True
        for item in emails if isinstance(emails, list)
    )
    if not login or not hmac.compare_digest(login, s["owner_login"]) or not verified_owner_email:
        raise PermissionError("the GitHub account and verified owner email do not match the configured owner")
    csrf = secrets.token_urlsafe(32)
    session = _sign({"sub": login, "csrf": csrf,
                     "exp": int(time.time()) + SESSION_TTL}, s["session_secret"])
    return session, csrf


def read_session(cookie: str) -> dict | None:
    s = _settings()
    if not configured() or not cookie:
        return None
    data = _verify(cookie, s["session_secret"])
    if not data or data.get("sub") != s["owner_login"] or not data.get("csrf"):
        return None
    return data


def site_origin() -> str:
    return _settings()["site_origin"]
