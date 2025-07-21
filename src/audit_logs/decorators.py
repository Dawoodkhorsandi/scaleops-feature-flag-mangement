from enum import Enum
from functools import wraps

from typing import Callable, Any
from contextvars import ContextVar

action_context: ContextVar[Enum] = ContextVar("action_context")


def with_audit_action(action: Enum) -> Callable:
    """
    A decorator to set the audit action context for a service method.

    Args:
        action: The specific audit action (e.g., "toggle") to log.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            token = action_context.set(action)
            try:
                return await func(*args, **kwargs)
            finally:
                action_context.reset(token)

        return wrapper

    return decorator
