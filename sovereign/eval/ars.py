"""ARS scoring utilities for the SOVEREIGN scaffold."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping


def compute_ars_step(state: Mapping[str, float], params: Mapping[str, float]) -> float:
    """Compute a single ARS score from step state and ARS weight parameters."""
    safety = float(state.get("safety", 0.0))
    efficiency = float(state.get("efficiency", 0.0))
    comfort = float(state.get("comfort", 0.0))
    compliance = float(state.get("compliance", 0.0))

    w_safety = float(params.get("safety", 0.50))
    w_efficiency = float(params.get("efficiency", 0.25))
    w_comfort = float(params.get("comfort", 0.15))
    w_compliance = float(params.get("compliance", 0.10))

    return (
        safety * w_safety
        + efficiency * w_efficiency
        + comfort * w_comfort
        + compliance * w_compliance
    )


def write_ars_timeseries(path: str | Path, rows: Iterable[Mapping[str, float]]) -> None:
    """Write ARS rows to CSV; writes only header if rows is empty."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["step", "t_s", "ars_score"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "step": row.get("step", 0),
                    "t_s": row.get("t_s", 0.0),
                    "ars_score": row.get("ars_score", 0.0),
                }
            )
