---
name: better-auth-best-practices
description: Configure, scaffold, or troubleshoot Better Auth in TS/JS apps. Use for auth.ts, login/sign-up pages, database adapters, sessions, plugins, OAuth, email/password, email verification, password reset, 2FA/MFA/OTP/TOTP, backup codes, organizations/teams/RBAC, or migrating from another auth library.
---

# Better Auth Integration Guide

**Always consult [better-auth.com/docs](https://better-auth.com/docs) for code examples and latest API.**

---

## Setup Workflow

1. Install: `npm install better-auth`
2. Set env vars: `BETTER_AUTH_SECRET` and `BETTER_AUTH_URL`
3. Create `auth.ts` with database + config
4. Create route handler for your framework
5. Run `npx @better-auth/cli@latest migrate`
6. Verify: call `GET /api/auth/ok` — should return `{ status: "ok" }`

---

## Implementation Planning

Before scaffolding auth in a repo, scan first and ask only for missing decisions.

Detect:

- **Framework:** `next.config`, `svelte.config`, `nuxt.config`, `astro.config`, `vite.config`, Express/Hono entry files.
- **Database/ORM:** `prisma/schema.prisma`, `drizzle.config`, `pg`, `mysql2`, `better-sqlite3`, `mongoose`, `mongodb`.
- **Existing auth:** `next-auth`, `lucia`, `clerk`, `supabase/auth`, `firebase/auth`, or existing auth imports.
- **Package manager:** `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`, `package-lock.json`.

Ask concise follow-up questions for unknowns:

- Project state: new auth setup, adding to an existing app, or migrating from another auth library.
- Framework and router style.
- Database and ORM/adapter.
- Sign-in methods: email/password, social OAuth, magic link, passkey, phone.
- OAuth providers, if social auth is needed.
- Email verification and password reset requirements.
- Extra plugins: 2FA, organizations, admin, API keys/bearer tokens.
- Auth pages needed: sign in, sign up, forgot password, reset password, email verification.
- UI direction, if creating pages.

Summarize the implementation as a short checklist before making broad changes. For small obvious fixes, proceed directly.

---

## Scaffolding Workflow

Choose the path based on project state:

| Project state | Approach                                                                                                                                        |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| New project   | Install Better Auth, create server/client config, route handler, env vars, migrations, plugins, and auth pages.                                 |
| Existing app  | Match existing structure, add Better Auth config and routes, run migrations, then integrate session checks and UI into current pages.           |
| Migration     | Audit current auth behavior, install Better Auth alongside it, migrate routes/session logic/UI incrementally, then remove the old auth library. |

At the end, call out remaining manual steps such as OAuth app credentials, production env vars, DNS/callback URL setup, and email provider configuration.

---

## Quick Reference

### Environment Variables

- `BETTER_AUTH_SECRET` - Encryption secret (min 32 chars). Generate: `openssl rand -base64 32`
- `BETTER_AUTH_URL` - Base URL (e.g., `https://example.com`)
- `DATABASE_URL` - Database connection string when the chosen adapter needs it.

Only define `baseURL`/`secret` in config if env vars are NOT set.

Add OAuth secrets as needed: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GOOGLE_CLIENT_ID`, etc.

### File Location

CLI looks for `auth.ts` in: `./`, `./lib`, `./utils`, or under `./src`. Use `--config` for custom path.

### CLI Commands

- `npx @better-auth/cli@latest migrate` - Apply schema (built-in adapter)
- `npx @better-auth/cli@latest generate` - Generate schema for Prisma/Drizzle
- `npx @better-auth/cli mcp --cursor` - Add MCP to AI tools

**Re-run after adding/changing plugins.**

---

## Core Config Options

| Option             | Notes                                          |
| ------------------ | ---------------------------------------------- |
| `appName`          | Optional display name                          |
| `baseURL`          | Only if `BETTER_AUTH_URL` not set              |
| `basePath`         | Default `/api/auth`. Set `/` for root.         |
| `secret`           | Only if `BETTER_AUTH_SECRET` not set           |
| `database`         | Required for most features. See adapters docs. |
| `secondaryStorage` | Redis/KV for sessions & rate limits            |
| `emailAndPassword` | `{ enabled: true }` to activate                |
| `socialProviders`  | `{ google: { clientId, clientSecret }, ... }`  |
| `plugins`          | Array of plugins                               |
| `trustedOrigins`   | CSRF whitelist                                 |

---

## Database

**Direct connections:** Pass `pg.Pool`, `mysql2` pool, `better-sqlite3`, or `bun:sqlite` instance.

**ORM adapters:** Import from `better-auth/adapters/drizzle`, `better-auth/adapters/prisma`, `better-auth/adapters/mongodb`.

**Critical:** Better Auth uses adapter model names, NOT underlying table names. If Prisma model is `User` mapping to table `users`, use `modelName: "user"` (Prisma reference), not `"users"`.

---

## Server Config

Default location: `lib/auth.ts`, `src/lib/auth.ts`, or another local convention already used by the app.

Minimum config:

- `database`: direct connection or adapter.
- `emailAndPassword: { enabled: true }` when email/password is needed.

Common additions:

- `socialProviders` for OAuth.
- `emailVerification.sendVerificationEmail` for verification.
- `emailAndPassword.sendResetPassword` for password reset.
- `plugins` for features such as 2FA, organizations, admin, passkeys, API keys, bearer tokens.
- `session`, `account.accountLinking`, `trustedOrigins`, and `rateLimit` for production behavior.

Export useful server types: `export type Session = typeof auth.$Infer.Session`.

---

## Route Handlers

| Framework            | File                             | Handler                                            |
| -------------------- | -------------------------------- | -------------------------------------------------- |
| Next.js App Router   | `app/api/auth/[...all]/route.ts` | `toNextJsHandler(auth)` and export `{ GET, POST }` |
| Next.js Pages Router | `pages/api/auth/[...all].ts`     | `toNextJsHandler(auth)` as default export          |
| Express              | App entry                        | `app.all("/api/auth/*", toNodeHandler(auth))`      |
| SvelteKit            | `src/hooks.server.ts`            | `svelteKitHandler(auth)`                           |
| SolidStart           | Route file                       | `solidStartHandler(auth)`                          |
| Hono                 | Route file                       | `auth.handler(c.req.raw)`                          |

For Next.js Server Components, add the `nextCookies()` plugin to the auth config.

---

## Client Config and UI

Create an auth client near the app's existing client utilities.

| Framework     | Import               |
| ------------- | -------------------- |
| React/Next.js | `better-auth/react`  |
| Vue           | `better-auth/vue`    |
| Svelte        | `better-auth/svelte` |
| Solid         | `better-auth/solid`  |
| Vanilla JS    | `better-auth/client` |

Common exports: `signIn`, `signUp`, `signOut`, `useSession`, `getSession`.

Auth UI flows:

- Sign in: `signIn.email({ email, password })` or `signIn.social({ provider, callbackURL })`.
- Sign up: `signUp.email(...)` for email/password.
- Client session check: `useSession()` returns session data and pending state.
- Server session check: `auth.api.getSession({ headers })`.
- Protected routes: check session and redirect to sign-in when absent.

Client plugins go in `createAuthClient({ plugins: [...] })` and should match the server-side plugins that expose client behavior.

---

## Session Management

**Storage priority:**

1. If `secondaryStorage` defined → sessions go there (not DB)
2. Set `session.storeSessionInDatabase: true` to also persist to DB
3. No database + `cookieCache` → fully stateless mode

**Cookie cache strategies:**

- `compact` (default) - Base64url + HMAC. Smallest.
- `jwt` - Standard JWT. Readable but signed.
- `jwe` - Encrypted. Maximum security.

**Key options:** `session.expiresIn` (default 7 days), `session.updateAge` (refresh interval), `session.cookieCache.maxAge`, `session.cookieCache.version` (change to invalidate all sessions).

---

## User & Account Config

**User:** `user.modelName`, `user.fields` (column mapping), `user.additionalFields`, `user.changeEmail.enabled` (disabled by default), `user.deleteUser.enabled` (disabled by default).

**Account:** `account.modelName`, `account.accountLinking.enabled`, `account.storeAccountCookie` (for stateless OAuth).

**Required for registration:** `email` and `name` fields.

---

## Email Flows

- `emailVerification.sendVerificationEmail` - Must be defined for verification to work
- `emailVerification.sendOnSignUp` / `sendOnSignIn` - Auto-send triggers
- `emailAndPassword.sendResetPassword` - Password reset email handler

---

## Email and Password

Enable credentials with `emailAndPassword: { enabled: true }`, configure `emailVerification.sendVerificationEmail` when verification is required, add `emailAndPassword.sendResetPassword` for reset flows, then re-run migrations/generation.

Email verification:

- `sendVerificationEmail` receives the full verification `url`; use `token` only when building a custom URL.
- `emailAndPassword.requireEmailVerification: true` blocks email/password sign-ins until verification.
- When required verification is enabled, unverified users receive a new verification email on sign-in attempts.
- This option depends on `sendVerificationEmail` and only applies to email/password sign-ins.

Callback URLs:

- Use absolute callback/redirect URLs, including origin, in sign-up, sign-in, and reset flows.
- Absolute URLs avoid bad origin inference when frontend and backend live on different domains.

Password reset:

- Provide `emailAndPassword.sendResetPassword` to send reset links.
- Use `emailAndPassword.onPasswordReset` for post-reset side effects.
- Trigger resets with `auth.api.requestPasswordReset({ body: { email, redirectTo } })` or `authClient.requestPasswordReset({ email, redirectTo })`.
- Prefer `redirectTo` so the user lands on the intended reset page.
- Reset tokens expire after 1 hour by default, are single-use, and can be shortened with `resetPasswordTokenExpiresIn`.
- Enable `revokeSessionsOnPasswordReset: true` for sensitive apps.

Password reset security:

- Better Auth uses background email sending, dummy operations for invalid requests, and constant response messages to reduce account enumeration and timing leaks.
- On serverless platforms, configure `advanced.backgroundTasks.handler` with the platform's background primitive, such as `waitUntil`.

Password policy and hashing:

- Set `minPasswordLength` and `maxPasswordLength` under `emailAndPassword` when defaults are insufficient.
- Default password hashing is `scrypt`.
- Custom algorithms can be provided with `emailAndPassword.password.hash` and `verify`.
- If changing hashing on an existing system, plan migration carefully because users with old hashes may fail sign-in unless old hashes remain verifiable.

---

## Security

**In `advanced`:**

- `useSecureCookies` - Force HTTPS cookies
- `disableCSRFCheck` - ⚠️ Security risk
- `disableOriginCheck` - ⚠️ Security risk
- `crossSubDomainCookies.enabled` - Share cookies across subdomains
- `ipAddress.ipAddressHeaders` - Custom IP headers for proxies
- `database.generateId` - Custom ID generation or `"serial"`/`"uuid"`/`false`

**Rate limiting:** `rateLimit.enabled`, `rateLimit.window`, `rateLimit.max`, `rateLimit.storage` ("memory" | "database" | "secondary-storage").

---

## Security Checklist

- `BETTER_AUTH_SECRET` is set and at least 32 chars.
- `advanced.useSecureCookies: true` is enabled in production.
- `trustedOrigins` includes deployed app origins.
- Rate limits are enabled for auth endpoints.
- Email verification and password reset are implemented when email/password auth is used.
- CSRF and origin checks are not disabled unless there is a documented, narrow reason.
- `account.accountLinking` behavior is reviewed before enabling multiple providers.
- 2FA is considered for sensitive or admin-heavy apps.

---

## Hooks

**Endpoint hooks:** `hooks.before` / `hooks.after` - Array of `{ matcher, handler }`. Use `createAuthMiddleware`. Access `ctx.path`, `ctx.context.returned` (after), `ctx.context.session`.

**Database hooks:** `databaseHooks.user.create.before/after`, same for `session`, `account`. Useful for adding default values or post-creation actions.

**Hook context (`ctx.context`):** `session`, `secret`, `authCookies`, `password.hash()`/`verify()`, `adapter`, `internalAdapter`, `generateId()`, `tables`, `baseURL`.

---

## Plugins

**Import from dedicated paths for tree-shaking:**

```ts
import { twoFactor } from "better-auth/plugins/two-factor";
```

NOT `from "better-auth/plugins"`.

**Popular plugins:** `twoFactor`, `organization`, `passkey`, `magicLink`, `emailOtp`, `username`, `phoneNumber`, `admin`, `apiKey`, `bearer`, `jwt`, `multiSession`, `sso`, `oauthProvider`, `oidcProvider`, `openAPI`, `genericOAuth`.

Client plugins go in `createAuthClient({ plugins: [...] })`.

---

## Two-Factor Plugin

Use `twoFactor()` for MFA with authenticator apps, OTP delivery, backup codes, and trusted devices.

Setup:

1. Add `twoFactor({ issuer })` to server plugins. Use the app name as issuer.
2. Add `twoFactorClient()` to client plugins.
3. Re-run the Better Auth CLI migration/generation command.
4. Verify the user schema includes 2FA fields such as `twoFactorSecret`.

```ts
import { twoFactor } from "better-auth/plugins";

export const auth = betterAuth({
  appName: "My App",
  plugins: [
    twoFactor({
      issuer: "My App",
    }),
  ],
});
```

```ts
import { twoFactorClient } from "better-auth/client/plugins";

export const authClient = createAuthClient({
  plugins: [
    twoFactorClient({
      onTwoFactorRedirect() {
        window.location.href = "/2fa";
      },
    }),
  ],
});
```

Enabling 2FA:

- `authClient.twoFactor.enable({ password })` requires password verification and returns `totpURI` plus backup codes.
- Show the `totpURI` as a QR code for authenticator apps.
- `twoFactorEnabled` is not true until first TOTP verification succeeds.
- `skipVerificationOnEnable: true` bypasses first verification, but avoid it for normal security-sensitive flows.

TOTP:

- Verify with `authClient.twoFactor.verifyTotp({ code, trustDevice })`.
- Default verification accepts adjacent time periods for clock skew.
- Configure `totpOptions.digits` and `totpOptions.period` when defaults are not appropriate.

OTP:

- Configure `otpOptions.sendOTP` for email/SMS delivery.
- Send with `authClient.twoFactor.sendOtp()`.
- Verify with `authClient.twoFactor.verifyOtp({ code, trustDevice })`.
- Configure `otpOptions.period`, `digits`, `allowedAttempts`, and `storeOTP`.
- Prefer encrypted or hashed OTP storage over plain storage; custom encrypt/decrypt functions are supported.

Backup codes:

- Generated automatically when 2FA is enabled and each code is single-use.
- Display backup codes once and tell the user to store them securely.
- Regenerate with `authClient.twoFactor.generateBackupCodes({ password })`, which invalidates previous codes.
- Verify recovery with `authClient.twoFactor.verifyBackupCode({ code, trustDevice })`.
- Configure `backupCodeOptions.amount`, `length`, and `storeBackupCodes`.

Sign-in flow:

- Call `signIn.email({ email, password })`.
- If the response has `twoFactorRedirect: true`, redirect to the 2FA verification page.
- Verify with TOTP, OTP, or backup code.
- A full session is created only after successful second-factor verification.
- Server-side sign-in should also check for `"twoFactorRedirect" in response`.

Trusted devices and session security:

- Pass `trustDevice: true` during verification when the user chooses to trust the device.
- `trustDeviceMaxAge` defaults to 30 days and refreshes on sign-in.
- Credentials create a temporary 2FA cookie after the initial session is removed; `twoFactorCookieMaxAge` defaults to 10 minutes.
- Built-in 2FA endpoint rate limiting is 3 requests per 10 seconds; OTP also has `allowedAttempts`.
- TOTP secrets are encrypted with the auth secret, backup codes are encrypted by default, and verification uses constant-time comparison.
- 2FA can only be enabled for credential/email-password accounts.
- Disabling 2FA requires password confirmation and revokes trusted device records.

---

## Organization Plugin

Use `organization()` for multi-tenant workspaces, invitations, member roles, teams, and RBAC.

Setup:

1. Add `organization()` to server plugins.
2. Add `organizationClient()` to client plugins.
3. Run the Better Auth CLI migration/generation command again.
4. Verify organization, member, invitation, and team tables exist when enabled.

```ts
import { organization } from "better-auth/plugins";

export const auth = betterAuth({
  plugins: [
    organization({
      allowUserToCreateOrganization: true,
      organizationLimit: 5,
      membershipLimit: 100,
    }),
  ],
});
```

```ts
import { createAuthClient } from "better-auth/client";
import { organizationClient } from "better-auth/client/plugins";

export const authClient = createAuthClient({
  plugins: [organizationClient()],
});
```

Key behavior:

- Creating an organization assigns the creator the `owner` role.
- `allowUserToCreateOrganization`, `organizationLimit`, and `membershipLimit` can be booleans, numbers, or policy functions based on the user/org.
- Server-side admins can create organizations for another user through `auth.api.createOrganization({ body: { name, slug, userId } })`; do not combine `userId` with session headers.
- Set an active org after selection with `authClient.organization.setActive({ organizationId })`; many member/invitation APIs use the active org when `organizationId` is omitted.
- Use `getFullOrganization()` when the UI needs organization, members, invitations, and teams together.

Members and invitations:

- Add members server-side with `auth.api.addMember({ body: { userId, role, organizationId } })`.
- For client-side member additions, prefer invitations.
- Members can have multiple roles, e.g. `role: ["admin", "moderator"]`.
- The last owner cannot be removed or demoted; transfer ownership first.
- Configure `sendInvitationEmail`, `invitationExpiresIn`, `invitationLimit`, and `cancelPendingInvitationsOnReInvite`.
- `getInvitationURL()` returns a shareable URL and does not call `sendInvitationEmail`; deliver it yourself.

Roles and permissions:

- Default roles are `owner`, `admin`, and `member`.
- Check dynamic permissions with `authClient.organization.hasPermission({ permission: "member:write" })`.
- Use static role checks only for UI rendering; enforce access with server checks or the permission endpoint.
- For custom roles, enable dynamic access control and use `createRole`, `updateRole`, and `deleteRole`. Built-in roles cannot be deleted, and assigned roles must be removed from members before deletion.

Teams:

- Enable with `organization({ teams: { enabled: true } })`.
- Create teams with `authClient.organization.createTeam({ name })`.
- Use `addTeamMember({ teamId, userId })` only after the user is already an org member.
- `removeTeamMember` removes from the team, not the organization.
- Configure `maximumTeams`, `maximumMembersPerTeam`, and `allowRemovingAllTeams` for limits.

Advanced organization options:

- Hooks can run before/after organization, member, and invitation lifecycle events. Use them for default resources, audit logs, notifications, or cleanup.
- `schema` can rename organization/member models, map fields, and add org/member metadata fields.
- `disableOrganizationDeletion: true` prevents destructive org deletion; otherwise implement archival or cleanup in hooks.
- Invitation security defaults matter: invitations expire, are email-bound, and can be canceled by admins.

---

## Client

Import from: `better-auth/client` (vanilla), `better-auth/react`, `better-auth/vue`, `better-auth/svelte`, `better-auth/solid`.

Key methods: `signUp.email()`, `signIn.email()`, `signIn.social()`, `signOut()`, `useSession()`, `getSession()`, `revokeSession()`, `revokeSessions()`.

---

## Type Safety

Infer types: `typeof auth.$Infer.Session`, `typeof auth.$Infer.Session.user`.

For separate client/server projects: `createAuthClient<typeof auth>()`.

---

## Common Gotchas

1. **Model vs table name** - Config uses ORM model name, not DB table name
2. **Plugin schema** - Re-run CLI after adding plugins
3. **Secondary storage** - Sessions go there by default, not DB
4. **Cookie cache** - Custom session fields NOT cached, always re-fetched
5. **Stateless mode** - No DB = session in cookie only, logout on cache expiry
6. **Change email flow** - Sends to current email first, then new email

---

## Troubleshooting

| Issue                             | Fix                                                                  |
| --------------------------------- | -------------------------------------------------------------------- |
| "Secret not set"                  | Add `BETTER_AUTH_SECRET`.                                            |
| "Invalid Origin"                  | Add the domain to `trustedOrigins`.                                  |
| Cookies not setting               | Check `baseURL`, deployed domain, HTTPS, and secure cookie settings. |
| OAuth callback errors             | Verify provider callback URLs and client credentials.                |
| Type errors after adding a plugin | Re-run Better Auth CLI generate/migrate commands.                    |

---

## Resources

- [Docs](https://better-auth.com/docs)
- [Options Reference](https://better-auth.com/docs/reference/options)
- [LLMs.txt](https://better-auth.com/llms.txt)
- [GitHub](https://github.com/better-auth/better-auth)
- [Init Options Source](https://github.com/better-auth/better-auth/blob/main/packages/core/src/types/init-options.ts)
