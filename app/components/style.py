"""Shared design system for the PEOS Streamlit app.

One place for colors, icons, and small styled components so every page
looks like it belongs to the same product instead of 11 pages each
improvising their own layout.
"""

import streamlit as st

DOMAIN_ICONS = {
    "career": "💼",
    "financial": "💰",
    "relationships": "🤝",
    "marriage": "💞",
    "french": "🇫🇷",
    "academics": "🎓",
    "spiritual": "🙏",
    "personal": "🧑",
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
        .peos-header { display: flex; align-items: baseline; gap: 0.6rem; margin-bottom: 0.1rem; }
        .peos-header .icon { font-size: 1.8rem; }
        .peos-subtitle { color: #64748B; font-size: 0.95rem; margin-top: -0.3rem; margin-bottom: 1.4rem; }
        .peos-pill {
            display: inline-block; padding: 0.15rem 0.65rem; border-radius: 999px;
            font-size: 0.78rem; font-weight: 600; white-space: nowrap;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(icon: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="peos-header"><span class="icon">{icon}</span><h1>{title}</h1></div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(f'<div class="peos-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def status_pill(label: str, status_key: str) -> str:
    text_color, bg_color = STATUS_COLORS.get(status_key, ("#334155", "#E2E8F0"))
    return (
        f'<span class="peos-pill" style="color:{text_color}; background:{bg_color};">'
        f"{label}</span>"
    )


def domain_icon(domain_id: str) -> str:
    return DOMAIN_ICONS.get(domain_id, "•")
