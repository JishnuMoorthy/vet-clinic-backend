# Vet Clinic VMS Backend - Setup Guide

Complete step-by-step guide to get the backend running.

## Prerequisites

- Python 3.8+
- Git
- Supabase account with a project created

## Step 1: Clone the Repository

```bash
git clone https://github.com/JishnuMoorthy/vet-clinic-backend.git
cd vet-clinic-backend
```

## Step 2: Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Configure Supabase Database

### 4.1 Create Database Schema

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor** (left sidebar)
3. Click **"New Query"**
4. Copy the entire content from `migrations/001_create_schema.sql`
5. Paste it into the SQL editor
6. Click **"Run"** to execute

You should see: **Query successful: 23 rows affected**

### 4.2 Verify Tables Created

After running the migration, verify in the **Table Editor** that these tables exist:
- clinics
- users
- pet_owners
- pets
- appointments
- medical_records
- medicines
- prescriptions
- invoices
- payments
- inventory
- reminder_logs
- message_logs

## Step 5: Configure Environment Variables

### 5.1 Get Supabase Credentials

1. In Supabase dashboard, go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (under "Project API keys")
   - **Anon Key** (public key)
   - **Service Role Key** (secret key)

### 5.2 Create `.env` File

```bash
# Copy the example file
cp .env.example .env
```

### 5.3 Edit `.env` with Your Credentials

```env
# Supabase Configuration
SUPABASE_URL=https://ogmywbnbcurwhkpuqhku.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# JWT Configuration
JWT_SECRET=generate-a-random-string-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=Vet Clinic VMS
```

**Generate JWT_SECRET:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 6: Start the Backend Server

```bash
# Run with auto-reload for development
python -m uvicorn app.main:app --reload

# Or with explicit host/port
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
✅ Application started successfully
```

## Step 7: Verify Backend is Running

### Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "message": "Vet Clinic VMS API is running",
  "version": "1.0.0"
}
```

### Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Step 8: Add Test Data (Optional)

Once the backend is running, you can add test data via Supabase SQL editor:

```sql
-- Insert test clinic
INSERT INTO clinics (name, email, phone, address)
VALUES ('Paws Care Clinic', 'admin@pawscare.com', '+1-234-567-8900', '123 Pet Street, Animal City');

-- Insert test user (admin)
INSERT INTO users (clinic_id, email, name, password_hash, role)
VALUES (
  (SELECT id FROM clinics LIMIT 1),
  'admin@pawscare.com',
  'Admin User',
  'hashed_password_here',
  'admin'
);
```

## Troubleshooting

### Database Connection Error

**Error**: `Database initialization failed`

**Solution**:
1. Verify `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`
2. Check that migration SQL was executed in Supabase
3. Ensure your Supabase project is active

### Python/Virtual Environment Issues

**Error**: `Command not found: python`

**Solution**:
```bash
# Use python3 instead
python3 -m venv venv
source venv/bin/activate
```

### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Use different port
python -m uvicorn app.main:app --port 8001
```

## Next Steps

1. ✅ Backend running locally
2. ⏳ Build API endpoints (pets, appointments, invoices, etc.)
3. ⏳ Implement authentication
4. ⏳ Add role-based access control
5. ⏳ Integration with frontend

## Support

For issues or questions, refer to:
- FastAPI docs: https://fastapi.tiangolo.com/
- Supabase docs: https://supabase.com/docs
- Pydantic docs: https://docs.pydantic.dev/
