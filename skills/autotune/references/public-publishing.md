# Public Publishing

Use this reference when the target skill is meant for public distribution through `skills.sh`, a shared Git repository, or a marketplace wrapper.

## Core Principle

Keep the core skill portable first.

- Put durable instructions in `SKILL.md`.
- Keep helpers in `scripts/`, `references/`, `assets/`, and `evals/`.
- Treat vendor-specific packaging as sidecar metadata, not as the core skill.

## Preferred Structure

Prefer a repo root with a short `README.md`, the skill folder, and optional vendor wrappers. Keep the skill folder centered on `SKILL.md`, `scripts/`, `references/`, `assets/`, `evals/`, and `agents/openai.yaml` when metadata is needed.

## Public-Safe Defaults

- Keep `name`, `description`, `compatibility`, and the instruction body portable.
- Avoid Claude-only features unless the skill is intentionally Claude-only, and prefer optional Claude packaging such as `.claude-plugin/` over embedding vendor-specific behavior in the core skill.
- Keep install guidance short and tool-agnostic. If the destination repo is known, show the right `npx skills add ... --skill <name>` command.

## Review Checklist

- The public export has no user-specific paths or maintainer-only clutter.
- The repo root has a short install README and a license.
- Codex-facing metadata still exists if `agents/openai.yaml` is part of the package.
- Optional Claude packaging is clearly separate and has no placeholder owner metadata.

## When to Reject a Change

Reject a proposed improvement if it narrows the skill to one vendor without benefit, adds packaging files that duplicate the core instructions, depends on unsupported runtime behavior, or bloats the public export with maintainer-only files.
