"""Cross-module notification helpers."""
from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification


def notify(db: Session, user_id: int, type: str, title: str, body: str = "", link: str | None = None):
    """Create an in-app notification (called from other modules)."""
    db.add(Notification(user_id=user_id, type=type, title=title, body=body, link=link))
    db.commit()
