import asyncio
from collections.abc import Iterable
from typing import Any, NewType
from unittest.mock import Mock

import pytest
from dishka import (
    AsyncContainer,
    Container,
    Provider,
    Scope,
    make_async_container,
    make_container,
    provide,
)
from dishka.exception_base import DishkaError
from fastmcp import FastMCP
from fastmcp.server.context import Context
from mcp import types as mt

from fastmcp_dishka import FastMCPProvider, FromDishka, inject, setup_dishka
from fastmcp_dishka._getters import get_container
from fastmcp_dishka._middlewares import (
    DishkaAsyncMiddleware,
    DishkaSyncMiddleware,
    _build_context_data,
)

AppDep = NewType("AppDep", str)
RequestDep = NewType("RequestDep", object)
ContextDep = NewType("ContextDep", int)
ReadUriDep = NewType("ReadUriDep", str)


class AppProvider(Provider):
    def __init__(self) -> None:
        super().__init__()
        self.app_released = Mock()
        self.request_released = Mock()
        self.mock = Mock()

    @provide(scope=Scope.APP)
    def app(self) -> Iterable[AppDep]:
        yield AppDep("APP")
        self.app_released()

    @provide(scope=Scope.REQUEST)
    def request(self) -> Iterable[RequestDep]:
        value = RequestDep(object())
        yield value
        self.request_released(value)

    @provide(scope=Scope.REQUEST)
    def context_id(self, context: Context) -> ContextDep:
        return ContextDep(id(context))

    @provide(scope=Scope.REQUEST)
    def read_uri(self, params: mt.ReadResourceRequestParams) -> ReadUriDep:
        return ReadUriDep(str(params.uri))

    @provide(scope=Scope.REQUEST)
    def get_mock(self) -> Mock:
        return self.mock


def test_async_tool_injects_dependencies_and_closes_request_scope() -> None:
    async def scenario() -> None:
        provider = AppProvider()
        container = make_async_container(provider, FastMCPProvider())
        mcp = FastMCP("test")
        setup_dishka(container, mcp)

        @mcp.tool
        @inject
        async def handle(
            name: str,
            app_dep: FromDishka[AppDep],
            request_dep: FromDishka[RequestDep],
            context_dep: FromDishka[ContextDep],
            mock: FromDishka[Mock],
        ) -> str:
            mock(app_dep, request_dep, context_dep)
            return f"{app_dep}:{name}"

        try:
            tools = await mcp.list_tools()
            assert tools[0].parameters["properties"].keys() == {"name"}

            first = await mcp.call_tool("handle", {"name": "first"})
            second = await mcp.call_tool("handle", {"name": "second"})

            assert first.content[0].text == "APP:first"
            assert second.content[0].text == "APP:second"
            assert provider.mock.call_count == 2
            assert (
                provider.mock.call_args_list[0].args[1]
                is not (provider.mock.call_args_list[1].args[1])
            )
            assert provider.request_released.call_count == 2
        finally:
            await container.close()

        provider.app_released.assert_called_once()

    asyncio.run(scenario())


def test_sync_tool_injects_dependencies_from_sync_container() -> None:
    async def scenario() -> None:
        provider = AppProvider()
        container = make_container(provider, FastMCPProvider())
        mcp = FastMCP("test")
        setup_dishka(container, mcp)

        @mcp.tool
        @inject
        def handle(
            app_dep: FromDishka[AppDep],
            request_dep: FromDishka[RequestDep],
            mock: FromDishka[Mock],
        ) -> str:
            mock(app_dep, request_dep)
            return str(app_dep)

        try:
            result = await mcp.call_tool("handle")

            assert result.content[0].text == "APP"
            provider.mock.assert_called_once()
            provider.request_released.assert_called_once()
        finally:
            container.close()

        provider.app_released.assert_called_once()

    asyncio.run(scenario())


def test_sync_resource_and_prompt_inject_from_sync_container() -> None:
    async def scenario() -> None:
        provider = AppProvider()
        container = make_container(provider, FastMCPProvider())
        mcp = FastMCP("test")
        setup_dishka(container, mcp)

        @mcp.resource("data://sync/{name}")
        @inject
        def item_resource(
            name: str,
            app_dep: FromDishka[AppDep],
            request_dep: FromDishka[RequestDep],
        ) -> str:
            del request_dep
            return f"{app_dep}:{name}"

        @mcp.prompt
        @inject
        def item_prompt(
            name: str,
            app_dep: FromDishka[AppDep],
            request_dep: FromDishka[RequestDep],
        ) -> str:
            del request_dep
            return f"Prompt {app_dep}:{name}"

        try:
            resource = await mcp.read_resource("data://sync/one")
            prompt = await mcp.render_prompt("item_prompt", {"name": "two"})

            assert resource.contents[0].content == "APP:one"
            assert prompt.messages[0].content.text == "Prompt APP:two"
            assert provider.request_released.call_count == 2
        finally:
            container.close()

    asyncio.run(scenario())


def test_resource_template_and_prompt_inject_dependencies() -> None:
    async def scenario() -> None:
        provider = AppProvider()
        container = make_async_container(provider, FastMCPProvider())
        mcp = FastMCP("test")
        setup_dishka(container, mcp)

        @mcp.resource("data://items/{name}")
        @inject
        async def item_resource(
            name: str,
            app_dep: FromDishka[AppDep],
            request_dep: FromDishka[RequestDep],
        ) -> str:
            del request_dep
            return f"{app_dep}:{name}"

        @mcp.prompt
        @inject
        async def item_prompt(
            name: str,
            app_dep: FromDishka[AppDep],
            request_dep: FromDishka[RequestDep],
        ) -> str:
            del request_dep
            return f"Prompt {app_dep}:{name}"

        try:
            resource = await mcp.read_resource("data://items/one")
            prompt = await mcp.render_prompt("item_prompt", {"name": "two"})

            assert resource.contents[0].content == "APP:one"
            assert prompt.messages[0].content.text == "Prompt APP:two"
            assert provider.request_released.call_count == 2
        finally:
            await container.close()

    asyncio.run(scenario())


def test_async_handler_with_sync_container_reports_container_type_error() -> None:
    async def scenario() -> None:
        provider = AppProvider()
        container = make_container(provider, FastMCPProvider())
        mcp = FastMCP("test", mask_error_details=False)
        setup_dishka(container, mcp)

        @mcp.tool
        @inject
        async def handle(app_dep: FromDishka[AppDep]) -> None:
            del app_dep

        try:
            with pytest.raises(Exception, match="Expected AsyncContainer"):
                await mcp.call_tool("handle")
        finally:
            container.close()

    asyncio.run(scenario())


def test_sync_handler_with_async_container_reports_container_type_error() -> None:
    async def scenario() -> None:
        provider = AppProvider()
        container = make_async_container(provider, FastMCPProvider())
        mcp = FastMCP("test", mask_error_details=False)
        setup_dishka(container, mcp)

        @mcp.tool
        @inject
        def handle(app_dep: FromDishka[AppDep]) -> None:
            del app_dep

        try:
            with pytest.raises(Exception, match="Expected Container"):
                await mcp.call_tool("handle")
        finally:
            await container.close()

    asyncio.run(scenario())


def test_missing_setup_dishka_reports_container_error() -> None:
    async def scenario() -> None:
        mcp = FastMCP("test", mask_error_details=False)

        @mcp.tool
        @inject
        async def handle(request_dep: FromDishka[RequestDep]) -> None:
            del request_dep

        with pytest.raises(Exception, match="Container not found"):
            await mcp.call_tool("handle")

    asyncio.run(scenario())


def test_nested_fastmcp_operation_gets_its_own_request_context() -> None:
    async def scenario() -> None:
        provider = AppProvider()
        container = make_async_container(provider, FastMCPProvider())
        mcp = FastMCP("test")
        setup_dishka(container, mcp)

        @mcp.resource("data://items/{name}")
        @inject
        async def item_resource(
            name: str,
            read_uri: FromDishka[ReadUriDep],
        ) -> str:
            del name
            return str(read_uri)

        @mcp.tool
        @inject
        async def read_item(context: FromDishka[Context]) -> str:
            result = await context.read_resource("data://items/nested")
            return str(result.contents[0].content)

        try:
            result = await mcp.call_tool("read_item")

            assert result.content[0].text == "data://items/nested"
        finally:
            await container.close()

    asyncio.run(scenario())


def test_inject_copies_fastmcp_metadata() -> None:
    def my_func() -> None:
        pass

    my_func.__fastmcp__ = {"type": "tool"}  # type: ignore[attr-defined]

    injected = inject(my_func)
    assert getattr(injected, "__fastmcp__", None) == {"type": "tool"}


def test_build_context_data_without_fastmcp_context() -> None:
    from fastmcp.server.middleware import MiddlewareContext

    context_mock = Mock()
    context_mock.message = "test_message"
    context_mock.fastmcp_context = None

    result = _build_context_data(context_mock)

    assert result[MiddlewareContext] == context_mock
    assert result[str] == "test_message"
    assert Context not in result
    assert FastMCP not in result


def test_get_container_without_fastmcp_context_raises() -> None:
    with pytest.raises(DishkaError, match="FastMCP Context is not available"):
        get_container()


def test_async_middleware_without_fastmcp_context() -> None:
    from fastmcp.server.middleware import MiddlewareContext

    async def scenario() -> None:
        provider = AppProvider()
        container = make_async_container(provider, FastMCPProvider())
        middleware = DishkaAsyncMiddleware(container)
        context = MiddlewareContext(message=Mock(), fastmcp_context=None)

        async def call_next(_: MiddlewareContext[Any]) -> str:
            return "ok"

        try:
            result = await middleware._run_with_container(context, call_next)
            assert result == "ok"
        finally:
            await container.close()

    asyncio.run(scenario())


def test_sync_middleware_without_fastmcp_context() -> None:
    from fastmcp.server.middleware import MiddlewareContext

    async def scenario() -> None:
        provider = AppProvider()
        container = make_container(provider, FastMCPProvider())
        middleware = DishkaSyncMiddleware(container)
        context = MiddlewareContext(message=Mock(), fastmcp_context=None)

        async def call_next(_: MiddlewareContext[Any]) -> str:
            return "ok"

        try:
            result = await middleware._run_with_container(context, call_next)
            assert result == "ok"
        finally:
            container.close()

    asyncio.run(scenario())


def test_async_initialize_uses_session_scope() -> None:
    from fastmcp.server.middleware import MiddlewareContext

    async def scenario() -> None:
        provider = AppProvider()
        container = make_async_container(provider, FastMCPProvider())
        middleware = DishkaAsyncMiddleware(container)
        mcp = FastMCP("test")

        async with Context(fastmcp=mcp) as fastmcp_context:
            context = MiddlewareContext(
                message=Mock(),
                fastmcp_context=fastmcp_context,
                method="initialize",
            )

            async def call_next(_: MiddlewareContext[Any]) -> None:
                current = get_container()
                assert isinstance(current, AsyncContainer)
                return None

            try:
                result = await middleware.on_initialize(context, call_next)
                assert result is None
            finally:
                await container.close()

    asyncio.run(scenario())


def test_sync_initialize_uses_session_scope() -> None:
    from fastmcp.server.middleware import MiddlewareContext

    async def scenario() -> None:
        provider = AppProvider()
        container = make_container(provider, FastMCPProvider())
        middleware = DishkaSyncMiddleware(container)
        mcp = FastMCP("test")

        async with Context(fastmcp=mcp) as fastmcp_context:
            context = MiddlewareContext(
                message=Mock(),
                fastmcp_context=fastmcp_context,
                method="initialize",
            )

            async def call_next(_: MiddlewareContext[Any]) -> None:
                current = get_container()
                assert isinstance(current, Container)
                return None

            try:
                result = await middleware.on_initialize(context, call_next)
                assert result is None
            finally:
                container.close()

    asyncio.run(scenario())
