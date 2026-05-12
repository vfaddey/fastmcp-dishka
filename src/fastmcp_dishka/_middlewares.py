from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Final

from dishka import AsyncContainer, Container, Scope
from fastmcp import FastMCP
from fastmcp.server.context import Context
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from mcp import types as mt

from ._getters import CONTAINER_STATE_KEY


def _build_context_data(context: MiddlewareContext[Any]) -> dict[Any, Any]:
    context_data: dict[Any, Any] = {
        MiddlewareContext: context,
        type(context.message): context.message,
    }

    fastmcp_context = context.fastmcp_context
    if fastmcp_context is not None:
        context_data[Context] = fastmcp_context
        context_data[FastMCP] = fastmcp_context.fastmcp

    return context_data


@contextmanager
def _use_container(
    context: Context,
    container: AsyncContainer | Container,
) -> Generator[None, None, None]:
    previous = context._request_state.get(CONTAINER_STATE_KEY)
    context._request_state[CONTAINER_STATE_KEY] = container
    try:
        yield
    finally:
        if previous is None:
            context._request_state.pop(CONTAINER_STATE_KEY, None)
        else:
            context._request_state[CONTAINER_STATE_KEY] = previous


class DishkaAsyncMiddleware(Middleware):
    def __init__(self, container: AsyncContainer) -> None:
        self._container: Final[AsyncContainer] = container

    async def _run_with_container(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
        scope: Scope = Scope.REQUEST,
    ) -> Any:
        context_data = _build_context_data(context)
        async with self._container(
            context=context_data,
            scope=scope,
        ) as scoped_container:
            fastmcp_context = context.fastmcp_context
            if fastmcp_context is None:
                return await call_next(context)

            with _use_container(fastmcp_context, scoped_container):
                return await call_next(context)

    async def on_initialize(
        self,
        context: MiddlewareContext[mt.InitializeRequest],
        call_next: CallNext[mt.InitializeRequest, mt.InitializeResult | None],
    ) -> mt.InitializeResult | None:
        return await self._run_with_container(
            context,
            call_next,
            scope=Scope.SESSION,
        )

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, Any],
    ) -> Any:
        return await self._run_with_container(context, call_next)

    async def on_read_resource(
        self,
        context: MiddlewareContext[mt.ReadResourceRequestParams],
        call_next: CallNext[mt.ReadResourceRequestParams, Any],
    ) -> Any:
        return await self._run_with_container(context, call_next)

    async def on_get_prompt(
        self,
        context: MiddlewareContext[mt.GetPromptRequestParams],
        call_next: CallNext[mt.GetPromptRequestParams, Any],
    ) -> Any:
        return await self._run_with_container(context, call_next)


class DishkaSyncMiddleware(Middleware):
    def __init__(self, container: Container) -> None:
        self._container: Final[Container] = container

    async def _run_with_container(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
        scope: Scope = Scope.REQUEST,
    ) -> Any:
        context_data = _build_context_data(context)
        with self._container(
            context=context_data,
            scope=scope,
        ) as scoped_container:
            fastmcp_context = context.fastmcp_context
            if fastmcp_context is None:
                return await call_next(context)

            with _use_container(fastmcp_context, scoped_container):
                return await call_next(context)

    async def on_initialize(
        self,
        context: MiddlewareContext[mt.InitializeRequest],
        call_next: CallNext[mt.InitializeRequest, mt.InitializeResult | None],
    ) -> mt.InitializeResult | None:
        return await self._run_with_container(
            context,
            call_next,
            scope=Scope.SESSION,
        )

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, Any],
    ) -> Any:
        return await self._run_with_container(context, call_next)

    async def on_read_resource(
        self,
        context: MiddlewareContext[mt.ReadResourceRequestParams],
        call_next: CallNext[mt.ReadResourceRequestParams, Any],
    ) -> Any:
        return await self._run_with_container(context, call_next)

    async def on_get_prompt(
        self,
        context: MiddlewareContext[mt.GetPromptRequestParams],
        call_next: CallNext[mt.GetPromptRequestParams, Any],
    ) -> Any:
        return await self._run_with_container(context, call_next)
