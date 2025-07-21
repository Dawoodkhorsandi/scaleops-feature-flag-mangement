from contextvars import ContextVar


actor_context: ContextVar[str] = ContextVar("actor_context", default="system")
