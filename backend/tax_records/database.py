"""Lazy database engine creation; importing the API never connects to a database."""
import os
from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

@lru_cache(maxsize=1)
def get_engine() -> Engine:
    url = os.getenv("TAX_RECORDS_DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("TAX_RECORDS_DATABASE_URL is not configured; Tax Records storage is disabled.")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(url, pool_pre_ping=True, future=True)
