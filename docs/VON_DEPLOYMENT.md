# VON_DEPLOYMENT — Von Router Deployment

Short companion to `HOSTING.md`. Diagrams and quickstart only.

## In-process (default)

```
┌─────────────┐
│   Pepe CLI  │   python -m pepe ask atlas "..."
│  (von-sdk)  │   → von.decide(...) in-process
└─────────────┘
```

Install:

```bash
pip install -e ".[router-cpu]"      # or .[router-gpu]
```

First classify downloads ~1.5 GB to `HF_HOME`.

## Sidecar (multi-process / Phase 2)

```
┌──────────────┐     ┌────────────────┐     ┌─────────────┐
│ Telegram gw  │     │  Pepe CLI/API  │     │  ...        │
└──────┬───────┘     └───────┬────────┘     └──────┬──────┘
       │                     │                     │
       └─────────── HTTP ────┴── /v1/systemone ────┘
                              │
                       ┌──────┴──────┐
                       │  von serve  │   127.0.0.1:8000
                       └─────────────┘
```

```bash
docker run --rm -p 8000:8000 -v von-hf:/data/huggingface ghcr.io/wfzyx/von:cpu
# or
von serve --host 127.0.0.1 --port 8000
```

Point Pepe at it:

```bash
PEPE_ROUTER=von-http VON_BASE_URL=http://127.0.0.1:8000 python -m pepe ask atlas "..."
```

## Health check

```bash
curl -X POST localhost:8000/v1/systemone \
  -H 'Content-Type: application/json' \
  -d '{"state": {"message": "compute irr for -100,110"}, "questions": {"intent": {"type": "choice", "instructions": "...", "criteria": {"compute_finance": "...", "status_query": "..."}}}}'
```

## Capacity

- CPU: ~96 ms p50 per message (4 vCPU, OpenVINO).
- GPU: ~23 ms p50 (A10G).
- Throughput: ~10 msg/s per CPU process; scale horizontally via sidecars.

See `HOSTING.md` for env vars, failure modes, calibration, and operational
signals.
