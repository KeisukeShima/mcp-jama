import json
import pytest
from tools.projects import handle, TOOLS


def test_tools_defined():
    names = [t.name for t in TOOLS]
    assert "get_projects" in names


def test_get_projects(mock_client):
    mock_client.get_projects.return_value = [{"id": 1, "name": "ProjectA"}]
    result = handle("get_projects", {})
    payload = json.loads(result[0].text)
    assert payload["data"] == [{"id": 1, "name": "ProjectA"}]
    assert payload["meta"]["total"] == 1


def test_get_projects_api_error(mock_client):
    mock_client.get_projects.side_effect = Exception("Connection refused")
    result = handle("get_projects", {})
    payload = json.loads(result[0].text)
    assert payload["code"] == 500
    assert "Connection refused" in payload["error"]


def test_unknown_tool():
    result = handle("unknown_tool", {})
    payload = json.loads(result[0].text)
    assert payload["code"] == 404
