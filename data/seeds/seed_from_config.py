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


def main() -> None:
    init_db()
    conn = get_connection()
    try:
        n_domains = seed_domains(conn)
        n_goals = seed_goals(conn)
        print(f"Seeded {n_domains} domains, {n_goals} goals.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
