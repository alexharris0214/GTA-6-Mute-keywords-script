#!/usr/bin/env python3
"""Add GTA 6 spoiler keywords to your X (Twitter) muted words.

Works in your normal browser, where you're already logged in to X. It moves
your real mouse and keyboard (PyAutoGUI), so there is no automated login for
X to block.

  1. Calibrate (first run only): you point at 4 spots on screen; they're saved.
  2. It reads your current muted words and skips ones you already have.
  3. For each keyword: open the add page, paste the word, pick the duration,
     click Save, and check the page moved on (i.e. the save worked).
  4. It re-reads your muted words, retries anything missing once, and reports.

Don't touch the mouse or keyboard while it runs.
EMERGENCY STOP: slam the mouse pointer into any corner of the screen.

Usage:
    python mute_keywords.py               # run (calibrates on first run)
    python mute_keywords.py --recalibrate # pick the 4 spots again
    python mute_keywords.py --dry-run     # list the keywords, touch nothing
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
CALIBRATION_FILE = ROOT / "calibration.json"

MUTED_LIST_URL = "https://x.com/settings/muted_keywords"
ADD_MUTED_URL = "https://x.com/settings/add_muted_keyword"

IS_MAC = sys.platform == "darwin"
MOD = "command" if IS_MAC else "ctrl"

# What each MUTE_DURATION is called on X's website.
DURATION_LABELS = {
    "forever": "Until you unmute the word",
    "24h": "24 hours",
    "7d": "7 days",
    "30d": "30 days",
}

# Spots the user points at during calibration, in the order they're asked for.
SPOTS = {
    "address_bar": "the browser's ADDRESS BAR (where the URL is)",
    "keyword_box": "the 'Enter word or phrase' BOX",
    "duration": "the '{duration}' option (the circle on the right)",
    "save": "the SAVE button",
}


@dataclass
class Config:
    duration: str
    keywords_file: Path
    page_wait: float
    delay_min: float
    delay_max: float


def load_config() -> Config:
    load_dotenv(ROOT / ".env")
    duration = os.getenv("MUTE_DURATION", "30d").strip().lower() or "30d"
    if duration not in DURATION_LABELS:
        sys.exit(f"MUTE_DURATION must be one of {', '.join(DURATION_LABELS)}, got {duration!r}")
    delay_min = float(os.getenv("DELAY_MIN", "1"))
    return Config(
        duration=duration,
        keywords_file=ROOT / os.getenv("KEYWORDS_FILE", "keywords.txt"),
        page_wait=float(os.getenv("PAGE_WAIT", "4")),
        delay_min=delay_min,
        delay_max=max(delay_min, float(os.getenv("DELAY_MAX", "3"))),
    )


# --- Keywords -------------------------------------------------------------------

# "GTA VI" / "GTA 6" as whole words (so "GTA 60" or "GTA VII" don't match).
GTA_NUMBER = re.compile(r"\b(GTA\s*)(VI|6)\b", re.I)


def expand_variants(keyword: str) -> list[str]:
    """Return the keyword plus its other spelling: 'GTA VI X' <-> 'GTA 6 X'."""
    match = GTA_NUMBER.search(keyword)
    if not match:
        return [keyword]
    other = "6" if match.group(2).upper() == "VI" else "VI"
    return [keyword, GTA_NUMBER.sub(lambda m: m.group(1) + other, keyword)]


def normalize(word: str) -> str:
    """X matches case-insensitively and treats 'word' and '#word' the same."""
    return " ".join(word.strip().lower().lstrip("#").split())


def load_keywords(path: Path) -> list[str]:
    if not path.exists():
        sys.exit(f"Keyword file not found: {path}")
    seen: set[str] = set()
    keywords: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        # "# comment" is a comment; "#hashtag" (no space) is a keyword.
        if not line or line == "#" or line.startswith("# "):
            continue
        for variant in expand_variants(line):
            key = normalize(variant)
            if key not in seen:
                seen.add(key)
                keywords.append(variant)
    return keywords


def parse_muted_page(text: str) -> set[str]:
    """Every line of the copied muted-words page, normalized. Extra lines
    (headers, durations) are harmless: we only check keywords against it."""
    return {normalize(line) for line in text.splitlines() if line.strip()}


# --- Mac permission check ---------------------------------------------------------

def mac_has_accessibility() -> bool:
    if not IS_MAC:
        return True
    try:
        import ctypes
        lib = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
        lib.AXIsProcessTrusted.restype = ctypes.c_bool
        return bool(lib.AXIsProcessTrusted())
    except Exception:
        return True  # can't tell; carry on


def require_accessibility() -> None:
    if mac_has_accessibility():
        return
    print("\nmacOS needs to allow this terminal to control the mouse and keyboard:")
    print("  System Settings > Privacy & Security > Accessibility > turn on your terminal app")
    print("  (Terminal, iTerm, VS Code, ...). Then quit and reopen the terminal and run this again.")
    os.system('open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"')
    sys.exit(1)


# --- Screen actions ----------------------------------------------------------------

class Driver:
    def __init__(self, cfg: Config, spots: dict[str, list[int]]):
        import pyautogui
        import pyperclip
        self.gui = pyautogui
        self.clip = pyperclip
        self.cfg = cfg
        self.spots = spots
        pyautogui.FAILSAFE = True  # mouse in a screen corner = stop
        pyautogui.PAUSE = 0.15

    def click(self, spot: str) -> None:
        x, y = self.spots[spot]
        self.gui.moveTo(x, y, duration=random.uniform(0.15, 0.35))
        self.gui.click()

    def keys(self, *keys: str) -> None:
        self.gui.hotkey(*keys, interval=0.05)

    def paste(self, text: str) -> None:
        self.clip.copy(text)
        self.keys(MOD, "v")

    def copy_selection(self) -> str:
        self.clip.copy("")
        self.keys(MOD, "c")
        time.sleep(0.3)
        return self.clip.paste() or ""

    def current_url(self) -> str:
        self.click("address_bar")
        self.keys(MOD, "a")
        url = self.copy_selection()
        self.gui.press("esc")
        return url.strip()

    def go(self, url: str) -> None:
        self.click("address_bar")
        self.keys(MOD, "a")
        self.paste(url)
        self.gui.press("enter")  # focus moves to the page after navigating
        time.sleep(self.cfg.page_wait)

    def read_muted_words(self) -> set[str]:
        """Copy the muted-words page text, scrolling until nothing new loads."""
        self.go(MUTED_LIST_URL)
        found: set[str] = set()
        for _ in range(15):
            self.keys(MOD, "a")
            before = len(found)
            found |= parse_muted_page(self.copy_selection())
            self.gui.press("end")
            time.sleep(1.2)
            if len(found) == before and before:
                break
        self.gui.click(self.spots["address_bar"])  # drop the page selection
        self.gui.press("esc")
        return found

    def add_keyword(self, keyword: str) -> bool:
        """Fill and save the add form. Returns True if the page moved on after Save."""
        self.go(ADD_MUTED_URL)
        self.click("keyword_box")
        self.keys(MOD, "a")
        self.paste(keyword)
        self.click("duration")
        self.click("save")
        time.sleep(self.cfg.page_wait)
        url = self.current_url()
        return "add_muted_keyword" not in url and "muted_keywords" in url


# --- Calibration ------------------------------------------------------------------

def countdown_position(gui, label: str, seconds: int = 5) -> list[int]:
    print(f"\n-> Move the mouse over {label}")
    for s in range(seconds, 0, -1):
        x, y = gui.position()
        print(f"   capturing in {s}s... (mouse at {x}, {y})   ", end="\r", flush=True)
        time.sleep(1)
    x, y = gui.position()
    print(f"   saved ({x}, {y})                              ")
    return [int(x), int(y)]


def calibrate(cfg: Config) -> dict[str, list[int]]:
    import pyautogui
    duration_label = DURATION_LABELS[cfg.duration]
    print("\n=== One-time calibration ===")
    print("Opening X's 'add muted word' page in your normal browser.")
    print("Make sure you're logged in to X there, and put the browser where you can see")
    print("it AND this terminal. Don't move or resize the browser window after this.")
    webbrowser.open(ADD_MUTED_URL)
    input("\nWhen the page has loaded, press Enter here to start... ")
    spots = {}
    for key, label in SPOTS.items():
        spots[key] = countdown_position(pyautogui, label.format(duration=duration_label))
    data = {"duration": cfg.duration, "screen": list(pyautogui.size()), "spots": spots}
    CALIBRATION_FILE.write_text(json.dumps(data, indent=2))
    print(f"\nSaved to {CALIBRATION_FILE.name}. Later runs reuse it (use --recalibrate to redo).")
    return spots


def load_calibration(cfg: Config) -> dict[str, list[int]] | None:
    if not CALIBRATION_FILE.exists():
        return None
    try:
        import pyautogui
        data = json.loads(CALIBRATION_FILE.read_text())
        if data.get("duration") != cfg.duration:
            print("MUTE_DURATION changed since calibration; recalibrating.")
            return None
        if data.get("screen") != list(pyautogui.size()):
            print("Screen size changed since calibration; recalibrating.")
            return None
        spots = data["spots"]
        return spots if set(spots) == set(SPOTS) else None
    except Exception:
        return None


# --- Main ------------------------------------------------------------------------------

def run(cfg: Config, keywords: list[str], spots: dict[str, list[int]], fresh_calibration: bool) -> int:
    d = Driver(cfg, spots)
    saved_clipboard = d.clip.paste()
    try:
        print("\nStarting in 3 seconds. Hands off! (Emergency stop: mouse into a screen corner.)")
        time.sleep(3)

        existing = d.read_muted_words()
        todo = [kw for kw in keywords if normalize(kw) not in existing]
        print(f"{len(keywords) - len(todo)} already muted, {len(todo)} to add.")
        if not todo:
            return 0

        if fresh_calibration:
            # One safety check after calibrating: fill the first word, but let the user Save.
            first = todo[0]
            d.go(ADD_MUTED_URL)
            d.click("keyword_box")
            d.keys(MOD, "a")
            d.paste(first)
            d.click("duration")
            print(f"\nCheck the browser: '{first}' is typed in, '{DURATION_LABELS[cfg.duration]}' is")
            print("selected, and Home timeline / Notifications / From anyone look right.")
            if input("Look right? The script will click Save and do the rest. [Y/n]: ").strip().lower().startswith("n"):
                print("Stopped. Fix the settings on X or run with --recalibrate.")
                return 1
            d.click("save")
            time.sleep(cfg.page_wait)
            todo = todo[1:]

        failed = []
        for i, kw in enumerate(todo, 1):
            ok = d.add_keyword(kw)
            print(f"  [{i}/{len(todo)}] {'muted' if ok else 'NOT SAVED'}: {kw}")
            if not ok:
                failed.append(kw)
            time.sleep(random.uniform(cfg.delay_min, cfg.delay_max))

        # Verify against the real list and retry anything missing once.
        print("\nChecking your muted words list...")
        muted = d.read_muted_words()
        missing = [kw for kw in keywords if normalize(kw) not in muted]
        if missing:
            print(f"{len(missing)} missing; retrying once.")
            for kw in missing:
                d.add_keyword(kw)
                time.sleep(random.uniform(cfg.delay_min, cfg.delay_max))
            muted = d.read_muted_words()
            missing = [kw for kw in keywords if normalize(kw) not in muted]

        print(f"\nDone. {len(keywords) - len(missing)}/{len(keywords)} keywords are muted.")
        if missing:
            print("Still missing (add by hand at x.com/settings/muted_keywords, or run again):")
            for kw in missing:
                print(f"  {kw}")
            return 1
        return 0
    except Exception as exc:
        if type(exc).__name__ == "FailSafeException":
            print("\nStopped (mouse moved to a screen corner).")
            return 1
        raise
    finally:
        try:
            d.clip.copy(saved_clipboard)
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="list the keywords and touch nothing")
    parser.add_argument("--recalibrate", action="store_true", help="pick the 4 screen spots again")
    args = parser.parse_args()

    cfg = load_config()
    keywords = load_keywords(cfg.keywords_file)
    print(f"{len(keywords)} keywords from {cfg.keywords_file.name} | duration: "
          f"{cfg.duration} ('{DURATION_LABELS[cfg.duration]}')")

    if args.dry_run:
        for kw in keywords:
            print(f"  would mute: {kw}")
        return 0

    require_accessibility()
    spots = None if args.recalibrate else load_calibration(cfg)
    fresh = spots is None
    if fresh:
        spots = calibrate(cfg)
    else:
        print("Using saved screen positions. Opening X in your browser...")
        webbrowser.open(MUTED_LIST_URL)
        time.sleep(cfg.page_wait)
    return run(cfg, keywords, spots, fresh)


if __name__ == "__main__":
    sys.exit(main())
