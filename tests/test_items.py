import json
import pytest
import requests
from tools.jama_client import JamaClient
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
        "location": {"parent": {"item": 7}},
        "fields": {"name": "New Req"},
    }


def test_update_item(mock_client):
    mock_client.get_item.return_value = {
        "project": 1, "itemType": 42,
        "location": {"parent": {"item": 7}},
        "fields": {"name": "Original"},
    }
    mock_client.put_item.return_value = {"id": 10}
    result = handle("update_item", {"item_id": 10, "fields": {"name": "Updated"}})
    payload = json.loads(result[0].text)
    assert payload["data"]["id"] == 10


@pytest.mark.parametrize("parent", [{"item": 7}, {"project": 1}])
@pytest.mark.parametrize("child_type", [None, 43])
def test_update_item_sends_expected_api_request(monkeypatch, parent, child_type):
    """SDK の必須引数を満たし、未指定フィールドと配置を保持する。"""
    current_item = {
        "id": 10,
        "project": 1,
        "itemType": 42,
        "location": {"parent": parent},
        "fields": {"name": "Original", "description": "Keep this"},
    }
    if child_type is not None:
        current_item["childItemType"] = child_type
    sent_requests = []

    def fake_send(session, request, **kwargs):
        sent_requests.append(request)
        response = requests.Response()
        response.request = request
        if request.method == "GET":
            response.status_code = 200
            response._content = json.dumps({"data": current_item}).encode()
        elif request.method == "PUT":
            response.status_code = 204
            response._content = b""
        else:
            pytest.fail(f"Unexpected HTTP method: {request.method}")
        return response

    monkeypatch.setattr(requests.Session, "send", fake_send)
    monkeypatch.setattr(config, "_client", JamaClient(
        "https://jama.invalid", credentials=("test-user", "test-password"), oauth=False,
    ))

    result = handle("update_item", {"item_id": 10, "fields": {"name": "Updated"}})

    assert json.loads(result[0].text) == {"data": 204}
    assert [r.method for r in sent_requests] == ["GET", "PUT"]
    assert all(r.url == "https://jama.invalid/rest/v1/items/10" for r in sent_requests)
    assert json.loads(sent_requests[1].body) == {
        "project": 1,
        "itemType": 42,
        "childItemType": child_type,
        "location": {"parent": parent},
        "fields": {"name": "Updated", "description": "Keep this"},
    }


def test_update_item_does_not_write_when_fetch_fails(mock_client):
    mock_client.get_item.side_effect = Exception("Not found")
    result = handle("update_item", {"item_id": 999, "fields": {"name": "Updated"}})
    assert json.loads(result[0].text) == {"error": "Not found", "code": 500}
    mock_client.put_item.assert_not_called()


def test_api_error_returns_err(mock_client):
    mock_client.get_item.side_effect = Exception("Not found")
    result = handle("get_item", {"item_id": 999})
    payload = json.loads(result[0].text)
    assert payload["code"] == 500
