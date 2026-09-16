# PRODUCT — Mental Model, UX, MVP, Core Test

## Mental model

Pepe is a junior PE associate. The human says:

"Pepe, look into this." / "Can you remodel this?" / "Wait until I get the debt
terms." / "Actually use the revised management accounts." / "Run a downside."
/ "Update the IC deck." / "What changed?" / "Why did the IRR fall?"
/ "Hold off on sending anything."

Pepe maintains between turns: which deal, which model is current, agreed
assumptions, completed work, missing info, outstanding tasks, past decisions.

## Target interaction (Atlas)

- User: "Pepe, start working on Atlas."
- Pepe: "Got it. I'll review the CIM, current model and management accounts and identify inconsistencies before changing the model." *(works async)*
- Pepe: "Found an EBITDA discrepancy between CIM and management accounts. Investigating."
- Pepe: "Traced $1.2m to normalisation adjustments. $600k unreconciled from available documents."
- User: "I'll get management's bridge tomorrow."
- Pepe: "Understood. Blocking dependent model changes on the EBITDA bridge."
- *(next day)* User: "Here's the bridge."
- Pepe: "Reconciled — one-off restructuring expense. I'll update the model unless you'd prefer otherwise."
- User: "Go ahead." → Pepe: "Done. Model updated, returns recalculated, schedules validated."
- User: "What does the downside look like?" → Pepe runs 7.0x exit / −15% EBITDA: MOIC 1.7x, IRR 11.4%; notes exit-multiple sensitivity.
- User: "Update the IC deck." → Pepe updates returns/downside/thesis slides, preserving structure.

## MVP (first meaningful slice)

Telegram → Pepe → one deal workspace (CIM + Excel model + management accounts)
→ read/analyse → identify discrepancy → ask question → wait → receive info →
modify Excel (working copy) → deterministic calc → validate → report IRR/MOIC/
sensitivities. Explicitly NOT: every platform, every data provider, autonomous
decisions.

## Core product test

Not "can Pepe generate an LBO" — many tools can. The test: hand Pepe a real
workspace Monday ("Start reviewing Atlas"), feed debt terms Tuesday, request
model updates + downside Wednesday, deck Thursday, and ask Friday "What changed
since Monday?" — with coherent state, correct artifacts, and a full audit trail.
