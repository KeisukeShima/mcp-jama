import json
from tools.relations import handle, TOOLS


def test_tools_defined():
    names = [t.name for t in TOOLS]
    for name in ["get_relationships", "create_relationship", "delete_relationship"]:
        assert name in names


def test_get_relationships(mock_client):
    mock_client.get_relationships.return_value = [
        {"id": 1, "fromItem": {"id": 10}, "toItem": {"id": 20}}
    ]
    result = handle("get_relationships", {"project_id": 1})
    payload = json.loads(result[0].text)
    assert payload["meta"]["total"] == 1
    mock_client.get_relationships.assert_called_once_with(project_id=1)


def test_create_relationship(mock_client):
    mock_client.post_relationship.return_value = {"id": 55}
    result = handle("create_relationship", {
        "from_item_id": 10,
        "to_item_id": 20,
        "relationship_type_id": 3,
    })
    payload = json.loads(result[0].text)
    assert payload["data"]["id"] == 55


def test_delete_relationship(mock_client):
    mock_client.delete_relationship.return_value = None
    result = handle("delete_relationship", {"relationship_id": 55})
    payload = json.loads(result[0].text)
    assert payload["data"] is None


def test_api_error(mock_client):
    mock_client.get_relationships.side_effect = Exception("Unauthorized")
    result = handle("get_relationships", {"project_id": 1})
    payload = json.loads(result[0].text)
    assert payload["code"] == 500
