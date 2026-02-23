-"""Adversary event schema and generation for SOVEREIGN."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class Event:
    name: str
    enabled: bool
    seed: int
    intensity: float


def generate_events_from_spec(adversary_section: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate concrete event records from the adversary section."""
    enabled = bool(adversary_section.get("enabled", True))
    seed = int(adversary_section.get("seed", 0))
    intensity = float(adversary_section.get("intensity", 0.0))
    suite = list(adversary_section.get("suite", []))

    events: List[Dict[str, Any]] = []
    for name in suite:
        event = Event(name=str(name), enabled=enabled, seed=seed, intensity=intensity)
        events.append(asdict(event))
    return events
