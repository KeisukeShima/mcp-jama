from mcp import types
from config import get_client
from tools.helpers import _ok, _err

TOOLS: list[types.Tool] = [
    types.Tool(
        name="get_items",
        description="プロジェクトのアイテム一覧を取得する（最大50件）。全件取得は start_at を増やして繰り返す。",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "integer"},
                "start_at": {"type": "integer", "default": 0},
            },
            "required": ["project_id"],
        },
    ),
    types.Tool(
        name="get_item",
        description="アイテムの詳細を取得する",
        inputSchema={
            "type": "object",
            "properties": {"item_id": {"type": "integer"}},
            "required": ["item_id"],
        },
    ),
    types.Tool(
        name="search_items",
        description="アイテムをキーワード検索する。query は contains パラメータにマップされ、ワイルドカード（例: brake*）が使用可能。",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "integer"},
                "query": {"type": "string"},
            },
            "required": ["project_id", "query"],
        },
    ),
    types.Tool(
        name="create_item",
        description="アイテムを作成する。parent_id はプロジェクトツリー上の親ノードで必須。",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "integer"},
                "item_type_id": {"type": "integer"},
                "parent_id": {"type": "integer"},
                "fields": {"type": "object"},
            },
            "required": ["project_id", "item_type_id", "parent_id", "fields"],
        },
    ),
    types.Tool(
        name="update_item",
        description="アイテムのフィールドを更新する",
        inputSchema={
            "type": "object",
            "properties": {
                "item_id": {"type": "integer"},
                "fields": {"type": "object"},
            },
            "required": ["item_id", "fields"],
        },
    ),
]


def handle(name: str, args: dict) -> list[types.TextContent]:
    try:
        if name == "get_items":
            items = get_client().get_items(
                project_id=args["project_id"],
                start_at=args.get("start_at", 0),
                max_results=50,
            )
            return _ok(items, total=len(items))
        if name == "get_item":
            item = get_client().get_item(args["item_id"])
            return _ok(item)
        if name == "search_items":
            items = get_client().get_abstract_items(
                project=[args["project_id"]],
                contains=args["query"],
            )
            return _ok(items, total=len(items))
        if name == "create_item":
            item = get_client().post_item(
                project_id=args["project_id"],
                item_type_id=args["item_type_id"],
                child_item_type_id=None,
                location={"parent": {"id": args["parent_id"]}},
                fields=args["fields"],
            )
            return _ok(item)
        if name == "update_item":
            item = get_client().put_item(
                item_id=args["item_id"],
                fields=args["fields"],
            )
            return _ok(item)
    except Exception as e:
        return _err(str(e))
    return _err(f"Unknown tool: {name}", code=404)
