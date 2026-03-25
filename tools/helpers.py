import json
from mcp import types


def _ok(data, total=None) -> list[types.TextContent]:
    """成功レスポンス。リスト応答は total を設定、単一オブジェクトは meta を省略。"""
    payload: dict = {"data": data}
    if total is not None:
        payload["meta"] = {"total": total}
    return [types.TextContent(type="text", text=json.dumps(payload))]


def _err(message: str, code: int = 500) -> list[types.TextContent]:
    """エラーレスポンス。"""
    return [types.TextContent(type="text", text=json.dumps({"error": message, "code": code}))]
