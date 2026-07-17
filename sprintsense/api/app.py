"""FastAPI application entry point for SprintSense."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import get_settings, setup_logging

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    settings = get_settings()
    logger.info("🚀 SprintSense AI Sprint Intelligence Agent starting up...")
    logger.info("Environment: %s", settings.app_env)
    logger.info("Port: %d", settings.app_port)
    logger.info("OpenAI Model: %s", settings.openai_model)
    logger.info("Jira Project: %s", settings.jira_project_key)
    logger.info("GitHub Repo: %s/%s", settings.github_repo_owner, settings.github_repo_name)
    yield
    logger.info("SprintSense shutting down.")


app = FastAPI(
    title="SprintSense API",
    description="AI Sprint Intelligence Agent — Autonomous sprint health monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from api.routes.health import router as health_router
from api.routes.sprint import router as sprint_router
from api.routes.report import router as report_router

app.include_router(health_router)
app.include_router(sprint_router)
app.include_router(report_router)


# Serve static audio/screenshot files if directories exist
audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio")
if os.path.exists(audio_dir):
    app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")

screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "screenshots")
if os.path.exists(screenshots_dir):
    app.mount("/screenshots", StaticFiles(directory=screenshots_dir), name="screenshots")
