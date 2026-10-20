import json
import asyncio
from datetime import timedelta
from pathlib import Path
import sys
import pytest
from unittest.mock import patch, MagicMock
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import types


def test_all_tools_registered():
    """全15ツールが server に登録されている"""
    import server
    tool_names = {t.name for t in server.ALL_TOOLS}
    expected = {
        "get_projects",
        "get_items", "get_item", "search_items", "create_item", "update_item",
        "get_relationships", "create_relationship", "delete_relationship",
        "get_test_plans", "create_test_plan", "get_test_cycles", "get_test_runs", "create_test_result",
        "add_comment",
    }
    assert tool_names == expected


def test_dispatch_routes_to_correct_module(mock_client):
    """call_tool が正しいモジュールの handle() を呼ぶ"""
    import server
    mock_client.get_projects.return_value = [{"id": 1}]
    result = asyncio.run(server._dispatch("get_projects", {}))
    payload = json.loads(result[0].text)
    assert "data" in payload


def test_dispatch_unknown_tool():
    import server
    result = asyncio.run(server._dispatch("no_such_tool", {}))
    payload = json.loads(result[0].text)
    assert payload["code"] == 404


def test_stdio_server_from_another_directory(tmp_path):
    """別の作業ディレクトリでも初期化、ツール一覧取得、呼び出しができる。"""
    missing_config = tmp_path / "missing-config.json"
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).resolve().parents[1] / "server.py")],
        env={"JAMA_CONFIG": str(missing_config)},
        cwd=str(tmp_path),
    )

    async def check_session():
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(
                read_stream,
                write_stream,
                read_timeout_seconds=timedelta(seconds=10),
            ) as session:
                initialized = await session.initialize()
                assert initialized.serverInfo.name == "jama"
                assert initialized.capabilities.tools is not None

                listed = await session.list_tools()
                assert len(listed.tools) == 15
                assert {"get_projects", "create_item", "create_relationship"} <= {
                    tool.name for tool in listed.tools
                }

                # 設定ファイルがなくてもサーバーは起動し、エラーを MCP 経由で返す。
                result = await session.call_tool("get_projects", {})
                payload = json.loads(result.content[0].text)
                assert payload["code"] == 500
                assert str(missing_config) in payload["error"]

    asyncio.run(asyncio.wait_for(check_session(), timeout=20))
