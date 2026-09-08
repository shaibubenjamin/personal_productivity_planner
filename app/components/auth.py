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
