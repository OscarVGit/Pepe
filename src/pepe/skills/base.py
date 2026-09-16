"""Skill manifest schema. Each skills/<name>/SKILL.md follows this contract."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Skill:
    name: str
    purpose: str = ""
    when_to_use: str = ""
    required_inputs: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    validation: str = ""
    approvals: str = ""
    failure_modes: str = ""
