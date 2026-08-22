## Backend authentication

The lender portal uses password authentication:

- New users enter full name, email, and password to create an account.
- Returning users sign in with email and password.
- The authenticated profile name is returned to the dashboard.

For Supabase-backed accounts, copy `.env.example` to `.env` and add `SUPABASE_URL` and `SUPABASE_KEY`. Without Supabase credentials, the API uses an in-memory development store.

Start the API with:

```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
