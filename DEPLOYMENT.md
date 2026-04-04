# Smart Bookmark Manager V1 — Deployment Guide for Ubuntu 24.04 VM

This guide walks you through deploying the Smart Bookmark Manager V1 on a university Ubuntu 24.04 VM from scratch.

---

## Overview

The application consists of **4 Docker containers**:

| Container | Service | Port (default) |
|-----------|---------|----------------|
| `bookmark-postgres` | PostgreSQL 16 database | 5432 |
| `bookmark-qwen-code-api` | Qwen LLM proxy (OpenAI-compatible) | 8080 |
| `bookmark-backend` | FastAPI REST API | 8000 |
| `bookmark-frontend` | React SPA (Nginx) | 80 |

---

## Step 1: Install Docker and Docker Compose

SSH into your VM and run:

```bash
# Update package list
sudo apt update -y

# Install Docker
sudo apt install -y docker.io

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose plugin (v2)
sudo apt install -y docker-compose-v2

# Add your user to the docker group (run without sudo)
sudo usermod -aG docker $USER

# Apply group change (or log out and back in)
newgrp docker

# Verify installation
docker --version
docker compose version
```

---

## Step 2: Set Up Qwen OAuth Credentials

The `qwen-code-api` container needs OAuth credentials to talk to the Qwen LLM service.

### Option A: Copy credentials from your local machine

If you already have Qwen Code configured locally:

```bash
# On your LOCAL machine, copy the credentials directory to the VM
scp -r ~/.qwen user@your-vm-ip:~/.qwen

# On the VM, verify the file exists
ls -la ~/.qwen/oauth_creds.json
```

### Option B: Generate credentials on the VM

```bash
# Install Qwen Code CLI (if available on the VM)
# Then run the login flow to generate OAuth credentials
qwen login

# Verify the file was created
cat ~/.qwen/oauth_creds.json
```

### Option C: Manual credentials file creation

If you have the OAuth tokens from the Qwen developer portal:

```bash
mkdir -p ~/.qwen

cat > ~/.qwen/oauth_creds.json << 'EOF'
{
  "accessToken": "YOUR_ACCESS_TOKEN",
  "refreshToken": "YOUR_REFRESH_TOKEN",
  "expiresAt": 1735689600000
}
EOF

chmod 600 ~/.qwen/oauth_creds.json
```

> **Important**: The file `~/.qwen/oauth_creds.json` **must exist on the VM** before starting Docker containers. It will be mounted read-only into the `qwen-code-api` container.

---

## Step 3: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/se-toolkit-hackathon.git
cd se-toolkit-hackathon

# Initialize the qwen-code-api git submodule
git submodule update --init --recursive

# Verify submodule is populated
ls qwen-code-api/Dockerfile
```

---

## Step 4: Configure Environment Variables

```bash
# Copy the environment template
cp .env.example .env

# Open for editing
nano .env
```

Replace the contents with your actual values. **Minimum required changes**:

```bash
# ─────────────────────────────────────────
# CHANGE THIS — generate a random secret
# ─────────────────────────────────────────
JWT_SECRET_KEY=$(openssl rand -base64 32)
# Run this command in your terminal and paste the output here:
JWT_SECRET_KEY=YOUR_GENERATED_SECRET_STRING_HERE

# ─────────────────────────────────────────
# Qwen Code API — model to use
# ─────────────────────────────────────────
QWEN_CODE_API_MODEL=qwen-plus
QWEN_CODE_API_AUTH_USE=true
QWEN_CODE_API_LOG_LEVEL=error

# ─────────────────────────────────────────
# CORS — add your VM's public IP or domain
# ─────────────────────────────────────────
# If accessing via IP (e.g., http://10.0.0.5):
CORS_ORIGINS=http://10.0.0.5,http://localhost:80,http://localhost:5173
# If you have a domain (e.g., http://bookmarks.example.com):
# CORS_ORIGINS=http://bookmarks.example.com,http://localhost:80
```

To find your VM's IP:
```bash
hostname -I | awk '{print $1}'
```

---

## Step 5: Build and Start All Services

```bash
# Build images and start containers in detached mode
docker compose up -d --build
```

This command:
1. Builds the `qwen-code-api` image from the submodule
2. Builds the `backend` FastAPI image
3. Builds the `frontend` React + Nginx image
4. Pulls the `postgres:16-alpine` image
5. Starts all 4 containers in correct order

Expected output:
```
✔ Network bookmark-network        Created
✔ Container bookmark-postgres     Started (healthy)
✔ Container bookmark-qwen-code-api Started
✔ Container bookmark-backend      Started
✔ Container bookmark-frontend     Started
```

---

## Step 6: Verify All Services Are Running

```bash
# Check container status — all 4 should show "Up"
docker compose ps
```

Expected output:
```
NAME                         IMAGE                      STATUS
bookmark-postgres            postgres:16-alpine         Up (healthy)
bookmark-qwen-code-api       se-toolkit-qwen-code-api   Up
bookmark-backend             se-toolkit-backend         Up
bookmark-frontend            se-toolkit-frontend        Up
```

### Run health checks:

```bash
# Backend health
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"Smart Bookmark Manager"}

# Frontend (should return HTML)
curl -s http://localhost:80 | head -5

# qwen-code-api health (may need API key header if configured)
curl http://localhost:8080/health
# Expected: {"status":"ok"}

# PostgreSQL connectivity
docker compose exec postgres pg_isready -U bookmarks_user
# Expected: accepting connections
```

### Run automated tests:

```bash
chmod +x test.sh
./test.sh
```

Expected output:
```
=========================================
Smart Bookmark Manager - Component Tests
=========================================

Test 1: Backend health check... PASS
Test 2: Frontend accessible... PASS
Test 3: Register new user... PASS
Test 4: Login with registered user... PASS
Test 5: List bookmarks (empty)... PASS

=========================================
Results: 5 passed, 0 failed
=========================================
```

---

## Step 7: Access the Application

Open your browser and navigate to:

```
http://YOUR_VM_IP
```

or if you changed the frontend port in `.env`:

```
http://YOUR_VM_IP:FRONTEND_PORT
```

### Test the full workflow:

1. **Register** — click "Register", enter email, username, password
2. **Add a bookmark** — paste any URL (e.g., `https://docs.python.org/3/`) and click "Save Bookmark"
3. **Wait 5-15 seconds** — the backend fetches the page and sends it to Qwen LLM for analysis
4. **See the result** — a card appears with auto-generated title, summary, tags, and category
5. **Add more bookmarks** — try URLs from different categories to see varied results
6. **Filter by category** — use the filter buttons to narrow down

---

## Step 8: Check Logs (for debugging)

```bash
# View all logs in real-time
docker compose logs -f

# View only backend logs
docker compose logs -f backend

# View only qwen-code-api logs
docker compose logs -f qwen-code-api

# View only PostgreSQL logs
docker compose logs -f postgres

# View only frontend (Nginx) access logs
docker compose logs -f frontend
```

### Common log indicators:

| Log message | Meaning |
|-------------|---------|
| `Database initialized successfully` | Backend connected to PostgreSQL |
| `INFO: Uvicorn running on http://0.0.0.0:8000` | Backend is ready |
| `LLM analysis failed` | qwen-code-api issue — check OAuth credentials |
| `pg_isready: accepting connections` | PostgreSQL is healthy |

---

## Troubleshooting

### Port already in use

```bash
# Check what's using the port
sudo lsof -i :80
sudo lsof -i :8000
sudo lsof -i :5432
sudo lsof -i :8080

# Stop conflicting services (e.g., Apache on port 80)
sudo systemctl stop apache2

# Or change the port in .env:
FRONTEND_HOST_PORT=8080
BACKEND_HOST_PORT=9000

# Then restart
docker compose down
docker compose up -d --build
```

### qwen-code-api health check failing

```bash
# Check logs
docker compose logs qwen-code-api

# Common causes:
# 1. ~/.qwen/oauth_creds.json does not exist
# 2. File has invalid JSON
# 3. Token is expired

# Verify the file on the VM:
cat ~/.qwen/oauth_creds.json | python3 -m json.tool
```

### Backend can't reach qwen-code-api

```bash
# Test from inside the backend container
docker compose exec backend curl -s http://qwen-code-api:8080/health

# Expected: {"status":"ok"}
# If fails: check that both containers are on the same network
docker compose exec backend cat /etc/hosts
docker network inspect se-toolkit-hackathon_bookmark-network
```

### Database errors on restart

```bash
# Check if PostgreSQL volume is intact
docker volume inspect se-toolkit-hackathon_postgres_data

# Re-initialize (WARNING: deletes all data):
docker compose down -v
docker compose up -d --build
```

### CORS errors in browser console

```bash
# Add your VM IP/domain to CORS_ORIGINS in .env
nano .env
# Update: CORS_ORIGINS=http://YOUR_IP,http://localhost:80

# Restart backend
docker compose restart backend
```

### Container stuck in "starting" state

```bash
# Force rebuild without cache
docker compose build --no-cache
docker compose up -d
```

---

## Managing the Application

### Stop the application

```bash
docker compose down
```

### Stop and remove all data (fresh start)

```bash
docker compose down -v
```

### Restart a single service

```bash
docker compose restart backend
```

### Update the application

```bash
cd ~/se-toolkit-hackathon
git pull
git submodule update --init --recursive
docker compose up -d --build
```

### View disk usage

```bash
docker system df
docker compose ls
```

### Clean up unused Docker resources

```bash
docker system prune -f
docker volume prune -f
```

---

## Firewall Configuration

If your VM has a firewall (UFW):

```bash
# Allow HTTP traffic
sudo ufw allow 80/tcp

# Allow backend API (if needed for external access)
sudo ufw allow 8000/tcp

# Verify rules
sudo ufw status
```

---

## What's Deployed

After successful deployment, you have:

1. **Web UI** at `http://YOUR_VM_IP` — React SPA for managing bookmarks
2. **REST API** at `http://YOUR_VM_IP:8000` — FastAPI with `/docs` for interactive testing
3. **PostgreSQL** on port 5432 — persistent bookmark data
4. **Qwen LLM Proxy** on port 8080 — handles AI analysis requests

### API Documentation

Once deployed, visit `http://YOUR_VM_IP:8000/docs` for the interactive Swagger UI where you can:
- Test all API endpoints
- See request/response schemas
- Authenticate with JWT and try bookmark CRUD operations

---

## Next Steps (Version 2)

After V1 is verified working:

1. Add natural language search with pgvector
2. Add collections/folders for bookmarks
3. Add import/export functionality
4. Deploy behind HTTPS with a domain name
5. Record the 2-minute demo video
