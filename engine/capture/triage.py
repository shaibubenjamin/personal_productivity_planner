"""Quick-capture triage: a keyword heuristic that SUGGESTS a domain/goal for
a raw captured thought - never commits it anywhere real. The owner always
confirms or overrides the suggestion (spec Section 4 confidence model: an
inference must never be presented as fact).
"""

import re

STOPWORDS = {
    "a", "an", "the", "to", "for", "of", "in", "on", "and", "or", "with",
    "my", "i", "is", "at", "by",
}

# Small keyword list per domain so short/casual captures ("book a swim
# lesson") still match even though the domain's own name ("personal")
# never appears in the text.
DOMAIN_KEYWORDS = {
    "career": {"job", "work", "career", "pmp", "capability", "programme", "project", "interview", "resume", "cv", "promotion", "boss"},
    "financial": {"money", "budget", "invest", "investing", "forex", "savings", "bank", "expense", "financial", "tax"},
    "relationships": {"friend", "network", "networking", "contact", "relationship", "connect", "meetup"},
    "marriage": {"marriage", "wedding", "spouse", "wife", "husband", "propose", "engagement"},
    "french": {"french", "language", "vocab", "vocabulary", "grammar", "tutor"},
    "academics": {"university", "course", "degree", "school", "program", "application", "academic"},
    "spiritual": {"pray", "prayer", "church", "sermon", "spiritual", "faith", "bible", "selman"},
    "personal": {"gym", "workout", "health", "swim", "swimming", "chess", "snooker", "horse", "riding", "mountain", "climbing", "sleep", "rest", "recharge", "habit"},
}


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z']+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def suggest_triage(text: str, goals: list) -> tuple[str | None, str | None]:
    """`goals`: sequence of objects with `id`, `domain_id`, `name`.
    Returns (suggested_domain_id, suggested_goal_id) - either may be None."""
    tokens = _tokenize(text)
    if not tokens:
        return None, None

    best_goal, best_goal_score = None, 0
    for g in goals:
        goal_words = _tokenize(g["name"])
        score = len(goal_words & tokens)
        if score > best_goal_score:
            best_goal, best_goal_score = g, score

    if best_goal and best_goal_score > 0:
        return best_goal["domain_id"], best_goal["id"]

    best_domain, best_domain_score = None, 0
    for domain_id, keywords in DOMAIN_KEYWORDS.items():
        score = len(keywords & tokens)
        if score > best_domain_score:
            best_domain, best_domain_score = domain_id, score

    if best_domain and best_domain_score > 0:
        return best_domain, None

    return None, None
