import json
import pytest
from unittest.mock import patch, MagicMock


def test_get_client_loads_config(tmp_path, monkeypatch):
    """config.json から JamaClient を初期化できる"""
    cfg = {"jama": {"base_url": "https://test.jamacloud.com", "username": "u", "password": "p"}}
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps(cfg))
    monkeypatch.setenv("JAMA_CONFIG", str(cfg_file))

    import config
    config._client = None  # reset singleton

    with patch("config.JamaClient") as MockClient:
        MockClient.return_value = MagicMock()
        client = config.get_client()
        MockClient.assert_called_once_with(
            "https://test.jamacloud.com",
            credentials=("u", "p"),
            oauth=False,
        )
        assert client is MockClient.return_value


def test_get_client_returns_singleton(tmp_path, monkeypatch):
    """2回呼んでも同一インスタンスを返す"""
    cfg = {"jama": {"base_url": "https://test.jamacloud.com", "username": "u", "password": "p"}}
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps(cfg))
    monkeypatch.setenv("JAMA_CONFIG", str(cfg_file))

    import config
    config._client = None

    with patch("config.JamaClient") as MockClient:
        MockClient.return_value = MagicMock()
        c1 = config.get_client()
        c2 = config.get_client()
        assert c1 is c2
        assert MockClient.call_count == 1


def test_get_client_missing_file(monkeypatch):
    """存在しないファイルを指定すると FileNotFoundError"""
    monkeypatch.setenv("JAMA_CONFIG", "/nonexistent/config.json")
    import config
    config._client = None
    with pytest.raises(FileNotFoundError):
        config.get_client()
