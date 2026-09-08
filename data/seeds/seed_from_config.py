"""Load config/life_domains.yaml and config/goals.yaml into the SQLite DB.

Idempotent: re-running upserts domains/goals rather than duplicating them.
Run with: python -m data.seeds.seed_from_config
"""

from engine.common.config import load_yaml
from engine.common.db import get_connection, init_db


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
                "active": 1 if d.get("active", True) else 0,
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


def seed_learning_items(conn) -> int:
    config = load_yaml("learning_items.yaml")
    courses = config.get("courses") or []
    books = config.get("books") or []
    count = 0

    for item_type, items in (("course", courses), ("book", books)):
        for item in items:
            item_id = f"{item_type}-{count}-{item['capability'][:20]}"
            conn.execute(
                """
                INSERT INTO learning_items (
                    id, domain_id, capability, course, item_type,
                    priority_rank, priority_label, status, progress
                ) VALUES (
                    :id, :domain_id, :capability, :course, :item_type,
                    :priority_rank, :priority_label, 'not_started', 0
                )
                ON CONFLICT(id) DO UPDATE SET
                    domain_id=excluded.domain_id, capability=excluded.capability,
                    course=excluded.course, priority_rank=excluded.priority_rank,
                    priority_label=excluded.priority_label
                """,
                {
                    "id": item_id,
                    "domain_id": item["domain_id"],
                    "capability": item["capability"],
                    "course": item.get("course"),
                    "item_type": item_type,
                    "priority_rank": item.get("priority_rank"),
                    "priority_label": item.get("priority_label"),
                },
            )
            count += 1
    conn.commit()
    return count


def seed_tasks(conn) -> int:
    tasks = load_yaml("course_modules.yaml").get("tasks") or []
    for i, t in enumerate(tasks):
        task_id = f"task-{t['goal_id']}-{i}"
        conn.execute(
            """
            INSERT INTO tasks (id, goal_id, domain_id, title, deadline, status)
            VALUES (:id, :goal_id, :domain_id, :title, :deadline, 'not_started')
            ON CONFLICT(id) DO UPDATE SET
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
        n_learning = seed_learning_items(conn)
        n_tasks = seed_tasks(conn)
        print(f"Seeded {n_domains} domains, {n_goals} goals, {n_learning} learning items, {n_tasks} tasks.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
