from mcp import types
from config import get_client
from tools.helpers import _ok, _err

VALID_STATUSES = {"PASSED", "FAILED", "BLOCKED", "NOT_RUN", "INPROGRESS"}

TOOLS: list[types.Tool] = [
    types.Tool(
        name="get_test_plans",
        description="プロジェクトのテストプラン一覧を取得する",
        inputSchema={
            "type": "object",
            "properties": {"project_id": {"type": "integer"}},
            "required": ["project_id"],
        },
    ),
    types.Tool(
        name="create_test_plan",
        description="テストプランを作成する",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "integer"},
                "name": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["project_id", "name"],
        },
    ),
    types.Tool(
        name="get_test_cycles",
        description="テストプランに属するテストサイクル一覧を取得する",
        inputSchema={
            "type": "object",
            "properties": {"test_plan_id": {"type": "integer"}},
            "required": ["test_plan_id"],
        },
    ),
    types.Tool(
        name="get_test_runs",
        description="テストサイクルのテストラン一覧を取得する（最大50件）。全件取得は start_at を増やして繰り返す。",
        inputSchema={
            "type": "object",
            "properties": {
                "test_cycle_id": {"type": "integer"},
                "start_at": {"type": "integer", "default": 0},
            },
            "required": ["test_cycle_id"],
        },
    ),
    types.Tool(
        name="create_test_result",
        description="テストランに結果を記録する。status は PASSED/FAILED/BLOCKED/NOT_RUN/INPROGRESS のいずれか。",
        inputSchema={
            "type": "object",
            "properties": {
                "test_run_id": {"type": "integer"},
                "status": {"type": "string", "enum": list(VALID_STATUSES)},
                "actual_results": {"type": "string"},
            },
            "required": ["test_run_id", "status", "actual_results"],
        },
    ),
]


def handle(name: str, args: dict) -> list[types.TextContent]:
    try:
        if name == "get_test_plans":
            plans = get_client().get_test_plans(project_id=args["project_id"])
            return _ok(plans, total=len(plans))
        if name == "create_test_plan":
            plan = get_client().post_test_plan(
                project_id=args["project_id"],
                name=args["name"],
                description=args.get("description", ""),
            )
            return _ok(plan)
        if name == "get_test_cycles":
            cycles = get_client().get_test_cycles(test_plan_id=args["test_plan_id"])
            return _ok(cycles, total=len(cycles))
        if name == "get_test_runs":
            runs = get_client().get_test_runs(
                test_cycle_id=args["test_cycle_id"],
                start_at=args.get("start_at", 0),
                max_results=50,
            )
            return _ok(runs, total=len(runs))
        if name == "create_test_result":
            status = args["status"]
            if status not in VALID_STATUSES:
                return _err(
                    f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
                    code=400,
                )
            result = get_client().post_test_run_results(
                test_run_id=args["test_run_id"],
                status=status,
                actual_results=args["actual_results"],
            )
            return _ok(result)
    except Exception as e:
        return _err(str(e))
    return _err(f"Unknown tool: {name}", code=404)
