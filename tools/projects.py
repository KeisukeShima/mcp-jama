from mcp import types
from config import get_client
from tools.helpers import _ok, _err

TOOLS: list[types.Tool] = [
    types.Tool(
        name="get_projects",
        description="JAMA プロジェクトの一覧を取得する",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


def handle(name: str, args: dict) -> list[types.TextContent]:
    if name == "get_projects":
        return _get_projects()
    return _err(f"Unknown tool: {name}", code=404)


def _get_projects() -> list[types.TextContent]:
    try:
        projects = get_client().get_projects()
        return _ok(projects, total=len(projects))
    except Exception as e:
        return _err(str(e))
