import json
import pytest
from tools.items import handle, TOOLS


def test_tools_defined():
    names = [t.name for t in TOOLS]
    for name in ["get_items", "get_item", "search_items", "create_item", "update_item"]:
        assert name in names


def test_get_items(mock_client):
    mock_client.get_items.return_value = [{"id": 10}, {"id": 11}]
    result = handle("get_items", {"project_id": 1})
    payload = json.loads(result[0].text)
    assert payload["meta"]["total"] == 2
    mock_client.get_items.assert_called_once_with(project_id=1, start_at=0, max_results=50)


def test_get_items_with_start_at(mock_client):
    mock_client.get_items.return_value = []
    handle("get_items", {"project_id": 1, "start_at": 50})
    mock_client.get_items.assert_called_once_with(project_id=1, start_at=50, max_results=50)


def test_get_item(mock_client):
    mock_client.get_item.return_value = {"id": 10, "fields": {"name": "REQ-001"}}
    result = handle("get_item", {"item_id": 10})
    payload = json.loads(result[0].text)
    assert payload["data"]["id"] == 10
    assert "meta" not in payload


def test_search_items(mock_client):
    mock_client.get_abstract_items.return_value = [{"id": 5}]
    result = handle("search_items", {"project_id": 1, "query": "brake*"})
    payload = json.loads(result[0].text)
    assert payload["meta"]["total"] == 1
    mock_client.get_abstract_items.assert_called_once_with(project=[1], contains="brake*")


def test_create_item(mock_client):
    mock_client.post_item.return_value = {"id": 99}
    result = handle("create_item", {
        "project_id": 1,
        "item_type_id": 42,
        "parent_id": 7,
        "fields": {"name": "New Req"},
    })
    payload = json.loads(result[0].text)
    assert payload["data"]["id"] == 99


def test_update_item(mock_client):
    mock_client.put_item.return_value = {"id": 10}
    result = handle("update_item", {"item_id": 10, "fields": {"name": "Updated"}})
    payload = json.loads(result[0].text)
    assert payload["data"]["id"] == 10


def test_api_error_returns_err(mock_client):
    mock_client.get_item.side_effect = Exception("Not found")
    result = handle("get_item", {"item_id": 999})
    payload = json.loads(result[0].text)
    assert payload["code"] == 500
