import inspect
from collections.abc import Awaitable, Callable
from typing import Any, overload

from dishka.integrations.base import wrap_injection

from ._getters import (
    get_async_container_from_args_kwargs,
    get_sync_container_from_args_kwargs,
)


def _copy_fastmcp_metadata(
    source: Callable[..., Any],
    target: Callable[..., Any],
) -> None:
    metadata = getattr(source, "__fastmcp__", None)
    if metadata is not None:
        target.__fastmcp__ = metadata  # type: ignore[attr-defined]


def inject_async[**ParamsP, ReturnT](
    func: Callable[ParamsP, Awaitable[ReturnT]],
) -> Callable[ParamsP, Awaitable[ReturnT]]:
    wrapped = wrap_injection(
        func=func,
        container_getter=get_async_container_from_args_kwargs,
        remove_depends=True,
        is_async=True,
        manage_scope=False,
    )
    _copy_fastmcp_metadata(func, wrapped)
    return wrapped


def inject_sync[**ParamsP, ReturnT](
    func: Callable[ParamsP, ReturnT],
) -> Callable[ParamsP, ReturnT]:
    wrapped = wrap_injection(
        func=func,
        container_getter=get_sync_container_from_args_kwargs,
        remove_depends=True,
        is_async=False,
        manage_scope=False,
    )
    _copy_fastmcp_metadata(func, wrapped)
    return wrapped


@overload
def inject[**ParamsP, ReturnT](
    func: Callable[ParamsP, Awaitable[ReturnT]],
) -> Callable[ParamsP, Awaitable[ReturnT]]: ...


@overload
def inject[**ParamsP, ReturnT](
    func: Callable[ParamsP, ReturnT],
) -> Callable[ParamsP, ReturnT]: ...


def inject[**ParamsP](func: Callable[ParamsP, Any]) -> Callable[ParamsP, Any]:
    if inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func):
        return inject_async(func)
    return inject_sync(func)
