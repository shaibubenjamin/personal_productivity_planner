"""Single-user login gate. Credentials come from environment variables
(local .env, loaded via python-dotenv) or Streamlit secrets (deployed) -
never hardcoded, never committed. The password itself is stored only as a
salted SHA-256 hash; see docs/security.md for how it was generated.
"""

import hashlib
import hmac
import os

import streamlit as st

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
    return f"""
    <svg viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice"
         style="position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:-1;">
      <defs>
        <linearGradient id="peosSky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0a2e42"/>
          <stop offset="45%" stop-color="#134e3a"/>
          <stop offset="100%" stop-color="#0d3b2c"/>
        </linearGradient>
      </defs>
      <rect width="1600" height="900" fill="url(#peosSky)"/>
      <circle cx="1320" cy="170" r="65" fill="#FDE68A" opacity="0.9"/>
      <circle cx="1320" cy="170" r="95" fill="#FDE68A" opacity="0.12"/>
      {birds}
      <path d="M0,620 Q400,540 800,600 T1600,580 L1600,900 L0,900 Z" fill="#12513c" opacity="0.75"/>
      {trees_back}
      {trees_front}
    </svg>
    """


def _login_chrome() -> None:
    """Forest/wildlife-themed animated background + rotating quote, login screen only."""
    quotes_js = ",".join(f'"{q}"' for q in MOTIVATION_QUOTES)
    st.markdown(
        f"""
        <style>
        @keyframes peosGlow {{
            0% {{ filter: brightness(1); }}
            50% {{ filter: brightness(1.08); }}
            100% {{ filter: brightness(1); }}
        }}
        .peos-forest-bg {{ animation: peosGlow 12s ease-in-out infinite; }}
        .peos-login-quote {{
            color: #ECFDF5; font-size: 1.1rem; font-style: italic; text-align: center;
            min-height: 4.5rem; padding: 1rem 1.5rem; margin-bottom: 1rem;
            text-shadow: 0 1px 4px rgba(0,0,0,0.5);
        }}
        [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background: transparent; }}
        </style>
        <div class="peos-forest-bg">{_forest_svg()}</div>
        <div class="peos-login-quote" id="peos-quote"></div>
        <script>
        const peosQuotes = [{quotes_js}];
        let peosQuoteIndex = 0;
        function peosRotateQuote() {{
            const el = document.getElementById("peos-quote");
            if (el) {{ el.textContent = peosQuotes[peosQuoteIndex % peosQuotes.length]; }}
            peosQuoteIndex++;
        }}
        peosRotateQuote();
        setInterval(peosRotateQuote, 10000);
        </script>
        """,
        unsafe_allow_html=True,
    )


def _get_secret(key: str) -> str | None:
    if hasattr(st, "secrets"):
        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass
    return os.environ.get(key)


def require_login() -> bool:
    """Renders a login form if not authenticated. Returns True once logged in."""
    if st.session_state.get(SESSION_KEY):
        return True

    username = _get_secret("PEOS_AUTH_USERNAME")
    salt = _get_secret("PEOS_AUTH_PASSWORD_SALT")
    pw_hash = _get_secret("PEOS_AUTH_PASSWORD_HASH")

    _login_chrome()
    st.title("PEOS")
    st.caption("Personal Executive Operating System")

    if not (username and salt and pw_hash):
        st.error(
            "Login is not configured - set PEOS_AUTH_USERNAME, "
            "PEOS_AUTH_PASSWORD_SALT, and PEOS_AUTH_PASSWORD_HASH in your "
            "local .env, or in Streamlit secrets once deployed."
        )
        return False

    with st.form("login"):
        input_user = st.text_input("Username")
        input_pw = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", type="primary")

    if submitted:
        candidate_hash = hashlib.sha256((salt + input_pw).encode()).hexdigest()
        user_ok = hmac.compare_digest(input_user.strip().lower(), username.strip().lower())
        pw_ok = hmac.compare_digest(candidate_hash, pw_hash)
        if user_ok and pw_ok:
            st.session_state[SESSION_KEY] = True
            st.rerun()
        else:
            st.error("Incorrect username or password.")

    return False
