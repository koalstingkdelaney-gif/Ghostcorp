# Owner sign-in and account identity

## Requested owner account

The requested owner sign-in address is supplied by the owner in the private setup conversation. Do not commit the address itself to this public repository, embed it in frontend JavaScript, or print it in logs.

When a supported authentication provider and production host are selected, configure the owner address as a private deployment secret named GHOSTCORP_OWNER_EMAIL. The authentication provider must verify control of that mailbox (for example, by a one-time sign-in link or code). An email address written into configuration is not proof of ownership.

## Required sign-in behavior

- Owner-only access to private GhostCorp business operations and the private VR command environment.
- Verified email sign-in with secure session cookies, CSRF protection, session expiry and revocation.
- No public signup that grants owner privileges.
- No owner email, password, access token, admin token or machine token in Git, browser source, local storage or public VR assets.
- Recovery must use the identity provider's verified recovery process.
- Public games and social spaces remain separated from private business data, bots, customer records, finances and owner controls.

## Current status

The existing ghostcorpnet-site repository is a static website. The backend repository currently has token-protected federation administration endpoints, but no production owner email authentication or website-to-backend session bridge is deployed. Do not describe the requested address as an active login until an authentication provider is configured, mailbox ownership is verified, the callback domain is configured and a live sign-in is tested.

## Cost policy

Use a provider-supported free tier only if its current limits meet the actual workload. Keep paid spend at $0 by default, prevent automatic upgrades and fail closed when free quotas are exhausted. Free tiers and hosted services can change or impose limits; no always-on hosting or email delivery should be promised as permanently free.
