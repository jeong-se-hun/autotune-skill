#!/usr/bin/env python3
"""Compare baseline and candidate metrics against an eval spec."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def load_json(path: str) -> dict:
    with Path(path).open() as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def read_metric(metrics: dict, name: str) -> float:
    if name not in metrics:
        raise KeyError(f"missing metric: {name}")
    value = metrics[name]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"metric {name} must be numeric")
    return float(value)


def compare_optimize(metric: dict, baseline: dict, candidate: dict) -> tuple[bool, str]:
    name = metric["name"]
    direction = metric["direction"]
    min_delta = float(metric.get("min_delta", 0))
    base = read_metric(baseline, name)
    cand = read_metric(candidate, name)

    if direction == "max":
        passed = cand >= base + min_delta
    elif direction == "min":
        passed = cand <= base - min_delta
    else:
        raise ValueError(f"unsupported optimize direction: {direction}")

    return passed, f"{name}: baseline={base}, candidate={cand}, direction={direction}, min_delta={min_delta}"


def compare_guard(metric: dict, baseline: dict, candidate: dict) -> tuple[bool, str]:
    name = metric["name"]
    kind = metric["kind"]
    cand = read_metric(candidate, name)

    if kind == "absolute_max":
        threshold = float(metric["value"])
        passed = cand <= threshold
        detail = f"{name}: candidate={cand}, threshold<={threshold}"
    elif kind == "absolute_min":
        threshold = float(metric["value"])
        passed = cand >= threshold
        detail = f"{name}: candidate={cand}, threshold>={threshold}"
    elif kind == "relative_max":
        base = read_metric(baseline, name)
        factor = float(metric["value"])
        threshold = base * factor
        passed = cand <= threshold or math.isclose(cand, threshold)
        detail = f"{name}: baseline={base}, candidate={cand}, threshold<={threshold}"
    elif kind == "relative_min":
        base = read_metric(baseline, name)
        factor = float(metric["value"])
        threshold = base * factor
        passed = cand >= threshold or math.isclose(cand, threshold)
        detail = f"{name}: baseline={base}, candidate={cand}, threshold>={threshold}"
    else:
        raise ValueError(f"unsupported guard kind: {kind}")

    return passed, detail


def normalize_score(value: float, best: float, worst: float) -> float:
    if best == worst:
        return 0.0
    if best > worst:
        raw = (value - worst) / (best - worst)
    else:
        raw = (worst - value) / (worst - best)
    return max(0.0, min(1.0, raw))


def score_scorecard(scorecard: dict, baseline: dict, candidate: dict) -> dict:
    total_weight = 0.0
    baseline_total = 0.0
    candidate_total = 0.0
    metrics: list[dict] = []

    for item in scorecard.get("metrics", []):
        name = item["name"]
        weight = float(item["weight"])
        best = float(item["best"])
        worst = float(item["worst"])
        base = read_metric(baseline, name)
        cand = read_metric(candidate, name)
        base_component = normalize_score(base, best, worst)
        cand_component = normalize_score(cand, best, worst)
        total_weight += weight
        baseline_total += base_component * weight
        candidate_total += cand_component * weight
        metrics.append(
            {
                "name": name,
                "weight": weight,
                "best": best,
                "worst": worst,
                "baseline_component": round(base_component, 4),
                "candidate_component": round(cand_component, 4),
            }
        )

    if total_weight <= 0:
        raise ValueError("scorecard must have positive total weight")

    baseline_score = baseline_total / total_weight
    candidate_score = candidate_total / total_weight
    min_improvement = float(scorecard.get("keep_if_score_improves_by", 0.0))
    passed = candidate_score >= baseline_score + min_improvement
    target = scorecard.get("stop_if_score_at_least")
    target_reached = candidate_score >= float(target) if target is not None else False

    return {
        "passed": passed,
        "baseline_score": round(baseline_score, 4),
        "candidate_score": round(candidate_score, 4),
        "score_delta": round(candidate_score - baseline_score, 4),
        "keep_if_score_improves_by": min_improvement,
        "stop_if_score_at_least": float(target) if target is not None else None,
        "target_reached": target_reached,
        "metrics": metrics,
    }


def evaluate_targets(targets: list[dict], candidate: dict, scorecard_result: dict | None) -> tuple[list[dict], bool]:
    results: list[dict] = []
    all_passed = True

    for item in targets:
        name = item["name"]
        kind = item["kind"]
        value = float(item["value"])
        if name == "overall_score":
            if not scorecard_result:
                raise ValueError("overall_score target requires scorecard result")
            actual = float(scorecard_result["candidate_score"])
        else:
            actual = read_metric(candidate, name)

        if kind == "at_least":
            passed = actual >= value
            detail = f"{name}: candidate={actual}, threshold>={value}"
        elif kind == "at_most":
            passed = actual <= value
            detail = f"{name}: candidate={actual}, threshold<={value}"
        else:
            raise ValueError(f"unsupported target kind: {kind}")

        results.append({"passed": passed, "detail": detail})
        all_passed = all_passed and passed

    return results, all_passed


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "usage: eval_gate.py <spec.json> <baseline.json> <candidate.json>",
            file=sys.stderr,
        )
        return 2

    spec = load_json(sys.argv[1])
    baseline = load_json(sys.argv[2])
    candidate = load_json(sys.argv[3])

    optimize_specs = spec.get("optimize", [])
    guard_specs = spec.get("guards", [])
    scorecard_spec = spec.get("scorecard")
    target_specs = spec.get("targets", [])
    strategy = spec.get("strategy", "all")

    if not optimize_specs:
        raise ValueError("spec must include at least one optimize metric")
    if strategy not in ("all", "primary", "pareto"):
        raise ValueError(f"unsupported strategy: {strategy!r}; expected 'all', 'primary', or 'pareto'")

    optimize_results = [compare_optimize(item, baseline, candidate) for item in optimize_specs]
    guard_results = [compare_guard(item, baseline, candidate) for item in guard_specs]
    scorecard_result = score_scorecard(scorecard_spec, baseline, candidate) if scorecard_spec else None

    scorecard_passed = scorecard_result["passed"] if scorecard_result else True

    optimize_passed_flags = [passed for passed, _ in optimize_results]
    if strategy == "all":
        optimize_gate = all(optimize_passed_flags)
    elif strategy == "primary":
        optimize_gate = optimize_passed_flags[0]
    else:  # pareto: at least one improves, none regress below baseline
        def no_regression(metric: dict) -> bool:
            name = metric["name"]
            direction = metric["direction"]
            base = read_metric(baseline, name)
            cand = read_metric(candidate, name)
            return cand >= base if direction == "max" else cand <= base

        optimize_gate = any(optimize_passed_flags) and all(
            no_regression(item) for item in optimize_specs
        )

    decision = (
        optimize_gate
        and all(passed for passed, _ in guard_results)
        and scorecard_passed
    )

    target_results, explicit_targets_reached = (
        evaluate_targets(target_specs, candidate, scorecard_result) if target_specs else ([], True)
    )
    score_target_defined = bool(scorecard_result and scorecard_result.get("stop_if_score_at_least") is not None)
    score_target_reached = bool(scorecard_result and scorecard_result.get("target_reached"))
    if target_specs and score_target_defined:
        targets_reached = explicit_targets_reached and score_target_reached
    elif target_specs:
        targets_reached = explicit_targets_reached
    elif score_target_defined:
        targets_reached = score_target_reached
    else:
        targets_reached = False
    targets_reached = targets_reached and decision

    result = {
        "decision": "keep" if decision else "reject",
        "strategy": strategy,
        "optimize": [
            {"passed": passed, "detail": detail} for passed, detail in optimize_results
        ],
        "guards": [{"passed": passed, "detail": detail} for passed, detail in guard_results],
        "scorecard": scorecard_result,
        "targets": target_results,
        "target_reached": targets_reached,
    }
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if decision else 1


if __name__ == "__main__":
    raise SystemExit(main())
