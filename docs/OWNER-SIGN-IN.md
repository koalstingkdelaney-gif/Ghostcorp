# Owner sign-in and account identity

## Implemented in code

The backend now supports GitHub OAuth owner sign-in with an exact account
allowlist and a separately configured, verified owner email. During the OAuth
callback it:

1. Validates a short-lived, signed OAuth state cookie.
2. Exchanges the authorization code server-side; the client secret is never
   sent to the browser.
3. Checks the returned GitHub login against `OWNER_GITHUB_LOGIN`.
4. Reads the account's email list using the `user:email` scope and requires
   `GHOSTCORP_OWNER_EMAIL` to be explicitly marked verified.
5. Issues an eight-hour HMAC-signed, Secure, HttpOnly, SameSite=Lax session
   cookie plus a CSRF token cookie.
6. Requires the CSRF token and exact configured site Origin on browser
   mutations.

No public signup grants owner access. The GitHub access token is not stored.
The owner browser Action Center and local research worker use the session
cookie; they do not store the raw federation admin secret or machine tokens.

## Private runtime configuration

Set these values only in the backend host's secret manager:

- `GITHUB_OAUTH_CLIENT_ID`
- `GITHUB_OAUTH_CLIENT_SECRET`
- `OWNER_GITHUB_LOGIN` — exact owner GitHub login
- `GHOSTCORP_OWNER_EMAIL` — exact verified email on that GitHub account
- `OWNER_SESSION_SECRET` — long random HMAC secret
- `GITHUB_OAUTH_REDIRECT_URI` — exact callback URL
- `GHOSTCORP_SITE_ORIGIN` — exact HTTPS origin, currently intended as
  `https://ghostcorpnet.com`
- `FEDERATION_ADMIN_TOKEN` — separate server/admin credential; never expose
  it to browser JavaScript

Register a GitHub OAuth App with the callback URI exactly matching
`GITHUB_OAUTH_REDIRECT_URI`. The requested OAuth scopes are `read:user`
and `user:email`. Do not paste any secret into a chat or commit it to Git.

## Deployment requirement

The static website and backend must be routed through a same-origin HTTPS
reverse proxy for `/auth/*`, `/api/*` and `/webhooks/*`, or an equivalent
secure same-site setup with a reviewed CORS/cookie configuration. The current
browser pages use relative same-origin API paths. A static GitHub Pages site
alone cannot run FastAPI.

## Status

The OAuth/session code and tests are in the backend repository. No OAuth App,
client secret, owner email environment setting, production callback, backend
host, reverse proxy or live browser sign-in has been configured or tested.
Therefore owner sign-in is **implemented in code but not activated or
deployed**. It is not yet a verified live login.
