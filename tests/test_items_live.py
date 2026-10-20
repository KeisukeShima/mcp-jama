"""明示的に有効化した場合だけ Sandbox で実データを作成・更新・削除する。"""

import json
import os
from uuid import uuid4

import pytest

from tools.items import handle


pytestmark = pytest.mark.skipif(
    os.environ.get("JAMA_RUN_LIVE") != "1",
    reason="JAMA_RUN_LIVE=1 で Sandbox 実環境テストを有効化する",
)

COMPONENT_TYPE = 30


@pytest.mark.parametrize("parent_kind", ["project", "item"])
def test_update_item_persists_in_sandbox(live_client, parent_kind):
    client, project_id = live_client
    name = f"mcp-jama-live-{uuid4().hex}"
    created_ids = []
    try:
        root_id = client.post_item(
            project=project_id,
            item_type_id=COMPONENT_TYPE,
            child_item_type_id=None,
            location={"project": project_id},
            fields={"name": name, "description": "<p>Keep this description</p>"},
        )
        created_ids.append(root_id)
        print(f"Created Sandbox test item: {root_id}", flush=True)
        item_id = root_id
        if parent_kind == "item":
            created = json.loads(handle("create_item", {
                "project_id": project_id,
                "item_type_id": COMPONENT_TYPE,
                "parent_id": root_id,
                "fields": {"name": name, "description": "<p>Keep this description</p>"},
            })[0].text)
            assert "error" not in created, created
            item_id = created["data"]
            created_ids.append(item_id)
            print(f"Created Sandbox test item: {item_id}", flush=True)

        before = client.get_item(item_id)
        assert before["project"] == project_id
        assert before["location"]["parent"] == (
            {"project": project_id} if parent_kind == "project" else {"item": root_id}
        )

        result = json.loads(handle("update_item", {
            "item_id": item_id, "fields": {"name": f"{name}-updated"},
        })[0].text)
        assert "error" not in result, result
        assert 200 <= result["data"] < 300

        after = client.get_item(item_id)
        assert after["fields"] == {**before["fields"], "name": f"{name}-updated"}
        assert after["project"] == before["project"]
        assert after["itemType"] == before["itemType"]
        assert after.get("childItemType") == before.get("childItemType")
        assert after["location"]["parent"] == before["location"]["parent"]
        assert after["version"] > before["version"]
    finally:
        # 子から削除。失敗時も残りの後片付けを試み、残存 ID を報告する。
        failed_ids = []
        for created_id in reversed(created_ids):
            try:
                client.delete_item(created_id)
                response = client._rest.get(f"items/{created_id}", timeout=30)
                assert response.status_code == 404
                print(f"Deleted Sandbox test item: {created_id}", flush=True)
            except Exception:
                failed_ids.append(created_id)
        assert not failed_ids, f"Sandbox のテストアイテム削除を確認できませんでした: {failed_ids}"
