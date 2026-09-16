"""Persistent agent runtime loop. Phase 0: pipeline definition only."""
from __future__ import annotations

# USER MESSAGE → ADAPTER → LOAD DEAL STATE → UNDERSTAND → PLAN → EXECUTE
#   → UPDATE STATE → WAIT/CONTINUE/ASK → SEND MESSAGE
# State persists across restarts; waiting states resume on user message / event / schedule.


def handle_message(payload: dict) -> dict:
    """Phase 1+: full loop. Phase 0: stub."""
    raise NotImplementedError
