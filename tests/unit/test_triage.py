from engine.capture.triage import suggest_triage

GOALS = [
    {"id": "goal-personal-learn-swim", "domain_id": "personal", "name": "Learn to swim"},
    {"id": "goal-french-c2-by-30", "domain_id": "french", "name": "Reach C2 French proficiency by age 30"},
    {"id": "goal-marriage-by-30", "domain_id": "marriage", "name": "Get married by age 30"},
]


def test_matches_specific_goal_by_name_overlap():
    domain, goal = suggest_triage("need to book a swim lesson for next week", GOALS)
    assert domain == "personal"
    assert goal == "goal-personal-learn-swim"


def test_falls_back_to_domain_keyword_when_no_goal_matches():
    domain, goal = suggest_triage("check my bank account and review the budget", GOALS)
    assert domain == "financial"
    assert goal is None


def test_no_match_returns_none_none():
    domain, goal = suggest_triage("xyz completely unrelated gibberish qqq", GOALS)
    assert domain is None
    assert goal is None


def test_empty_text_returns_none_none():
    assert suggest_triage("", GOALS) == (None, None)


def test_french_keyword_without_goal_name_match():
    domain, goal = suggest_triage("practice french vocab tonight", GOALS)
    assert domain == "french"
