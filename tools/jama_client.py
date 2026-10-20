"""SDK にないコメント・テスト管理 API を補う Basic 認証クライアント。"""
import requests
from py_jama_rest_client.client import JamaClient as SDKJamaClient
from py_jama_rest_client.core import Core


class JamaClient(SDKJamaClient):
    def __init__(self, host_domain, credentials, oauth=False):
        host_domain = host_domain.rstrip("/")
        super().__init__(host_domain, credentials=credentials, oauth=oauth)
        self._rest = Core(host_domain, credentials, oauth=oauth)

    def _request(self, method, path, **kwargs):
        # DATETIME フィールドとテスト実行日時の時刻部分を保持する。
        kwargs["headers"] = {"x-jama-date-fields-with-time": "true", **kwargs.get("headers", {})}
        response = getattr(self._rest, method)(path, timeout=30, **kwargs)
        if response.status_code >= 400:
            try:
                message = response.json().get("meta", {}).get("message", response.reason)
            except ValueError:
                message = response.reason
            raise requests.HTTPError(f"HTTP {response.status_code}: {message}", response=response)
        response.raise_for_status()
        return response

    def get_item(self, item_id):
        return self._request("get", f"items/{item_id}").json()["data"]

    def put_item(self, project, item_id, item_type_id, child_item_type_id, location, fields):
        return self._request("put", f"items/{item_id}", json={
            "project": project,
            "itemType": item_type_id,
            "childItemType": child_item_type_id,
            "location": {"parent": location},
            "fields": fields,
        }).status_code

    def get_relationships(self, project_id, allowed_results_per_page=50):
        result = []
        last_id = 0
        while True:
            page = self._request("get", "relationships", params={
                "project": project_id, "lastId": last_id, "maxResults": allowed_results_per_page,
            }).json()
            data = page["data"]
            result.extend(data)
            info = page.get("meta", {}).get("pageInfo", {})
            if not data or ("totalResults" in info and len(result) >= info["totalResults"]):
                return result
            next_id = max(item["id"] for item in data)
            if next_id <= last_id:
                raise ValueError("Relationship pagination did not advance")
            last_id = next_id

    def _list(self, path, **params):
        result = []
        start_at = 0
        while True:
            page = self._request("get", path, params={
                **params, "startAt": start_at, "maxResults": 50,
            }).json()
            result.extend(page["data"])
            info = page.get("meta", {}).get("pageInfo")
            if not info or not page["data"]:
                return result
            start_at = info["startIndex"] + info["resultCount"]
            if start_at >= info["totalResults"]:
                return result

    def post_item_comment(self, item_id, comment):
        return self._request("post", "comments", json={
            "body": {"text": comment},
            "location": {"item": item_id},
            "commentType": "GENERAL",
        }).json()["meta"]["id"]

    def get_test_plans(self, project_id):
        return self._list("testplans", project=project_id)

    def post_test_plan(self, project_id, name, description=None):
        fields = {"name": name}
        if description is not None:
            fields["description"] = description
        return self._request("post", "testplans", json={
            "project": project_id, "fields": fields,
        }).json()["meta"]["id"]

    def get_test_cycles(self, test_plan_id):
        return self._list(f"testplans/{test_plan_id}/testcycles")

    def get_test_runs(self, test_cycle_id, start_at=0, max_results=50):
        return self._request("get", f"testcycles/{test_cycle_id}/testruns", params={
            "startAt": start_at, "maxResults": max_results,
        }).json()["data"]

    def post_test_run_results(self, test_run_id, status, actual_results):
        return self._request("put", f"testruns/{test_run_id}", json={
            "fields": {"testRunStatus": status, "actualResults": actual_results},
        }).status_code
