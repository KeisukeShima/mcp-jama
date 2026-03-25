import json
import asyncio
import pytest
from unittest.mock import patch, MagicMock
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
