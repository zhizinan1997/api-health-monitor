"""
FastAPI main application entry point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import init_db
from app.logger import set_db_ready, log_debug, cleanup_old_logs
from app.scheduler import start_scheduler, cleanup_old_results
from app.routers import admin, settings, models, tests, logs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    init_db()
    set_db_ready()
    log_debug("INFO", "main", "Database initialized")
    
    # Cleanup old data
    cleanup_old_results(days=90)
    cleanup_old_logs(days=7)
    
    # Start scheduler
    start_scheduler()
    log_debug("INFO", "main", "Application started")
    
    yield
    
    # Shutdown
    log_debug("INFO", "main", "Application shutting down")


app = FastAPI(
    title="API Health Monitor",
    description="Monitor OpenAI-format API connectivity",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin.router)
app.include_router(settings.router)
app.include_router(models.router)
app.include_router(tests.router)
app.include_router(logs.router)

# Static files directory
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def customer_page():
    """Serve customer page"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/admin")
async def admin_page():
    """Serve admin page"""
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {"status": "healthy"}
