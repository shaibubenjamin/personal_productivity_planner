# Personal Executive Operating System (PEOS)

A personal Chief-of-Staff / strategic-planning / life-balance system. Not a task manager.

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

1. Copy `.env.example` to `.env` and fill in real values locally. Never commit `.env`.
2. See `docs/security.md` for credential handling rules before running anything against real accounts.

## Automation

The 4 AM daily review, weekly/monthly/quarterly reviews run as a scheduled Claude cloud agent against claude.ai's Google Workspace connectors (Gmail/Calendar/Drive) — not from this repo's code directly. See `docs/automation.md`.
