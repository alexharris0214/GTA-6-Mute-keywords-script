#!/usr/bin/env python3
"""Setup questions for the GTA 6 mute script. Writes .env, then offers to run.

Called by setup.sh (Mac/Linux) and setup.bat (Windows). Run it again any time
to change settings:  python configure.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".env"
EXAMPLE = ROOT / ".env.example"
DURATIONS = ("30d", "7d", "24h", "forever")


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


def write_env(values: dict[str, str]) -> None:
    lines = []
    for line in EXAMPLE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Z_]+)=", line)
        if m and m.group(1) in values:
            line = f"{m.group(1)}={values[m.group(1)]}"
        lines.append(line)
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    print("\n== Settings ==")
    if ENV.exists() and not yes_no(".env already exists. Replace it?", False):
        print("Keeping your existing .env.")
    else:
        print(f"How long should the mutes last?  {' | '.join(DURATIONS)}")
        print('(forever = "Until you unmute the word" on X)')
        duration = ask("Duration", "30d").lower()
        if duration not in DURATIONS:
            print("Unknown value, using 30d.")
            duration = "30d"
        write_env({"MUTE_DURATION": duration})
        print("Saved settings to .env.")

    print("\nHow it works: the script uses YOUR normal browser (log in to X there first)")
    print("and moves your mouse and keyboard for you. The first run asks you to point at")
    print("4 spots on the X page; after that it runs on its own. Don't touch anything while")
    print("it runs. Emergency stop: move the mouse into a corner of the screen.")
    if sys.platform == "darwin":
        print("\nOn a Mac, your terminal app needs Accessibility permission (System Settings >")
        print("Privacy & Security > Accessibility). The script opens that page if it's missing.")

    run_cmd = r".venv\Scripts\python mute_keywords.py" if os.name == "nt" else ".venv/bin/python mute_keywords.py"
    if yes_no("\nRun it now?", True):
        return subprocess.call([sys.executable, str(ROOT / "mute_keywords.py")])
    print(f"\nRun it later with:  {run_cmd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
