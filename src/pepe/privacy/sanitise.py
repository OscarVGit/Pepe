"""Privacy: classification + local sanitisation. Raw deal data stays local by default."""
from __future__ import annotations

from enum import Enum


class Classification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    DEAL_SENSITIVE = "DEAL_SENSITIVE"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"  # local-only unless explicit approval
    APPROVED_CLOUD = "APPROVED_CLOUD"


def sanitise_locally(text: str, mapping: dict[str, str]) -> tuple[str, dict]:
    """Replace identifiers per mapping inside the private env. Returns (sanitised, report).

    Phase 1: deterministic templating primary, Presidio NER secondary.
    Never send the raw CIM to a cloud model to be anonymised.
    """
    raise NotImplementedError
