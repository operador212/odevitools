"""Lazy SQLAlchemy session dependency for future authenticated Tax Records routes."""
from collections.abc import Iterator
from functools import lru_cache
from sqlalchemy.orm import Session, sessionmaker
from tax_records.database import get_engine

@lru_cache(maxsize=1)
def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)

def get_db_session() -> Iterator[Session]:
    factory = get_session_factory()
    with factory() as session:
        yield session
