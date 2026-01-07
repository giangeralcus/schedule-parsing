# Supabase Docker Setup (Offline Mode)

## Quick Start

### 1. Install Docker Desktop
- Windows: https://docs.docker.com/desktop/install/windows-install/
- macOS: https://docs.docker.com/desktop/install/mac-install/

### 2. Clone Supabase Docker

```bash
# Clone only docker folder
git clone --depth 1 https://github.com/supabase/supabase
cd supabase/docker

# Copy environment file
cp .env.example .env
```

### 3. Start Supabase

```bash
docker compose up -d
```

### 4. Access Points

| Service | URL |
|---------|-----|
| Studio (Dashboard) | http://localhost:54323 |
| API | http://localhost:54321 |
| Database | localhost:54322 |

### 5. Run Migration

Open Studio: http://localhost:54323/project/default/sql/new

Paste the SQL from `migrations/001_create_vessels_tables.sql` and run.

### 6. Default Credentials

```env
# Docker default anon key (same for all local instances)
SUPABASE_DOCKER_URL=http://localhost:54321
SUPABASE_DOCKER_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
```

---

## Sync Workflow

### Scenario 1: Work Offline, Sync Later

```
1. Start Docker Supabase (offline)
2. Use Schedule Parser → auto-learns new vessels
3. When back online:

   from core.vessel_db import get_vessel_db
   db = get_vessel_db()
   db.sync("docker_to_cloud")  # Push local changes to cloud
```

### Scenario 2: Get Latest from Cloud

```
1. Connect to internet
2. Run sync:

   from core.vessel_db import get_vessel_db
   db = get_vessel_db()
   db.sync("cloud_to_docker")  # Pull cloud data to local
```

---

## Commands

### Start Docker
```bash
cd supabase/docker
docker compose up -d
```

### Stop Docker
```bash
docker compose down
```

### Check Status
```bash
docker compose ps
```

### View Logs
```bash
docker compose logs -f
```

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 54321
netstat -ano | findstr :54321

# Kill the process or change port in .env
```

### Reset Database
```bash
docker compose down -v  # Remove volumes
docker compose up -d    # Fresh start
```

### Check Connection from Python
```python
from core.vessel_db import VesselDatabase
db = VesselDatabase()
print(db.get_stats())
# Should show: mode: "docker" or "cloud"
```
