from mcp import types
from config import get_client
from tools.helpers import _ok, _err

TOOLS: list[types.Tool] = [
    types.Tool(
        name="get_relationships",
        description="プロジェクト内のリレーション（トレーサビリティリンク）一覧を取得する。特定アイテムのリンクを確認する場合は返された一覧から item_id でフィルタする。",
        inputSchema={
            "type": "object",
            "properties": {"project_id": {"type": "integer"}},
            "required": ["project_id"],
        },
    ),
    types.Tool(
        name="create_relationship",
        description="2つのアイテム間にトレーサビリティリンクを作成する",
        inputSchema={
            "type": "object",
            "properties": {
                "from_item_id": {"type": "integer"},
                "to_item_id": {"type": "integer"},
                "relationship_type_id": {"type": "integer"},
            },
            "required": ["from_item_id", "to_item_id", "relationship_type_id"],
        },
    ),
    types.Tool(
        name="delete_relationship",
        description="リレーションを削除する",
        inputSchema={
            "type": "object",
            "properties": {"relationship_id": {"type": "integer"}},
            "required": ["relationship_id"],
        },
    ),
]


def handle(name: str, args: dict) -> list[types.TextContent]:
    try:
        if name == "get_relationships":
            rels = get_client().get_relationships(project_id=args["project_id"])
            return _ok(rels, total=len(rels))
        if name == "create_relationship":
            rel = get_client().post_relationship(
                from_item=args["from_item_id"],
                to_item=args["to_item_id"],
                relationship_type=args["relationship_type_id"],
            )
            return _ok(rel)
        if name == "delete_relationship":
            get_client().delete_relationship(relationship_id=args["relationship_id"])
            return _ok(None)
    except Exception as e:
        return _err(str(e))
    return _err(f"Unknown tool: {name}", code=404)
