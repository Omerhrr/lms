from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

DATABASE_URL = settings.database_url
_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, pool_pre_ping=True)

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):
        # SQLite ignores foreign keys (and ON DELETE CASCADE) unless this is enabled per connection
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
else:
    # Postgres (Supabase). On serverless (Vercel) each invocation is short-lived, so let
    # Supabase's pooler (port 6543, transaction mode) do the pooling: NullPool here, and no
    # server-side prepared statements, which transaction-mode pooling doesn't support.
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args={"prepare_threshold": None, "connect_timeout": 10},
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    """FastAPI dependency yielding a scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Columns added after the first release. create_all() never alters existing tables, so
# existing databases get them here. (Adopt Alembic migrations as the schema keeps growing.)
_ADDED_COLUMNS = {
    "users": {
        "token_version": ("INTEGER NOT NULL DEFAULT 0", "INTEGER NOT NULL DEFAULT 0"),
        "instructor_requested": ("BOOLEAN NOT NULL DEFAULT 0", "BOOLEAN NOT NULL DEFAULT FALSE"),
    },
    "lessons": {
        "drip_days": ("INTEGER", "INTEGER"),
    },
}


def ensure_columns() -> None:
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, cols in _ADDED_COLUMNS.items():
            if not insp.has_table(table):
                continue
            existing = {c["name"] for c in insp.get_columns(table)}
            for name, (sqlite_ddl, pg_ddl) in cols.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sqlite_ddl if _is_sqlite else pg_ddl}"))
