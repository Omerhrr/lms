"""Database management commands (run from mini-services/lms-api).

    python -m app.manage init-db     create missing tables/columns (safe to re-run; never deletes)
    python -m app.manage check       test the database connection and print the table count
    python -m app.manage create-admin you@example.com "Your Name"   (asks for a password)

Point it at Supabase by setting LMS_DATABASE_URL (in .env or the shell) first.
"""
import sys

from sqlalchemy import inspect, text


def _load_models():
    from app import main  # noqa: F401  (imports every module's models)


def init_db():
    _load_models()
    from app.core.database import engine, ensure_columns
    from app.shared.base import Base
    Base.metadata.create_all(bind=engine)
    ensure_columns()
    print(f"✓ schema ready ({len(inspect(engine).get_table_names())} tables)")


def check():
    from app.core.database import engine
    with engine.connect() as conn:
        conn.execute(text("select 1"))
    print(f"✓ connected to {engine.url.render_as_string(hide_password=True)}")
    print(f"  tables: {len(inspect(engine).get_table_names())}")


def create_admin():
    import getpass
    if len(sys.argv) < 4:
        sys.exit('usage: python -m app.manage create-admin you@example.com "Your Name"')
    email, name = sys.argv[2].strip().lower(), sys.argv[3].strip()
    password = getpass.getpass("Password (min 8 chars): ")
    if len(password) < 8 or password != getpass.getpass("Repeat password: "):
        sys.exit("Passwords must match and be at least 8 characters")
    init_db()
    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.modules.auth.models import User, UserRole
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.role, user.password_hash, user.is_active = UserRole.admin, hash_password(password), True
    else:
        db.add(User(email=email, full_name=name, password_hash=hash_password(password), role=UserRole.admin))
    db.commit()
    print(f"✓ {email} is an admin")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"init-db": init_db, "check": check, "create-admin": create_admin}.get(cmd, lambda: sys.exit(__doc__))()
