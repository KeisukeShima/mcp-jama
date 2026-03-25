import pytest
from unittest.mock import MagicMock
import config


@pytest.fixture(autouse=True)
def mock_client(monkeypatch):
    """全テストで config._client を MagicMock に差し替える。
    config.json が存在しなくてもテストが動作する。"""
    mock = MagicMock()
    monkeypatch.setattr(config, "_client", mock)
    return mock
