# Smart Bookmark Manager

AI-powered bookmark manager that automatically analyzes saved pages using Qwen LLM, generates tags, summaries, and categories — making search and navigation instant.

**Demo:** [See it in action](#) (link after deployment)

---

## Context

### End Users
Students, developers, researchers, and anyone who actively consumes web content and saves useful links for future reference.

### Problem
When saving many web links, users lose context: they forget what a page was about, struggle to find a specific bookmark among hundreds, and waste time on manual categorization and tagging.

### Solution
A smart bookmark manager that automatically analyzes saved page content using AI (Qwen LLM via qwen-code-api proxy), generates tags, summaries, and categories — making search and navigation instant.

---

## Features

### Implemented (Version 1)
- ✅ User registration and authentication (JWT)
- ✅ Save bookmarks by URL with automatic AI analysis via Qwen LLM
- ✅ Auto-generated title, summary, tags, and category
- ✅ Page thumbnail extraction (og:image)
- ✅ Filter bookmarks by category
- ✅ Delete bookmarks
- ✅ Responsive web UI with Bootstrap 5
- ✅ Docker-compose deployment with qwen-code-api container

### Planned (Version 2)
- ⏳ Natural language search (pgvector + embeddings)
- ⏳ Collections / folders
- ⏳ Manual tag editing
- ⏳ Import/Export (CSV/JSON)
- ⏳ Full-text search

---

## Architecture

```
┌──────────────────────────────────────────────┐
│        React SPA (Nginx :80)                 │
│  ┌────────┐  ┌─────────┐  ┌──────────────┐  │
│  │ Login  │  │Register │  │ BookmarkList │  │
│  │        │  │         │  │              │  │
│  └────────┘  └─────────┘  └──────────────┘  │
└───────────────────┬──────────────────────────┘
                    │ HTTP API
┌───────────────────┼──────────────────────────┐
│        FastAPI Backend (:8000)               │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │  Auth    │  │Bookmarks │  │ LLM       │  │
│  │  (JWT)   │  │  CRUD    │  │ Service   │  │
│  └──────────┘  └──────────┘  └─────┬─────┘  │
└────────────────────────────────────┼─────────┘
               │                      │ OpenAI-compatible API
┌──────────────┼──────────────┐  ┌────┼──────────────────────┐
│  PostgreSQL  │              │  │    │  qwen-code-api (:8080)│
│  (:5432)     │              │  │    │  (LLM Proxy)          │
│ ┌──────────┐ │              │  │    │  ┌───────────────┐    │
│ │  users   │ │              │  │    │  │ Qwen OAuth    │    │
│ │bookmarks │ │              │  │    │  │ (~/.qwen/)    │    │
│ └──────────┘ │              │  │    │  └───────┬───────┘    │
└──────────────┘              │  │            │               │
                              │  │            │ Forward to    │
                              │  │            ▼ Qwen API      │
                              │  │  ┌───────────────────┐     │
                              │  │  │  Qwen Cloud (LLM) │     │
                              │  │  └───────────────────┘     │
└──────────────────────────────┼──┴───────────────────────────┘
```

### Components

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| **frontend** | bookmark-frontend | 80 | React SPA served via Nginx |
| **backend** | bookmark-backend | 8000 | FastAPI REST API |
| **postgres** | bookmark-postgres | 5432 | PostgreSQL 16 database |
| **qwen-code-api** | bookmark-qwen-code-api | 8080 | Qwen LLM proxy (OpenAI-compatible) |

---

## Usage

### 1. Start the Application
```bash
docker compose up -d
```

### 2. Access the Web Interface
Open your browser and navigate to:
- **http://localhost** (production) or **http://localhost:5173** (development)

### 3. Register an Account
- Click "Register" and create an account with email, username, and password

### 4. Add Bookmarks
- Paste any URL into the input field and click "Save Bookmark"
- The AI (Qwen LLM) will analyze the page and generate:
  - Title
  - 2-3 sentence summary
  - 5 relevant tags
  - Category (tech, science, education, entertainment, news, etc.)
  - Thumbnail (if available)

### 5. Manage Bookmarks
- Filter by category using the filter buttons
- Click bookmark title to open the original page
- Delete bookmarks with the × button

---

## Deployment

### Prerequisites (Ubuntu 24.04 VM)

The following should be installed on your VM:

```bash
# Update package list
sudo apt update

# Install Docker
sudo apt install -y docker.io

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose (v2)
sudo apt install -y docker-compose-v2

# Add your user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### Qwen Authentication Setup

The qwen-code-api container authenticates with the Qwen LLM service using OAuth credentials. You need to set up the credentials file:

```bash
# Create the Qwen credentials directory
mkdir -p ~/.qwen

# Place your OAuth credentials file at ~/.qwen/oauth_creds.json
# This file is obtained by running `qwen login` locally
# or by following the Qwen Code OAuth flow.
#
# Example format:
# {
#   "accessToken": "your-access-token",
#   "refreshToken": "your-refresh-token",
#   "expiresAt": 1735689600000
# }
```

### Step-by-Step Deployment

#### 1. Clone the Repository

```bash
# On your VM
git clone https://github.com/YOUR_USERNAME/se-toolkit-hackathon.git
cd se-toolkit-hackathon

# Initialize the qwen-code-api submodule
git submodule update --init
```

#### 2. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit the file
nano .env
```

Update these values in `.env`:

```bash
# Generate a strong JWT secret
JWT_SECRET_KEY=$(openssl rand -base64 32)

# Qwen Code API settings
QWEN_CODE_API_MODEL=qwen-plus
QWEN_CODE_API_AUTH_USE=true
QWEN_CODE_API_LOG_LEVEL=error

# Update CORS origins for your domain
CORS_ORIGINS=http://your-domain.com,http://localhost:80
```

#### 3. Start All Services

```bash
# Build and start containers
docker compose up -d --build

# Check status (should show 4 running containers)
docker compose ps

# View logs
docker compose logs -f

# Check qwen-code-api health
docker compose logs qwen-code-api
```

#### 4. Verify Deployment

```bash
# Check backend health endpoint
curl http://localhost:8000/health

# Check frontend
curl http://localhost:80

# Run automated tests
chmod +x test.sh
./test.sh
```

#### 5. Access the Application

Open your browser and go to:
- **http://YOUR_VM_IP** or **http://YOUR_DOMAIN**

The frontend is served on port 80, API on port 8000.

#### 6. (Optional) Set Up HTTPS with Nginx + Let's Encrypt

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# If using Nginx as reverse proxy:
sudo apt install -y nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/bookmarks
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/bookmarks /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### Stopping the Application

```bash
# Stop all containers
docker compose down

# Stop and remove volumes (WARNING: deletes all data)
docker compose down -v
```

### Updating the Application

```bash
# Pull latest changes (including submodule)
git pull
git submodule update --init

# Rebuild and restart
docker compose up -d --build
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Database | PostgreSQL 16 with JSONB support |
| Frontend | React 18, TypeScript, Vite, Bootstrap 5 |
| LLM Proxy | qwen-code-api (OpenAI-compatible proxy for Qwen) |
| LLM | Qwen (qwen-plus model) |
| Auth | JWT (python-jose + bcrypt) |
| DevOps | Docker, Docker Compose |

---

## Project Structure

```
se-toolkit-hackathon/
├── backend/                      # FastAPI backend
│   ├── src/bookmark_manager/
│   │   ├── main.py              # App entry point
│   │   ├── settings.py          # Pydantic settings
│   │   ├── database.py          # SQLAlchemy async engine
│   │   ├── auth.py              # JWT auth utilities
│   │   ├── llm_service.py       # LLM integration (via qwen-code-api)
│   │   ├── models/              # SQLModel definitions
│   │   │   ├── user.py
│   │   │   └── bookmark.py
│   │   ├── db/                  # Database operations
│   │   │   └── bookmarks.py
│   │   └── routers/             # API routes
│   │       ├── auth.py
│   │       └── bookmarks.py
│   ├── requirements.txt
│   └── Dockerfile
├── client-web-react/            # React frontend
│   ├── src/
│   │   ├── App.tsx              # Router & auth
│   │   ├── Login.tsx            # Login page
│   │   ├── Register.tsx         # Registration page
│   │   └── BookmarkList.tsx     # Main bookmark UI
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf               # Nginx config for prod
│   └── Dockerfile
├── qwen-code-api/               # Qwen LLM proxy (git submodule)
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   ├── src/
│   └── ...                      # OpenAI-compatible API proxy
├── data/
│   └── init.sql                 # Database initialization
├── docker-compose.yml           # Service orchestration (4 services)
├── .env.example                 # Environment template
├── test.sh                      # Bash test script
├── test.ps1                     # PowerShell test script
├── Plan.md                      # Implementation plan
└── README.md                    # This file
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login and get JWT token | No |

### Bookmarks

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/bookmarks` | Create bookmark (auto-analyzes URL via Qwen LLM) | Yes (JWT) |
| GET | `/bookmarks` | List user's bookmarks | Yes (JWT) |
| GET | `/bookmarks/{id}` | Get single bookmark | Yes (JWT) |
| PUT | `/bookmarks/{id}` | Update bookmark | Yes (JWT) |
| DELETE | `/bookmarks/{id}` | Delete bookmark | Yes (JWT) |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |

---

## qwen-code-api Details

The `qwen-code-api` service is a proxy that:

1. Accepts **OpenAI-compatible API requests** (same format as OpenAI's `/v1/chat/completions`)
2. Authenticates with **Qwen Cloud** using OAuth credentials from `~/.qwen/oauth_creds.json`
3. Forwards requests to the **Qwen LLM service**
4. Returns responses in **OpenAI-compatible format**

This means the backend can use the standard `openai` Python client library, simply pointing `base_url` at `http://qwen-code-api:8080/v1` instead of `https://api.openai.com/v1`.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QWEN_CODE_API_MODEL` | Model name to use | `qwen-plus` |
| `QWEN_CODE_API_AUTH_USE` | Use ~/.qwen/oauth_creds.json | `true` |
| `QWEN_CODE_API_LOG_LEVEL` | Logging: off, error, debug | `error` |
| `QWEN_CODE_API_MAX_RETRIES` | Retry on 500 errors | `5` |
| `QWEN_CODE_API_KEY` | Optional API key for proxy auth | (empty) |

---

## Troubleshooting

### Database connection refused
Ensure PostgreSQL container is running:
```bash
docker compose ps postgres
```

### qwen-code-api health check failing
Check the logs:
```bash
docker compose logs qwen-code-api
```
Ensure `~/.qwen/oauth_creds.json` exists and is valid.

### LLM analysis fails
Check that qwen-code-api is reachable from the backend:
```bash
docker compose exec backend curl http://qwen-code-api:8080/health
```

### CORS errors
Verify `CORS_ORIGINS` in `.env` includes your frontend URL.

### Port already in use
Change the port mapping in `docker-compose.yml` or `.env`:
```bash
BACKEND_HOST_PORT=8080
FRONTEND_HOST_PORT=8080
```

---

## License

MIT License - see [LICENSE](LICENSE) file for details.
