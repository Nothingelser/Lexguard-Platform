# Lexguard-Platform

Multi-jurisdictional police case management for the **Coast Region** (multi-county) — INSY 492 Senior Project.

## Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 5 (Python) |
| Frontend | Django Templates + HTMX + Tailwind CSS (CDN) |
| Charts | Chart.js (CDN) |
| Database | SQLite (local) or PostgreSQL / Supabase (production) |

## Features (starter scaffold)

- **Station workspace** — case registration, MO tag matrix, suspect linking by National ID
- **Tenant isolation** — officers scoped to `{station_id}`; command accounts are read-only
- **Centralized suspect directory** — deduplication via unique `national_id`
- **Command console** — precinct performance metrics, county crime charts, deterministic MO pattern matching

## Quick start

```powershell
cd C:\Users\JAYSON\Projects\lexguard-platform
python -m venv .venv
```

**Activate the venv** (pick one):

```powershell
# Option A — bypass PowerShell script policy for this session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\activate

# Option B — skip activate; call venv python directly
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python manage.py makemigrations
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py seed_demo
.venv\Scripts\python manage.py runserver
```

If you already ran `migrate` before app migrations existed, delete `db.sqlite3` and run `migrate` + `seed_demo` again.

```powershell
pip install -r requirements.txt
copy env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000 and sign in:

| Role | Username | Password |
|------|----------|----------|
| Role | Username | Password | Jurisdiction |
|------|----------|----------|--------------|
| Officer (Mombasa) | `officer1` | `demo1234` | Mvita · MSA-MVT |
| Officer (Mombasa) | `officer2` | `demo1234` | Nyali · MSA-NYL |
| Officer (Kilifi) | `officer3` | `demo1234` | Kilifi · KLF-KIL |
| Officer (Lamu) | `officer5` | `demo1234` | Lamu · LAM-LAM |
| Officer (Taita Taveta) | `officer6` | `demo1234` | Voi · TTV-VOI |
| Officer (Tana River) | `officer7` | `demo1234` | Hola · TNR-HOL |
| Regional Commander | `commander` | `demo1234` | Coast Region (60 precincts) |

## Super Admin Workflow

LexGuard does not expose public sign-up. Create privileged accounts from the server CLI:

```powershell
python manage.py bootstrap_super_admin --username rootadmin --badge-number CST-ROOT-0001 --password "StrongPass123!"
python manage.py provision_officer --station MSA-MVT --first-name Amina --last-name Njoroge --password "TempPass123!"
python manage.py lock_account --username compromised_user
```

The super admin account lands in Django's built-in admin panel after login.

Login uses the badge number, not the username. Officer and commander accounts created through the admin screen or CLI start with a temporary password and are forced to change it on first login.

## Project layout

```
config/           Django settings & URLs
apps/accounts/    Custom user model, auth, tenant middleware
apps/stations/    Police station (tenant) registry
apps/cases/       Case files, MO tags, witnesses, audit log
apps/suspects/    Centralized suspect directory
apps/analytics/   Pattern matcher & command dashboards
templates/        HTMX-ready UI templates
```

## Supabase / PostgreSQL

Set `DATABASE_URL` in `.env`:

```
DATABASE_URL=postgresql://user:password@db.xxxx.supabase.co:5432/postgres
```

Then run `python manage.py migrate` and `python manage.py seed_demo`.

## Next steps for your proposal

1. Wire Vercel deployment (WSGI via serverless adapter or use Railway/Render for Django)
2. Add PDF/CSV export on the command console
3. Expand witness & evidence modules in the station UI
4. Harden audit logging and role permissions for production
