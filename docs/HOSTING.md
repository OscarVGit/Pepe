# HOSTING — Running the Von Intent Router

This is the operational runbook for hosting the Von System One intent router
that classifies every inbound Pepe message. Von is the only model in the
routing hot path. Everything below assumes Phase 1 defaults; Phase 2 multi-process
notes are called out.

## Topologies

### 1. In-process (default)

`VonRouter` loads `von-sdk` inside the Pepe Python process. No daemon.

- Weights (~1.5 GB fp32) are fetched from the Hub on first use into `HF_HOME`.
- One forward pass per message; ~96 ms p50 on a 4-vCPU CPU.
- Best for the CLI and any single-process Pepe.

### 2. Sidecar HTTP server (multi-process / Phase 2)

`von serve` exposes `/v1/systemone` on `127.0.0.1:8000` (byte-compatible with
TypeSafe Jev). Pepe talks to it via `VonHttpRouter` (httpx).

- Weights load once, shared by every Pepe process and by the Telegram gateway.
- Standard wire protocol; easy to scale horizontally.

```
PEPE_ROUTER=von-http VON_BASE_URL=http://127.0.0.1:8000  python -m pepe ...
```

## Environment variables

| Var | Default | Effect |
|---|---|---|
| `PEPE_ROUTER` | `von` | `von` (in-process), `von-http` (sidecar), `fake` (tests only) |
| `VON_BASE_URL` | `http://127.0.0.1:8000` | Sidecar endpoint for `von-http` |
| `VON_DEVICE` | `auto` | `auto` → OpenVINO CPU > torch CPU; also `cuda`, `mps`, `rocm` |
| `VON_CONFIDENCE` | `0.80` | Choice confidence threshold for abstention |
| `HF_HOME` | `~/.cache/huggingface` | Model weight cache |
| `PEPE_INTENTS_PATH` | `<repo>/intents.json` | Override the taxonomy file |

## Storage and cache

- Weights live under `HF_HOME` (`~/.cache/huggingface/hub/models--wfzyx--von`).
- The calibration map (`marker_calibration.json`) is loaded from the checkpoint
  directory; a custom calibration is written next to it (see Phase 1.5).
- Clear cache with `rm -rf "$HF_HOME/hub/models--wfzyx--von"`; next run
  re-downloads.

## Devices

- Default `auto` prefers OpenVINO CPU over plain torch CPU.
- To verify the active device: run one classify and read the `served_by` and
  `device` audit fields, or set `VON_DEVICE=cpu` and check latency.
- GPU is a Phase 2 nicety; the CLI is fast enough on CPU.

## Calibration (Phase 1.5)

The shipped confidence map is JevBench-shaped and does not carry to PE
phrasing. Phase 1.5 adds:

```
pepe calibrate --labels path/to/labels.jsonl
```

Each line of `labels.jsonl` is a wire question plus gold:

```json
{"state": {"message": "Pepe, run a downside"}, "instructions": "...", "choices": {...}, "gold": "run_analysis"}
```

This refits `marker_calibration.json` with frozen weights on CPU in minutes.

## Failure and degradation

| Condition | Behaviour |
|---|---|
| Confidence < threshold, or `unclear` intent | `WAITING_FOR_INFORMATION` + clarifying question |
| Von SDK error / weights missing | Blocked outcome with `router_error` reason; audited |
| Von timeout | Blocked outcome with `router_timeout` reason; audited |
| `PEPE_ROUTER=fake` | Deterministic `FakeRouter` (tests only) |

Messages are never dropped. Every router decision is audit-logged with
`router.served_by`, top-3 probabilities, and confidence.

## Operational signals

Audit fields (see `pepe.db` audit_log, or `runs/<run_id>/trajectory.jsonl`):

- `router.served_by` — which implementation (`von` / `von-http` / `fake`).
- `router.confidence` — calibrated choice confidence.
- `router.top3` — top-3 intents and probabilities.
- `router.error` / `router.error_reason` — on failure.

Alert on sustained `router_error` or a spike in low-confidence routing.

## Threat model notes

- Von runs locally on CPU; no message leaves the box for routing.
- Calibration is a non-PE-shaped prior; do not trust confidence on
  out-of-domain phrasing until `pepe calibrate` has run.
- English only. Non-English content gets token overlap with unearned
  confidence.
