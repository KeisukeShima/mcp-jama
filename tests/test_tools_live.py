"""全ツールの実 API 検証。専用データだけを作成・変更・削除する。"""
import json
import os
import time
from datetime import date
from uuid import uuid4

import pytest

from tools import comments, items, projects, relations, tests as test_tools

pytestmark = pytest.mark.skipif(
    os.environ.get("JAMA_RUN_LIVE") != "1",
    reason="JAMA_RUN_LIVE=1 で実環境テストを有効化する",
)


def call(module, tool_name, **args):
    payload = json.loads(module.handle(tool_name, args)[0].text)
    assert "error" not in payload, payload
    return payload


@pytest.fixture
def workspace(live_client):
    client, project_id = live_client
    created = []
    name = f"mcp-jama-live-{uuid4().hex}"

    def remember(resource, resource_id):
        created.append((resource, resource_id))
        print(f"Created {resource}/{resource_id}", flush=True)
        return resource_id

    def create(resource, body):
        resource_id = client._request("post", resource, json=body).json()["meta"]["id"]
        return remember(resource, resource_id)

    root_id = None
    try:
        root_id = create("items", {
            "project": project_id, "itemType": 30,
            "location": {"parent": {"project": project_id}},
            "fields": {"name": name},
        })
        yield client, project_id, root_id, name, create, remember
    finally:
        failures = []
        for resource, resource_id in reversed(created):
            path = f"{resource}/{resource_id}"
            try:
                deleted = client._rest.delete(path, timeout=30)
                assert deleted.status_code in (200, 204, 404), deleted.status_code
                response = client._rest.get(path, timeout=30)
                assert response.status_code == 404, f"Unexpected post-delete status: {response.status_code}"
                print(f"Deleted {path}", flush=True)
            except Exception as error:
                failures.append(f"{path}: {error}")
        assert not failures, "後片付けに失敗: " + "; ".join(failures)


def test_read_tools_and_create_item(workspace):
    client, project_id, root_id, name, _, remember = workspace
    child_id = call(items, "create_item", project_id=project_id,
                    item_type_id=30, parent_id=root_id, fields={"name": f"{name}-child"})["data"]
    remember("items", child_id)
    child = call(items, "get_item", item_id=child_id)["data"]
    assert child["fields"]["name"] == f"{name}-child"
    assert child["location"]["parent"] == {"item": root_id}
    assert child["project"] == project_id

    found = []
    # 検索インデックスの反映待ち。更新 API 自体は再試行しない。
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        found = call(items, "search_items", project_id=project_id, query=f"{name}-child")["data"]
        if child_id in {item["id"] for item in found}:
            break
        time.sleep(1)
    assert child_id in {item["id"] for item in found}

    listed = call(items, "get_items", project_id=project_id)
    assert 0 < len(listed["data"]) <= 50
    assert listed["meta"]["total"] >= len(listed["data"])
    assert all(item["project"] == project_id for item in listed["data"])
    assert project_id in {p["id"] for p in call(projects, "get_projects")["data"]}


def test_comment_persists(workspace):
    client, _, root_id, name, _, remember = workspace
    comment_id = call(comments, "add_comment", item_id=root_id, comment=f"{name}\nsecond line")["data"]
    # コメントを削除する公開 API はないため、ID を記録し親アイテムを削除する。
    print(f"Created comment: {comment_id} (parent item will be deleted)", flush=True)
    saved = client._request("get", f"comments/{comment_id}").json()["data"]
    assert saved["location"]["item"] == root_id
    assert name in saved["body"]["text"]
    assert "second line" in saved["body"]["text"]
    assert "<br" in saved["body"]["text"]
    assert comment_id in {c["id"] for c in client._list(f"items/{root_id}/comments")}


def test_relationship_lifecycle(workspace):
    client, project_id, root_id, name, create, remember = workspace
    child_id = create("items", {
        "project": project_id, "itemType": 30,
        "location": {"parent": {"item": root_id}}, "fields": {"name": name + "-target"},
    })
    relationship_types = client.get_relationship_types()
    assert relationship_types
    relationship_id = call(relations, "create_relationship", from_item_id=root_id,
                           to_item_id=child_id, relationship_type_id=relationship_types[0]["id"])["data"]
    remember("relationships", relationship_id)
    saved = client.get_relationship(relationship_id)
    assert saved["fromItem"] == root_id
    assert saved["toItem"] == child_id
    assert saved["relationshipType"] == relationship_types[0]["id"]
    assert relationship_id in {r["id"] for r in call(relations, "get_relationships", project_id=project_id)["data"]}
    call(relations, "delete_relationship", relationship_id=relationship_id)
    response = client._rest.get(f"relationships/{relationship_id}", timeout=30)
    assert response.status_code == 404


@pytest.mark.parametrize("with_description", [False, True])
def test_create_test_plan_persists(workspace, with_description):
    client, project_id, _, name, _, remember = workspace
    args = {"project_id": project_id, "name": name}
    if with_description:
        args["description"] = "<p>Live test plan description</p>"
    plan_id = call(test_tools, "create_test_plan", **args)["data"]
    remember("testplans", plan_id)
    saved = client._request("get", f"testplans/{plan_id}").json()["data"]
    assert saved["project"] == project_id
    assert saved["fields"]["name"] == name
    if with_description:
        assert "Live test plan description" in saved["fields"]["description"]
    assert plan_id in {p["id"] for p in call(test_tools, "get_test_plans", project_id=project_id)["data"]}


def test_test_management_workflow(workspace):
    client, project_id, root_id, name, create, remember = workspace
    # 組織固有の型 ID は保存せず、追加の必須フィールドがない Test Case 型を選ぶ。
    case_type = None
    for candidate in client.get_item_types():
        if candidate.get("category") != "TEST_CASE":
            continue
        definition = client.get_item_type(candidate["id"])
        if all(not f.get("required") or f.get("readOnly") or f["name"] == "name"
               for f in definition["fields"]):
            case_type = candidate["id"]
            break
    assert case_type is not None, "追加の必須フィールドがない Test Case 型が必要です"
    set_id = create("items", {
        "project": project_id, "itemType": 31, "childItemType": case_type,
        "location": {"parent": {"item": root_id}},
        "fields": {"name": name + "-cases", "setKey": "MCP" + uuid4().hex[:6]},
    })
    case_id = create("items", {
        "project": project_id, "itemType": case_type,
        "location": {"parent": {"item": set_id}},
        "fields": {"name": name + "-case", "description": "<p>Live API test case</p>"},
    })
    plan_id = call(test_tools, "create_test_plan", project_id=project_id, name=name)["data"]
    remember("testplans", plan_id)
    groups = client._list(f"testplans/{plan_id}/testgroups")
    if groups:
        group_id = groups[0]["id"]
    else:
        group_id = client._request("post", f"testplans/{plan_id}/testgroups",
                                   json={"name": name}).json()["meta"]["id"]
    client._request("post", f"testplans/{plan_id}/testgroups/{group_id}/testcases", json={"testCase": case_id})
    today = date.today().isoformat()
    cycle_id = client.post_testplans_testcycles(plan_id, name, today, today)
    remember("testcycles", cycle_id)
    assert cycle_id in {c["id"] for c in call(test_tools, "get_test_cycles", test_plan_id=plan_id)["data"]}
    runs = call(test_tools, "get_test_runs", test_cycle_id=cycle_id)["data"]
    assert len(runs) == 1
    run_id = runs[0]["id"]
    remember("testruns", run_id)
    assert call(test_tools, "get_test_runs", test_cycle_id=cycle_id, start_at=50)["data"] == []
    for status in sorted(test_tools.VALID_STATUSES):
        actual = f"{name}: {status}"
        result = call(test_tools, "create_test_result", test_run_id=run_id, status=status, actual_results=actual)
        assert 200 <= result["data"] < 300
        saved = client._request("get", f"testruns/{run_id}").json()["data"]
        assert saved["fields"]["testRunStatus"] == status, saved["fields"]
        assert actual in saved["fields"]["actualResults"]
        assert saved["fields"]["testCase"] == case_id
        assert saved["fields"]["name"] == runs[0]["fields"]["name"]
        print(f"Verified test result: {status}", flush=True)
