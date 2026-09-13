"""Shared domain-card rendering so the Dashboard and Life Balance pages show
identical, uniform cards (owner request, 2026-09-08: cards should all follow
an equal pattern/width/height) instead of each page laying them out slightly
differently. Fixed height uses Streamlit's native container `height` param,
not a guess at private CSS internals.
"""

import streamlit as st

from app.components.style import domain_color, domain_icon, icon_md

CARD_HEIGHT = 230


def render_domain_card(d, badge_html: str | None = None, goal_summary: tuple[int, int] | None = None) -> None:
    """`goal_summary`, if given, is (on_course_count, total_goal_count) for
    this domain - a real count from the schedule-status engine, not a
    fabricated score."""
    icon = domain_icon(d["id"])
    color = domain_color(d["id"])
    weight = d["strategic_weight"]

    with st.container(border=True, height=CARD_HEIGHT):
        st.markdown(
            f'<div class="peos-accent-bar" style="background:{color};"></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<span class="peos-icon-chip" style="background:{color}22; color:{color};">'
            f"{icon_md(icon)}</span>"
            f'<span style="font-size:1.05rem; font-weight:600; vertical-align:middle;">{d["name"]}</span>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        c1.metric(
            f"{icon_md('center_focus_strong')} Target focus",
            f"{weight:.0f}%" if weight is not None else "—",
            help="How much of your overall attention this domain should get, "
                 "relative to the other domains (they all add up to 100%).",
        )
        if goal_summary is not None:
            on_course, total = goal_summary
            c2.metric(
                f"{icon_md('check_circle')} On course",
                f"{on_course}/{total}" if total else "—",
                help="Goals in this domain currently on course, out of all goals here.",
            )

        if badge_html:
            st.markdown(badge_html, unsafe_allow_html=True)

        st.page_link(
            "views/domain_detail.py",
            label="View goals & to-dos",
            icon=":material/arrow_forward:",
            query_params={"domain": d["id"]},
        )
