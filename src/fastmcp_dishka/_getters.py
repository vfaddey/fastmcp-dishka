from typing import Any, Final

from dishka import AsyncContainer, Container
from dishka.exception_base import DishkaError
from fastmcp.server.dependencies import get_context

CONTAINER_NAME: Final[str] = "dishka_container"
CONTAINER_STATE_KEY: Final[str] = "fastmcp_dishka_container"


def get_container() -> AsyncContainer | Container:
    try:
        context = get_context()
    except RuntimeError as exc:
        msg = (
            "FastMCP Context is not available. "
            "Make sure you called setup_dishka() for the FastMCP app."
        )
        raise DishkaError(msg) from exc

    container = context._request_state.get(CONTAINER_STATE_KEY)
    if container is None:
        msg = (
            f"Container not found in FastMCP request context for key "
            f"'{CONTAINER_NAME}'. Make sure you called setup_dishka() "
            "for the FastMCP app."
        )
        raise DishkaError(msg)
    return container


def get_async_container_from_args_kwargs(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> AsyncContainer:
    del args, kwargs
    container = get_container()
    if not isinstance(container, AsyncContainer):
        msg = (
            "Expected AsyncContainer in FastMCP request context "
            f"for key '{CONTAINER_NAME}'."
        )
        raise DishkaError(msg)
    return container


def get_sync_container_from_args_kwargs(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Container:
    del args, kwargs
    container = get_container()
    if not isinstance(container, Container):
        msg = (
            f"Expected Container in FastMCP request context for key '{CONTAINER_NAME}'."
        )
        raise DishkaError(msg)
    return container
