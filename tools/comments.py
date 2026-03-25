from mcp import types
from config import get_client
from tools.helpers import _ok, _err

TOOLS: list[types.Tool] = [
    types.Tool(
        name="add_comment",
        description="アイテムにコメントを追加する。改行は自動的に <br> に変換される。",
        inputSchema={
            "type": "object",
            "properties": {
                "item_id": {"type": "integer"},
                "comment": {"type": "string"},
            },
            "required": ["item_id", "comment"],
        },
    ),
]


def handle(name: str, args: dict) -> list[types.TextContent]:
    if name == "add_comment":
        try:
            comment_body = args["comment"].replace("\n", "<br>")
            result = get_client().post_item_comment(
                item_id=args["item_id"],
                comment=comment_body,
            )
            return _ok(result)
        except Exception as e:
            return _err(str(e))
    return _err(f"Unknown tool: {name}", code=404)
