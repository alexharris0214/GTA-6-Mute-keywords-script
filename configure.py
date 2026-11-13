#!/usr/bin/env python3
"""Interactive settings for the GTA 6 mute script. Writes .env, then offers to run.

Called by setup.sh (Mac/Linux) and setup.bat (Windows); you can also run it
directly any time to change your settings:  python configure.py
"""

from __future__ import annotations

import getpass
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".env"
EXAMPLE = ROOT / ".env.example"
DURATIONS = ("forever", "24h", "7d", "30d")


def ask(question: str, default: str = "") -> str:
    try:
        reply = input(f"{question} [{default}]: ").strip()
    except EOFError:
        reply = ""
    return reply or default


def yes_no(question: str, default: bool) -> bool:
    hint = "Y/n" if default else "y/N"
    reply = ask(question, hint)
    if reply == hint:
        return default
    return reply.lower().startswith("y")


def secret(question: str) -> str:
    try:
        return getpass.getpass(f"{question} (hidden): ")
    except EOFError:
        return ""


def quote(value: str) -> str:
    """Single-quote a value for .env, escaping backslashes and quotes."""
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def write_env(values: dict[str, str]) -> None:
    lines = []
    for line in EXAMPLE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Z_]+)=", line)
        if m and m.group(1) in values:
            line = f"{m.group(1)}={quote(values[m.group(1)])}"
        lines.append(line)
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if os.name != "nt":
        ENV.chmod(0o600)


def collect_settings() -> dict[str, str]:
    values = {"X_USERNAME": "", "X_PASSWORD": "", "X_TOTP_SECRET": ""}

    print("\nHow do you want to log in to X?")
    print("  1) By hand in the browser window (recommended, nothing is saved to disk)")
    print("  2) Save my username and password in .env")
    if ask("Choose 1 or 2", "1") == "2":
        values["X_USERNAME"] = ask("X username, email or phone")
        values["X_PASSWORD"] = secret("X password")
        print("\nIf your account uses an authenticator app for 2FA, the script can type the")
        print("codes for you using the app's secret key. This is optional and weakens 2FA,")
        print("because the key would sit next to your password. Otherwise you type codes yourself.")
        if yes_no("Save an authenticator secret key?", False):
            values["X_TOTP_SECRET"] = secret("Authenticator secret key").replace(" ", "")

    print(f"\nHow long should the mutes last?  {' | '.join(DURATIONS)}")
    print("(forever = \"Until you unmute the word\" on X)")
    duration = ask("Duration", "30d").lower()
    if duration not in DURATIONS:
        print("Unknown value, using 30d.")
        duration = "30d"
    values["MUTE_DURATION"] = duration
    return values


def main() -> int:
    print("\n== Settings ==")
    if ENV.exists() and not yes_no(".env already exists. Replace it with new answers?", False):
        print("Keeping your existing .env.")
    else:
        write_env(collect_settings())
        print("Saved settings to .env.")

    script = [sys.executable, str(ROOT / "mute_keywords.py")]
    print("\nKeywords to mute are in keywords.txt. Edit it any time.")
    if yes_no("Show the keywords that will be muted (dry run)?", True):
        subprocess.call(script + ["--dry-run"])
    if yes_no("\nRun it now and mute the keywords on X?", False):
        return subprocess.call(script)
    run_cmd = r".venv\Scripts\python mute_keywords.py" if os.name == "nt" else ".venv/bin/python mute_keywords.py"
    print(f"\nRun it later with:  {run_cmd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
