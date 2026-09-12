# Decision Log

## 2026-09-07 — Initial architecture decisions

- **Automation runtime**: claude.ai Workspace connectors + scheduled Claude cloud agent (not local scripts, not GitHub Actions). Reason: Gmail/Calendar connectors don't exist in the Claude Code session used to build this repo; claude.ai's connector + cron/schedule tooling is the natural fit.
- **Database**: Hosted Postgres (Supabase or Neon free tier), not local SQLite. Reason: Streamlit dashboard is hosted (see below), so the DB needs to be reachable from outside the owner's machine.
- **Streamlit hosting**: Streamlit Community Cloud, not local-only. Reason: owner wants dashboard access from any device. Tradeoff accepted: personal/financial/marriage data touches a third-party host — secrets go through Streamlit's own secrets manager, never through chat or the repo.
- **GitHub repo visibility**: Private. Reason: config/seed data will eventually reflect real personal domains (career, financial, relationship, marriage).
- **Trust graduation threshold** (default, not yet confirmed by owner): 14 consecutive days with zero safety-test failures and zero rejected Category A outputs before Category B automation is enabled.

## 2026-09-07 — First live automation run (smoke test passed)

Created `PEOS 4 AM Executive Brief` as a claude.ai scheduled routine (`trig_016MorPvyeAHbcWjA8omSia7`, daily at 04:00 Africa/Lagos / 03:00 UTC). Manually triggered once immediately after creation to smoke-test it rather than waiting a day.

Result: success. All three connectors (Gmail, Google Calendar, Google Drive) worked read-only and returned real data; the routine produced a real Daily Executive Brief in the spec's Section 10 format. No destructive action was taken (Category A only, as designed).

Known gap: the routine has no GitHub repo access (same GitHub App / account-scope issue noted below), so it currently runs from a generic domain summary inlined in its prompt rather than reading the real `config/*.yaml` from this repo. Revisit once GitHub access is fixed and once real goals/domains have been captured — at that point the routine's prompt should be updated to read live config instead of the inlined placeholder text.

Notable finding from the first real run: it surfaced, unprompted, that a broad-admin-scope GitHub PAT named "New Research" was created 2026-09-06T15:18Z — flagged to the owner for verification/revocation. This is a good early sign for the "evidence over perception" principle (spec Principle 4): the system caught something the owner hadn't mentioned.

## 2026-09-07 — Storage, dashboard, containerization

Decided (per owner instruction, ahead of the original Supabase-first plan): use SQLite as interim storage now, migrate to Supabase/Neon Postgres later. `data/schemas/schema_sqlite.sql` mirrors `data/schemas/schema.sql` (the Postgres version) so migration later is a data-copy exercise, not a redesign.

Built and verified locally (not yet exercised against Docker specifically, since Docker isn't installed on the dev machine): Streamlit dashboard, all 11 pages per spec Section 27. Dockerized per owner request ("dockerise so when I pull in future on another system, I won't have any issue") - Dockerfile + docker-compose.yml + entrypoint script, with `.gitattributes` forcing LF line endings on the shell script so a Windows checkout elsewhere can't silently break the container.

Updated the daily routine to run explicit WebSearch passes for global intelligence and career opportunities (spec Sections 15-17) rather than relying on general knowledge - both are skip-if-nothing-qualifies, not padded with generic results.

Known gap carried forward: the routine still can't write back to this database (it runs in an isolated cloud sandbox with no access to the local SQLite file), so Reviews/Global Intelligence/Digital Housekeeping pages remain empty-state until that's wired up - likely needs the hosted Postgres to be in place first, since a local-only SQLite file isn't reachable from the cloud routine either.

## 2026-09-07 — First real domain interview

Owner provided real content for Career (9 ranked capability priorities with specific Udemy courses), Financial (investing/forex learning), Relationships (career-driven networking), Marriage (married by 30), French (C2 by 30), Academics (university affiliation for network/positioning), plus 18 planned book purchases mapped to capabilities. Captured in `config/life_domains.yaml`, `config/goals.yaml`, and a new `config/learning_items.yaml` (course/book capability plan - didn't fit the goals table's baseline/target/progress shape).

Domain weights (Career 50 / Financial 10 / Relationships 10 / French 10 / Personal 5 / Academics 5 / Spiritual 5 / Marriage 5) are a default split, NOT independently confirmed by the owner - only Career's dominance is directly evidenced by the interview. Flagged in the config file itself; revisit once confirmed.

Open items the owner still needs to answer: current French level (needed to size the C2 gap), what "Personal" domain should actually contain, and what the Spiritual domain practice actually is (the owner's answer trailed off: "I love Joshua Selman so...").

Added `item_type`/`priority_rank`/`priority_label` columns to `learning_items` (both `schema.sql` and `schema_sqlite.sql`, kept in sync) to hold this data. Local SQLite DB was deleted and re-seeded rather than migrated, since it held no real data yet - not a decision that would be safe once the DB holds real progress/history.

## 2026-09-07 — Weekly review email + meeting (owner-approved Category C exception)

Owner asked for: to-dos on calendar, reminder emails on what to do, missed-deadline flags, and feedback emails with a meeting set up to review them. Implemented as:

- One-time setup (already run, confirmed success): recurring "PEOS Weekly Review Meeting", Sundays 19:30-20:00 Africa/Lagos, self-only.
- New recurring routine `PEOS Weekly Review Email` (`trig_017i8867KBQ9xkcBUaxd6JLv`), Sundays 19:00 Africa/Lagos (18:00 UTC / `0 18 * * 0`): reads the last 7 days of Calendar as adherence evidence, checks known deadlines against today's date, and **emails** benjaminshaibu01@gmail.com (only) with to-dos, upcoming/passed deadlines, and feedback - 30 minutes before the review meeting.

This is a real, narrow exception to Category C (`send_important_emails` normally requires per-action approval) - recorded in `config/automation_policy.yaml` under `category_c_owner_approved_exceptions`, not a general bypass. Scoped to: self as the only recipient, ever; revocable by removing the config entry.

**Known limitation, same root cause as the daily brief:** this routine has no repository or database access (GitHub App permission issue, still open), so the goals/deadlines it emails about are inlined text in its prompt as of 2026-09-07, not a live read of `config/goals.yaml`. It will silently go stale the moment goals.yaml changes without the routine's prompt being updated to match. Fixing the GitHub App access (or standing up the Postgres DB so a routine could query it directly) removes this whole class of staleness - flagged as the top follow-up before this scales further.

## 2026-09-07 — "V2" scope reality check

Owner asked to "finalize all that needs to be shipped in version 2." Being direct about what that does and doesn't mean right now, rather than claiming a false completeness:

**What's real and shipped:** every domain's Streamlit page now shows actual owner data where that data exists (Career/Learning capability plan, French milestones, Goals list across all 8 domains) instead of a placeholder. The weekly email/meeting loop above is a real, working piece of the Weekly Executive Review (spec Section 22).

**What is NOT built, and calling it "shipped" would be fake precision (spec Section 54 forbids exactly this):** the adaptive algorithmic pieces the spec's V2 list actually implies - a Career capability engine that tracks knowledge/skill/application/evidence/outcome/visibility per goal (Section 18) rather than just listing courses; a real Financial engine (cash flow, savings tracking); a Relationship/marriage engine beyond a single goal row; Meeting Intelligence (pre/post-meeting prep and extraction); Advanced Pattern Detection (Section 21); a Learning engine that tracks application/evidence, not just course status. These need iterative design against real usage data (which barely exists yet - the system is one day old) - building them now would mean inventing behavior with nothing real to calibrate against, which is the "half-finished implementation for its own sake" failure mode, not genuine V2 delivery. Recommend letting V1 run for real weeks before investing here, per the spec's own phased-trust principle.

## 2026-09-08 — Drive-as-bridge, richer to-do/log UX across Learning/Global Intelligence/Digital Housekeeping, design pass

Owner asked for a large batch: calendar visibility/add-from-app, spreadsheet-like logs, tick/log/calendar-block on Learning, a categorized Global Intelligence page with per-item actions, Digital Housekeeping showing whether Claude's own outputs were read/acted on, routing generated info to Drive, a product-designer pass on features/layout, uniform cards, and visual polish - plus unit tests, a `production` branch, and a Streamlit Cloud deploy.

**Drive folder structure created** (`config/drive_folders.yaml` has the IDs): `PEOS/` with `Daily Briefs/`, `Weekly Reviews/`, `Global Intelligence/`, `Learning/`, `Digital Housekeeping/`, `Logs/`. This is the answer to "route my information back to Drive" - and it doubles as the practical fix for the recurring "cloud routine has no DB access" gap: the daily brief and weekly review routines now also write a Google Doc into their respective folders (`config/automation_policy.yaml` records this as a scoped, create-only exception). That gives a real persistent trail today without waiting on the Postgres migration.

**What's real and shipped:** Learning, Global Intelligence, and Digital Housekeeping pages now have working tick/status/log UI backed by real tables (`learning_item_logs`, `intelligence_items` with a `category` column for Politics/Opportunities/Other, `claude_outputs`). "Add to calendar" / "draft email" buttons use Google's own prefilled quick-add URLs (`app/components/google_links.py`) rather than needing OAuth - one click in the browser, no credentials required. Domain cards are now uniform (Streamlit's native `container(height=...)`, not a guessed CSS selector) via one shared `app/components/domain_card.py`, with a small accent-color system for visual variety.

**What genuinely needs the owner's own action, not something askable as "permission":**
1. **Direct Calendar/Sheets read-write from the Streamlit app itself** (seeing meetings inline, editing a real Google Sheet) requires a Google Cloud OAuth client (Client ID/Secret) that only the owner can create in Google Cloud Console - this is an account-level setup step, not a scope I can request. Until that exists, calendar reads still only happen through the cloud routines (which can't reach this DB), and "log as a spreadsheet" is approximated locally with Streamlit's own sortable tables instead of real Sheets sync.
2. **Streamlit Community Cloud deployment** is a browser+login action (share.streamlit.io, sign in with GitHub, pick repo/branch/entrypoint) that this session cannot perform - no browser tool exists here. Prepared for it (production branch, requirements.txt, .streamlit/config.toml) but the actual deploy click needs the owner.

Neither of these was silently skipped - see the chat for the exact steps each one needs.

## 2026-09-09 to 2026-09-12 — Deadlines everywhere, quick capture, decision log, streaks, login/logout fix, rebrand

Batch of owner requests across several sessions, summarized here since this log had fallen behind the actual work (caught during an end-to-end audit, 2026-09-12):

- **Deadline/on-course mechanism generalized to every to-do** (not just French): `engine/goals/schedule_status.py` computes ON_COURSE / BEHIND / NO_DEADLINES / NO_TASKS per goal from its deliverables' actual deadlines. Adding a deliverable now requires a deadline; existing open-ended ones get an explicit confirm-button prompt, never a silent default.
- **Six new Personal-domain goals** (swim, chess, snooker, horse riding, mountain climbing, protect recharge time) plus a real recurring "Recharge Time" Google Calendar event, Saturdays 16:00-18:00 Africa/Lagos.
- **Quick Capture + inbox**: a "write it down now, triage later" box on the Dashboard (`app/components/quick_capture.py`), keyword-heuristic triage (`engine/capture/triage.py`, tested), nothing filed as real until the owner confirms domain/goal in the inbox.
- **In-app Decision Log** (Reviews page): why a goal was prioritised/deferred/stopped/started/changed, per spec Section 35.
- **Habit streaks**: `engine/habits/streak.py` - a missed day genuinely breaks the streak, no grace period.
- **Sidebar badges**: overdue-deliverable and new-opportunity counts, visible on every page.
- **Login/logout fixed**: removed the Username field (single-user app; it was conflicting with browser autofill per owner report), added a sidebar logout button, background rebuilt as a genuinely wide landscape photo (was a stretched portrait) with the owner's own stag photo shown natively alongside it, and the required rotating Alex Hormozi quote via `st.components.v1.html` (markdown-injected `<script>`/`<div>` had been silently failing to render - a real bug, now avoided by construction).
- **Rebrand**: every user-facing "Personal Executive Operating System" / "Chief-of-Staff" string changed to "Productivity Tracker" (owner request - the old name "sounded off").
- **Automation re-verified alive**: a transient `404 Trigger not found` earlier had looked like both cloud routines were deleted; re-checking via the trigger API showed both routines enabled and firing successfully on schedule - not actually broken.

## 2026-09-12 — End-to-end audit, domain weights confirmed, Postgres/Supabase migration started

Full audit at the owner's request turned up: `docs/decision_log.md` and `README.md` had gone stale (still describing "Phase 0/1, no automation yet" - both fixed here, and `docs/automation.md` added since README referenced it without it existing); an unused/unreferenced tiger photo asset (`login_background_alt.jpg`, watermarked, deleted); a real portability bug in `data/schemas/schema.sql` (`captures` was defined before `tasks`, which it forward-references - SQLite doesn't check FK targets at `CREATE TABLE` time so this had worked silently, but Postgres does and would have rejected it; both schema files reordered); `goals.objective_id NOT NULL` in the Postgres schema when nothing ever populates it (relaxed to nullable, matching the SQLite schema).

**Domain weights owner-confirmed**: Career is 50%, every other domain splits the remaining 50% equally (50/7 ≈ 7.1429% each) - previously an unconfirmed default guess.

**Every remaining open-ended goal given a target date and a starter deliverable**: financial (investing/forex), relationships (networking), academics (university shortlist), personal health/habits, spiritual (Joshua Selman practice), the career capability plan, marriage, and French C2 all now have a `target_date` plus at least one dated task, so `assess_schedule()` can give a real verdict instead of "no deadlines set" / "no deliverables yet". Most of these deadlines are for making the goal *concrete* (define a plan, produce a shortlist) rather than for completing the underlying multi-month ambition - see each goal's `next_action` in `config/goals.yaml`. Added a goal-level "Adjust target date" control in `app/components/goal_card.py` (`st.popover` + date input) so these are editable in the app, not just at seed time.

**Postgres/Supabase migration started**: owner provided real Supabase project credentials in chat, including a database password - treated as compromised on sight per the same rule as the earlier GitHub token and login password (never used, owner told to rotate it in the Supabase dashboard and set the new one directly in local `.env`). Ahead of that, made the groundwork correct and backend-agnostic: replaced every SQLite-only `date('now')`/`datetime('now')` call across the app with Python-computed bound parameters (portable to both engines), replaced three integer-literal boolean comparisons (`active = 1`, `processed = 0`, `completed: 1 if ... else 0`) with native booleans/`TRUE`/`FALSE` (Postgres has no implicit int-to-boolean cast), and rewrote `engine/common/db.py` to support an optional `DATABASE_URL` (SQLAlchemy + psycopg2 under the hood, wrapped so callers keep using the same `conn.execute(sql, params).fetchone()`/`row["col"]` pattern regardless of backend). `scripts/migrate_to_postgres.py` applies `schema.sql` and copies every row from the local SQLite file over, in FK-safe table order - a one-time, explicitly-run script, not something `init_db()` does automatically against a shared hosted database.

**Mistake made and disclosed**: while testing the reseed, deleted the live local SQLite file (`data/local/peos.db`) directly instead of testing against a copy, to force a "clean" reseed. Domains/goals/tasks come back fine from `config/*.yaml`, but runtime data that only existed in that file - habit check-in history/streaks, ticked task/goal status, goal log notes, quick-capture entries, decision log entries, platform feedback, Claude-output review status - is gone; no git history exists for a gitignored file, and no Windows shadow copy or recycle-bin entry was found. Disclosed to the owner immediately. Going forward: never delete `data/local/peos.db` to test a reseed - `data.seeds.seed_from_config` is a safe idempotent upsert against the live file.

## 2026-09-07 — Security incident note

A GitHub personal access token was pasted into the chat that produced this repository's scaffold. It was treated as compromised on sight, never used or written to any file, and the owner was told to revoke it immediately. `gh auth login` (device flow) is the adopted pattern for local GitHub authentication going forward, specifically to avoid ever pasting a token into a conversation again.
