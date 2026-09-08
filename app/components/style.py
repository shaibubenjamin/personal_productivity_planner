"""Shared design system for the PEOS Streamlit app.

One place for colors, icons, and small styled components so every page
looks like it belongs to the same product instead of improvising its own
layout. Icons are Material Symbols (clean monochrome line icons, built into
Streamlit's ":material/name:" markdown shorthand) - not emoji.
"""

import streamlit as st

DOMAIN_ICONS = {
    "career": "work",
    "financial": "payments",
    "relationships": "handshake",
    "marriage": "favorite",
    "french": "translate",
    "academics": "school",
    "spiritual": "self_improvement",
    "personal": "person",
}

# One accent color per domain - the "bring it to life" touch, used sparingly
# (a thin top bar + icon chip on cards), not as loud full-card color.
DOMAIN_COLORS = {
    "career": "#4F46E5",
    "financial": "#059669",
    "relationships": "#DB2777",
    "marriage": "#E11D48",
    "french": "#2563EB",
    "academics": "#D97706",
    "spiritual": "#7C3AED",
    "personal": "#0891B2",
}

STATUS_COLORS = {
    "HEALTHY": ("#15803D", "#DCFCE7"),          # text, background
    "OVER_INVESTMENT": ("#B45309", "#FEF3C7"),
    "UNDER_INVESTMENT": ("#B91C1C", "#FEE2E2"),
}


def inject_css() -> None:
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1100px; }
        h1, h2, h3 { font-weight: 600; letter-spacing: -0.01em; }
        [data-testid="stMetricValue"] { font-size: 1.4rem; }
        [data-testid="stMetricLabel"] { color: #64748B; font-size: 0.85rem; }
        .peos-header h1 { margin-bottom: 0; }
        .peos-subtitle { color: #64748B; font-size: 0.95rem; margin-top: 0.1rem; margin-bottom: 1.4rem; }
        .peos-pill {
            display: inline-block; padding: 0.15rem 0.65rem; border-radius: 999px;
            font-size: 0.78rem; font-weight: 600; white-space: nowrap;
        }
        .peos-accent-bar { height: 4px; border-radius: 4px; margin-bottom: 0.6rem; }
        .peos-icon-chip {
            display: inline-flex; align-items: center; justify-content: center;
            width: 2rem; height: 2rem; border-radius: 0.5rem; margin-right: 0.5rem;
        }
        /* Best-effort hover lift on bordered containers - cosmetic only, safe
           to no-op if this testid changes in a future Streamlit version. */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            transition: box-shadow 0.15s ease, transform 0.15s ease;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def icon_md(name: str) -> str:
    """Material Symbols markdown shorthand, e.g. icon_md('work') -> ':material/work:'."""
    return f":material/{name}:"


def page_header(icon: str, title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="peos-header">', unsafe_allow_html=True)
    st.markdown(f"# {icon_md(icon)} {title}")
    st.markdown("</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="peos-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def status_pill(label: str, status_key: str) -> str:
    text_color, bg_color = STATUS_COLORS.get(status_key, ("#334155", "#E2E8F0"))
    return (
        f'<span class="peos-pill" style="color:{text_color}; background:{bg_color};">'
        f"{label}</span>"
    )


def domain_icon(domain_id: str) -> str:
    return DOMAIN_ICONS.get(domain_id, "circle")


def domain_color(domain_id: str) -> str:
    return DOMAIN_COLORS.get(domain_id, "#334155")
