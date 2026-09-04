"""
Notification System for FINRES.
Generates alerts for distress triggers, policy violations, and SLA breaches.
Stores notifications and provides unread count for UI badges.
"""
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from src_py.observability.logging import get_logger

logger = get_logger("finres.notifications")


class NotificationType(str, Enum):
    DISTRESS_ALERT = "DISTRESS_ALERT"
    SCORE_CHANGE = "SCORE_CHANGE"
    INTERVENTION_RECOMMENDED = "INTERVENTION_RECOMMENDED"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    SLA_BREACH = "SLA_BREACH"
    MODEL_DRIFT = "MODEL_DRIFT"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    AUDIT_REQUIRED = "AUDIT_REQUIRED"


class NotificationPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Notification:
    def __init__(self, type_: NotificationType, priority: NotificationPriority,
                 title: str, message: str, customer_id: Optional[str] = None,
                 metadata: Optional[Dict] = None):
        self.id = str(uuid.uuid4())[:12]
        self.type = type_
        self.priority = priority
        self.title = title
        self.message = message
        self.customer_id = customer_id
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow().isoformat() + "Z"
        self.read = False
        self.acknowledged = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "customer_id": self.customer_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "read": self.read,
            "acknowledged": self.acknowledged,
        }


class NotificationStore:
    """In-memory notification store with persistence to disk."""

    def __init__(self, max_size: int = 5000):
        self._notifications: List[Notification] = []
        self._max_size = max_size
        self._store_dir = os.environ.get("NOTIFICATION_DIR", "src_py/data/notifications")
        os.makedirs(self._store_dir, exist_ok=True)
        self._load()

    def push(self, notification: Notification) -> Notification:
        self._notifications.insert(0, notification)
        if len(self._notifications) > self._max_size:
            self._notifications = self._notifications[:self._max_size]
        self._persist()
        return notification

    def get_all(self, unread_only: bool = False, limit: int = 100) -> List[Dict]:
        notifs = self._notifications
        if unread_only:
            notifs = [n for n in notifs if not n.read]
        return [n.to_dict() for n in notifs[:limit]]

    def unread_count(self) -> int:
        return sum(1 for n in self._notifications if not n.read)

    def mark_read(self, notification_id: str) -> bool:
        for n in self._notifications:
            if n.id == notification_id:
                n.read = True
                self._persist()
                return True
        return False

    def mark_all_read(self) -> int:
        count = 0
        for n in self._notifications:
            if not n.read:
                n.read = True
                count += 1
        self._persist()
        return count

    def acknowledge(self, notification_id: str) -> bool:
        for n in self._notifications:
            if n.id == notification_id:
                n.acknowledged = True
                n.read = True
                self._persist()
                return True
        return False

    def stats(self) -> Dict[str, int]:
        total = len(self._notifications)
        unread = self.unread_count()
        by_type = {}
        for n in self._notifications:
            by_type[n.type.value] = by_type.get(n.type.value, 0) + 1
        return {"total": total, "unread": unread, "by_type": by_type}

    def _persist(self) -> None:
        import json
        path = os.path.join(self._store_dir, "notifications.json")
        data = [n.to_dict() for n in self._notifications[:200]]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        import json
        path = os.path.join(self._store_dir, "notifications.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for item in data:
                    n = Notification(
                        type_=NotificationType(item.get("type", "SYSTEM_ERROR")),
                        priority=NotificationPriority(item.get("priority", "LOW")),
                        title=item.get("title", ""),
                        message=item.get("message", ""),
                        customer_id=item.get("customer_id"),
                        metadata=item.get("metadata", {}),
                    )
                    n.read = item.get("read", False)
                    n.acknowledged = item.get("acknowledged", False)
                    n.created_at = item.get("created_at", n.created_at)
                    self._notifications.append(n)
            except Exception as e:
                logger.warning(f"Failed to load notifications: {e}")


# Global singleton
_store: Optional[NotificationStore] = None


def get_notification_store() -> NotificationStore:
    global _store
    if _store is None:
        _store = NotificationStore()
    return _store


def alert_distress(customer_id: str, score: float, threshold: float = 0.7) -> Optional[Notification]:
    if score < threshold:
        return None
    store = get_notification_store()
    priority = NotificationPriority.CRITICAL if score > 0.9 else NotificationPriority.HIGH
    n = Notification(
        type_=NotificationType.DISTRESS_ALERT,
        priority=priority,
        title=f"Distress Alert: {customer_id}",
        message=f"Customer {customer_id} distress score {score:.3f} exceeds threshold {threshold:.3f}. Immediate review recommended.",
        customer_id=customer_id,
        metadata={"score": score, "threshold": threshold},
    )
    store.push(n)
    logger.warning(f"DISTRESS ALERT: {customer_id} score={score:.3f}")
    return n


def alert_score_change(customer_id: str, old_score: float, new_score: float) -> Optional[Notification]:
    delta = new_score - old_score
    if abs(delta) < 0.1:
        return None
    store = get_notification_store()
    n = Notification(
        type_=NotificationType.SCORE_CHANGE,
        priority=NotificationPriority.MEDIUM,
        title=f"Score Change: {customer_id}",
        message=f"Distress score changed from {old_score:.3f} to {new_score:.3f} ({'+'if delta>0 else ''}{delta:.3f})",
        customer_id=customer_id,
        metadata={"old_score": old_score, "new_score": new_score, "delta": delta},
    )
    store.push(n)
    return n


def alert_model_drift(model_name: str, drift_psi: float) -> Notification:
    store = get_notification_store()
    n = Notification(
        type_=NotificationType.MODEL_DRIFT,
        priority=NotificationPriority.HIGH if drift_psi > 0.1 else NotificationPriority.MEDIUM,
        title=f"Model Drift Detected: {model_name}",
        message=f"PSI={drift_psi:.4f} for {model_name}. Consider retraining.",
        metadata={"model_name": model_name, "psi": drift_psi},
    )
    store.push(n)
    return n
