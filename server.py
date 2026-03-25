import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

import tools.projects as _projects
import tools.items as _items
import tools.relations as _relations
import tools.tests as _tests
import tools.comments as _comments

_MODULES = [_projects, _items, _relations, _tests, _comments]

ALL_TOOLS: list[types.Tool] = []
for _mod in _MODULES:
    ALL_TOOLS.extend(_mod.TOOLS)

server = Server("jama")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return ALL_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    return await _dispatch(name, arguments)


async def _dispatch(name: str, arguments: dict) -> list[types.TextContent]:
    for mod in _MODULES:
        if any(t.name == name for t in mod.TOOLS):
            return mod.handle(name, arguments)
    return [types.TextContent(
        type="text",
        text='{"error": "Unknown tool: ' + name + '", "code": 404}',
    )]


if __name__ == "__main__":
    asyncio.run(stdio_server(server))
