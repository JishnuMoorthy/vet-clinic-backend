# vet-clinic-backend

FastAPI backend for the Mia VMS veterinary clinic management system, backed by Supabase.

## Multi-Clinic Roadmap

### Current state
The backend is already **multi-clinic ready at the data layer**:

- `clinic_id` is present on `users`, `pet_owners`, `pets`, `appointments`, `medical_records`, `invoices`, `inventory`, and `services`.
- The JWT issued at login embeds `clinic_id` (see `app/routes/auth.py` — the token payload includes `sub`, `email`, `role`, `clinic_id`).
- Every route reads `clinic_id` from `current_user` (via `get_current_user` in `app/auth.py`) and filters **all** queries by it. See `app/routes/owners.py`, `app/routes/pets.py`, `app/routes/services.py`, etc.
- Data is fully isolated per clinic today. A user logged into Clinic A cannot see Clinic B's records.

### What works today
- Each staff user belongs to **exactly one** clinic via the `users.clinic_id` column.
- Login is role-based (`admin`, `vet`, `staff`) and clinic-scoped automatically through the JWT.
- No code change is needed to spin up additional clinics — insert a row in `clinics`, create users with that `clinic_id`, and they'll see only their own data.

### To support multiple clinics per user
If a single user (e.g. a vet who rounds at two clinics) needs to switch between clinics:

1. **Add a join table** `clinic_memberships(user_id, clinic_id, role)` and backfill from `users.clinic_id`.
2. **Login response**: return the user's list of clinics. Frontend shows a clinic picker after authentication.
3. **Re-issue JWT** with the selected `clinic_id` when the user switches clinics. Do not trust a `clinic_id` from the request body.
4. **Add endpoint** `GET /clinics/mine` that returns the clinics the current token grants access to.
5. Frontend caches should be keyed by `clinic_id` so switching clears stale data.

### To support public self-serve signup for new clinics
If you want new clinics to register themselves (SaaS-style):

1. `POST /clinics` — creates a clinic row.
2. `POST /auth/signup` — creates an admin user and links to the new clinic.
3. Email-invite flow for staff: generate a single-use token tied to `(clinic_id, role, email)`, accept it at `POST /auth/accept-invite`.
4. Per-clinic branding: store `logo_url`, `primary_color`, `address`, `license_number` on the `clinics` row; surface them on invoices and the login screen.
5. Billing/plan limits: consider a `subscription_tier` column if clinics need feature gating.

### Security notes for multi-tenant expansion
- The backend uses Supabase's **service-role key** and bypasses RLS, so multi-tenant isolation is enforced **only** by `clinic_id` filters in the FastAPI routes. Any new route MUST include the filter.
- Never accept `clinic_id` from the request body or URL — always read it from `current_user["clinic_id"]`.
- If you ever expose the Supabase anon key to clients again, you must re-enable RLS policies with `clinic_id = auth.jwt() ->> 'clinic_id'` as a second line of defense.
