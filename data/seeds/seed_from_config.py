"""Load config/life_domains.yaml and config/goals.yaml into the SQLite DB.

Idempotent: re-running upserts domains/goals rather than duplicating them.
Run with: python -m data.seeds.seed_from_config
"""

import re
from datetime import date, timedelta

from engine.common.config import load_yaml
from engine.common.db import get_connection, init_db


def _slug(text: str, max_len: int = 40) -> str:
    """Stable, content-derived slug - NOT based on list position. Task and
    learning-item IDs used to be `{prefix}-{global_list_index}`, which
    silently shifted (creating orphaned duplicate rows) every time an
    earlier entry was added to the same YAML file - hit repeatedly this
    session (French/Relationships domain merges, several rounds of new
    goals). A slug of the actual content stays the same regardless of
    what else is added elsewhere in the file."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-")


def seed_domains(conn) -> int:
    domains = load_yaml("life_domains.yaml").get("domains", [])
    for d in domains:
        conn.execute(
            """
            INSERT INTO domains (id, name, strategic_weight, minimum_attention_pct, active)
            VALUES (:id, :name, :strategic_weight, :minimum_attention_pct, :active)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                strategic_weight=excluded.strategic_weight,
                minimum_attention_pct=excluded.minimum_attention_pct,
                active=excluded.active
            """,
            {
                "id": d["id"],
                "name": d["name"],
                "strategic_weight": d.get("strategic_weight"),
                "minimum_attention_pct": d.get("minimum_attention_pct"),
                "active": bool(d.get("active", True)),
            },
        )
    conn.commit()
    return len(domains)


def seed_goals(conn) -> int:
    goals = load_yaml("goals.yaml").get("goals") or []
    for g in goals:
        conn.execute(
            """
            INSERT INTO goals (
                id, objective_id, domain_id, name, description, why_it_matters,
                strategic_importance, baseline, target, progress, confidence,
                deadline, status, next_action, review_frequency, last_reviewed, owner
            ) VALUES (
                :id, :objective_id, :domain_id, :name, :description, :why_it_matters,
                :strategic_importance, :baseline, :target, :progress, :confidence,
                :deadline, :status, :next_action, :review_frequency, :last_reviewed, :owner
            )
            ON CONFLICT(id) DO UPDATE SET
                domain_id=excluded.domain_id,
                name=excluded.name, description=excluded.description,
                why_it_matters=excluded.why_it_matters,
                strategic_importance=excluded.strategic_importance,
                baseline=excluded.baseline, target=excluded.target,
                progress=excluded.progress, confidence=excluded.confidence,
                deadline=excluded.deadline, status=excluded.status,
                next_action=excluded.next_action,
                review_frequency=excluded.review_frequency,
                last_reviewed=excluded.last_reviewed, owner=excluded.owner
            """,
            {
                "id": g["id"],
                "objective_id": g.get("objective_id"),
                "domain_id": g["domain_id"],
                "name": g.get("name", ""),
                "description": g.get("description"),
                "why_it_matters": g.get("why_it_matters"),
                "strategic_importance": g.get("strategic_importance"),
                "baseline": g.get("baseline"),
                "target": g.get("target"),
                "progress": g.get("progress", 0),
                "confidence": g.get("confidence", "LOW"),
                "deadline": g.get("target_date"),
                "status": g.get("status", "not_started"),
                "next_action": g.get("next_action"),
                "review_frequency": g.get("review_frequency"),
                "last_reviewed": g.get("last_reviewed"),
                "owner": g.get("owner"),
            },
        )
    conn.commit()
    return len(goals)


def seed_learning_goals(conn, today: date | None = None) -> int:
    """Every course/book becomes a real goal with its own dated task,
    instead of a standalone learning_items row with no timeline (owner
    request 2026-09-14: "books to read are not standalone... every single
    action should align with a goal... goal subdivided into task with
    timeline"). Deadlines are computed here (staggered, not all piled on
    one date) rather than hand-authored in YAML - config/learning_items.yaml
    stays just the source list (capability/course/domain/priority);
    priority_rank drives pacing for courses, list order for books.
    """
    today = today or date.today()
    config = load_yaml("learning_items.yaml")
    courses = config.get("courses") or []
    books = config.get("books") or []
    count = 0

    def _upsert(item_type: str, item: dict, deadline: str) -> None:
        capability = item["capability"]
        course = item.get("course") or ""
        domain_id = item["domain_id"]
        slug = _slug(f"{capability}-{course}", 50)
        goal_id = f"goal-learning-{slug}"
        verb = "Complete" if item_type == "course" else "Finish reading"
        name = f"{verb}: {course.split('/')[0].split('(')[0].strip() or capability}"
        importance = 10 - (item.get("priority_rank") or 5) if item_type == "course" else 5

        conn.execute(
            """
            INSERT INTO goals (
                id, domain_id, name, why_it_matters, strategic_importance,
                deadline, status, progress, confidence, next_action
            ) VALUES (
                :id, :domain_id, :name, :why, :importance,
                :deadline, 'not_started', 0, 'LOW', :next_action
            )
            ON CONFLICT(id) DO UPDATE SET
                domain_id=excluded.domain_id, name=excluded.name,
                why_it_matters=excluded.why_it_matters,
                strategic_importance=excluded.strategic_importance,
                deadline=excluded.deadline, next_action=excluded.next_action
            """,
            {
                "id": goal_id,
                "domain_id": domain_id,
                "name": name,
                "why": f"Capability build: {capability}." + (
                    f" Priority: {item['priority_label']}." if item.get("priority_label") else ""
                ),
                "importance": importance,
                "deadline": deadline,
                "next_action": course or capability,
            },
        )
        task_id = f"task-{goal_id}-main"
        conn.execute(
            """
            INSERT INTO tasks (id, goal_id, domain_id, title, deadline, status)
            VALUES (:id, :goal_id, :domain_id, :title, :deadline, 'not_started')
            ON CONFLICT(id) DO UPDATE SET
                domain_id=excluded.domain_id, title=excluded.title, deadline=excluded.deadline
            """,
            {
                "id": task_id,
                "goal_id": goal_id,
                "domain_id": domain_id,
                "title": name,
                "deadline": deadline,
            },
        )

    # Courses: staggered by priority_rank, 3 weeks apart, starting 6 weeks
    # out - these are substantial capability-building courses.
    for item in courses:
        rank = item.get("priority_rank") or (len(courses) + 1)
        deadline = (today + timedelta(weeks=6 + (rank - 1) * 3)).isoformat()
        _upsert("course", item, deadline)
        count += 1

    # Books: staggered by list order, 2 weeks apart, starting 4 weeks out.
    for i, item in enumerate(books):
        deadline = (today + timedelta(weeks=4 + i * 2)).isoformat()
        _upsert("book", item, deadline)
        count += 1

    conn.commit()
    return count


TASK_SOURCE_FILES = ["course_modules.yaml", "personal_deliverables.yaml", "life_domain_deliverables.yaml"]


def seed_tasks(conn) -> int:
    tasks = []
    for filename in TASK_SOURCE_FILES:
        tasks.extend(load_yaml(filename).get("tasks") or [])
    for t in tasks:
        task_id = f"task-{t['goal_id']}-{_slug(t['title'])}"
        conn.execute(
            """
            INSERT INTO tasks (id, goal_id, domain_id, title, deadline, status)
            VALUES (:id, :goal_id, :domain_id, :title, :deadline, 'not_started')
            ON CONFLICT(id) DO UPDATE SET
                domain_id=excluded.domain_id,
                title=excluded.title, deadline=excluded.deadline
            """,
            {
                "id": task_id,
                "goal_id": t["goal_id"],
                "domain_id": t["domain_id"],
                "title": t["title"],
                "deadline": t.get("deadline"),
            },
        )
    conn.commit()
    return len(tasks)


def main() -> None:
    init_db()
    conn = get_connection()
    try:
        n_domains = seed_domains(conn)
        n_goals = seed_goals(conn)
        n_tasks = seed_tasks(conn)
        n_learning = seed_learning_goals(conn)
        print(
            f"Seeded {n_domains} domains, {n_goals + n_learning} goals "
            f"({n_learning} from learning items), {n_tasks + n_learning} tasks."
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
