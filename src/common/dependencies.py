from typing import Optional
from fastapi import Header, Request

from .context import actor_context


async def set_actor_from_header(x_actor: Optional[str] = Header(None, alias="X-Actor")):
    """
    A dependency that sets the actor context for a request.
    """
    actor = x_actor or "system"
    token = actor_context.set(actor)
    try:
        yield
    finally:
        actor_context.reset(token)
