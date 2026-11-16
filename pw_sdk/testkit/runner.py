import difflib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pw_sdk.adapter import Adapter, AdapterContext, TransformResult
from pw_sdk.loader import load

DEFAULT_RECEIVED_AT = "2026-01-01T00:00:00+00:00"
KINDS = ("records", "events")


@dataclass
class CaseResult:
    name: str
    passed: bool
    problems: list[str] = field(default_factory=list)


def _read(path: Path) -> Any:
    return json.loads(path.read_text())


def _context(case: Path, adapter_name: str, defaults: dict) -> AdapterContext:
    extra = case.with_name(case.name.replace(".json", ".context.json"))
    data = {"intake_id": adapter_name, "received_at": DEFAULT_RECEIVED_AT, **defaults}
    if extra.exists():
        data.update(_read(extra))
    data["received_at"] = datetime.fromisoformat(str(data["received_at"]))
    return AdapterContext(**data)


def _summarise(result: TransformResult) -> dict:
    return {
        "items": [{"index": item.index, "value": item.value.model_dump(mode="json", exclude_none=True)} for item in result.items],
        "rejections": [r.model_dump(mode="json") for r in result.rejections],
        "skipped": [s.model_dump(mode="json") for s in result.skipped],
    }


def _diff(expected: dict, actual: dict) -> str:
    left = json.dumps(expected, indent=2, sort_keys=True).splitlines()
    right = json.dumps(actual, indent=2, sort_keys=True).splitlines()
    return "\n".join(difflib.unified_diff(left, right, "expected", "actual", lineterm=""))


def default_kind(adapter: Adapter) -> str:
    accepts_records = type(adapter).transform_records is not Adapter.transform_records
    return "records" if accepts_records else "events"


def run_case(adapter: Adapter, case: Path, defaults: dict | None = None, update: bool = False) -> CaseResult:
    expected_path = case.with_name(case.name.replace(".json", ".expected.json"))
    payload = _read(case)
    defaults = dict(defaults or {})
    fallback = defaults.pop("kind", None) or default_kind(adapter)
    expected = _read(expected_path) if expected_path.exists() else {"kind": fallback}
    kind = expected.get("kind", fallback)
    if kind not in KINDS:
        return CaseResult(case.name, False, [f"unknown kind {kind!r}"])
    ctx = _context(case, adapter.name, defaults)
    method = adapter.transform_records if kind == "records" else adapter.transform_events
    result = method(payload, ctx)
    problems: list[str] = []
    count = len(payload) if isinstance(payload, list) else 1
    if not result.covers(count):
        problems.append(f"reported indexes {sorted(result.reported())} do not cover all {count} inputs")
    actual = {"kind": kind, **_summarise(result)}
    if update:
        expected_path.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n")
    elif not expected_path.exists():
        problems.append(f"missing {expected_path.name}; run with --update to create it")
    elif actual != expected:
        problems.append(_diff(expected, actual))
    return CaseResult(case.name, not problems, problems)


def cases(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.glob("*.json")
        if not path.name.endswith(".expected.json") and not path.name.endswith(".context.json")
    )


def check_directory(directory: Path, adapter_spec: str | None = None, update: bool = False) -> list[CaseResult]:
    results: list[CaseResult] = []
    groups = [d for d in sorted(directory.iterdir()) if d.is_dir()] if adapter_spec is None else [directory]
    for group in groups:
        spec = adapter_spec or group.name
        adapter = load(spec)
        defaults_path = group / "context.json"
        defaults = _read(defaults_path) if defaults_path.exists() else {}
        for case in cases(group):
            if case.name == "context.json":
                continue
            outcome = run_case(adapter, case, defaults, update)
            outcome.name = f"{spec}/{case.name}"
            results.append(outcome)
    return results
