# PEOS — Architecture (canonical copy)

This is the canonical, in-repo copy of the implementation blueprint. The original draft (created before this repo existed) lives at `../../PEOS_ARCHITECTURE_BLUEPRINT.md` outside the repo — treat *this* file as source of truth going forward; update it, not the outside copy.

Status: Phase 0/1 (Discovery/Foundation). No live Gmail/Calendar/Drive integration yet. No automation runs yet.

## 0. Tooling reality

- **Gmail / Calendar**: only usable via claude.ai's Google Workspace connector, authorized in claude.ai → Settings → Connectors. Not available from a local Claude Code session.
- **Google Drive**: same connector family; must be authorized the same way.
- **GitHub**: via `gh`/`git` CLI, authenticated locally with `gh auth login` (device flow) — no token ever pasted into chat.
- **Web search**: available to any Claude session for the Global Intelligence Engine.

## 1. Layers → tech mapping

| Layer | Responsibility | Implementation |
|---|---|---|
| Strategy | Domains, objectives, goals | `config/*.yaml` |
| Intelligence | Priority engine, balance engine, classification | `engine/`, invoked by Claude Skills |
| Execution | Gmail/Calendar/Drive/GitHub | claude.ai Workspace connectors (scheduled cloud agent) + `integrations/github` |
| Evidence | System of record | Hosted Postgres (Supabase/Neon) + `audit_log` |
| Interface | Visibility/control | Streamlit app on Streamlit Community Cloud |

## 2. Resolved decisions (2026-09-07)

See `decision_log.md` for full rationale. Summary:
- Automation runtime: claude.ai connectors + scheduled Claude cloud agent.
- Database: hosted Postgres (Supabase/Neon free tier).
- Streamlit hosting: Streamlit Community Cloud.
- Repo visibility: private.
- Trust graduation (default, unconfirmed): 14 consecutive clean days before Category B automation.

## 3. Data model

Spec's table list (domains, objectives, goals, projects, tasks, commitments, calendar_events, emails, documents, learning_items, reviews, intelligence_items, actions, audit_log) with:
- `domain_id` FK added to domain-linked tables for fast balance queries.
- `actions` (mutable queue: proposed/pending/approved/executed/rejected) kept separate from `audit_log` (immutable history).
- `automation_category` (A/B/C) on `actions`, enforced from `config/automation_policy.yaml`.
- `confidence` (HIGH/MEDIUM/LOW) on `intelligence_items`, `emails`, `actions`.

DDL to be written as Postgres migrations (Alembic or plain SQL in `data/schemas/`) once account is created.

## 4. Priority scoring

```
priority_score =
    0.30 * strategic_importance
  + 0.20 * urgency
  + 0.15 * strategic_value
  + 0.15 * risk_of_neglect
  + 0.10 * deadline_pressure
  + 0.10 * dependency_criticality
```
Weights live in `config/priorities.yaml`, never hard-coded.

## 5. Life-balance engine

Per domain, per rolling window: `attention_actual` vs `attention_required` (config minimum, adjusted by goal urgency) → `neglect_risk`. Three flags only: OVER_INVESTMENT / UNDER_INVESTMENT / HEALTHY. No composite "life score."

## 6. Automation policy

Category A (read/analyze/classify/recommend) runs unattended. Category B (archive, label, low-risk calendar blocks) is proposed into the `actions` queue for **batched morning approval** — never silent, even after the trust-graduation threshold is met. Category C (delete, send, cancel, move important meetings, financial/relationship-sensitive actions) always requires per-action approval, no batching. Enforced via `config/automation_policy.yaml`.

## 7. Skill architecture

Master skill `personal-executive-os` orchestrates specialist skills (`goal-management`, `priority-engine`, `life-balance-engine`, `daily-executive-review`, `weekly/monthly/quarterly-review`, `email-intelligence`, `drive-housekeeping`, `calendar-intelligence`, `global-intelligence`, `career-development`, `learning-manager`, `french-coach`, `financial-manager`, `relationship-manager`, `knowledge-manager`, `meeting-intelligence`, `executive-communication`) — one skill.md per concern, resources/scripts alongside, no monolithic prompt file.

## 8. Testing strategy

Safety tests (no accidental delete/send/cancel) and the balance test (career-dominance scenario must trigger neglect flags on other domains) are written against fixtures *before* any live connector is wired up.

## 9. Contradictions found in the original spec

1. Spec assumed a Workspace connector already present in the build environment — it wasn't, in the Claude Code session used to scaffold this repo.
2. Category B "automatic after confidence" conflicts with "human approval" principle during unattended 4 AM runs — resolved via batched morning approval, never silent execution.
3. No numeric definition of "reliably" for graduating from V1 to automation — resolved with a 14-day default, owner can override.
4. Financial domain (bank-account-level tracking) has no proposed data connector — V1 treats financial data as manually entered via Streamlit, not auto-ingested from a bank API, unless the owner explicitly wants that larger scope.

## 10. Roadmap

**V1**: Life domains → Goals → Priority engine → Balance engine → Gmail/Calendar/Drive intelligence (read-only) → 4 AM daily review → Daily executive brief → Weekly review → Streamlit dashboard → GitHub repo → Audit/security layer. Category A only.

**V2**: Career/Learning/French/Financial/Relationship engines, full global intelligence, career opportunity engine, meeting intelligence, advanced pattern detection. Category B turns on only after trust graduation.

**V3**: Adaptive priority learning, opportunity management, strategic-stopping analysis, Category C automation with an explicit per-action approval UI in Streamlit (still never silent), executive communication drafting.
