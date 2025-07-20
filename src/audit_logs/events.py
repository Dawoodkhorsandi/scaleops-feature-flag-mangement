from typing import Any

from sqlalchemy import event, inspect
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapper, Session, attributes, object_session

from src.infrastructure.database import Base
from .auditable import Auditable
from .enums import AuditAction
from .model import AuditLog


def _model_to_dict(model_instance: Any) -> dict[str, Any]:
    """A simple utility to serialize a model's column values into a dictionary."""
    mapper: Mapper = inspect(model_instance.__class__)
    return {c.key: getattr(model_instance, c.key) for c in mapper.column_attrs}


def _get_session(target: Any) -> Session | None:
    """Helper to retrieve the session from a model instance."""
    return object_session(target)




def log_create(mapper: Mapper, connection: Connection, target: Any) -> None:
    """Generic listener for the 'after_insert' event."""
    session = _get_session(target)
    if not session:
        return

    log_details = {"created": _model_to_dict(target)}
    log_entry = AuditLog(
        action=AuditAction.CREATE,
        target_entity=target.__tablename__,
        target_id=str(target.id),
        details=log_details,
    )
    session.add(log_entry)


def log_update(mapper: Mapper, connection: Connection, target: Any) -> None:
    """Generic listener for the 'after_update' event."""
    session = _get_session(target)
    if not session:
        return

    changes: dict[str, dict[str, Any]] = {}
    for attr in attributes.instance_state(target).history.keys():
        hist = attributes.get_history(target, attr)
        if hist.has_changes():
            old_value = hist.deleted[0] if hist.deleted else None
            new_value = hist.added[0] if hist.added else None
            changes[attr] = {"before": old_value, "after": new_value}

    if not changes:
        return

    log_entry = AuditLog(
        action=AuditAction.UPDATE,
        target_entity=target.__tablename__,
        target_id=str(target.id),
        details={"changes": changes},
    )
    session.add(log_entry)


def log_delete(mapper: Mapper, connection: Connection, target: Any) -> None:
    """Generic listener for the 'before_delete' event."""
    session = _get_session(target)
    if not session:
        return

    log_details = {"deleted": _model_to_dict(target)}
    log_entry = AuditLog(
        action=AuditAction.DELETE,
        target_entity=target.__tablename__,
        target_id=str(target.id),
        details=log_details,
    )
    session.add(log_entry)


# --- Automatic Registration ---


def register_audit_listeners() -> None:
    """
    Finds all models that inherit from the 'Auditable' mixin and
    attaches the generic audit event listeners to them.
    This should be called once at application startup.
    """
    print("Searching for auditable models to register listeners...")
    # The mapper is of type Mapper, but we don't need to use the type hint here
    # as it's part of the loop variable declaration.
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if issubclass(cls, Auditable):
            print(f"  -> Registering audit listeners for model: {cls.__name__}")
            event.listen(cls, "after_insert", log_create)
            event.listen(cls, "after_update", log_update)
            event.listen(cls, "before_delete", log_delete)
