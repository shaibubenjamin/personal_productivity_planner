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

## 2026-09-07 — Security incident note

A GitHub personal access token was pasted into the chat that produced this repository's scaffold. It was treated as compromised on sight, never used or written to any file, and the owner was told to revoke it immediately. `gh auth login` (device flow) is the adopted pattern for local GitHub authentication going forward, specifically to avoid ever pasting a token into a conversation again.
