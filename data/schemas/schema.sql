-- PEOS data model (Postgres). Matches docs/architecture.md section 3.
-- IDs are human-readable TEXT (e.g. 'career', 'goal-001') to stay consistent
-- with config/*.yaml, which uses the same ids. Not yet applied to a live
-- database — run this once Supabase/Neon project + DATABASE_URL exist.

CREATE TYPE confidence_level AS ENUM ('HIGH', 'MEDIUM', 'LOW');
CREATE TYPE automation_category AS ENUM ('A', 'B', 'C');
CREATE TYPE action_status AS ENUM ('proposed', 'pending_batch_approval', 'pending_approval', 'approved', 'rejected', 'executed', 'failed');

-- Single row (id = 'singleton'). Login credentials, created through the
-- app's own "create your password" first-run form rather than requiring
-- Streamlit secrets/env vars to be pre-configured - since the local and
-- deployed app already share this same database, setting the password
-- once works everywhere immediately.
CREATE TABLE app_auth (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE domains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    strategic_weight NUMERIC,
    minimum_attention_pct NUMERIC,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE objectives (
    id TEXT PRIMARY KEY,
    domain_id TEXT NOT NULL REFERENCES domains(id),
    name TEXT NOT NULL,
    description TEXT,
    importance NUMERIC,
    target_date DATE,
    status TEXT NOT NULL DEFAULT 'not_started',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    objective_id TEXT REFERENCES objectives(id),
    domain_id TEXT NOT NULL REFERENCES domains(id),
    name TEXT NOT NULL,
    description TEXT,
    why_it_matters TEXT,
    strategic_importance NUMERIC,
    baseline TEXT,
    target TEXT,
    progress NUMERIC NOT NULL DEFAULT 0,
    confidence confidence_level NOT NULL DEFAULT 'LOW',
    deadline DATE,
    status TEXT NOT NULL DEFAULT 'not_started',
    next_action TEXT,
    review_frequency TEXT,
    last_reviewed DATE,
    owner TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
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
    date DATE NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (habit_key, date)
);

-- Platform UX/usability feedback, separate from life-domain goal logs.
CREATE TABLE platform_feedback (
    id TEXT PRIMARY KEY,
    note TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','reviewed','actioned')),
    response TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_at TIMESTAMPTZ
);

CREATE TABLE goal_logs (
    id SERIAL PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(id),
    note TEXT NOT NULL,
    status_at_time TEXT,
    progress_at_time NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE goal_risks (
    id SERIAL PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(id),
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(id),
    domain_id TEXT NOT NULL REFERENCES domains(id),
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started',
    deadline DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
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
    priority NUMERIC,
    deadline DATE,
    status TEXT NOT NULL DEFAULT 'not_started' CHECK (status IN ('not_started','in_progress','done')),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Quick capture inbox: "write it down now, triage later" (GTD-style). A
-- capture starts with a best-guess domain/goal (keyword heuristic, see
-- engine/capture/triage.py) but is not committed anywhere real until the
-- owner confirms it - the suggestion is never silently treated as fact.
-- Defined after tasks/projects: Postgres validates FK target tables at
-- CREATE TABLE time (unlike SQLite, which only checks at DML time), so
-- resulting_task_id -> tasks(id) requires tasks to already exist here.
CREATE TABLE captures (
    id TEXT PRIMARY KEY,
    raw_text TEXT NOT NULL,
    suggested_domain_id TEXT REFERENCES domains(id),
    suggested_goal_id TEXT REFERENCES goals(id),
    domain_id TEXT REFERENCES domains(id),
    goal_id TEXT REFERENCES goals(id),
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'triaged', 'discarded')),
    resulting_task_id TEXT REFERENCES tasks(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    triaged_at TIMESTAMPTZ
);

-- Spec Section 35: why a goal was prioritised/deferred/stopped - the
-- owner's own strategic reasoning, not this repo's engineering decisions
-- (those stay in docs/decision_log.md).
CREATE TABLE decision_log (
    id TEXT PRIMARY KEY,
    decision_type TEXT NOT NULL CHECK (
        decision_type IN ('prioritised', 'deferred', 'stopped', 'started', 'changed', 'other')
    ),
    goal_id TEXT REFERENCES goals(id),
    description TEXT NOT NULL,
    rationale TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE commitments (
    id TEXT PRIMARY KEY,
    domain_id TEXT REFERENCES domains(id),
    source TEXT NOT NULL,          -- e.g. 'email', 'meeting', 'self'
    description TEXT NOT NULL,
    due_date DATE,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE calendar_events (
    id TEXT PRIMARY KEY,
    external_id TEXT UNIQUE,       -- Google Calendar event id
    domain_id TEXT REFERENCES domains(id),
    title TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    category TEXT,                 -- meeting, deep_work, learning, exercise, relationship, admin, ...
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE emails (
    id TEXT PRIMARY KEY,
    external_id TEXT UNIQUE,       -- Gmail message id
    domain_id TEXT REFERENCES domains(id),
    sender TEXT NOT NULL,
    subject TEXT,
    category TEXT,                 -- one of the 16 spec categories
    importance TEXT,
    action_required BOOLEAN NOT NULL DEFAULT FALSE,
    deadline DATE,
    confidence confidence_level NOT NULL DEFAULT 'MEDIUM',
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    received_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    external_id TEXT UNIQUE,       -- Drive file id
    domain_id TEXT REFERENCES domains(id),
    name TEXT NOT NULL,
    location TEXT,
    category TEXT,
    status TEXT,                   -- active, duplicate_candidate, obsolete_candidate, ...
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
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
    progress NUMERIC NOT NULL DEFAULT 0,
    notes TEXT,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE learning_item_logs (
    id SERIAL PRIMARY KEY,
    learning_item_id TEXT NOT NULL REFERENCES learning_items(id),
    note TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE reviews (
    id TEXT PRIMARY KEY,
    review_type TEXT NOT NULL,     -- daily, weekly, monthly, quarterly
    review_date DATE NOT NULL,
    summary TEXT,
    recommendations TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE intelligence_items (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    category TEXT NOT NULL DEFAULT 'other' CHECK (category IN ('politics','opportunity','other')),
    topic TEXT,
    relevance NUMERIC,
    actionability NUMERIC,
    confidence confidence_level NOT NULL DEFAULT 'MEDIUM',
    feedback TEXT,                 -- accepted/rejected, used to tune relevance_threshold
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','reviewed','actioned')),
    action_taken TEXT,
    item_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- What the owner did with a system-generated communication (weekly review
-- email, daily brief, etc.) - answers "have I read this, what did I do".
CREATE TABLE claude_outputs (
    id TEXT PRIMARY KEY,
    output_type TEXT NOT NULL,
    subject TEXT,
    summary TEXT,
    reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    action_taken TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Mutable queue: proposed -> (batch/individual) approval -> executed/rejected.
CREATE TABLE actions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    action_type TEXT NOT NULL,
    description TEXT NOT NULL,
    automation_category automation_category NOT NULL,
    status action_status NOT NULL DEFAULT 'proposed',
    approval_required BOOLEAN NOT NULL DEFAULT TRUE,
    confidence confidence_level NOT NULL DEFAULT 'MEDIUM',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    executed_at TIMESTAMPTZ
);

-- Immutable history. Never updated or deleted; a correction is a new row.
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    action_id TEXT REFERENCES actions(id),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    system TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT,
    confidence confidence_level,
    approval_required BOOLEAN,
    approval_given BOOLEAN,
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
