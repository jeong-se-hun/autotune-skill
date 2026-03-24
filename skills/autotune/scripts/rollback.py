#!/usr/bin/env python3
"""Snapshot and restore files during an autotune loop.

Commands:
    snapshot <file> [file ...]   Copy files to /tmp/autotune-snapshots/ with a timestamp.
    restore  <file> [file ...]   Restore each file from its most recent snapshot.
    list     [file]              List all snapshots (or just for one file).
    clean    [file] [--keep N]   Remove old snapshots, keeping the N most recent (default: 5).

Exit codes:
    0  success
    1  error (missing file, no snapshot found, etc.)
    2  usage error
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path

SNAPSHOT_ROOT = Path("/tmp/autotune-snapshots")
META_FILENAME = "_meta.json"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S_%f"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _slot_dir(path: Path) -> Path:
    """Return the snapshot directory for a given absolute path."""
    key = sha1(str(path).encode()).hexdigest()[:12]
    return SNAPSHOT_ROOT / key


def _load_meta(slot: Path) -> dict:
    meta_path = slot / META_FILENAME
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_meta(slot: Path, meta: dict) -> None:
    slot.mkdir(parents=True, exist_ok=True)
    (slot / META_FILENAME).write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _list_snapshots(slot: Path) -> list[Path]:
    """Return snapshot files sorted oldest → newest (by filename timestamp)."""
    if not slot.exists():
        return []
    return sorted(
        p for p in slot.iterdir()
        if p.is_file() and p.name != META_FILENAME
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_snapshot(files: list[str]) -> int:
    if not files:
        print("snapshot: no files specified", file=sys.stderr)
        return 2

    ts = datetime.now(tz=timezone.utc).strftime(TIMESTAMP_FORMAT)
    errors = 0
    for raw in files:
        src = Path(raw).resolve()
        if not src.exists():
            print(f"snapshot: file not found: {src}", file=sys.stderr)
            errors += 1
            continue

        slot = _slot_dir(src)
        slot.mkdir(parents=True, exist_ok=True)

        snap_name = f"{ts}_{src.name}"
        dest = slot / snap_name
        shutil.copy2(src, dest)

        meta = _load_meta(slot)
        meta["original_path"] = str(src)
        _save_meta(slot, meta)

        print(f"snapshot: {src} -> {dest}")

    return 1 if errors else 0


def cmd_restore(files: list[str]) -> int:
    if not files:
        print("restore: no files specified", file=sys.stderr)
        return 2

    errors = 0
    for raw in files:
        src = Path(raw).resolve()
        slot = _slot_dir(src)
        snaps = _list_snapshots(slot)

        if not snaps:
            print(f"restore: no snapshot found for: {src}", file=sys.stderr)
            errors += 1
            continue

        latest = snaps[-1]
        src.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(latest, src)
        print(f"restore: {latest} -> {src}")

    return 1 if errors else 0


def cmd_list(files: list[str]) -> int:
    if files:
        targets = [Path(f).resolve() for f in files]
    else:
        # All known slots
        if not SNAPSHOT_ROOT.exists():
            print("list: no snapshots found")
            return 0
        targets = []
        for slot in sorted(SNAPSHOT_ROOT.iterdir()):
            if not slot.is_dir():
                continue
            meta = _load_meta(slot)
            orig = meta.get("original_path")
            if orig:
                targets.append(Path(orig))

    found_any = False
    for path in targets:
        slot = _slot_dir(path)
        snaps = _list_snapshots(slot)
        if snaps:
            found_any = True
            print(f"{path}:")
            for snap in snaps:
                size = snap.stat().st_size
                print(f"  {snap.name}  ({size} bytes)")

    if not found_any:
        print("list: no snapshots found")
    return 0


def cmd_clean(files: list[str], keep: int) -> int:
    if keep < 1:
        print("clean: --keep must be >= 1", file=sys.stderr)
        return 2

    if files:
        targets = [Path(f).resolve() for f in files]
        slots = [_slot_dir(p) for p in targets]
    else:
        if not SNAPSHOT_ROOT.exists():
            print("clean: no snapshots to clean")
            return 0
        slots = [d for d in SNAPSHOT_ROOT.iterdir() if d.is_dir()]

    removed_total = 0
    for slot in slots:
        snaps = _list_snapshots(slot)
        to_remove = snaps[:-keep] if len(snaps) > keep else []
        for snap in to_remove:
            snap.unlink()
            print(f"clean: removed {snap}")
            removed_total += 1

    if removed_total == 0:
        print("clean: nothing to remove")
    else:
        print(f"clean: removed {removed_total} snapshot(s)")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", metavar="command")

    p_snap = sub.add_parser("snapshot", help="copy files to /tmp snapshot store")
    p_snap.add_argument("files", nargs="+", metavar="file")

    p_rest = sub.add_parser("restore", help="restore files from most recent snapshot")
    p_rest.add_argument("files", nargs="+", metavar="file")

    p_list = sub.add_parser("list", help="list stored snapshots")
    p_list.add_argument("files", nargs="*", metavar="file")

    p_clean = sub.add_parser("clean", help="remove old snapshots")
    p_clean.add_argument("files", nargs="*", metavar="file")
    p_clean.add_argument("--keep", type=int, default=5, metavar="N",
                         help="number of snapshots to keep per file (default: 5)")

    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        return 2

    args = parser.parse_args()

    if args.command == "snapshot":
        return cmd_snapshot(args.files)
    elif args.command == "restore":
        return cmd_restore(args.files)
    elif args.command == "list":
        return cmd_list(args.files)
    elif args.command == "clean":
        return cmd_clean(args.files, args.keep)
    else:
        parser.print_help(sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
