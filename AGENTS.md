# Dengue Data Pipeline

Goberlab's open-source data pipeline for dengue forecasting in Peru. It builds a district × epi-week panel from surveillance, climate and static sources. Model training lives elsewhere and consumes the panel.

The work is still at the planning stage. The plan is a wayfinder map: the GitHub issue labelled `wayfinder:map`. Read it before starting any work.

## Ground rules

- Raw and derived data never go in git (see `.gitignore`). Commit code, docs and small fixtures only.
- Never treat a missing dengue count as zero. Never assume a value was known before its `available_at`.
- Read `GLOSSARY.md` before naming anything. Use its terms in code, issues and docs.

## Agent skills

### Issue tracker

GitHub Issues on `Goberlab/dengue-data-pipeline` via the `gh` CLI, with native sub-issues and blocking. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
