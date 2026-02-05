# PostgreSQL Setup Guide for Windows

## Option 1: Download and Install PostgreSQL (Recommended)

1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. Choose PostgreSQL 15 or 16 (latest versions)
3. Run the installer and follow these steps:
   - Set superuser password (remember this!)
   - Keep port as 5432 (default)
   - Choose locale as English
4. Complete the installation

## Option 2: Using Docker (Alternative)

If you prefer containerized PostgreSQL:
```bash
docker pull postgres
docker run --name vehicle-detection-db -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres
```

## Option 3: SQLite Alternative (No Installation Required)

For development/testing without PostgreSQL:
- Change DATABASE_URL in .env to use SQLite:
  ```
  DATABASE_URL=sqlite:///vehicle_detection.db
  ```
- SQLite works out-of-the-box with SQLAlchemy!

---

## Quick Start After Installation

Once PostgreSQL is running, create the database:

```powershell
# Connect to PostgreSQL (you'll be prompted for password)
psql -U postgres

# Then in the psql shell, run:
CREATE DATABASE vehicle_detection;
CREATE USER vehicle_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE vehicle_detection TO vehicle_user;
\q
```

Then update your `.env` file:
```
DATABASE_URL=postgresql://vehicle_user:your_secure_password@localhost:5432/vehicle_detection
```

## Quick Test

```bash
# Install Python requirements
pip install -r requirements.txt

# Run the server (it will auto-create tables)
python anpr_server.py
```

Tables will be created automatically on first run!
