import json
import os
from pathlib import Path
from unittest.mock import create_autospec

import pytest
import requests

import config


@pytest.fixture(autouse=True)
def mock_client(monkeypatch):
    """全テストで config._client を実クライアントのシグネチャ付きモックに差し替える。
    config.json が存在しなくてもテストが動作する。"""
    mock = create_autospec(config.JamaClient, instance=True)
    monkeypatch.setattr(config, "_client", mock)
    return mock


# 実環境テストは各モジュールの JAMA_RUN_LIVE ガードで有効化する。
@pytest.fixture
def live_client(monkeypatch):
    base_url = os.environ.get("JAMA_LIVE_BASE_URL", "").rstrip("/")
    project_id_text = os.environ.get("JAMA_LIVE_PROJECT_ID", "")
    if not base_url or not project_id_text:
        pytest.fail("JAMA_LIVE_BASE_URL と JAMA_LIVE_PROJECT_ID を明示指定してください")
    if not project_id_text.isascii() or not project_id_text.isdecimal() or int(project_id_text) <= 0:
        pytest.fail("JAMA_LIVE_PROJECT_ID は正の整数で指定してください")
    project_id = int(project_id_text)
    path = Path(os.environ.get("JAMA_CONFIG", "./config.json")).expanduser()
    settings = json.loads(path.read_text())["jama"]
    assert settings["base_url"].rstrip("/") == base_url, "設定ファイルと JAMA_LIVE_BASE_URL が一致しません"

    # 通信は実際に行い、各リクエストの待ち時間のみ制限する。
    original_send = requests.Session.send

    def send(session, request, **kwargs):
        kwargs["timeout"] = 30
        return original_send(session, request, **kwargs)

    monkeypatch.setattr(requests.Session, "send", send)
    response = requests.get(
        f"{base_url}/rest/v1/projects/{project_id}",
        auth=(settings["username"], settings["password"]),
    )
    response.raise_for_status()
    project = response.json()["data"]
    assert project["id"] == project_id

    # conftest の自動モックを解除し、ローカル実装から実 SDK を利用する。
    monkeypatch.setattr(config, "_client", None)
    return config.get_client(), project_id
