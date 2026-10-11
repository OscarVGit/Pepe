"""Select the IntentRouter implementation via PEPE_ROUTER.

- `von` (default): in-process `VonRouter` (requires `von-sdk` + weights).
- `von-http`: `VonHttpRouter` against a `von serve` sidecar.
- `fake`: deterministic `FakeRouter` (tests / offline; never downloads a model).

Tests should call `make_router(force="fake")` or set `PEPE_ROUTER=fake`.
"""
from __future__ import annotations

import os

from .intent import FakeRouter, IntentRouter


def make_router(force: str | None = None) -> IntentRouter:
    which = (force or os.environ.get("PEPE_ROUTER", "von")).lower()
    if which == "fake":
        return FakeRouter()
    if which == "von-http":
        from .von_http_router import VonHttpRouter
        return VonHttpRouter()
    if which == "von":
        from .von_router import VonRouter
        return VonRouter()
    raise ValueError(f"unknown PEPE_ROUTER: {which}")
