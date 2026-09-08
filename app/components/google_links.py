"""Zero-OAuth Google actions: URL builders for Calendar's "quick add" and
Gmail's prefilled compose. Both open the real Google UI, prefilled, and just
need the owner to click confirm/send in their browser - no API credentials
needed. This is the pragmatic path for "add to my calendar" / "send a mail"
buttons from a locally-run app that has no Google OAuth client configured
yet (see docs/decision_log.md for what full read/write integration needs).
"""

from datetime import datetime
from urllib.parse import quote


def calendar_quick_add_url(title: str, start: datetime, end: datetime, details: str = "") -> str:
    fmt = "%Y%m%dT%H%M%SZ"
    dates = f"{start.strftime(fmt)}/{end.strftime(fmt)}"
    return (
        "https://calendar.google.com/calendar/render?action=TEMPLATE"
        f"&text={quote(title)}&dates={dates}&details={quote(details)}"
    )


def gmail_compose_url(subject: str, body: str = "", to: str = "") -> str:
    params = f"su={quote(subject)}&body={quote(body)}"
    if to:
        params += f"&to={quote(to)}"
    return f"https://mail.google.com/mail/?view=cm&fs=1&{params}"
