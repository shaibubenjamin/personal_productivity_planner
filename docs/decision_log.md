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

## 2026-09-07 — Security incident note

A GitHub personal access token was pasted into the chat that produced this repository's scaffold. It was treated as compromised on sight, never used or written to any file, and the owner was told to revoke it immediately. `gh auth login` (device flow) is the adopted pattern for local GitHub authentication going forward, specifically to avoid ever pasting a token into a conversation again.
