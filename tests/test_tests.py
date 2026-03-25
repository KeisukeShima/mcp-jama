import json
import pytest
from tools.tests import handle, TOOLS

VALID_STATUSES = ["PASSED", "FAILED", "BLOCKED", "NOT_RUN", "INPROGRESS"]


def test_tools_defined():
    names = [t.name for t in TOOLS]
    for name in ["get_test_plans", "create_test_plan", "get_test_cycles", "get_test_runs", "create_test_result"]:
        assert name in names


def test_get_test_plans(mock_client):
    mock_client.get_test_plans.return_value = [{"id": 1}]
    result = handle("get_test_plans", {"project_id": 1})
    payload = json.loads(result[0].text)
    assert payload["meta"]["total"] == 1


def test_create_test_plan(mock_client):
    mock_client.post_test_plan.return_value = {"id": 10}
    result = handle("create_test_plan", {"project_id": 1, "name": "Sprint 1"})
    payload = json.loads(result[0].text)
    assert payload["data"]["id"] == 10


def test_create_test_plan_with_description(mock_client):
    mock_client.post_test_plan.return_value = {"id": 11}
    handle("create_test_plan", {"project_id": 1, "name": "Sprint 2", "description": "Desc"})
    mock_client.post_test_plan.assert_called_once_with(
        project_id=1, name="Sprint 2", description="Desc"
    )


def test_create_test_plan_without_description(mock_client):
    mock_client.post_test_plan.return_value = {"id": 12}
    handle("create_test_plan", {"project_id": 1, "name": "Sprint 3"})
    call_args = mock_client.post_test_plan.call_args
    assert "description" not in call_args.kwargs


def test_get_test_cycles(mock_client):
    mock_client.get_test_cycles.return_value = [{"id": 2}]
    result = handle("get_test_cycles", {"test_plan_id": 1})
    payload = json.loads(result[0].text)
    assert payload["meta"]["total"] == 1


def test_get_test_runs(mock_client):
    mock_client.get_test_runs.return_value = [{"id": 3}]
    result = handle("get_test_runs", {"test_cycle_id": 2})
    payload = json.loads(result[0].text)
    assert payload["meta"]["total"] == 1
    mock_client.get_test_runs.assert_called_once_with(test_cycle_id=2, start_at=0, max_results=50)


def test_create_test_result_valid_status(mock_client):
    mock_client.post_test_run_results.return_value = {"id": 99}
    result = handle("create_test_result", {
        "test_run_id": 3, "status": "PASSED", "actual_results": "All checks passed."
    })
    payload = json.loads(result[0].text)
    assert payload["data"]["id"] == 99


def test_create_test_result_invalid_status(mock_client):
    result = handle("create_test_result", {
        "test_run_id": 3, "status": "UNKNOWN", "actual_results": "?"
    })
    payload = json.loads(result[0].text)
    assert payload["code"] == 400
    assert "UNKNOWN" in payload["error"]


def test_api_error(mock_client):
    mock_client.get_test_plans.side_effect = Exception("Server error")
    result = handle("get_test_plans", {"project_id": 1})
    payload = json.loads(result[0].text)
    assert payload["code"] == 500
