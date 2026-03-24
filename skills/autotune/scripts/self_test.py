#!/usr/bin/env python3
"""Smoke test all bundled scripts by running them with minimal or --help args."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

USAGE_TESTS = [
    (["scripts/extract_metrics.py"], 2),
    (["scripts/validate_log.py"], 2),
    (["scripts/resume_session.py"], 2),
    (["scripts/eval_gate.py"], 2),
    (["scripts/lint_eval_spec.py"], 2),
    (["scripts/lint_contract.py"], 2),
    (["scripts/render_review_pack.py"], 2),
    (["scripts/rollback.py"], 2),
]


def run_script(args: list[str], expected_code: int) -> tuple[bool, str]:
    cmd = [sys.executable] + [str(ROOT / args[0])] + args[1:]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
    if result.returncode != expected_code:
        return False, f"exit {result.returncode} (expected {expected_code}): {' '.join(args)}"
    return True, ""


def test_lint_eval_spec() -> tuple[bool, str]:
    spec_path = ROOT / "assets" / "fixtures" / "code-latency" / "spec.json"
    cmd = [sys.executable, str(ROOT / "scripts" / "lint_eval_spec.py"), str(spec_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
    if result.returncode != 0:
        return False, f"lint_eval_spec.py failed on fixture spec: {result.stderr.strip()}"
    return True, ""


def test_eval_gate() -> tuple[bool, str]:
    fixture = ROOT / "assets" / "fixtures" / "code-latency"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "eval_gate.py"),
        str(fixture / "spec.json"),
        str(fixture / "baseline.json"),
        str(fixture / "keep.json"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
    if result.returncode != 0:
        return False, f"eval_gate.py rejected keep fixture: {result.stderr.strip()}"
    return True, ""


def test_extract_metrics() -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as fh:
        fh.write("some output\nMETRIC score=42\nmore output\nMETRIC cost=3.14\n")
        fh.flush()
        cmd = [sys.executable, str(ROOT / "scripts" / "extract_metrics.py"), fh.name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
    if result.returncode != 0:
        return False, f"extract_metrics.py failed: {result.stderr.strip()}"
    data = json.loads(result.stdout)
    if data.get("score") != 42 or abs(data.get("cost", 0) - 3.14) > 0.001:
        return False, f"extract_metrics.py wrong output: {result.stdout.strip()}"
    return True, ""


def test_validate_log() -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as fh:
        fh.write('{"iteration":0,"hypothesis":"baseline","optimize_value":10,"guard_passed":true,"decision":"baseline","note":"initial"}\n')
        fh.flush()
        cmd = [sys.executable, str(ROOT / "scripts" / "validate_log.py"), fh.name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
    if result.returncode != 0:
        return False, f"validate_log.py failed on valid log: {result.stderr.strip()}"
    return True, ""


def test_validate_log_reset_baseline() -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as fh:
        fh.write(
            '{"iteration":4,"hypothesis":"new baseline","optimize_value":7,'
            '"guard_passed":true,"decision":"reset_baseline","note":"reseed"}\n'
        )
        fh.flush()
        cmd = [sys.executable, str(ROOT / "scripts" / "validate_log.py"), fh.name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
    if result.returncode != 0:
        return False, f"validate_log.py rejected reset_baseline: {result.stderr.strip()}"
    return True, ""


def test_resume_session_truncated_tail() -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as fh:
        fh.write(
            '{"iteration":0,"hypothesis":"baseline","optimize_value":10,'
            '"guard_passed":true,"decision":"baseline","note":"initial"}\n'
        )
        fh.write('{"iteration":1,"hypothesis":"candidate"')
        fh.flush()
        cmd = [sys.executable, str(ROOT / "scripts" / "resume_session.py"), fh.name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
    if result.returncode != 0:
        return False, f"resume_session.py failed on truncated tail: {result.stderr.strip()}"
    payload = json.loads(result.stdout)
    if payload.get("total_iterations") != 1:
        return False, f"resume_session.py wrong iteration count: {result.stdout.strip()}"
    warnings = payload.get("warnings", [])
    if not warnings:
        return False, "resume_session.py should report an ignored malformed trailing line"
    return True, ""


def test_public_release_manifest_sync() -> tuple[bool, str]:
    sys.path.insert(0, str(ROOT / "scripts"))
    import export_public_repo
    import public_release_check

    exported = set(export_public_repo.SKILL_FILES)
    required = set(public_release_check.REQUIRED_SKILL_FILES)
    if exported != required:
        missing = sorted(exported - required)
        extra = sorted(required - exported)
        return False, f"public release manifest drift: missing={missing}, extra={extra}"
    return True, ""


def test_rollback() -> tuple[bool, str]:
    import os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write("original content\n")
        src = fh.name

    rollback = str(ROOT / "scripts" / "rollback.py")

    # snapshot
    result = subprocess.run(
        [sys.executable, rollback, "snapshot", src],
        capture_output=True, text=True, check=False, timeout=30,
    )
    if result.returncode != 0:
        return False, f"rollback snapshot failed: {result.stderr.strip()}"

    # overwrite the file
    Path(src).write_text("modified content\n", encoding="utf-8")

    # restore
    result = subprocess.run(
        [sys.executable, rollback, "restore", src],
        capture_output=True, text=True, check=False, timeout=30,
    )
    if result.returncode != 0:
        return False, f"rollback restore failed: {result.stderr.strip()}"

    restored = Path(src).read_text(encoding="utf-8")
    if restored != "original content\n":
        return False, f"rollback restore: content mismatch: {restored!r}"

    # list
    result = subprocess.run(
        [sys.executable, rollback, "list", src],
        capture_output=True, text=True, check=False, timeout=30,
    )
    if result.returncode != 0:
        return False, f"rollback list failed: {result.stderr.strip()}"

    # clean --keep 0 is invalid; clean --keep 1 keeps the one snapshot
    result = subprocess.run(
        [sys.executable, rollback, "clean", src, "--keep", "1"],
        capture_output=True, text=True, check=False, timeout=30,
    )
    if result.returncode != 0:
        return False, f"rollback clean failed: {result.stderr.strip()}"

    os.unlink(src)
    return True, ""


def main() -> int:
    failures: list[str] = []
    test_fns = [
        test_lint_eval_spec,
        test_eval_gate,
        test_extract_metrics,
        test_validate_log,
        test_validate_log_reset_baseline,
        test_resume_session_truncated_tail,
        test_public_release_manifest_sync,
        test_rollback,
    ]

    for args, expected_code in USAGE_TESTS:
        passed, msg = run_script(args, expected_code)
        if not passed:
            failures.append(msg)

    for test_fn in test_fns:
        passed, msg = test_fn()
        if not passed:
            failures.append(msg)

    total = len(USAGE_TESTS) + len(test_fns)
    if failures:
        print("self-test: failed", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)
        return 1

    print(f"self-test: ok ({total} tests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
