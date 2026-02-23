#!/usr/bin/env python3
"""Spec-first run scaffold for SOVEREIGN hospital corridor navigation v0.1."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

REQUIRED_TOP_LEVEL_KEYS = [
    "version",
    "project",
    "scenario",
    "robot",
    "scene",
    "task",
    "adversary",
    "metrics",
    "run",
]


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "null":
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def _split_top_level(text: str, delimiter: str) -> List[str]:
    parts: List[str] = []
    depth = 0
    current: List[str] = []
    for char in text:
        if char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1

        if char == delimiter and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)

    if current:
        parts.append("".join(current).strip())
    return [item for item in parts if item]


def _parse_inline(value: str) -> Any:
    value = value.strip()
    if value.startswith("{") and value.endswith("}"):
        body = value[1:-1].strip()
        if not body:
            return {}
        result: Dict[str, Any] = {}
        for part in _split_top_level(body, ","):
            if ":" not in part:
                raise ValueError(f"Invalid inline mapping entry: {part}")
            key, raw = part.split(":", 1)
            result[key.strip()] = _parse_inline(raw.strip())
        return result

    if value.startswith("[") and value.endswith("]"):
        body = value[1:-1].strip()
        if not body:
            return []
        return [_parse_inline(part) for part in _split_top_level(body, ",")]

    return _parse_scalar(value)


def _parse_simple_yaml(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any, str | None]] = [(-1, root, None)]

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]

        if content.startswith("- "):
            item_content = content[2:].strip()
            if not isinstance(parent, list):
                parent_key = stack[-1][2]
                parent_container = stack[-2][1]
                if not isinstance(parent_container, dict) or parent_key is None:
                    raise ValueError("Invalid YAML list nesting")
                new_list: List[Any] = []
                parent_container[parent_key] = new_list
                stack[-1] = (stack[-1][0], new_list, parent_key)
                parent = new_list
            parent.append(_parse_inline(item_content))
            continue

        if ":" not in content:
            raise ValueError(f"Invalid YAML line: {content}")

        key, raw_value = content.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        if not isinstance(parent, dict):
            raise ValueError("Invalid YAML mapping placement")

        if raw_value == "":
            child: Dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child, key))
        else:
            parent[key] = _parse_inline(raw_value)

    return root


def load_spec(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")

    try:
        payload = _parse_simple_yaml(text)
    except Exception as yaml_err:
        json_fallback = path.with_suffix(".json")
        if json_fallback.exists():
            payload = json.loads(json_fallback.read_text(encoding="utf-8"))
        else:
            raise RuntimeError(
                "Failed to parse YAML with stdlib parser. "
                "Please provide a JSON version of the spec (e.g., hospital_nav_v0.1.json)."
            ) from yaml_err

    if not isinstance(payload, dict):
        raise ValueError("Spec root must be a mapping/object.")
    return payload


def validate_spec(spec: Dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in spec]
    if missing:
        raise ValueError(f"Spec missing required top-level keys: {missing}")


def generate_execution_plan(spec: Dict[str, Any]) -> Dict[str, Any]:
    run = spec["run"]
    adversary = spec["adversary"]
    return {
        "scenario": spec["scenario"],
        "dt_s": run["dt_s"],
        "max_time_s": run["max_time_s"],
        "max_steps": run["max_steps"],
        "ros2_enabled": run["ros2_enabled"],
        "seed": run.get("seed", adversary.get("seed")),
        "intensity": adversary["intensity"],
    }


def write_artifacts(repo_root: Path, spec_path: Path, spec: Dict[str, Any]) -> None:
    artifacts_dir = repo_root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "spec_hash": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "scenario": spec["scenario"],
        "seed": spec["run"].get("seed", spec["adversary"].get("seed")),
        "intensity": spec["adversary"]["intensity"],
    }

    (artifacts_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (artifacts_dir / "event_log.jsonl").write_text(
        json.dumps({"type": "header", "schema": "sovereign.event_log.v0"}) + "\n",
        encoding="utf-8",
    )
    (artifacts_dir / "ars_timeseries.csv").write_text("step,t_s,ars_score\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SOVEREIGN spec scaffold")
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path("sovereign/specs/hospital_nav_v0.1.yaml"),
        help="Path to spec file",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    spec = load_spec(args.spec)
    validate_spec(spec)
    plan = generate_execution_plan(spec)
    write_artifacts(repo_root=repo_root, spec_path=args.spec, spec=spec)

    print(json.dumps({"status": "ok", "plan": plan}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
