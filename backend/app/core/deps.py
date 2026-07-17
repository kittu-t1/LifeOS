"""
Shared FastAPI dependencies.

`get_current_user` is a placeholder: real authentication (JWT
signup/login) hasn't been built yet (see docs/roadmap.md - "Auth +
Workspace foundation" is the next phase). Every request today resolves to
a single, lazily-created demo user, so the Goal/Workspace API can be built
and used now without blocking on the full auth system - and every route
already depends on "the current user" rather than a hardcoded id, so
swapping this function for real JWT verification later won't require
touching any route handler.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User

DEMO_USER_EMAIL = "demo@lifeos.local"


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Returns the single demo user, creating it on first use.

    TODO(auth-phase): replace this body with real JWT verification once
    login/signup exist. The function signature (db -> User) should stay
    the same so callers don't need to change.
    """
    user = db.query(User).filter(User.email == DEMO_USER_EMAIL).first()
    if user is None:
        user = User(email=DEMO_USER_EMAIL, name="Krishna")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
