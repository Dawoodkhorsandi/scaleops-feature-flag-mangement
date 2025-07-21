from typing import Optional
from fastapi import Header, Request

from .context import actor_context


async def set_actor_from_header(
    x_actor: str = Header(
        ...,
        alias="X-Actor",
        description="This only mimics authentication, Consider it as jwt token.",
    )
):
    """
    A dependency that sets the actor context for a request.
    """
    token = actor_context.set(x_actor)
    try:
        yield
    finally:
        actor_context.reset(token)
