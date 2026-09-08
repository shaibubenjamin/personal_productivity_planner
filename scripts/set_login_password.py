"""Run this yourself, locally: python scripts/set_login_password.py

Prompts for a username/password right here in your own terminal (hidden
input) and writes the salted hash to .env - the plaintext never leaves
this machine, and never needs to be typed into any chat.
"""

import getpass
import hashlib
import os
import secrets

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(REPO_ROOT, ".env")


def main() -> None:
    username = input("Username (e.g. your email): ").strip()
    password = getpass.getpass("New password (hidden as you type): ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords did not match - nothing was changed.")
        return
    if len(password) < 8:
        print("Password should be at least 8 characters - nothing was changed.")
        return

    salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((salt + password).encode()).hexdigest()

    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            lines = [l for l in f if not l.startswith("PEOS_AUTH_")]

    with open(ENV_PATH, "w") as f:
        f.writelines(lines)
        f.write(f"\nPEOS_AUTH_USERNAME={username}\n")
        f.write(f"PEOS_AUTH_PASSWORD_SALT={salt}\n")
        f.write(f"PEOS_AUTH_PASSWORD_HASH={pw_hash}\n")

    print("Done. .env updated. Restart the Streamlit app for it to take effect.")
    print("Remember: paste the SALT and HASH lines (not the password) into")
    print("Streamlit Cloud secrets when you deploy - see DEPLOY.txt.")


if __name__ == "__main__":
    main()
