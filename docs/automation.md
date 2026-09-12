# Automation

Two scheduled claude.ai routines (Category A / read-mostly, per `config/automation_policy.yaml`) run against the owner's Gmail/Calendar/Drive Workspace connectors - not from this repo's own code, since a local Claude Code session has no connector access.

## PEOS 4 AM Executive Brief

Daily at 04:00 Africa/Lagos (03:00 UTC). Reads yesterday/today's Calendar, recent Gmail, recent Drive activity, runs a few targeted web searches for global intelligence and career opportunities matching the owner's career direction, and produces a brief (strategic focus, risks, neglected areas, opportunities, recommended schedule). Writes a Google Doc into `PEOS/Daily Briefs/` in Drive - its only write action.

## PEOS Weekly Review Email

Weekly, Sundays 19:00 Africa/Lagos (18:00 UTC), 30 minutes before a matching "PEOS Weekly Review Meeting" calendar event. Reads the last 7 days of Calendar as adherence evidence, checks known deadlines against today's date, and emails the owner (only) a review: to-dos, upcoming/passed deadlines, feedback. Also writes a copy into `PEOS/Weekly Reviews/` in Drive.

## Known limitation: no repository or database access

Neither routine can read `config/goals.yaml` or the local database directly (GitHub App repo access for the connector was never resolved, and the local SQLite file isn't reachable from a cloud sandbox regardless). Their goal/deadline context is therefore **inlined as text in each routine's prompt**, frozen at the date the routine was last created/updated - it goes stale the moment `config/goals.yaml` changes without the routine's prompt being manually updated to match.

Migrating to hosted Postgres (see `decision_log.md`) removes this limitation entirely, since a routine could then query live goal/deadline data directly instead of relying on inlined text.

## Drive folder structure

`PEOS/` at the root of the owner's My Drive, with subfolders: `Daily Briefs/`, `Weekly Reviews/`, `Global Intelligence/`, `Learning/`, `Digital Housekeeping/`, `Logs/`. IDs are in `config/drive_folders.yaml`. This is the practical bridge for "cloud routine can't reach the app's database" - it gives a real persistent trail today, ahead of the Postgres migration.
