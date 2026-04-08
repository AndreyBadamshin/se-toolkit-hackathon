import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bookmark_manager.settings import settings
from bookmark_manager.database import init_db
from bookmark_manager.routers import auth, bookmarks, collections, search, import_export

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")
    yield
    # Shutdown
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers — all under /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(bookmarks.router, prefix="/api")
app.include_router(collections.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(import_export.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.app_name}
