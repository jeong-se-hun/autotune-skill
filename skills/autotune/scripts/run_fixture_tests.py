#!/usr/bin/env python3
"""Run the bundled fixture scenarios against lint_eval_spec.py and eval_gate.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "assets" / "fixtures"
LINT_SPEC = ROOT / "scripts" / "lint_eval_spec.py"
EVAL_GATE = ROOT / "scripts" / "eval_gate.py"


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"missing required fixture file: {path}")


def _parse_result(run: subprocess.CompletedProcess[str], fixture_name: str, failures: list[str]) -> dict | None:
    try:
        payload = json.loads(run.stdout)
    except json.JSONDecodeError as exc:
        failures.append(f"{fixture_name}: eval_gate.py emitted invalid JSON: {exc}")
        return None

    if not isinstance(payload, dict):
        failures.append(f"{fixture_name}: eval_gate.py output must be a JSON object")
        return None
    if "decision" not in payload or payload["decision"] not in {"keep", "reject"}:
        failures.append(f"{fixture_name}: eval_gate.py output missing valid decision field")
    if not isinstance(payload.get("optimize"), list):
        failures.append(f"{fixture_name}: eval_gate.py output missing optimize results list")
    if not isinstance(payload.get("guards"), list):
        failures.append(f"{fixture_name}: eval_gate.py output missing guards results list")
    if "target_reached" not in payload or not isinstance(payload.get("target_reached"), bool):
        failures.append(f"{fixture_name}: eval_gate.py output missing target_reached bool")
    return payload


def run_fixture(fixture_dir: Path) -> list[str]:
    failures: list[str] = []

    contract = fixture_dir / "contract.txt"
    spec = fixture_dir / "spec.json"
    baseline = fixture_dir / "baseline.json"
    keep = fixture_dir / "keep.json"
    reject = fixture_dir / "reject.json"

    for path in (contract, spec, baseline, keep, reject):
        _require_file(path)

    spec_data = json.loads(spec.read_text(encoding="utf-8"))

    lint_run = _run([sys.executable, str(LINT_SPEC), str(spec)])
    if lint_run.returncode != 0:
        failures.append(f"{fixture_dir.name}: spec lint failed: {lint_run.stderr.strip()}")

    keep_run = _run([sys.executable, str(EVAL_GATE), str(spec), str(baseline), str(keep)])
    keep_payload = _parse_result(keep_run, fixture_dir.name, failures)
    if keep_run.returncode != 0:
        failures.append(
            f"{fixture_dir.name}: keep candidate rejected: "
            f"{keep_run.stderr.strip() or keep_run.stdout.strip()}"
        )
    elif keep_payload and keep_payload.get("decision") != "keep":
        failures.append(f"{fixture_dir.name}: keep candidate returned decision={keep_payload.get('decision')}")
    elif keep_payload and "scorecard" in spec_data and not isinstance(keep_payload.get("scorecard"), dict):
        failures.append(f"{fixture_dir.name}: keep payload missing scorecard details")
    elif keep_payload and "targets" in spec_data and not isinstance(keep_payload.get("targets"), list):
        failures.append(f"{fixture_dir.name}: keep payload missing target details")

    reject_run = _run([sys.executable, str(EVAL_GATE), str(spec), str(baseline), str(reject)])
    reject_payload = _parse_result(reject_run, fixture_dir.name, failures)
    if reject_run.returncode == 0:
        failures.append(f"{fixture_dir.name}: reject candidate unexpectedly passed")
    elif reject_payload and reject_payload.get("decision") != "reject":
        failures.append(
            f"{fixture_dir.name}: reject candidate returned decision={reject_payload.get('decision')}"
        )

    return failures


def main() -> int:
    fixture_dirs = sorted(path for path in FIXTURES_DIR.iterdir() if path.is_dir())
    if not fixture_dirs:
        print("no fixtures found", file=sys.stderr)
        return 1

    failures: list[str] = []
    for fixture_dir in fixture_dirs:
        failures.extend(run_fixture(fixture_dir))

    if failures:
        print("fixture-tests: failed", file=sys.stderr)
        for item in failures:
            print(f"- {item}", file=sys.stderr)
        return 1

    print(f"fixture-tests: ok ({len(fixture_dirs)} fixtures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
