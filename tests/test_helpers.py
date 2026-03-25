import json
from mcp import types
from tools.helpers import _ok, _err


def test_ok_list_response():
    result = _ok([{"id": 1}], total=1)
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    payload = json.loads(result[0].text)
    assert payload == {"data": [{"id": 1}], "meta": {"total": 1}}


def test_ok_single_response_omits_meta():
    result = _ok({"id": 1})
    payload = json.loads(result[0].text)
    assert "meta" not in payload
    assert payload == {"data": {"id": 1}}


def test_err_default_code():
    result = _err("Something went wrong")
    payload = json.loads(result[0].text)
    assert payload == {"error": "Something went wrong", "code": 500}


def test_err_custom_code():
    result = _err("Not found", code=404)
    payload = json.loads(result[0].text)
    assert payload["code"] == 404
