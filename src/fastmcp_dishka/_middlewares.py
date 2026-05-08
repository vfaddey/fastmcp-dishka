from typing import Any, Final

from dishka import AsyncContainer, Container, Scope
from fastmcp import FastMCP
from fastmcp.server.context import Context
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from mcp import types as mt

from ._context import current_container


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


class DishkaAsyncMiddleware(Middleware):
    def __init__(self, container: AsyncContainer) -> None:
        self._container: Final[AsyncContainer] = container

    async def _run_with_container(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
    ) -> Any:
        context_data = _build_context_data(context)
        async with self._container(
            context=context_data,
            scope=Scope.REQUEST,
        ) as request_container:
            token = current_container.set(request_container)
            try:
                return await call_next(context)
            finally:
                current_container.reset(token)

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
    ) -> Any:
        context_data = _build_context_data(context)
        with self._container(
            context=context_data,
            scope=Scope.REQUEST,
        ) as request_container:
            token = current_container.set(request_container)
            try:
                return await call_next(context)
            finally:
                current_container.reset(token)

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
