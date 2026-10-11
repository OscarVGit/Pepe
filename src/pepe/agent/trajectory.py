"""Per-run trajectory recorder: full step-by-step conversation, JSONL.

Each run writes `deals/<deal>/runs/<run_id>/trajectory.jsonl`. This is the
self-documenting record the AI documentation and evals read from.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schemas import Step


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TrajectoryRecorder:
    def __init__(self, deal_root: Path, deal_id: str) -> None:
        self.deal_id = deal_id
        self.run_id = uuid.uuid4().hex[:12]
        self.dir = deal_root / "runs" / self.run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "trajectory.jsonl"

    def record(self, step: Step) -> None:
        entry = {"ts": _now(), "run_id": self.run_id, **step.model_dump()}
        with self.path.open("a") as f:
            f.write(json.dumps(entry, default=str) + "\n")


def latest_run_dir(deal_root: Path) -> Path | None:
    runs = deal_root / "runs"
    if not runs.exists():
        return None
    dirs = sorted([d for d in runs.iterdir() if d.is_dir()])
    return dirs[-1] if dirs else None


def read_trajectory(deal_root: Path, run_id: str | None = None) -> list[dict[str, Any]]:
    d = (deal_root / "runs" / run_id) if run_id else latest_run_dir(deal_root)
    if d is None or not (d / "trajectory.jsonl").exists():
        return []
    out = []
    with (d / "trajectory.jsonl").open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
