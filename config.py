import json
import os
import threading
from py_jama_rest_client.client import JamaClient

_client: JamaClient | None = None
_lock = threading.Lock()


def get_client() -> JamaClient:
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                _client = _load_client()
    return _client


def _load_client() -> JamaClient:
    config_path = os.environ.get("JAMA_CONFIG", "./config.json")
    with open(config_path) as f:
        cfg = json.load(f)
    try:
        jama = cfg["jama"]
        base_url = jama["base_url"]
        username = jama["username"]
        password = jama["password"]
    except KeyError as e:
        raise ValueError(
            f"Missing required key {e} in config file: {config_path}. "
            f"See config.json.example for the expected format."
        ) from e
    return JamaClient(base_url, credentials=(username, password), oauth=False)
