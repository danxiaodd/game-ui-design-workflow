# Repository guidance

- Canonical skills are under `skills/`; `.agents/skills/` links expose them to Codex. Windows users can run the copying installer instead of relying on Git symlinks.
- Existing GDDs are authoritative. Visual workflows must not require rewriting GDD/PRD/interaction docs. Keep facts, visual defaults and new suggestions distinct.
- Preserve user confirmation after direction, concept and formal page drafts. Never infer approval from successful generation or validation.
- No Figma dependency. Inspect actual tools in the current environment. Preserve older outputs; do not fabricate generation, file paths or engine verification.
- Shared scripts live in `scripts/`. Per-skill `scripts/run.py` copies must match `scripts/skill_runner.py`; installation deploys a versioned runtime.
- Before handoff run `python -m unittest discover -s tests -v`, `python scripts/validate_skills.py`, and strict validation of the three existing complete examples. State, pixel validation, visual review and actual engine import are distinct evidence.
- Keep LICENSE and ORIGIN.md. Reference projects supply design ideas; do not transplant their service credentials, Figma integrations or large frameworks.
