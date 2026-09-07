-- PEOS data model (Postgres). Matches docs/architecture.md section 3.
-- IDs are human-readable TEXT (e.g. 'career', 'goal-001') to stay consistent
-- with config/*.yaml, which uses the same ids. Not yet applied to a live
-- database — run this once Supabase/Neon project + DATABASE_URL exist.

CREATE TYPE confidence_level AS ENUM ('HIGH', 'MEDIUM', 'LOW');
CREATE TYPE automation_category AS ENUM ('A', 'B', 'C');
CREATE TYPE action_status AS ENUM ('proposed', 'pending_batch_approval', 'pending_approval', 'approved', 'rejected', 'executed', 'failed');

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
    objective_id TEXT NOT NULL REFERENCES objectives(id),
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

CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    domain_id TEXT NOT NULL REFERENCES domains(id),
    title TEXT NOT NULL,
    priority NUMERIC,
    deadline DATE,
    status TEXT NOT NULL DEFAULT 'not_started',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
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
    status TEXT NOT NULL DEFAULT 'not_started',
    progress NUMERIC NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
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
    topic TEXT,
    relevance NUMERIC,
    actionability NUMERIC,
    confidence confidence_level NOT NULL DEFAULT 'MEDIUM',
    feedback TEXT,                 -- accepted/rejected, used to tune relevance_threshold
    item_date DATE,
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

CREATE INDEX idx_goals_domain ON goals(domain_id);
CREATE INDEX idx_projects_domain ON projects(domain_id);
CREATE INDEX idx_tasks_domain ON tasks(domain_id);
CREATE INDEX idx_calendar_events_domain ON calendar_events(domain_id);
CREATE INDEX idx_calendar_events_start ON calendar_events(start_time);
CREATE INDEX idx_emails_domain ON emails(domain_id);
CREATE INDEX idx_actions_status ON actions(status);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
