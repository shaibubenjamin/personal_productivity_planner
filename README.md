# Productivity Tracker

_Repository: `personal_productivity_planner`_

A personal productivity tracker for goals, habits, and life-balance across every domain of your life. Not just a task manager.

This repository is private. It will eventually hold configuration and (synthetic/redacted) fixtures spanning career, financial, relationship, marriage, and other personal domains — never real credentials, and real personal data only in the local, gitignored `data/` working files, not in commits.

## Status

Pre-implementation. See `docs/architecture.md` for the full blueprint and `docs/decision_log.md` for the decisions made so far. Currently in **Phase 0/1 (Discovery/Foundation)** — no live Gmail/Calendar/Drive integration exists yet, no automation runs yet.

## Layers

1. **Strategy** — `config/*.yaml` (life domains, goals, priority weights)
2. **Intelligence** — `engine/` (priority engine, balance engine, classification)
3. **Execution** — `integrations/` (Gmail, Calendar, Drive, GitHub, news)
4. **Evidence** — Postgres (Supabase/Neon) + `audit_log`
5. **Interface** — `app/streamlit/`

## Setup

### Docker (recommended — works the same on any machine)

```
docker compose up --build
```

Then open http://localhost:8501. SQLite data persists in `data/local/` on the host (mounted as a volume), so `docker compose down` / `up` again doesn't lose it. Copy `.env.example` to `.env` first if you need any of those variables set — it's optional for local SQLite-only runs.

### Without Docker

1. Copy `.env.example` to `.env` and fill in real values locally. Never commit `.env`.
2. See `docs/security.md` for credential handling rules before running anything against real accounts.
3. `python -m venv .venv && .venv\Scripts\pip install -r requirements.txt` (Windows) or the POSIX equivalent.
4. `.venv\Scripts\python -m streamlit run app/streamlit/Home.py`

## Automation

The 4 AM daily review, weekly/monthly/quarterly reviews run as a scheduled Claude cloud agent against claude.ai's Google Workspace connectors (Gmail/Calendar/Drive) — not from this repo's code directly. See `docs/automation.md`.
