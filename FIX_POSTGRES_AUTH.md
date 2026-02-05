## Fix PostgreSQL Authentication Error

Your server is running but PostgreSQL authentication is failing. Here's how to fix it:

### Step 1: Reset PostgreSQL Password

Open PowerShell or Command Prompt and connect to PostgreSQL:

```bash
psql -U postgres
```

If you get prompted for a password and it fails, you need to reset it. In PostgreSQL prompt:

```sql
ALTER USER postgres WITH PASSWORD 'postgres';
\q
```

### Step 2: Update .env File

Make sure your `.env` file has the correct credentials:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vehicle_detection
FLASK_ENV=development
```

**Note:** Update `postgres` password if you changed it in Step 1.

### Step 3: Verify Database Exists

In PostgreSQL, check if the database exists:

```bash
psql -U postgres -l
```

You should see `vehicle_detection` in the list.

If not, create it:

```bash
psql -U postgres
CREATE DATABASE vehicle_detection;
\q
```

### Step 4: Restart the Server

Kill the current process:

```bash
# In PowerShell
Get-Process python | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
```

Start the server again:

```bash
cd c:\vehicle-detection
python anpr_server_combined.py
```

### Step 5: Test Connection

Once running, test with:

```bash
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/health1
```

You should see:
```json
{"status": "healthy", "camera": "camera1", "vehicle_count": 0, "database": "PostgreSQL"}
```

### Troubleshooting

**Error: "password authentication failed"**
- Check your password in .env matches PostgreSQL
- Reset password: `ALTER USER postgres WITH PASSWORD 'postgres';`

**Error: "database vehicle_detection does not exist"**
- Create it: `CREATE DATABASE vehicle_detection;`

**Error: "server not running"**
- Start PostgreSQL service in Windows Services or use:
  - `pg_ctl start` (if installed in PATH)

### Dashboard Access

Once working, visit:
- **Dashboard:** http://127.0.0.1:5000/
- **Vehicle Count:** http://127.0.0.1:5000/vehicle/count
- **Camera 1 Events:** http://127.0.0.1:5000/webhook/events
- **Camera 2 Events:** http://127.0.0.1:5000/webhook/events1

### Send Test Vehicle Data

**Camera 1:**
```bash
curl -X POST http://127.0.0.1:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"Plate":"ABC123","Image":"base64_data_here"}'
```

**Camera 2:**
```bash
curl -X POST http://127.0.0.1:5000/webhook1 \
  -H "Content-Type: application/json" \
  -d '{"Plate":"XYZ789","Image":"base64_data_here"}'
```

The counts should increment and data saves to PostgreSQL!
