-- PEOS data model (SQLite). Interim storage until Supabase/Neon Postgres is
-- wired up (see docs/decision_log.md) - same logical model as
-- data/schemas/schema.sql, adapted for SQLite (no native ENUM, no SERIAL).

PRAGMA foreign_keys = ON;

CREATE TABLE domains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    strategic_weight REAL,
    minimum_attention_pct REAL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE objectives (
    id TEXT PRIMARY KEY,
    domain_id TEXT NOT NULL REFERENCES domains(id),
    name TEXT NOT NULL,
    description TEXT,
    importance REAL,
    target_date TEXT,
    status TEXT NOT NULL DEFAULT 'not_started',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    objective_id TEXT REFERENCES objectives(id),
    domain_id TEXT NOT NULL REFERENCES domains(id),
    name TEXT NOT NULL,
    description TEXT,
    why_it_matters TEXT,
    strategic_importance REAL,
    baseline TEXT,
    target TEXT,
    progress REAL NOT NULL DEFAULT 0,
    confidence TEXT NOT NULL DEFAULT 'LOW' CHECK (confidence IN ('HIGH','MEDIUM','LOW')),
    deadline TEXT,
    status TEXT NOT NULL DEFAULT 'not_started',
    next_action TEXT,
    review_frequency TEXT,
    last_reviewed TEXT,
    owner TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE goal_dependencies (
    goal_id TEXT NOT NULL REFERENCES goals(id),
    depends_on_goal_id TEXT NOT NULL REFERENCES goals(id),
    PRIMARY KEY (goal_id, depends_on_goal_id)
);

-- One row per (habit_key, date). "Did I do X today" trackers - French AI
-- tutor session, etc. Not tied to a goal/domain since these are pure daily
-- habits, simpler than the goal/task model.
CREATE TABLE daily_habits (
    id TEXT PRIMARY KEY,
    habit_key TEXT NOT NULL,
    habit_label TEXT NOT NULL,
    date TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (habit_key, date)
);

-- Platform UX/usability feedback, separate from life-domain goal logs.
CREATE TABLE platform_feedback (
    id TEXT PRIMARY KEY,
    note TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','reviewed','actioned')),
    response TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at TEXT
);

CREATE TABLE goal_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id TEXT NOT NULL REFERENCES goals(id),
    note TEXT NOT NULL,
    status_at_time TEXT,
    progress_at_time REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE goal_risks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id TEXT NOT NULL REFERENCES goals(id),
    description TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(id),
    domain_id TEXT NOT NULL REFERENCES domains(id),
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started',
    deadline TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- project_id/goal_id are both nullable: a task can hang directly off a goal
-- (the common case right now, since most goals have no project yet) or off
-- a project once that layer is actually populated.
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    goal_id TEXT REFERENCES goals(id),
    domain_id TEXT NOT NULL REFERENCES domains(id),
    title TEXT NOT NULL,
    notes TEXT,
    priority REAL,
    deadline TEXT,
    status TEXT NOT NULL DEFAULT 'not_started' CHECK (status IN ('not_started','in_progress','done')),
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE commitments (
    id TEXT PRIMARY KEY,
    domain_id TEXT REFERENCES domains(id),
    source TEXT NOT NULL,
    description TEXT NOT NULL,
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE calendar_events (
    id TEXT PRIMARY KEY,
    external_id TEXT UNIQUE,
    domain_id TEXT REFERENCES domains(id),
    title TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    category TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE emails (
    id TEXT PRIMARY KEY,
    external_id TEXT UNIQUE,
    domain_id TEXT REFERENCES domains(id),
    sender TEXT NOT NULL,
    subject TEXT,
    category TEXT,
    importance TEXT,
    action_required INTEGER NOT NULL DEFAULT 0,
    deadline TEXT,
    confidence TEXT NOT NULL DEFAULT 'MEDIUM' CHECK (confidence IN ('HIGH','MEDIUM','LOW')),
    processed INTEGER NOT NULL DEFAULT 0,
    received_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    external_id TEXT UNIQUE,
    domain_id TEXT REFERENCES domains(id),
    name TEXT NOT NULL,
    location TEXT,
    category TEXT,
    status TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE learning_items (
    id TEXT PRIMARY KEY,
    domain_id TEXT NOT NULL REFERENCES domains(id),
    capability TEXT NOT NULL,
    course TEXT,
    item_type TEXT NOT NULL DEFAULT 'course' CHECK (item_type IN ('course','book')),
    priority_rank INTEGER,
    priority_label TEXT,
    status TEXT NOT NULL DEFAULT 'not_started' CHECK (status IN ('not_started','in_progress','done')),
    progress REAL NOT NULL DEFAULT 0,
    notes TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE learning_item_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    learning_item_id TEXT NOT NULL REFERENCES learning_items(id),
    note TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE reviews (
    id TEXT PRIMARY KEY,
    review_type TEXT NOT NULL,
    review_date TEXT NOT NULL,
    summary TEXT,
    recommendations TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE intelligence_items (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    category TEXT NOT NULL DEFAULT 'other' CHECK (category IN ('politics','opportunity','other')),
    topic TEXT,
    relevance REAL,
    actionability REAL,
    confidence TEXT NOT NULL DEFAULT 'MEDIUM' CHECK (confidence IN ('HIGH','MEDIUM','LOW')),
    feedback TEXT,
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','reviewed','actioned')),
    action_taken TEXT,
    item_date TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- What the owner did with a system-generated communication (weekly review
-- email, daily brief, etc.) - answers "have I read this, what did I do".
CREATE TABLE claude_outputs (
    id TEXT PRIMARY KEY,
    output_type TEXT NOT NULL,
    subject TEXT,
    summary TEXT,
    reviewed INTEGER NOT NULL DEFAULT 0,
    action_taken TEXT,
    sent_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE actions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    action_type TEXT NOT NULL,
    description TEXT NOT NULL,
    automation_category TEXT NOT NULL CHECK (automation_category IN ('A','B','C')),
    status TEXT NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed','pending_batch_approval','pending_approval','approved','rejected','executed','failed')),
    approval_required INTEGER NOT NULL DEFAULT 1,
    confidence TEXT NOT NULL DEFAULT 'MEDIUM' CHECK (confidence IN ('HIGH','MEDIUM','LOW')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    executed_at TEXT
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id TEXT REFERENCES actions(id),
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    system TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT,
    confidence TEXT CHECK (confidence IN ('HIGH','MEDIUM','LOW')),
    approval_required INTEGER,
    approval_given INTEGER,
    result TEXT,
    reversal_method TEXT
);

CREATE INDEX idx_goal_logs_goal ON goal_logs(goal_id);
CREATE INDEX idx_goal_logs_created ON goal_logs(created_at);
CREATE INDEX idx_goals_domain ON goals(domain_id);
CREATE INDEX idx_tasks_goal ON tasks(goal_id);
CREATE INDEX idx_projects_domain ON projects(domain_id);
CREATE INDEX idx_tasks_domain ON tasks(domain_id);
CREATE INDEX idx_calendar_events_domain ON calendar_events(domain_id);
CREATE INDEX idx_calendar_events_start ON calendar_events(start_time);
CREATE INDEX idx_emails_domain ON emails(domain_id);
CREATE INDEX idx_actions_status ON actions(status);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
