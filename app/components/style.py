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
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1100px; }
        h1, h2, h3 { font-weight: 600; letter-spacing: -0.01em; }
        [data-testid="stMetricValue"] { font-size: 1.4rem; }
        [data-testid="stMetricLabel"] { color: #64748B; font-size: 0.85rem; }
        .peos-header h1 {
            margin-bottom: 0; position: relative; padding-bottom: 0.6rem;
        }
        .peos-header h1::after {
            content: ""; position: absolute; left: 0; bottom: 0;
            width: 3rem; height: 4px; border-radius: 4px;
            background: linear-gradient(90deg, #4F46E5, #7C3AED);
        }
        .peos-subtitle { color: #64748B; font-size: 0.95rem; margin-top: 0.6rem; margin-bottom: 1.4rem; }
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

        /* Sidebar: give it a distinct tint + branded header block instead of
           plain white, so navigation reads as a real product shell. */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
            border-right: 1px solid #E2E8F0;
        }
        .peos-sidebar-brand {
            display: flex; align-items: center; gap: 0.6rem;
            padding: 0.4rem 0 1rem 0; margin-bottom: 0.6rem;
            border-bottom: 1px solid #E2E8F0;
        }
        .peos-sidebar-brand .peos-sidebar-logo {
            width: 2.2rem; height: 2.2rem; border-radius: 0.6rem;
            background: linear-gradient(135deg, #4F46E5, #7C3AED);
            display: flex; align-items: center; justify-content: center;
            color: white; font-size: 1.2rem; flex-shrink: 0;
        }
        .peos-sidebar-brand .peos-sidebar-name {
            font-weight: 700; font-size: 1.02rem; color: #0F172A; line-height: 1.15;
        }
        .peos-sidebar-brand .peos-sidebar-tag {
            font-size: 0.72rem; color: #64748B;
        }

        /* Buttons: rounded, slightly elevated primary actions instead of
           Streamlit's flat default rectangles. */
        .stButton > button, .stFormSubmitButton > button, .stLinkButton > a {
            border-radius: 0.6rem; font-weight: 600;
            transition: transform 0.1s ease, box-shadow 0.15s ease;
        }
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
            box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);
        }
        .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);
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
    text_color, bg_color = STATUS_COLORS.get(status_key, ("#334155", "#E2E8F0"))
    return (
        f'<span class="peos-pill" style="color:{text_color}; background:{bg_color};">'
        f"{label}</span>"
    )


def domain_icon(domain_id: str) -> str:
    return DOMAIN_ICONS.get(domain_id, "circle")


def domain_color(domain_id: str) -> str:
    return DOMAIN_COLORS.get(domain_id, "#334155")
