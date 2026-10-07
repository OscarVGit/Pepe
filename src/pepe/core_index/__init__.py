"""Pepe Core Index — firm-level mirror of per-deal state.

Read-aggregated, never authoritative. Per-deal pepe.db remains sovereign.
"""

from . import sync as sync_mod  # re-export helpers
from .connection import get_firm_db, get_lock
from .query import (
    global_search,
    list_active_deals,
    list_deals,
    pipeline_summary,
)
from .schema import SCHEMA, init
from .sync import sync_all, sync_deal

__all__ = [
    "SCHEMA",
    "get_firm_db",
    "get_lock",
    "global_search",
    "init",
    "list_active_deals",
    "list_deals",
    "pipeline_summary",
    "sync_all",
    "sync_deal",
]
