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
    "marriage": "favorite",
    "academics": "school",
    "spiritual": "self_improvement",
    "personal": "person",
}

# One accent color per domain - the "bring it to life" touch, used sparingly
# (a thin top bar + icon chip on cards), not as loud full-card color.
DOMAIN_COLORS = {
    "career": "#4F46E5",
    "financial": "#059669",
    "marriage": "#E11D48",
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
    # Warm neutrals (stone, not the generic slate-gray + indigo/violet
    # combination that reads as a templated AI-tool default) and a deep
    # teal accent instead - owner feedback 2026-09-13: "generic look, not
    # a real color/type system... not default AI-purple."
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1100px; }
        h1 { font-weight: 800; letter-spacing: -0.02em; font-size: 2.1rem; }
        h2 { font-weight: 700; letter-spacing: -0.015em; }
        h3 { font-weight: 700; letter-spacing: -0.01em; font-size: 1.15rem; }
        [data-testid="stMetricValue"] { font-size: 1.4rem; font-weight: 700; }
        [data-testid="stMetricLabel"] { color: #78716C; font-size: 0.85rem; }
        .peos-header h1 {
            margin-bottom: 0; position: relative; padding-bottom: 0.7rem;
        }
        .peos-header h1::after {
            content: ""; position: absolute; left: 0; bottom: 0;
            width: 2.75rem; height: 4px; border-radius: 4px;
            background: #0D7C66;
        }
        .peos-subtitle { color: #78716C; font-size: 0.95rem; margin-top: 0.7rem; margin-bottom: 1.4rem; }
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
            box-shadow: 0 4px 14px rgba(28, 25, 23, 0.08);
        }
        /* Sidebar: give it a distinct tint + branded header block instead of
           plain white, so navigation reads as a real product shell.
           NOTE: no blank lines anywhere in this block - CommonMark ends a
           raw-HTML block (which <style> counts as) at the first blank line,
           so anything after one renders as literal visible text instead of
           being applied as CSS. Real bug, caught via owner screenshot. */
        [data-testid="stSidebar"] {
            background: #FAFAF9;
            border-right: 1px solid #E7E5E4;
        }
        .peos-sidebar-brand {
            display: flex; align-items: center; gap: 0.6rem;
            padding: 0.4rem 0 1rem 0; margin-bottom: 0.6rem;
            border-bottom: 1px solid #E7E5E4;
        }
        .peos-sidebar-brand .peos-sidebar-logo {
            width: 2.2rem; height: 2.2rem; border-radius: 0.6rem;
            background: #0D7C66;
            display: flex; align-items: center; justify-content: center;
            color: white; font-size: 1.2rem; flex-shrink: 0;
        }
        .peos-sidebar-brand .peos-sidebar-name {
            font-weight: 700; font-size: 1.02rem; color: #1C1917; line-height: 1.15;
        }
        .peos-sidebar-brand .peos-sidebar-tag {
            font-size: 0.72rem; color: #78716C;
        }
        /* Buttons: rounded, slightly elevated primary actions instead of
           Streamlit's flat default rectangles. */
        .stButton > button, .stFormSubmitButton > button, .stLinkButton > a {
            border-radius: 0.5rem; font-weight: 600;
            transition: transform 0.1s ease, box-shadow 0.15s ease;
        }
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
            box-shadow: 0 2px 8px rgba(13, 124, 102, 0.25);
        }
        .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(13, 124, 102, 0.35);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    """Branded sidebar header (icon mark + name). Simple, self-contained
    <div> markup in one markdown call, styled via the <style> block above -
    the same pattern already used successfully throughout this app
    (domain_card.py's accent bar/icon chip). The pattern that actually
    failed earlier in this app was a <script> tag (JS doesn't execute via
    markdown - see auth.py's module docstring); plain nested <div>s with
    CSS classes have worked reliably every time they've been used here."""
    st.sidebar.markdown(
        '<div class="peos-sidebar-brand">'
        '<div class="peos-sidebar-logo">&#9679;</div>'
        '<div><div class="peos-sidebar-name">Productivity Tracker</div>'
        '<div class="peos-sidebar-tag">Your life, on course</div></div>'
        "</div>",
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
    text_color, bg_color = STATUS_COLORS.get(status_key, ("#44403C", "#E7E5E4"))
    return (
        f'<span class="peos-pill" style="color:{text_color}; background:{bg_color};">'
        f"{label}</span>"
    )


def domain_icon(domain_id: str) -> str:
    return DOMAIN_ICONS.get(domain_id, "circle")


def domain_color(domain_id: str) -> str:
    return DOMAIN_COLORS.get(domain_id, "#44403C")
