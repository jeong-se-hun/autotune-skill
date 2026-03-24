#!/usr/bin/env python3
"""Run a live trigger benchmark against Codex using holdout routing prompts."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALS_PATH = ROOT / "evals" / "evals.json"
SKILL_PATH = ROOT / "SKILL.md"


def load_cases(split: str) -> list[dict]:
    data = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    cases = []
    for item in data.get("evals", []):
        routing = item.get("routing", {})
        if not isinstance(routing, dict):
            continue
        if routing.get("split") != split:
            continue
        cases.append(
            {
                "id": item.get("id"),
                "prompt": str(item.get("prompt", "")),
                "should_trigger": bool(routing.get("should_trigger")),
                "tags": routing.get("tags", []),
            }
        )
    return cases


def collect_trace(stdout: str) -> dict[str, list[str]]:
    agent_messages: list[str] = []
    command_reads: list[str] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        item = event.get("item")
        if not isinstance(item, dict):
            continue

        item_type = item.get("type")
        if item_type == "agent_message":
            text = " ".join(str(item.get("text", "")).split())
            if text:
                agent_messages.append(text[:280])
        elif item_type == "command_execution":
            command = " ".join(str(item.get("command", "")).split())
            if command:
                command_reads.append(command[:280])
    return {
        "agent_messages_tail": agent_messages[-3:],
        "command_reads_tail": command_reads[-3:],
    }


def build_trigger_probe_prompt(prompt: str) -> str:
    return (
        f"{prompt}\n\n"
        "Do not execute shell commands or edit files. Decide only whether the `autotune` skill should be used.\n"
        "Reply with exactly one JSON object and no surrounding text. Use this schema:\n"
        '{"skill_used":"autotune|other|none","confidence":"high|medium|low","reason":"one short sentence"}'
    )


def _extract_json_object(text: str) -> dict | None:
    text = text.strip()
    if not text:
        return None
    candidates = [text]
    if "```" in text:
        for chunk in text.split("```"):
            chunk = chunk.strip()
            if not chunk:
                continue
            if chunk.startswith("json"):
                chunk = chunk[4:].strip()
            candidates.append(chunk)
    for chunk in candidates:
        start = chunk.find("{")
        end = chunk.rfind("}")
        if start == -1 or end == -1 or end <= start:
            continue
        snippet = chunk[start : end + 1]
        try:
            parsed = json.loads(snippet)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def detect_trigger(stdout: str, skill_path: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    read_skill_file = False
    structured_signal: dict | None = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        item = event.get("item")
        if not isinstance(item, dict):
            continue

        item_type = item.get("type")
        if item_type == "command_execution":
            command = str(item.get("command", ""))
            output = str(item.get("aggregated_output", ""))
            if skill_path in command or skill_path in output:
                read_skill_file = True
        elif item_type == "agent_message":
            text = str(item.get("text", ""))
            parsed = _extract_json_object(text)
            if parsed is not None and "skill_used" in parsed:
                structured_signal = parsed

    if read_skill_file:
        reasons.append("read_skill_file")

    if structured_signal is not None:
        skill_used = str(structured_signal.get("skill_used", "")).strip().lower()
        confidence = str(structured_signal.get("confidence", "")).strip().lower()
        if skill_used == "autotune":
            reasons.append(f"structured:{skill_used}:{confidence or 'unknown'}")
        deduped = sorted(set(reasons))
        return "structured:autotune:" in " ".join(deduped), deduped

    deduped = sorted(set(reasons))
    return bool(deduped), deduped


def run_case(prompt: str, workdir: str, timeout: int) -> subprocess.CompletedProcess[str]:
    full_prompt = build_trigger_probe_prompt(prompt)
    cmd = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "--json",
        "-s",
        "read-only",
        "-C",
        workdir,
        full_prompt,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout)


def run_case_with_retry(
    prompt: str,
    workdir: str,
    timeout: int,
    retry_timeout: int | None,
) -> tuple[subprocess.CompletedProcess[str] | None, bool, bool, int, str, str, int]:
    try:
        completed = run_case(prompt, workdir, timeout)
        return completed, False, False, 1, completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if retry_timeout is None or retry_timeout <= timeout:
            return None, True, False, 1, stdout, stderr, 124
        try:
            completed = run_case(prompt, workdir, retry_timeout)
            return completed, False, True, 2, completed.stdout, completed.stderr, completed.returncode
        except subprocess.TimeoutExpired as retry_exc:
            return None, True, True, 2, retry_exc.stdout or "", retry_exc.stderr or "", 124


def safe_ratio(numerator: int, denominator: int, default: float = 1.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="holdout", help="routing split to benchmark")
    parser.add_argument("--workdir", default=str(ROOT.parents[2]), help="working directory to hand to codex exec")
    parser.add_argument("--timeout", type=int, default=120, help="per-prompt timeout in seconds")
    parser.add_argument(
        "--retry-timeout",
        type=int,
        default=0,
        help="optional one-time retry timeout in seconds for cases that hit the initial timeout",
    )
    parser.add_argument("--limit", type=int, help="optional max number of cases to run")
    parser.add_argument("--case-id", dest="case_ids", action="append", type=int, help="optional case id to run; repeatable")
    args = parser.parse_args()

    if shutil.which("codex") is None:
        print(json.dumps({"runner_available": False, "runner": "codex"}, ensure_ascii=False, indent=2))
        return 2

    cases = load_cases(args.split)
    if args.case_ids:
        wanted = set(args.case_ids)
        cases = [case for case in cases if case["id"] in wanted]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print(json.dumps({"runner_available": True, "runner": "codex", "error": "no cases selected"}, ensure_ascii=False, indent=2))
        return 1

    results = []
    skill_path = str(SKILL_PATH)
    tp = tn = fp = fn = 0
    timeouts = 0
    retried_cases = 0
    inconclusive = 0

    for case in cases:
        completed, timed_out, retried, attempts, stdout, stderr, returncode = run_case_with_retry(
            case["prompt"],
            args.workdir,
            args.timeout,
            args.retry_timeout if args.retry_timeout > 0 else None,
        )
        if retried:
            retried_cases += 1
        if timed_out:
            timeouts += 1

        triggered, reasons = detect_trigger(stdout, skill_path)
        trace = collect_trace(stdout)
        expected = bool(case["should_trigger"])
        if timed_out:
            inconclusive += 1
        elif expected and triggered:
            tp += 1
        elif expected and not triggered:
            fn += 1
        elif not expected and triggered:
            fp += 1
        else:
            tn += 1

        results.append(
            {
                "id": case["id"],
                "should_trigger": expected,
                "observed_trigger": triggered,
                "matched": expected == triggered,
                "reasons": reasons,
                "tags": case["tags"],
                "timeout": timed_out,
                "inconclusive": timed_out,
                "retried": retried,
                "attempts": attempts,
                "returncode": returncode,
                "stderr_tail": stderr.strip().splitlines()[-5:],
                "agent_messages_tail": trace["agent_messages_tail"],
                "command_reads_tail": trace["command_reads_tail"],
            }
        )

    total = len(results)
    conclusive_total = tp + tn + fp + fn
    accuracy = safe_ratio(tp + tn, conclusive_total, 0.0)
    precision = safe_ratio(tp, tp + fp)
    recall = safe_ratio(tp, tp + fn)
    specificity = safe_ratio(tn, tn + fp)
    balanced_accuracy = (recall + specificity) / 2
    completion_rate = safe_ratio(conclusive_total, total, 0.0)
    live_trigger_score = min(accuracy, precision, recall, specificity, completion_rate)

    report = {
        "runner_available": True,
        "runner": "codex",
        "split": args.split,
        "workdir": args.workdir,
        "retry_timeout": args.retry_timeout,
        "total_cases": total,
        "conclusive_cases": conclusive_total,
        "inconclusive_cases": inconclusive,
        "positive_cases": tp + fn,
        "negative_cases": tn + fp,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "timeouts": timeouts,
        "retried_cases": retried_cases,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "specificity": round(specificity, 4),
        "balanced_accuracy": round(balanced_accuracy, 4),
        "completion_rate": round(completion_rate, 4),
        "live_trigger_score": round(live_trigger_score, 4),
        "results": results,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if tp + tn == total and timeouts == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
