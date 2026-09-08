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


def _login_chrome() -> None:
    """Nature-inspired animated background + rotating quote, login screen only."""
    quotes_js = ",".join(f'"{q}"' for q in MOTIVATION_QUOTES)
    st.markdown(
        f"""
        <style>
        .peos-login-bg {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            z-index: -1;
            background: linear-gradient(-45deg, #0f3d2e, #1a5c42, #2d7a52, #0a2e42, #14532d);
            background-size: 400% 400%;
            animation: peosGradient 18s ease infinite;
        }}
        @keyframes peosGradient {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        .peos-login-quote {{
            color: #ECFDF5; font-size: 1.1rem; font-style: italic; text-align: center;
            min-height: 4.5rem; padding: 1rem 1.5rem; margin-bottom: 1rem;
            text-shadow: 0 1px 4px rgba(0,0,0,0.4);
        }}
        [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background: transparent; }}
        </style>
        <div class="peos-login-bg"></div>
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
