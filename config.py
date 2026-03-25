import json
import os
from py_jama_rest_client.client import JamaClient

_client: JamaClient | None = None


def get_client() -> JamaClient:
    global _client
    if _client is None:
        config_path = os.environ.get("JAMA_CONFIG", "./config.json")
        with open(config_path) as f:
            cfg = json.load(f)
        jama = cfg["jama"]
        _client = JamaClient(
            jama["base_url"],
            credentials=(jama["username"], jama["password"]),
            oauth=False,
        )
    return _client
