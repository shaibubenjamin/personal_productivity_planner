"""Single-user login gate. Credentials live in the app_auth table (one row,
id='singleton') - not Streamlit secrets/env vars. The app itself renders a
"create your password" form on first run; the password is stored only as a
salted SHA-256 hash. Since the local app and the deployed app already share
the same database (see docs/decision_log.md - Postgres/Supabase
migration), setting the password once works everywhere immediately,
without needing to duplicate it into Streamlit Cloud's secrets box.

Design note: an earlier version injected raw <div>/<svg>/<script> HTML via
st.markdown(unsafe_allow_html=True) and it rendered as literal escaped text
instead of real elements (owner-reported, 2026-09-08). Rather than keep
guessing at that, this version uses two mechanisms that don't depend on
markdown interpreting arbitrary HTML at all:
  1. The background is pure CSS (a data-URI SVG on an existing Streamlit
     container's `background-image`) via a <style> block - the same
     st.markdown(unsafe_allow_html=True) mechanism, but CSS-only, which is
     the part that was already proven to work (fonts/card styling elsewhere
     in this app use the identical pattern).
  2. The rotating quote uses st.components.v1.html, Streamlit's dedicated
     API for embedding real interactive HTML/JS in a real iframe - not the
     markdown pathway, so it isn't subject to whatever broke the div/script.
"""

import base64
import hashlib
import hmac
import secrets
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from engine.common.db import get_connection

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
FIXED_USERNAME = "benjaminshaibu01@gmail.com"
# The wide landscape is the actual full-bleed background (genuinely wide/HD,
# so background-size:cover doesn't have to stretch/distort it). The owner's
# own stag photo is portrait and low-res (640x958) - stretching ANY portrait
# photo edge-to-edge across a wide screen looks soft/distorted regardless of
# source quality, which is what prompted this redesign (owner feedback,
# 2026-09-10). It's now shown via native st.image() at its real aspect
# ratio in a framed panel instead, so it stays sharp.
BACKGROUND_PHOTO_PATH = ASSETS_DIR / "login_background_landscape.jpg"
FEATURE_PHOTO_PATH = ASSETS_DIR / "login_background.jpg"

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

SESSION_KEY = "peos_authenticated"

# The one quote the owner explicitly required (2026-09-08) is first and
# fixed. The rest are additional widely-circulated Hormozi quotes - if any
# wording is off from the exact verbatim source, swap it out; better to
# under-quote a real person than risk misattributing invented words to them.
MOTIVATION_QUOTES = [
    "Do so much work, it's impossible not to achieve your dream.",
    "Don't wish it were easier, wish you were better.",
    "The obstacle in the path becomes the path. Never forget, within every obstacle is an opportunity to improve our condition.",
    "Volume negates luck.",
    "Skills are more valuable than money, because skills can get you money, but money can't buy skills.",
]


def _pine(x: float, base_y: float, scale: float, fill: str) -> str:
    """One pine-tree silhouette (two stacked triangles + trunk), hand-drawn
    SVG shapes - not a photo, so there's no licensing/sourcing question."""
    w, h = 70 * scale, 130 * scale
    trunk_w, trunk_h = 10 * scale, 18 * scale
    return (
        f'<polygon points="{x},{base_y - h} {x - w/2},{base_y - h*0.45} {x + w/2},{base_y - h*0.45}" fill="{fill}"/>'
        f'<polygon points="{x},{base_y - h*0.55} {x - w*0.65},{base_y - trunk_h} {x + w*0.65},{base_y - trunk_h}" fill="{fill}"/>'
        f'<rect x="{x - trunk_w/2}" y="{base_y - trunk_h}" width="{trunk_w}" height="{trunk_h}" fill="{fill}"/>'
    )


def _bird(x: float, y: float, scale: float, stroke: str) -> str:
    s = 14 * scale
    return (
        f'<path d="M{x - s},{y} Q{x - s/2},{y - s} {x},{y} Q{x + s/2},{y - s} {x + s},{y}" '
        f'stroke="{stroke}" stroke-width="{2 * scale}" fill="none" stroke-linecap="round"/>'
    )


def _forest_svg() -> str:
    """A complete, self-contained <svg>...</svg> string, flattened to one
    line (no embedded newlines/indentation) so it's safe to URL-encode into
    a CSS data URI."""
    trees_back = "".join(
        _pine(x, 640, scale, "#0d3b2c")
        for x, scale in [(80, 0.8), (230, 1.1), (400, 0.7), (560, 1.0), (740, 0.85),
                          (900, 1.15), (1060, 0.75), (1220, 1.0), (1380, 0.9), (1520, 0.7)]
    )
    trees_front = "".join(
        _pine(x, 760, scale, "#04170f")
        for x, scale in [(20, 1.3), (180, 1.6), (350, 1.1), (520, 1.5), (700, 1.2),
                          (880, 1.7), (1050, 1.15), (1230, 1.5), (1410, 1.3), (1560, 1.1)]
    )
    birds = "".join(_bird(x, y, s, "#04170f") for x, y, s in [(340, 160, 1.0), (420, 190, 0.8), (500, 155, 0.7)])
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900">'
        "<defs><linearGradient id=\"sky\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">"
        '<stop offset="0%" stop-color="#0a2e42"/>'
        '<stop offset="45%" stop-color="#134e3a"/>'
        '<stop offset="100%" stop-color="#0d3b2c"/>'
        "</linearGradient></defs>"
        '<rect width="1600" height="900" fill="url(#sky)"/>'
        '<circle cx="1320" cy="170" r="65" fill="#FDE68A" opacity="0.9"/>'
        '<circle cx="1320" cy="170" r="95" fill="#FDE68A" opacity="0.12"/>'
        f"{birds}"
        '<path d="M0,620 Q400,540 800,600 T1600,580 L1600,900 L0,900 Z" fill="#12513c" opacity="0.75"/>'
        f"{trees_back}{trees_front}"
        "</svg>"
    )


def _background_data_uri() -> str:
    """Real HD photo if the asset is present (read + base64 at runtime, not
    baked into source); falls back to the hand-drawn SVG scene otherwise so
    the login screen never breaks if the asset is ever missing."""
    if BACKGROUND_PHOTO_PATH.exists():
        encoded = base64.b64encode(BACKGROUND_PHOTO_PATH.read_bytes()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"
    return "data:image/svg+xml," + urllib.parse.quote(_forest_svg())


def _inject_background() -> None:
    """CSS-only: background-image data URI + a glass-card look for the
    login form, all via a <style> block - the mechanism already proven to
    render correctly elsewhere in this app (app/components/style.py)."""
    data_uri = _background_data_uri()
    st.markdown(
        "<style>"
        f'[data-testid="stAppViewContainer"] {{ background-image: url("{data_uri}"); '
        "background-size: cover; background-position: center center; "
        "background-attachment: fixed; background-repeat: no-repeat; }}"
        '[data-testid="stHeader"] { background: transparent; }'
        ".block-container { padding-top: 3rem; max-width: 780px; }"
        ".block-container h1 { color: #ECFDF5; text-align: center; "
        "text-shadow: 0 2px 10px rgba(0,0,0,0.6); font-weight: 700; }"
        '.block-container [data-testid="stCaptionContainer"] { color: #D1FAE5; '
        "text-align: center; text-shadow: 0 1px 6px rgba(0,0,0,0.6); }"
        '[data-testid="stForm"] { background: rgba(255,255,255,0.94); '
        "padding: 1.75rem 1.75rem 1rem; border-radius: 1rem; "
        "box-shadow: 0 12px 40px rgba(0,0,0,0.45); backdrop-filter: blur(4px); }"
        '[data-testid="stImage"] img { border-radius: 1rem; '
        "box-shadow: 0 12px 40px rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.25); }"
        "</style>",
        unsafe_allow_html=True,
    )


def _render_rotating_quote() -> None:
    """Real, executing JS via Streamlit's component API (not markdown)."""
    quotes_json = "[" + ",".join(
        '"' + q.replace("\\", "\\\\").replace('"', '\\"') + '"' for q in MOTIVATION_QUOTES
    ) + "]"
    components.html(
        f"""
        <div id="q" style="font-family: Inter, sans-serif; color: #ECFDF5;
             font-size: 1.05rem; font-style: italic; text-align: center;
             padding: 1.1rem 1.25rem; background: rgba(4, 23, 15, 0.55);
             border-radius: 0.75rem; box-shadow: 0 6px 20px rgba(0,0,0,0.35);"></div>
        <script>
        const quotes = {quotes_json};
        let i = 0;
        function rotate() {{
            document.getElementById("q").textContent = quotes[i % quotes.length];
            i++;
        }}
        rotate();
        setInterval(rotate, 10000);
        </script>
        """,
        height=95,
    )


def _load_credentials():
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT username, password_salt, password_hash FROM app_auth WHERE id = 'singleton'"
        ).fetchone()
    finally:
        conn.close()


def _save_credentials(password: str) -> None:
    salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO app_auth (id, username, password_salt, password_hash, created_at, updated_at) "
            "VALUES ('singleton', :username, :salt, :hash, :now, :now)",
            {"username": FIXED_USERNAME, "salt": salt, "hash": pw_hash, "now": now},
        )
        conn.commit()
    finally:
        conn.close()


def _render_create_password_form() -> None:
    st.caption(f"First-time setup - create a password for {FIXED_USERNAME}")
    with st.form("create_password"):
        pw1 = st.text_input("New password", type="password")
        pw2 = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create password", type="primary", use_container_width=True)

    if submitted:
        if len(pw1) < 8:
            st.error("Password must be at least 8 characters.")
        elif pw1 != pw2:
            st.error("Passwords don't match.")
        else:
            _save_credentials(pw1)
            st.session_state[SESSION_KEY] = True
            st.rerun()


def _render_login_form(username: str, salt: str, pw_hash: str) -> None:
    # Single-user app with one fixed account - asking for a username field
    # alongside password was redundant, and the owner reported the field
    # conflicting with the browser's own email/username autofill UI
    # (2026-09-10). Password-only removes that entirely.
    st.caption(f"Signing in as {username}")
    with st.form("login"):
        input_pw = st.text_input(
            "Password", type="password", autocomplete="current-password",
        )
        submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)

    if submitted:
        candidate_hash = hashlib.sha256((salt + input_pw).encode()).hexdigest()
        if hmac.compare_digest(candidate_hash, pw_hash):
            st.session_state[SESSION_KEY] = True
            st.rerun()
        else:
            st.error("Incorrect password.")


def require_login() -> bool:
    """Renders a login (or first-run create-password) form if not
    authenticated. Returns True once logged in."""
    if st.session_state.get(SESSION_KEY):
        return True

    credentials = _load_credentials()

    _inject_background()
    st.title("Productivity Tracker")
    st.caption("Track your goals, habits, and progress across every domain of your life.")

    if FEATURE_PHOTO_PATH.exists():
        col_photo, col_form = st.columns([1, 1.2], vertical_alignment="center")
        with col_photo:
            st.image(str(FEATURE_PHOTO_PATH), use_container_width=True)
    else:
        col_form = st.container()

    with col_form:
        _render_rotating_quote()
        if credentials is None:
            _render_create_password_form()
        else:
            _render_login_form(credentials["username"], credentials["password_salt"], credentials["password_hash"])

    return False


def render_logout_button() -> None:
    """Sidebar logout - visible on every page once authenticated."""
    if st.sidebar.button("Log out", icon=":material/logout:", use_container_width=True):
        st.session_state[SESSION_KEY] = False
        st.rerun()
