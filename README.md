# Smart Bookmark Manager

AI-powered bookmark manager that automatically analyzes saved pages using Qwen LLM, generates summaries and categories — making search and navigation instant.

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
- ✅ Auto-generated title, summary, and categories (up to 5)
- ✅ Page thumbnail extraction (og:image)
- ✅ Filter bookmarks by category
- ✅ Edit categories inline (add/remove with max 5 per bookmark)
- ✅ Delete bookmarks
- ✅ Responsive web UI with Bootstrap 5
- ✅ Docker-compose deployment with qwen-code-api container

### Implemented (Version 2)
- ✅ Natural language search with embeddings (pgvector)
- ✅ Collections/folders for organizing bookmarks
- ✅ Export bookmarks to JSON/CSV
- ✅ Import bookmarks from CSV
- ✅ Embedding generation for semantic search

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
  - Up to 5 relevant categories
  - Thumbnail (if available)

### 5. Manage Bookmarks
- Filter by category using the filter buttons
- Edit categories inline: click "×" to remove a category, or "+" to add a new one (max 5 per bookmark)
- Search bookmarks using natural language in the search bar
- Organize bookmarks into collections (click "📁 Collections" to create and manage)
- Add bookmarks to collections using the dropdown in each bookmark card
- Export bookmarks to JSON or CSV (click "📥 Export/Import")
- Import bookmarks from CSV file
- Click bookmark title to open the original page
- Delete bookmarks with the × button

---

## Deployment

For detailed step-by-step deployment instructions, see [**DEPLOYMENT.md**](DEPLOYMENT.md).

Quick start:

```bash
# 1. Install Docker
sudo apt update && sudo apt install -y docker.io docker-compose-v2

# 2. Clone + init submodule
git clone https://github.com/YOUR_USERNAME/se-toolkit-hackathon.git
cd se-toolkit-hackathon
git submodule update --init

# 3. Set up Qwen credentials
mkdir -p ~/.qwen
# Place oauth_creds.json in ~/.qwen/

# 4. Configure
cp .env.example .env
nano .env  # Set JWT_SECRET_KEY, CORS_ORIGINS, etc.

# 5. Deploy
docker compose up -d --build

# 6. Open http://YOUR_VM_IP in browser
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for troubleshooting, firewall config, and HTTPS setup.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Database | PostgreSQL 16 with JSONB support |
| Frontend | React 18, TypeScript, Vite, Bootstrap 5 |
| LLM Proxy | qwen-code-api (OpenAI-compatible proxy for Qwen) |
| LLM | Qwen (coder-model) |
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
│   │   │   ├── bookmark.py
│   │   │   ├── collection.py
│   │   │   └── bookmark_collection.py
│   │   ├── db/                  # Database operations
│   │   │   ├── bookmarks.py
│   │   │   └── collections.py
│   │   └── routers/             # API routes
│   │       ├── auth.py
│   │       ├── bookmarks.py
│   │       ├── collections.py
│   │       ├── search.py
│   │       └── import_export.py
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
| PUT | `/bookmarks/{id}/categories` | Update all categories (max 5) | Yes (JWT) |
| POST | `/bookmarks/{id}/categories` | Add a single category | Yes (JWT) |
| DELETE | `/bookmarks/{id}/categories/{category}` | Remove a category | Yes (JWT) |

### Collections

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/collections` | Create collection | Yes (JWT) |
| GET | `/collections` | List user's collections | Yes (JWT) |
| GET | `/collections/{id}` | Get single collection | Yes (JWT) |
| PUT | `/collections/{id}` | Update collection | Yes (JWT) |
| DELETE | `/collections/{id}` | Delete collection | Yes (JWT) |
| POST | `/collections/{id}/bookmarks/{bookmark_id}` | Add bookmark to collection | Yes (JWT) |
| DELETE | `/collections/{id}/bookmarks/{bookmark_id}` | Remove bookmark from collection | Yes (JWT) |
| GET | `/collections/{id}/bookmarks` | Get all bookmarks in collection | Yes (JWT) |

### Search

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/search?q=query` | Natural language search | Yes (JWT) |

### Import/Export

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/import-export/export/json` | Export bookmarks to JSON | Yes (JWT) |
| GET | `/import-export/export/csv` | Export bookmarks to CSV | Yes (JWT) |
| POST | `/import-export/import/csv` | Import bookmarks from CSV | Yes (JWT) |

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
| `QWEN_CODE_API_MODEL` | Model name to use | `coder-model` |
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
