# Smart Bookmark Manager — Implementation Plan

## Product Context

### End-user
Students, developers, researchers, and anyone who actively consumes web content and saves useful links for future reference.

### Problem
When saving many web links, users lose context: they forget what a page was about, struggle to find a specific bookmark among hundreds, and waste time on manual categorization and tagging.

### Solution in one sentence
A smart bookmark manager that automatically analyzes saved page content using AI, generates tags, summaries, and categories — making search and navigation instant.

### Core feature
AI-powered automatic classification and tagging of saved links.

---

## Version 1 — Core Feature (MVP)

> Goal: a functioning product that does one thing well — saves links with automatic AI classification.

### Scope

| Component | What will be implemented |
|-----------|--------------------------|
| **Backend** | FastAPI REST API with endpoints: registration/authentication (JWT), bookmark CRUD, LLM requests for URL analysis |
| **Database** | PostgreSQL with tables: `users`, `bookmarks` (url, title, summary, tags[], category, created_at), user ↔ bookmarks relation |
| **Client** | React SPA: URL input form, bookmark list with tags/categories, filter by tags, delete |
| **LLM** | OpenAI API integration (or Ollama for local deployment): prompt for page content analysis → generate title, summary, 5 tags, category |

### User Flow (V1)
1. User registers / logs in
2. Pastes a URL into the form → clicks "Save"
3. Backend:
   - Fetches page metadata (title, description, open graph)
   - Sends data to LLM with prompt: `"Analyze this web content. Return JSON: {title, summary (2-3 sentences), tags (5 keywords), category (one of: tech, science, education, entertainment, news, other)}"`
   - Saves result to PostgreSQL
4. Client displays a bookmark card with auto-generated summary, tags, and category
5. User can filter bookmarks by tags and categories

### Tech Stack
| Component | Technology |
|-----------|------------|
| Backend | Python 3.12+, FastAPI, Uvicorn, HTTPX (for page fetching), Pydantic |
| Auth | JWT (python-jose / passlib + bcrypt) |
| Database | PostgreSQL 16, SQLAlchemy ORM, Alembic (migrations) |
| LLM | OpenAI API (gpt-4o-mini) **or** Ollama (llama3) for offline |
| Client | React 18, Vite, Bootstrap 5, Axios, React Router |
| DevOps | Docker, docker-compose for local deployment |

### Deliverables (V1)
- [ ] FastAPI backend with JWT auth + bookmark CRUD
- [ ] Alembic migrations for DB schema
- [ ] LLM integration (prompt → parse JSON response → save)
- [ ] React frontend (add, view, filter, delete)
- [ ] Docker-compose: backend + db + frontend
- [ ] End-to-end local testing
- [ ] README with launch instructions

### Success Criteria (V1)
- User can register, add a URL, and see an auto-classified bookmark
- Tags and categories are generated correctly in ≥80% of cases
- All services start with a single `docker-compose up` command

---

## Version 2 — Enhanced Features & Deployment

> Goal: improve the core scenario, add search, address TA feedback, deploy the product.

### Enhancements (based on expected TA feedback)

| Feedback | Solution |
|----------|----------|
| "I want to search by meaning, not just by tags" | Natural language search via LLM embeddings |
| "No import/export" | Add bulk import (CSV) and export |
| "No page previews" | Save og:image and show thumbnails |
| "Tags are sometimes irrelevant" | Few-shot prompt engineering + ability to manually edit tags |
| "I want folders/collections" | Add bookmark collections (groups) |

### New Features (V2)

#### 1. Natural Language Search
- Use OpenAI embeddings (text-embedding-3-small) to vectorize summary + tags
- PostgreSQL pgvector extension for storage and similarity search
- User enters query → embedding → cosine similarity → sorted by relevance
- Fallback: standard text search on tags/title if pgvector is unavailable

#### 2. Collections / Folders
- Table `collections` (id, user_id, name, color)
- Many-to-many: `bookmarks` ↔ `collections`
- UI: sidebar with collections, drag-and-drop or assign on save

#### 3. Page Thumbnails
- Extract `og:image` meta tag when fetching the page
- Save image URL in bookmark
- Show thumbnail in bookmark card

#### 4. Edit Tags & Summary
- User can manually edit tags and summary if LLM made a mistake
- PUT endpoint for updating fields

#### 5. Export / Import
- Export bookmarks to JSON/CSV
- Import from CSV (bulk upload)

### Updated Architecture (V2)

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Add URL  │  │Bookmarks │  │ Collections│  │ Search  │ │
│  │  Form    │  │  List    │  │  Sidebar  │  │  Bar    │ │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  └────┬────┘ │
└───────┼─────────────┼──────────────┼──────────────┼──────┘
        │             │              │              │
        └─────────────┴──────────────┴──────────────┘
                          │ HTTP / REST API
┌─────────────────────────┼────────────────────────────────┐
│                    FastAPI Backend                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Auth    │  │ Bookmarks│  │ LLM      │  │ Search   │  │
│  │  (JWT)   │  │  CRUD    │  │ Service  │  │ Service  │  │
│  └──────────┘  └──────────┘  └────┬─────┘  └────┬─────┘  │
└───────────────────────────────────┼─────────────┼─────────┘
        │                           │             │
        └───────────────────────────┼─────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │     PostgreSQL + pgvector     │
                    │  ┌─────────┐ ┌──────────────┐ │
                    │  │  users  │ │  bookmarks   │ │
                    │  │         │ │ (title,      │ │
                    │  │         │ │  summary,    │ │
                    │  │         │ │  tags,       │ │
                    │  │         │ │  embedding)  │ │
                    │  └─────────┘ └──────────────┘ │
                    │  ┌─────────┐ ┌──────────────┐ │
                    │  │collections│ │bookmark_coll │ │
                    │  └─────────┘ └──────────────┘ │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │     LLM Provider (OpenAI)     │
                    │  ┌─────────────┐ ┌──────────┐ │
                    │  │ Chat API    │ │Embeddings│ │
                    │  │(summarize,  │ │(search   │ │
                    │  │ tag, categor│ │ vectors) │ │
                    │  └─────────────┘ └──────────┘ │
                    └───────────────────────────────┘
```

### LLM Integration Details (V2)

| Scenario | Model | Prompt / Task |
|----------|-------|---------------|
| Bookmark classification | gpt-4o-mini | `"Analyze this web content. Return JSON: {title, summary (2-3 sentences), tags (5 keywords), category}"` |
| Natural Language Search | text-embedding-3-small | Vectorize summary + tags on save; query embedding → cosine similarity → top-10 results |
| Search refinement | gpt-4o-mini (optional) | `"Given these bookmarks [list], which best match the query: [user_query]?"` — reranking top-5 |

### Deployment Plan

| Component | Hosting |
|-----------|---------|
| Backend + Frontend | University VM (Ubuntu 24.04) or Render/Railway |
| PostgreSQL | University VM (Docker volume) or Supabase (managed) |
| LLM | OpenAI API (external) **or** Ollama on VM if GPU available |

#### Deployment Steps
1. On VM: install Docker + docker-compose
2. Configure `.env` with DATABASE_URL, OPENAI_API_KEY, JWT_SECRET
3. `docker-compose -f docker-compose.prod.yml up -d`
4. Set up Nginx reverse proxy + Let's Encrypt SSL
5. Frontend accessible at `bookmarks.yourdomain.com`, API at `api.bookmarks.yourdomain.com`

### Deliverables (V2)
- [ ] Natural language search with pgvector
- [ ] Collections / folders
- [ ] Page thumbnails (og:image)
- [ ] Edit tags/summary manually
- [ ] Export/Import (CSV/JSON)
- [ ] TA feedback addressed
- [ ] Docker-compose for production
- [ ] Deploy to VM / cloud
- [ ] Presentation (5 slides) + video demo (≤2 min)
- [ ] README with full documentation
- [ ] MIT License
- [ ] Repo: se-toolkit-hackathon

### Success Criteria (V2)
- Natural language search returns relevant results in ≥75% of cases
- All services are deployed and accessible via HTTPS
- User can complete the full workflow: register → add bookmarks → search → organize into collections → export
- Video demo covers all key features in ≤2 minutes

---

## Git Workflow

| Branch | Purpose |
|--------|---------|
| `main` | Stable version (V1 after completion, V2 after deployment) |
| `develop` | Integration branch |
| `feat/auth` | JWT authentication |
| `feat/bookmark-crud` | Bookmark CRUD |
| `feat/llm-integration` | OpenAI/Ollama integration |
| `feat/search` | Natural language search (V2) |
| `feat/collections` | Collections feature (V2) |

### Commit Convention
```
feat: add bookmark CRUD with LLM tagging
fix: handle LLM JSON parse errors gracefully
docs: update README with deployment instructions
chore: add docker-compose for production
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| OpenAI API unavailable / expensive | Fallback to Ollama (llama3) locally |
| pgvector is complex to set up | Fallback to PostgreSQL full-text search |
| LLM returns invalid JSON | Retry logic + strict JSON schema validation + Pydantic parsing |
| CORS issues when fetching pages | Use HTTPX with proper headers, fallback to metadata only |
| VM limitations (Telegram blocked) | Not using Telegram; web app only |

---

## Timeline Summary

| Phase | Task | Outcome |
|-------|------|---------|
| **V1** | Backend + DB + LLM + Frontend | Working MVP with auto-classification |
| **V1** | Docker-compose | Local launch with one command |
| **V1** | TA demo & feedback | Receive feedback |
| **V2** | Search + Collections + Thumbnails | Improved product |
| **V2** | Deployment | Public access |
| **V2** | Presentation + Demo | Final submission |
