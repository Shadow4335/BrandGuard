# Security notes

How accounts, passwords and demo access work, what is protected, and what still needs a decision or a dashboard setting.

## Accounts and passwords

- **Sign-in uses Supabase Auth.** Supabase stores passwords only as **bcrypt hashes**. BrandGuard never stores a password after sign-up and never logs one.
- **Sign-up goes through our API, not the browser.** The server checks the password rules, limits which roles can be chosen, rate-limits, and only then creates the user with the service role. The rules (`backend/app/passwords.py`): 10 to 128 characters, not a common password, not the product or brand name, not containing your name or email, not repetitive or digits-only. Length and unpredictability matter more than composition rules (NIST SP 800-63B).
- **Admin isn't self-service.** Admins can change the shared brand sources that every review relies on, so new accounts can only pick Creator, Manager or Reviewer (`SIGNUP_ALLOWED_ROLES`). The one-click Admin demo shows that view.
- **Roles come from the server.** Every API call takes the role and workspace from the database profile of the verified token. The browser is trusted for neither, and the UI never falls back to a role in user-editable metadata.
- **Offline demo mode** (no Supabase configured) stores PBKDF2-HMAC-SHA256 hashes with a random per-account salt and 600,000 iterations, in a format that records its parameters (`pbkdf2_sha256$iterations$salt$digest`), compared in constant time.

## Demo accounts

- The four demo users sign in through `POST /api/auth/demo-session`: **the server signs them in and returns the session tokens.** The demo password is no longer in the browser bundle, the README or the login page.
- `DEMO_MODE=false` turns this off: the endpoint returns 404 and the login page hides the demo buttons.
- The role switcher only appears while signed in as a demo user, so real accounts keep their own identity in comments and the audit trail.
- Demo accounts and real sign-ups share one fictional workspace. Don't upload confidential material.

## Abuse protection

- Per-IP limits: 5 sign-ups, 30 demo sessions and 10 password logins (offline mode) per 10 minutes. The client address is the **right-most** `X-Forwarded-For` entry, which the host's proxy adds, so a forged header can't get around the limit.
- The limits live in memory on each server instance: they reset on restart and aren't shared between instances.
- Password sign-in is also rate-limited by Supabase (Auth → Rate limits in the dashboard).

## Browser protections

`frontend/next.config.ts` sends `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy` and HSTS. There is **no** Content-Security-Policy yet: Next.js inline scripts need nonces, so add one deliberately and test it.

## Supabase dashboard settings (can't be done from the code)

1. **Authentication → Sign In / Providers: turn off "Allow new users to sign up".** The app creates users with the service role, which keeps working. If it stays on, anyone with the public anon key can create an auth user directly and skip the server's password and role rules. That user has no BrandGuard profile, so the API refuses them, but the account still exists.
2. **Password requirements:** set the minimum length to 10 (the default is 6) and, if your plan has it, turn on leaked-password protection.
3. **Rate limits:** review the sign-in and token-refresh limits.
4. **Email confirmation (optional):** sign-ups are confirmed automatically so judges can try the app straight away. For real use, turn confirmation on, set up custom SMTP (the built-in sender is heavily limited) and change `email_confirm` in `backend/app/routers/core.py`.

## Changing the demo password without breaking the live demo

1. Deploy the **backend first**, then the frontend (the new login calls `/api/auth/demo-session`).
2. Generate a secret, e.g. `openssl rand -base64 24`, and set it as `DEMO_USER_PASSWORD` on Render and in `backend/.env`.
3. Run `backend/.venv/bin/python seed/rotate_demo_passwords.py`. It refuses the old default and short values, and never prints the secret.
4. Restart or redeploy the backend if you added the variable after deploying.

## Known limitations

- **No multi-factor authentication**, and no account recovery beyond what Supabase provides.
- **Sign-up reveals whether an email is registered** ("an account with this email already exists"). Hiding that requires email confirmation to be on first.
- **Row Level Security isn't exercised.** The API uses the service-role key and enforces role and workspace checks itself; RLS is only a second layer for direct database access.
- **Emails aren't verified.** Anyone can register any address (see the dashboard settings above).
- **Shared workspace.** Real and demo accounts see the same fictional brand data.
