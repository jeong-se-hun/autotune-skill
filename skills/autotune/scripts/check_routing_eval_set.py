#!/usr/bin/env python3
"""Validate that autotune's routing eval set covers the important trigger boundaries."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALS_PATH = ROOT / "evals" / "evals.json"


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def _is_positive(expected_output: str) -> bool:
    return "does not trigger" not in expected_output.lower()


def _contains_hangul(text: str) -> bool:
    return any("\uac00" <= char <= "\ud7a3" for char in text)


def main() -> int:
    data = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    evals = data.get("evals", [])
    if len(evals) < 16:
        return fail("routing eval set should contain at least 16 prompts")

    prompts = [str(item.get("prompt", "")) for item in evals]
    outputs = [str(item.get("expected_output", "")) for item in evals]
    pairs = list(zip(prompts, outputs))
    positives = [(p, o) for p, o in pairs if _is_positive(o)]
    negatives = [(p, o) for p, o in pairs if not _is_positive(o)]
    train_positive = 0
    train_negative = 0
    holdout_positive = 0
    holdout_negative = 0

    for index, item in enumerate(evals):
        routing = item.get("routing")
        if not isinstance(routing, dict):
            return fail(f"evals[{index}].routing must be an object")
        split = routing.get("split")
        if split not in {"train", "holdout"}:
            return fail(f"evals[{index}].routing.split must be 'train' or 'holdout'")
        should_trigger = routing.get("should_trigger")
        if not isinstance(should_trigger, bool):
            return fail(f"evals[{index}].routing.should_trigger must be a boolean")
        if split == "train" and should_trigger:
            train_positive += 1
        elif split == "train":
            train_negative += 1
        elif should_trigger:
            holdout_positive += 1
        else:
            holdout_negative += 1

    if not any(_contains_hangul(prompt) for prompt in prompts):
        return fail("routing eval set should include at least one Korean prompt")
    if not any(any("a" <= ch.lower() <= "z" for ch in prompt) for prompt in prompts):
        return fail("routing eval set should include at least one English prompt")
    if train_positive < 4 or train_negative < 4:
        return fail("routing eval set should keep at least 4 positive and 4 negative prompts in train")
    if holdout_positive < 3 or holdout_negative < 3:
        return fail("routing eval set should keep at least 3 positive and 3 negative prompts in holdout")

    positive_checks = {
        "bounded positive": any("bounded" in output.lower() for _, output in positives),
        "threshold positive": any("threshold mode" in output.lower() for _, output in positives),
        "continuous positive": any("continuous mode" in output.lower() for _, output in positives),
        "eval-first positive": any(
            "build the eval harness first" in output.lower() or "build the evaluator first" in output.lower()
            for _, output in positives
        ),
        "human-review positive": any(
            "human review" in output.lower() or "blind comparison" in output.lower() for _, output in positives
        ),
    }
    for label, passed in positive_checks.items():
        if not passed:
            return fail(f"routing eval set is missing coverage for: {label}")

    negative_checks = {
        "review-first negative": any("review" in output.lower() for _, output in negatives),
        "open-ended negative": any("open-ended" in output.lower() for _, output in negatives),
        "debugging-first negative": any(
            "debug" in output.lower() or "investigation" in output.lower() for _, output in negatives
        ),
        "missing-stop-rules negative": any("stop rule" in output.lower() for _, output in negatives),
        "missing-eval negative": any("eval harness" in output.lower() for _, output in negatives),
    }
    for label, passed in negative_checks.items():
        if not passed:
            return fail(f"routing eval set is missing coverage for: {label}")

    print("routing-evals: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
