import json
from tools.comments import handle, TOOLS


def test_tools_defined():
    names = [t.name for t in TOOLS]
    assert "add_comment" in names


def test_add_comment_plain_text(mock_client):
    mock_client.post_item_comment.return_value = {"id": 7}
    result = handle("add_comment", {"item_id": 10, "comment": "LGTM"})
    payload = json.loads(result[0].text)
    assert payload["data"]["id"] == 7
    mock_client.post_item_comment.assert_called_once_with(
        item_id=10, comment="LGTM"
    )


def test_add_comment_newlines_converted(mock_client):
    mock_client.post_item_comment.return_value = {"id": 8}
    handle("add_comment", {"item_id": 10, "comment": "line1\nline2"})
    mock_client.post_item_comment.assert_called_once_with(
        item_id=10, comment="line1<br>line2"
    )


def test_api_error(mock_client):
    mock_client.post_item_comment.side_effect = Exception("Forbidden")
    result = handle("add_comment", {"item_id": 10, "comment": "test"})
    payload = json.loads(result[0].text)
    assert payload["code"] == 500
