# Decision Log

## 2026-09-07 — Initial architecture decisions

- **Automation runtime**: claude.ai Workspace connectors + scheduled Claude cloud agent (not local scripts, not GitHub Actions). Reason: Gmail/Calendar connectors don't exist in the Claude Code session used to build this repo; claude.ai's connector + cron/schedule tooling is the natural fit.
- **Database**: Hosted Postgres (Supabase or Neon free tier), not local SQLite. Reason: Streamlit dashboard is hosted (see below), so the DB needs to be reachable from outside the owner's machine.
- **Streamlit hosting**: Streamlit Community Cloud, not local-only. Reason: owner wants dashboard access from any device. Tradeoff accepted: personal/financial/marriage data touches a third-party host — secrets go through Streamlit's own secrets manager, never through chat or the repo.
- **GitHub repo visibility**: Private. Reason: config/seed data will eventually reflect real personal domains (career, financial, relationship, marriage).
- **Trust graduation threshold** (default, not yet confirmed by owner): 14 consecutive days with zero safety-test failures and zero rejected Category A outputs before Category B automation is enabled.

## 2026-09-07 — Security incident note

A GitHub personal access token was pasted into the chat that produced this repository's scaffold. It was treated as compromised on sight, never used or written to any file, and the owner was told to revoke it immediately. `gh auth login` (device flow) is the adopted pattern for local GitHub authentication going forward, specifically to avoid ever pasting a token into a conversation again.
