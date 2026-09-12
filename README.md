# Productivity Tracker

_Repository: `personal_productivity_planner`_

A personal productivity tracker for goals, habits, and life-balance across every domain of your life. Not just a task manager.

This repository is private. It will eventually hold configuration and (synthetic/redacted) fixtures spanning career, financial, relationship, marriage, and other personal domains — never real credentials, and real personal data only in the local, gitignored `data/` working files, not in commits.

## Status

Live and in daily use (updated 2026-09-12). See `docs/architecture.md` for the full blueprint and `docs/decision_log.md` for the decisions made so far and a running history of what's shipped. The daily 4 AM executive brief and weekly review email run unattended via claude.ai's Google Workspace connectors (see `docs/automation.md`). Every domain has real goals with deadlines, an "on course / falling behind" status, a quick-capture inbox, a decision log, and habit streaks. Currently migrating storage from local SQLite to hosted Postgres (Supabase) - see `docs/decision_log.md` for progress.

## Layers

1. **Strategy** — `config/*.yaml` (life domains, goals, priority weights)
2. **Intelligence** — `engine/` (priority engine, balance engine, classification)
3. **Execution** — `integrations/` (Gmail, Calendar, Drive, GitHub, news)
4. **Evidence** — Postgres (Supabase/Neon) + `audit_log`
5. **Interface** — `app/streamlit/`

## Setup

1. Copy `.env.example` to `.env` and fill in real values locally. Never commit `.env`.
2. See `docs/security.md` for credential handling rules before running anything against real accounts.
3. `python -m venv .venv && .venv\Scripts\pip install -r requirements.txt` (Windows) or the POSIX equivalent.
4. `.venv\Scripts\python -m streamlit run app/streamlit/Home.py`

Storage is hosted Postgres (Supabase) via `DATABASE_URL` in `.env` - see `docs/decision_log.md` for the migration. No local database setup is required beyond that.

## Automation

The 4 AM daily review, weekly/monthly/quarterly reviews run as a scheduled Claude cloud agent against claude.ai's Google Workspace connectors (Gmail/Calendar/Drive) — not from this repo's code directly. See `docs/automation.md`.
