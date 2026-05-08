from dishka import Provider, Scope, make_async_container, provide
from fastmcp import FastMCP
from fastmcp.server.context import Context
from fastmcp.server.middleware import MiddlewareContext

from fastmcp_dishka import FastMCPProvider, FromDishka, inject, setup_dishka


class GreetingService:
    def __init__(self, request_name: str) -> None:
        self._request_name = request_name

    def greet(self, name: str) -> str:
        return f"Hello, {name}! (request={self._request_name})"


class CounterService:
    def __init__(self) -> None:
        self._count = 0

    def increment(self) -> int:
        self._count += 1
        return self._count


class AppProvider(Provider):
    scope = Scope.APP

    @provide(scope=Scope.REQUEST)
    def greeting_service(
        self,
        context: Context,
        middleware_context: MiddlewareContext,
    ) -> GreetingService:
        request_name = middleware_context.method or context.fastmcp.name
        return GreetingService(request_name=request_name)

    counter_service = provide(CounterService)


mcp = FastMCP("DishkaFastMCP")

provider = AppProvider()
container = make_async_container(provider, FastMCPProvider())
setup_dishka(container=container, app=mcp)


@mcp.tool
@inject
async def greet(
    name: str,
    greeting: FromDishka[GreetingService],
    counter: FromDishka[CounterService],
) -> str:
    count = counter.increment()
    return f"{greeting.greet(name)} count={count}"


@mcp.resource("data://greetings/{name}")
@inject
async def greeting_resource(
    name: str,
    greeting: FromDishka[GreetingService],
) -> str:
    return greeting.greet(name)


@mcp.prompt
@inject
async def greeting_prompt(
    name: str,
    greeting: FromDishka[GreetingService],
) -> str:
    return f"Write a short friendly welcome message for: {greeting.greet(name)}"


if __name__ == "__main__":
    mcp.run()
