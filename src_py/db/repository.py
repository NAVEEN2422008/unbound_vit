"""
Generic Repository Pattern for FINRES.
Abstracts CRUD operations behind typed repositories, enabling swap between
in-memory and database-backed implementations.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Type, TypeVar
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Generic CRUD repository for any SQLAlchemy model."""

    model: Type[T]

    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> T:
        obj = self.model(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get(self, id: Any) -> Optional[T]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def update(self, id: Any, **kwargs) -> Optional[T]:
        obj = self.get(id)
        if obj is None:
            return None
        for k, v in kwargs.items():
            setattr(obj, k, v)
        self.db.flush()
        return obj

    def delete(self, id: Any) -> bool:
        obj = self.get(id)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.flush()
        return True

    def count(self) -> int:
        return self.db.query(self.model).count()


class CustomerRepository(BaseRepository):
    """Customer-specific repository with archetype filtering."""
    from src_py.models.db_models import CustomerDB as model

    def get_by_archetype(self, archetype: str, limit: int = 50) -> List:
        return self.db.query(self.model).filter(
            self.model.archetype == archetype
        ).limit(limit).all()

    def search(self, query: str, limit: int = 50) -> List:
        return self.db.query(self.model).filter(
            self.model.name.ilike(f"%{query}%")
        ).limit(limit).all()


class AuditRepository(BaseRepository):
    """Immutable audit log — appends only, never updates."""
    from src_py.models.db_models import AuditEntryDB as model

    def append(self, **kwargs) -> Any:
        return self.create(**kwargs)

    def get_customer_trail(self, customer_id: str, limit: int = 100) -> List:
        return self.db.query(self.model).filter(
            self.model.customer_id == customer_id
        ).order_by(self.model.timestamp.desc()).limit(limit).all()


class OutcomeRepository(BaseRepository):
    from src_py.models.db_models import OutcomeRecordDB as model

    def get_by_customer(self, customer_id: str) -> List:
        return self.db.query(self.model).filter(
            self.model.customer_id == customer_id
        ).all()