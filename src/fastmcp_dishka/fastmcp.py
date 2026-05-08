__all__ = ("FastMCPProvider", "inject", "setup_dishka")

from dishka import AsyncContainer, Container, Provider, Scope, from_context
from fastmcp import FastMCP
from fastmcp.server.context import Context
from fastmcp.server.middleware import MiddlewareContext
from mcp import types as mt

from ._injectors import inject
from ._middlewares import DishkaAsyncMiddleware, DishkaSyncMiddleware


class FastMCPProvider(Provider):
    app = from_context(FastMCP, scope=Scope.REQUEST)
    context = from_context(Context, scope=Scope.REQUEST)
    middleware_context = from_context(MiddlewareContext, scope=Scope.REQUEST)
    call_tool_params = from_context(mt.CallToolRequestParams, scope=Scope.REQUEST)
    read_resource_params = from_context(
        mt.ReadResourceRequestParams,
        scope=Scope.REQUEST,
    )
    get_prompt_params = from_context(mt.GetPromptRequestParams, scope=Scope.REQUEST)


def setup_dishka(container: AsyncContainer | Container, app: FastMCP) -> None:
    if isinstance(container, AsyncContainer):
        app.add_middleware(DishkaAsyncMiddleware(container))
    else:
        app.add_middleware(DishkaSyncMiddleware(container))
