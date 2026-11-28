# GhostCorp GitHub organization and product distribution

## Recommended account structure

Use a GitHub Organization as the business-owned namespace rather than creating a bot-owned personal account or sharing the owner's personal login. An organization can own repositories, control member permissions, and present a business identity. A human personal account must still create and administer it; GitHub organizations are not standalone human login accounts.

Proposed organization display name: GhostCorp. Check handle availability before choosing. No organization has been created by this repository change.

The owner should remain an organization owner, with two-factor authentication enabled. Agents should never receive the owner's password, recovery codes, personal access token, or unrestricted account session. When automated GitHub work is later enabled, use a dedicated GitHub App or narrowly scoped fine-grained credentials, limited to selected repositories and operations. Keep credentials in server-side secret storage, never in the public VR website, Git, agent prompts, dream artifacts, or browser storage.

## Repository migration

The current backend and website repositories should continue to operate in place until an owner-approved migration plan is ready:

- koalstingkdelaney-gif/Ghostcorp
- koalstingkdelaney-gif/ghostcorpnet-site

GitHub supports transferring repositories to an organization when the current owner has admin access and permission to create repositories in the target organization. Review visibility, GitHub Pages/custom-domain settings, Actions secrets, package links, deploy keys, webhooks, branch rules, and redirects before transfer. Transferring does not make the owner's personal account disappear from Git history or erase historical commit attribution. Do not promise anonymity from a repository transfer.

A safer initial step is to create the organization, add the owner account as an owner, configure private membership visibility and repository permissions, and create a new business-owned test repository. Then migrate existing repositories one at a time after checking deployment and domain continuity.

## Product sales and distribution

1. Open-source or free developer tools: public repository, README, tagged GitHub Releases, and GitHub Packages where relevant.
2. Paid GitHub integrations: GitHub Marketplace is limited to eligible GitHub Apps and Actions. Paid app plans require organization ownership, publisher verification and other eligibility/billing requirements. This is not a generic checkout for arbitrary ZIP files or services.
3. Digital downloads, templates, hosted services, and non-Marketplace products: publish source or release assets in GitHub, but sell through an approved payment provider/storefront. Verify payment with provider webhooks before unlocking delivery. Keep fulfillment, refunds, tax, and customer support records in the commerce system.

Dream agents can research, design, prototype, document, and prepare release packages. They cannot publish paid listings, change prices, promise delivery, contact customers, activate paid services, or move money without owner approval. GitHub repository access does not grant access to payment systems or customer data.

## Owner setup checklist

- Create the organization from the owner's signed-in GitHub account: https://github.com/account/organizations/new
- Choose the organization handle after checking availability and trademark/confusion risks.
- Keep the owner's account as an owner; enable two-factor authentication and recovery methods.
- Set member base permissions to the minimum needed; keep sensitive repositories private.
- Create a separate test repository and verify access before transferring production repositories.
- Review Pages/custom domain, Actions, secrets, environments, packages, webhooks, deploy keys, branch protection, and repository transfer implications.
- Only then authorize a GitHub App or scoped automation credential for selected repositories.