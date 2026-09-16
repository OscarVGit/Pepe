# Skill: powerpoint

- **Purpose:** Update IC decks while preserving structure and formatting.
- **When to use:** Returns/downside/thesis slide refreshes.
- **Required inputs:** Deck path, slide registry, new deal facts.
- **Available tools:** python-pptx wrappers (Phase 4), Excel skill outputs.
- **Expected outputs:** Versioned deck + slide-change log.
- **Validation:** Diff slides vs prior version; numbers match model.
- **Approval requirements:** Content changes medium; distribution high.
- **Failure modes:** Template drift → stop, preserve structure, ask.
