"""SDK をモックせず HTTP 境界でツールのリクエストを検証する。"""
import json
from urllib.parse import parse_qs, urlparse

import pytest
import requests

import config
from tools import comments, items, relations, tests as test_tools


@pytest.mark.parametrize("module,name,args,method,path,query,body,response_data,want", [
    (relations, "delete_relationship", {"relationship_id": 55}, "DELETE", "relationships/55", {}, None, None, None),
    (comments, "add_comment", {"item_id": 10, "comment": "one\ntwo"}, "POST", "comments", {},
     {"body": {"text": "one<br>two"}, "location": {"item": 10}, "commentType": "GENERAL"}, {"meta": {"id": 7}}, 7),
    (test_tools, "get_test_plans", {"project_id": 1}, "GET", "testplans", {"project": ["1"], "startAt": ["0"], "maxResults": ["50"]}, None, {"data": [{"id": 3}]}, [{"id": 3}]),
    (test_tools, "create_test_plan", {"project_id": 1, "name": "Plan", "description": "Description"}, "POST", "testplans", {},
     {"project": 1, "fields": {"name": "Plan", "description": "Description"}}, {"meta": {"id": 3}}, 3),
    (test_tools, "create_test_plan", {"project_id": 1, "name": "Plan"}, "POST", "testplans", {},
     {"project": 1, "fields": {"name": "Plan"}}, {"meta": {"id": 3}}, 3),
    (test_tools, "get_test_cycles", {"test_plan_id": 3}, "GET", "testplans/3/testcycles", {"startAt": ["0"], "maxResults": ["50"]}, None, {"data": [{"id": 4}]}, [{"id": 4}]),
    (test_tools, "get_test_runs", {"test_cycle_id": 4, "start_at": 50}, "GET", "testcycles/4/testruns", {"startAt": ["50"], "maxResults": ["50"]}, None, {"data": [{"id": 5}]}, [{"id": 5}]),
    (test_tools, "create_test_result", {"test_run_id": 5, "status": "PASSED", "actual_results": "OK"}, "PUT", "testruns/5", {},
     {"fields": {"testRunStatus": "PASSED", "actualResults": "OK"}}, None, 200),
])
def test_tool_sends_expected_request(monkeypatch, module, name, args, method, path, query, body, response_data, want):
    sent = []

    def send(session, request, **kwargs):
        sent.append(request)
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(response_data).encode() if response_data else b""
        response.request = request
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    monkeypatch.setattr(config, "_client", config.JamaClient(
        "https://jama.invalid", credentials=("user", "password"), oauth=False,
    ))
    result = json.loads(module.handle(name, args)[0].text)
    assert result.get("data") == want and "error" not in result, result
    assert len(sent) == 1
    request = sent[0]
    url = urlparse(request.url)
    assert request.method == method
    assert url.path == f"/rest/v1/{path}"
    assert parse_qs(url.query) == query
    assert (json.loads(request.body) if request.body else None) == body
    if name == "create_test_result":
        assert request.headers.get("x-jama-date-fields-with-time") == "true"


def test_relationships_uses_last_id_cursor(monkeypatch):
    queries = []
    pages = [
        {"data": [{"id": 2}, {"id": 7}], "meta": {"pageInfo": {"totalResults": 3}}},
        {"data": [{"id": 11}], "meta": {"pageInfo": {"totalResults": 3}}},
    ]

    def send(session, request, **kwargs):
        queries.append(parse_qs(urlparse(request.url).query))
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(pages[len(queries) - 1]).encode()
        response.request = request
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    monkeypatch.setattr(config, "_client", config.JamaClient("https://jama.invalid", ("u", "p")))
    result = json.loads(relations.handle("get_relationships", {"project_id": 1})[0].text)
    assert result == {"data": [{"id": 2}, {"id": 7}, {"id": 11}], "meta": {"total": 3}}
    assert queries == [
        {"project": ["1"], "lastId": ["0"], "maxResults": ["50"]},
        {"project": ["1"], "lastId": ["7"], "maxResults": ["50"]},
    ]


def test_test_plans_follows_server_page_info(monkeypatch):
    starts = []

    def send(session, request, **kwargs):
        start = int(parse_qs(urlparse(request.url).query)["startAt"][0])
        starts.append(start)
        data = [{"id": 1}, {"id": 2}] if start == 0 else [{"id": 3}]
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps({"data": data, "meta": {"pageInfo": {
            "startIndex": start, "resultCount": len(data), "totalResults": 3,
        }}}).encode()
        response.request = request
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    client = config.JamaClient("https://jama.invalid", ("u", "p"))
    assert client.get_test_plans(1) == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert starts == [0, 2]


def test_rest_api_error_is_not_reported_as_success(monkeypatch):
    def send(session, request, **kwargs):
        response = requests.Response()
        response.status_code = 403
        response._content = b'{"meta": {"message": "Forbidden"}}'
        response.request = request
        response.url = request.url
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    monkeypatch.setattr(config, "_client", config.JamaClient("https://jama.invalid", ("u", "p")))
    result = json.loads(comments.handle("add_comment", {"item_id": 1, "comment": "hello"})[0].text)
    assert result["code"] == 500
    assert "403" in result["error"]
    assert "data" not in result


def test_item_update_preserves_datetime_header_and_value(monkeypatch):
    sent = []
    timestamp = "2026-01-02T13:14:15.123+0000"

    def send(session, request, **kwargs):
        sent.append(request)
        response = requests.Response()
        response.request = request
        response.status_code = 200 if request.method == "GET" else 204
        response._content = json.dumps({"data": {
            "project": 1, "itemType": 42, "location": {"parent": {"item": 7}},
            "fields": {"name": "Before", "customDatetime": timestamp},
        }}).encode() if request.method == "GET" else b""
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    monkeypatch.setattr(config, "_client", config.JamaClient("https://jama.invalid", ("u", "p")))
    result = json.loads(items.handle(
        "update_item", {"item_id": 10, "fields": {"name": "After"}},
    )[0].text)
    assert result == {"data": 204}
    assert [r.method for r in sent] == ["GET", "PUT"]
    assert all(r.headers.get("x-jama-date-fields-with-time") == "true" for r in sent)
    assert json.loads(sent[1].body)["fields"] == {"name": "After", "customDatetime": timestamp}
