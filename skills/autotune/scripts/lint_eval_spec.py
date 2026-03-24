#!/usr/bin/env python3
"""Validate an eval spec before using it with eval_gate.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

OPT_DIRECTIONS = {"max", "min"}
GUARD_KINDS = {"absolute_max", "absolute_min", "relative_max", "relative_min"}
TARGET_KINDS = {"at_least", "at_most"}


def load_spec(path: str) -> dict:
    with Path(path).open() as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("spec must be a JSON object")
    return data


def _require_number(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    return float(value)


def _validate_optimize(items: object) -> list[str]:
    if not isinstance(items, list) or not items:
        raise ValueError("optimize must be a non-empty array")

    seen: set[str] = set()
    metrics: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"optimize[{index}] must be an object")
        name = item.get("name")
        direction = item.get("direction")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"optimize[{index}].name must be a non-empty string")
        if name in seen:
            raise ValueError(f"duplicate optimize metric: {name}")
        if direction not in OPT_DIRECTIONS:
            raise ValueError(f"optimize[{index}].direction must be one of {sorted(OPT_DIRECTIONS)}")
        if "min_delta" in item:
            min_delta = _require_number(item["min_delta"], f"optimize[{index}].min_delta")
            if min_delta < 0:
                raise ValueError(f"optimize[{index}].min_delta must be >= 0")
        seen.add(name)
        metrics.append(name)
    return metrics


def _validate_guards(items: object, optimize_metrics: set[str]) -> list[str]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValueError("guards must be an array")

    seen: set[tuple[str, str]] = set()
    metrics: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"guards[{index}] must be an object")
        name = item.get("name")
        kind = item.get("kind")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"guards[{index}].name must be a non-empty string")
        if kind not in GUARD_KINDS:
            raise ValueError(f"guards[{index}].kind must be one of {sorted(GUARD_KINDS)}")
        if "value" not in item:
            raise ValueError(f"guards[{index}].value is required")
        value = _require_number(item["value"], f"guards[{index}].value")
        if kind.startswith("relative_") and value <= 0:
            raise ValueError(f"guards[{index}].value must be > 0 for relative guards")
        key = (name, kind)
        if key in seen:
            raise ValueError(f"duplicate guard metric/kind pair: {name}/{kind}")
        seen.add(key)
        metrics.append(name)

    overlap = sorted(optimize_metrics & set(metrics))
    if overlap:
        raise ValueError(
            f"optimize and guard metrics must be separate; overlap found: {', '.join(overlap)}"
        )
    return metrics


def _validate_scorecard(items: object, known_metrics: set[str]) -> dict | None:
    if items is None:
        return None
    if not isinstance(items, dict):
        raise ValueError("scorecard must be an object")

    unexpected = sorted(set(items) - {"metrics", "keep_if_score_improves_by", "stop_if_score_at_least"})
    if unexpected:
        raise ValueError(f"unexpected scorecard keys: {', '.join(unexpected)}")

    metrics = items.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        raise ValueError("scorecard.metrics must be a non-empty array")

    seen: set[str] = set()
    metric_names: list[str] = []
    for index, item in enumerate(metrics):
        if not isinstance(item, dict):
            raise ValueError(f"scorecard.metrics[{index}] must be an object")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"scorecard.metrics[{index}].name must be a non-empty string")
        if name in seen:
            raise ValueError(f"duplicate scorecard metric: {name}")
        if name not in known_metrics:
            raise ValueError(
                f"scorecard.metrics[{index}].name must reference an optimize or guard metric: {name}"
            )
        weight = _require_number(item.get("weight"), f"scorecard.metrics[{index}].weight")
        if weight <= 0:
            raise ValueError(f"scorecard.metrics[{index}].weight must be > 0")
        best = _require_number(item.get("best"), f"scorecard.metrics[{index}].best")
        worst = _require_number(item.get("worst"), f"scorecard.metrics[{index}].worst")
        if best == worst:
            raise ValueError(f"scorecard.metrics[{index}] best and worst must differ")
        seen.add(name)
        metric_names.append(name)

    if "keep_if_score_improves_by" in items:
        delta = _require_number(items["keep_if_score_improves_by"], "scorecard.keep_if_score_improves_by")
        if delta < 0:
            raise ValueError("scorecard.keep_if_score_improves_by must be >= 0")

    if "stop_if_score_at_least" in items:
        threshold = _require_number(items["stop_if_score_at_least"], "scorecard.stop_if_score_at_least")
        if threshold < 0 or threshold > 1:
            raise ValueError("scorecard.stop_if_score_at_least must be between 0 and 1")

    return {"metric_names": metric_names}


def _validate_targets(items: object, known_metrics: set[str], has_scorecard: bool) -> list[str]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValueError("targets must be an array")

    seen: set[tuple[str, str]] = set()
    target_names: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"targets[{index}] must be an object")
        name = item.get("name")
        kind = item.get("kind")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"targets[{index}].name must be a non-empty string")
        if kind not in TARGET_KINDS:
            raise ValueError(f"targets[{index}].kind must be one of {sorted(TARGET_KINDS)}")
        _require_number(item.get("value"), f"targets[{index}].value")
        if name == "overall_score":
            if not has_scorecard:
                raise ValueError("targets using overall_score require a scorecard")
        elif name not in known_metrics:
            raise ValueError(f"targets[{index}].name must reference a known metric: {name}")
        key = (name, kind)
        if key in seen:
            raise ValueError(f"duplicate target metric/kind pair: {name}/{kind}")
        seen.add(key)
        target_names.append(name)
    return target_names


def validate_spec(spec: dict) -> dict:
    unexpected = sorted(set(spec) - {"optimize", "guards", "scorecard", "targets", "strategy"})
    if unexpected:
        raise ValueError(f"unexpected top-level keys: {', '.join(unexpected)}")

    optimize_metrics = _validate_optimize(spec.get("optimize"))
    guard_metrics = _validate_guards(spec.get("guards", []), set(optimize_metrics))
    known_metrics = set(optimize_metrics) | set(guard_metrics)
    scorecard = _validate_scorecard(spec.get("scorecard"), known_metrics)
    target_metrics = _validate_targets(spec.get("targets", []), known_metrics, scorecard is not None)

    return {
        "optimize_metrics": optimize_metrics,
        "guard_metrics": guard_metrics,
        "scorecard_metrics": scorecard["metric_names"] if scorecard else [],
        "target_metrics": target_metrics,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: lint_eval_spec.py <spec.json>", file=sys.stderr)
        return 2

    try:
        spec = load_spec(sys.argv[1])
        summary = validate_spec(spec)
    except Exception as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "optimize_metrics": summary["optimize_metrics"],
                "guard_metrics": summary["guard_metrics"],
                "scorecard_metrics": summary["scorecard_metrics"],
                "target_metrics": summary["target_metrics"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
