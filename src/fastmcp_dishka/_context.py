from contextvars import ContextVar
from typing import Final

from dishka import AsyncContainer, Container

CONTAINER_NAME: Final[str] = "dishka_container"

current_container: ContextVar[AsyncContainer | Container | None] = ContextVar(
    "fastmcp_dishka_container",
    default=None,
)
