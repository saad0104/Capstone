import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .models import Base


def get_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_url = f"sqlite:///{os.path.join(base_dir, 'data', 'threatgpt.db')}"
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, connect_args=connect_args)


engine = get_engine()
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))


def init_db():
    Base.metadata.create_all(bind=engine)
