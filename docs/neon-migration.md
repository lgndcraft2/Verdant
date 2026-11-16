# Neon migration

Set `DATABASE_URL` to a Neon Postgres connection string with TLS and set a
random `JWT_SECRET` of at least 32 characters on the API host. Run
`python neon/migrate.py` once before starting the API. The API checks its
database connection at startup and rejects writes when Neon is unavailable.

The dashboard needs `VERDANT_API_URL` (or `NEXT_PUBLIC_API_URL`) pointing
to the API. Its sign-in flow stores the app JWT in an HTTP-only cookie. Remove
the old Supabase variables from both deployment environments.

Register an account in the dashboard, then promote the intended provider-key
administrator with `python neon/promote_admin.py email@example.com`.
Only that role can edit the shared Anthropic and Gemini credentials. Users
must register again because Supabase Auth sessions and passwords are not
accepted by the new auth service.

Existing Supabase rows are **not transferred** by the schema command.
The old audit table has no owner field, so there is no safe automatic way
to assign historic decisions to new users. Export and map those rows with
the account owners before importing them. Keep the old database available
until that mapping and import are reviewed and verified. API keys from the
old database also need to be reissued from the new dashboard.
