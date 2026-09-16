#!/bin/sh
# Dev entry: compile check + test collection (Phase 0 verification).
set -e
python -m compileall src
pytest --collect-only
