"""Approval tiers are architectural, not prompt suggestions. See docs/HUMAN_IN_LOOP.md."""
from __future__ import annotations

from enum import Enum


class RiskTier(str, Enum):
    LOW = "low"      # read/extract/calculate/reconcile/draft — auto
    MEDIUM = "medium"  # modify working model, assumptions, outputs, deck — execute + report
    HIGH = "high"    # send external, delete, overwrite originals, IC conclusions — explicit approval


HIGH_RISK_ACTIONS = frozenset({
    "send_external", "delete_file", "overwrite_original",
    "commit_investment_conclusion", "distribute_ic", "external_transaction",
})

MEDIUM_RISK_ACTIONS = frozenset({
    "modify_working_model", "update_assumption", "create_output", "change_presentation",
})


def classify(action: str) -> RiskTier:
    if action in HIGH_RISK_ACTIONS:
        return RiskTier.HIGH
    if action in MEDIUM_RISK_ACTIONS:
        return RiskTier.MEDIUM
    return RiskTier.LOW


def requires_approval(action: str) -> bool:
    return classify(action) is RiskTier.HIGH
