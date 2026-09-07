# Security

## Rules

- No credentials of any kind (PATs, OAuth secrets, DB connection strings, API keys) ever committed to this repo. `.gitignore` blocks `.env`, `*.token`, `credentials.json`, `.streamlit/secrets.toml`.
- No credentials pasted into a Claude conversation, ever — a chat transcript is not a secret store. If one is exposed, revoke/rotate it immediately regardless of whether it was used.
- GitHub auth: `gh auth login` (device flow) locally, not a hand-typed token.
- Google Workspace access: claude.ai connector OAuth, scoped to the minimum needed (start read-only: `gmail.readonly`, `calendar.readonly`, `drive.readonly`; escalate scope only when the corresponding automation category is actually being built and approved).
- Hosted secrets (`DATABASE_URL`, any Streamlit Cloud secret) are set via each platform's own secrets UI, never passed through chat.

## Automation approval model

- **Category A** (read/analyze/classify/recommend): runs unattended, logged to `audit_log`.
- **Category B** (archive, label, low-risk calendar blocks): proposed only, batched for morning approval — never executes silently, even after the trust-graduation window.
- **Category C** (delete, send, cancel, move important meetings, financial/relationship-sensitive, irreversible): per-action human approval, always.

## Audit trail

Every automated action writes to `audit_log`: what happened, why, source, confidence, timestamp, action taken, whether approval was required/given, result, reversal procedure. If an integration fails, the failure is recorded (not silently treated as success) and surfaced when it materially affects the day's plan.
