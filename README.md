<div align="center">

# FastMCP Dishka

[![CI](https://github.com/vfaddey/fastmcp-dishka/actions/workflows/ci.yml/badge.svg)](https://github.com/vfaddey/fastmcp-dishka/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/fastmcp-dishka.svg)](https://pypi.org/project/fastmcp-dishka/)
[![Python](https://img.shields.io/pypi/pyversions/fastmcp-dishka.svg)](https://pypi.org/project/fastmcp-dishka/)
[![License](https://img.shields.io/pypi/l/fastmcp-dishka.svg)](https://github.com/vfaddey/fastmcp-dishka/blob/main/LICENSE)
[![Ruff](https://img.shields.io/badge/lint-ruff-46a3ff.svg)](https://github.com/astral-sh/ruff)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](#development)

Integration package for using [dishka](https://dishka.readthedocs.io/) dependency
injection with [FastMCP](https://gofastmcp.com/) tools, resources, and prompts.

</div>

It provides:

* `FastMCPProvider` with FastMCP request context objects for dishka.
* `setup_dishka()` middleware that opens a `Scope.REQUEST` container per
  tool/resource/prompt call.
* `@inject` support for parameters marked as `FromDishka[T]`.

## Usage

```python
from dishka import Provider, Scope, make_async_container, provide
from fastmcp import FastMCP
from fastmcp_dishka import FastMCPProvider, FromDishka, inject, setup_dishka


class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


class AppProvider(Provider):
    greeting = provide(GreetingService, scope=Scope.REQUEST)


mcp = FastMCP("GreetMCP")
container = make_async_container(AppProvider(), FastMCPProvider())
setup_dishka(container, mcp)


@mcp.tool
@inject
async def greet(name: str, service: FromDishka[GreetingService]) -> str:
    return service.greet(name)
```

Place `@inject` below FastMCP decorators so FastMCP registers the wrapped
function signature.

`@mcp.prompt` defines a reusable prompt template exposed to MCP clients. A
prompt does not perform an action like a tool; it returns text or chat messages
that a client can insert into an LLM conversation.

```python
@mcp.prompt
@inject
async def welcome_prompt(
    name: str,
    service: FromDishka[GreetingService],
) -> str:
    return f"Write a short welcome message for: {service.greet(name)}"
```

See [examples/fastmcp_app.py](examples/fastmcp_app.py) for a complete FastMCP
server with a tool, resource, prompt, and Dishka providers.

## Development

Install development dependencies:

```bash
uv sync --dev
```

Run tests with coverage:

```bash
make test
```

Run linting and formatting:

```bash
make lint
make format
```

Install pre-commit hooks:

```bash
make pre-commit-install
```
