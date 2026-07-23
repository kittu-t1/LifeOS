"""
Memory Engine routes - CRUD + category filtering, generic enough for
Planner/Habits/future AI services to all read through (see
app/memory/services/memory_service.py's module docstring).

Memory is user-scoped, not Goal-scoped, same reasoning as Habits (see
app/api/v1/habits.py) - a remembered preference or pattern isn't tied to
one goal's workspace, so there's no goal_id/plan_id in any of these
paths; every route resolves ownership straight from the current user.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.memory.models.memory import MemoryCategory
from app.memory.repositories.memory_repository import SqlAlchemyMemoryRepository
from app.memory.schemas.memory import MemoryCreate, MemoryRead, MemoryUpdate
from app.memory.services.memory_service import MemoryService
from app.models.user import User

router = APIRouter(prefix="/memories", tags=["memory"])


def get_memory_service(db: Session = Depends(get_db)) -> MemoryService:
    """FastAPI dependency assembling a request-scoped MemoryService over
    the real SQLAlchemy repository - the one place this module wires the
    abstract MemoryRepository to a concrete implementation (see
    app/memory/repositories/memory_repository.py)."""
    return MemoryService(SqlAlchemyMemoryRepository(db))


def _get_owned_memory(service: MemoryService, *, user: User, memory_id: uuid.UUID):
    memory = service.get_owned_memory(user_id=user.id, memory_id=memory_id)
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return memory


@router.post("", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
def create_memory(
    payload: MemoryCreate,
    service: MemoryService = Depends(get_memory_service),
    current_user: User = Depends(get_current_user),
) -> MemoryRead:
    memory = service.create_memory(user_id=current_user.id, data=payload)
    return MemoryRead.model_validate(memory)


@router.get("", response_model=list[MemoryRead])
def list_memories(
    category: MemoryCategory | None = Query(
        default=None, description="Filter to a single memory category."
    ),
    service: MemoryService = Depends(get_memory_service),
    current_user: User = Depends(get_current_user),
) -> list[MemoryRead]:
    """Doubles as the spec's "Search by category" endpoint - a category
    filter on the same list call rather than a separate route, since it's
    the identical query with one optional parameter."""
    memories = service.list_memories(user_id=current_user.id, category=category)
    return [MemoryRead.model_validate(m) for m in memories]


@router.get("/{memory_id}", response_model=MemoryRead)
def get_memory(
    memory_id: uuid.UUID,
    service: MemoryService = Depends(get_memory_service),
    current_user: User = Depends(get_current_user),
) -> MemoryRead:
    memory = _get_owned_memory(service, user=current_user, memory_id=memory_id)
    return MemoryRead.model_validate(memory)


@router.patch("/{memory_id}", response_model=MemoryRead)
def update_memory(
    memory_id: uuid.UUID,
    payload: MemoryUpdate,
    service: MemoryService = Depends(get_memory_service),
    current_user: User = Depends(get_current_user),
) -> MemoryRead:
    memory = _get_owned_memory(service, user=current_user, memory_id=memory_id)
    updated = service.update_memory(memory=memory, data=payload)
    return MemoryRead.model_validate(updated)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: uuid.UUID,
    service: MemoryService = Depends(get_memory_service),
    current_user: User = Depends(get_current_user),
) -> None:
    memory = _get_owned_memory(service, user=current_user, memory_id=memory_id)
    service.delete_memory(memory=memory)
