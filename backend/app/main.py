"""LifeOS backend entrypoint - creates and configures the FastAPI app."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import execution, goals, habits, health, planner, replan, workspaces
from app.core.config import get_settings
from app.memory.api.routes import router as memory_router

# Without this, `logging.getLogger(__name__).info(...)` calls scattered
# through the app (planner_service._build_memory_context, replan.py's
# memory lookup, ...) silently go nowhere at runtime - uvicorn only
# configures its OWN loggers ("uvicorn", "uvicorn.access"), never the
# root logger, which defaults to WARNING with no handler attached. Every
# app-level `.info()` call was being dropped even though uvicorn's own
# request lines printed fine - the tests never caught this because
# pytest's `caplog` fixture captures log records directly, independent
# of whether a console handler exists. `basicConfig` is a no-op if a
# handler is already attached to root, so this is safe to call
# unconditionally regardless of import order.
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(goals.router, prefix=settings.api_v1_prefix)
app.include_router(workspaces.router, prefix=settings.api_v1_prefix)
app.include_router(planner.router, prefix=settings.api_v1_prefix)
app.include_router(execution.router, prefix=settings.api_v1_prefix)
app.include_router(replan.router, prefix=settings.api_v1_prefix)
app.include_router(habits.router, prefix=settings.api_v1_prefix)
app.include_router(memory_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict:
    return {"message": "LifeOS backend is running", "docs": "/docs"}
