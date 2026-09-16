# THREAT_MODEL — What We Defend Against

| Threat | Control |
|---|---|
| Confidential CIM sent to cloud | Local-only default; sanitise-before-send; gateway policy; approval |
| Re-identification of "Company A" | Quasi-identifier review; RESTRICTED default; minimum-necessary payloads |
| Provider retention of deal data | Approved-provider list; zero-retention terms; payload-hash audit |
| Prompt injection via CIM/email | Instruction hierarchy; tool-arg scanning; sandbox; approval for side effects |
| Malicious doc / macro | Parse-only libraries; no macro execution; containerised conversion |
| Tool exfiltration (webhook/SSRF) | Egress allowlist; MCP firewall; audit on every external call |
| Model overwrites originals | Copy-on-write; HIGH-risk tier; immutable `original.*` |
| Hallucinated figures | Deterministic calc; validation gate; facts-vs-assumptions labels |
| Lost state on restart | SQLite-sync persistence; no context-only truth |
| Affecting IC without approval | HIGH-risk gate on conclusions/distribution |

Out of scope Phase 0: full red-team suite, DLP integration, SIEM export.
