import json
import pytest
import requests
from py_jama_rest_client.client import JamaClient
import config
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
    assert payload["data"] == [{"id": 10}, {"id": 11}]
    mock_client.get_items.assert_called_once_with(project_id=1)


def test_get_items_with_start_at(mock_client):
    mock_client.get_items.return_value = [{"id": i} for i in range(73)]
    result = handle("get_items", {"project_id": 1, "start_at": 50})
    payload = json.loads(result[0].text)
    assert len(payload["data"]) == 23
    assert payload["data"][0] == {"id": 50}
    assert payload["data"][-1] == {"id": 72}
    assert payload["meta"]["total"] == 73
    mock_client.get_items.assert_called_once_with(project_id=1)


def test_get_items_limits_response_to_one_page(mock_client):
    mock_client.get_items.return_value = [{"id": i} for i in range(51)]
    result = handle("get_items", {"project_id": 1})
    payload = json.loads(result[0].text)
    assert len(payload["data"]) == 50
    assert payload["data"][0] == {"id": 0}
    assert payload["data"][-1] == {"id": 49}
    assert payload["meta"]["total"] == 51


def test_get_items_start_at_past_end(mock_client):
    mock_client.get_items.return_value = [{"id": 10}]
    result = handle("get_items", {"project_id": 1, "start_at": 50})
    payload = json.loads(result[0].text)
    assert payload == {"data": [], "meta": {"total": 1}}


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


def test_create_item_sends_expected_api_request(monkeypatch):
    """実際の SDK を通し、引数名と parent の JSON 構造を検証する。"""
    sent_requests = []

    def fake_send(session, request, **kwargs):
        sent_requests.append(request)
        response = requests.Response()
        response.status_code = 201
        response._content = b'{"meta": {"id": 99}}'
        response.request = request
        return response

    monkeypatch.setattr(requests.Session, "send", fake_send)
    monkeypatch.setattr(config, "_client", JamaClient(
        "https://jama.invalid", credentials=("test-user", "test-password"), oauth=False,
    ))

    result = handle("create_item", {
        "project_id": 1,
        "item_type_id": 42,
        "parent_id": 7,
        "fields": {"name": "New Req"},
    })

    assert json.loads(result[0].text) == {"data": 99}
    assert len(sent_requests) == 1
    request = sent_requests[0]
    assert request.method == "POST"
    assert request.url == "https://jama.invalid/rest/v1/items/"
    assert json.loads(request.body) == {
        "project": 1,
        "itemType": 42,
        "childItemType": None,
        "location": {"parent": {"id": 7}},
        "fields": {"name": "New Req"},
    }


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
