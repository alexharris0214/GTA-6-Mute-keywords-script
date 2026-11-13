#!/usr/bin/env python3
"""Add GTA 6 spoiler keywords to your X (Twitter) muted words.

Opens a visible browser, makes sure you're logged in (by hand, or with the
credentials in .env), reads your current muted words, and adds every keyword
from keywords.txt that isn't muted yet.

Usage:
    python mute_keywords.py             # add missing keywords
    python mute_keywords.py --dry-run   # show what would happen, no browser
    python mute_keywords.py --login-only
"""

from __future__ import annotations

import argparse
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent

# --- X URLs and selectors ---------------------------------------------------
# X changes its markup often. If something stops working, these are the only
# values that should need updating.
HOME_URL = "https://x.com/home"
LOGIN_URL = "https://x.com/i/flow/login"
MUTED_LIST_URL = "https://x.com/settings/muted_keywords"
ADD_MUTED_URL = "https://x.com/settings/add_muted_keyword"

SEL_LOGGED_IN = '[data-testid="SideNav_AccountSwitcher_Button"]'
SEL_USERNAME = 'input[autocomplete="username"]'
SEL_PASSWORD = 'input[name="password"]'
SEL_TEXT_CHALLENGE = 'input[data-testid="ocfEnterTextTextInput"]'
SEL_PRIMARY = '[data-testid="primaryColumn"]'
SEL_KEYWORD_INPUT = 'input[name="keyword"]'

DURATION_LABELS = {
    # The website labels "forever" as "Until you unmute the word".
    "forever": re.compile(r"until you unmute|forever", re.I),
    "24h": re.compile(r"24 hours", re.I),
    "7d": re.compile(r"7 days", re.I),
    "30d": re.compile(r"30 days", re.I),
}
FROM_LABELS = {
    "anyone": re.compile(r"from anyone", re.I),
    "not_following": re.compile(r"people you don.t follow", re.I),
}


@dataclass
class Config:
    username: str
    password: str
    totp_secret: str
    duration: str
    home_timeline: bool
    notifications: bool
    mute_from: str
    keywords_file: Path
    profile_dir: Path
    delay_min: float
    delay_max: float


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def load_config() -> Config:
    load_dotenv(ROOT / ".env")
    duration = os.getenv("MUTE_DURATION", "30d").strip().lower() or "30d"
    if duration not in DURATION_LABELS:
        sys.exit(f"MUTE_DURATION must be one of {', '.join(DURATION_LABELS)}, got {duration!r}")
    mute_from = os.getenv("MUTE_FROM", "anyone").strip().lower() or "anyone"
    if mute_from not in FROM_LABELS:
        sys.exit(f"MUTE_FROM must be one of {', '.join(FROM_LABELS)}, got {mute_from!r}")
    cfg = Config(
        username=os.getenv("X_USERNAME", "").strip(),
        password=os.getenv("X_PASSWORD", ""),
        totp_secret=os.getenv("X_TOTP_SECRET", "").replace(" ", ""),
        duration=duration,
        home_timeline=env_bool("MUTE_HOME_TIMELINE", True),
        notifications=env_bool("MUTE_NOTIFICATIONS", True),
        mute_from=mute_from,
        keywords_file=ROOT / os.getenv("KEYWORDS_FILE", "keywords.txt"),
        profile_dir=ROOT / os.getenv("PROFILE_DIR", ".browser-profile"),
        delay_min=float(os.getenv("DELAY_MIN", "2")),
        delay_max=float(os.getenv("DELAY_MAX", "5")),
    )
    if not (cfg.home_timeline or cfg.notifications):
        sys.exit("At least one of MUTE_HOME_TIMELINE or MUTE_NOTIFICATIONS must be true.")
    if cfg.delay_max < cfg.delay_min:
        cfg.delay_max = cfg.delay_min
    return cfg


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


# "GTA VI" / "GTA 6" as whole words (so "GTA 60" or "GTA VII" don't match).
GTA_NUMBER = re.compile(r"\b(GTA\s*)(VI|6)\b", re.I)


def expand_variants(keyword: str) -> list[str]:
    """Return the keyword plus its other spelling: 'GTA VI X' <-> 'GTA 6 X'."""
    match = GTA_NUMBER.search(keyword)
    if not match:
        return [keyword]
    other = "6" if match.group(2).upper() == "VI" else "VI"
    swapped = GTA_NUMBER.sub(lambda m: m.group(1) + other, keyword)
    return [keyword, swapped]


def normalize(word: str) -> str:
    """X matches case-insensitively and treats 'word' and '#word' the same."""
    return word.strip().lower().lstrip("#")


def pause(cfg: Config) -> None:
    time.sleep(random.uniform(cfg.delay_min, cfg.delay_max))


# --- Login --------------------------------------------------------------------

def is_logged_in(page) -> bool:
    page.goto(HOME_URL, wait_until="domcontentloaded")
    try:
        page.wait_for_selector(SEL_LOGGED_IN, timeout=8000)
        return True
    except Exception:
        return False


def wait_for_manual_login(page) -> None:
    print("\nPlease log in to X in the browser window (complete any 2FA or checks there).")
    print("Waiting up to 5 minutes...")
    page.wait_for_selector(SEL_LOGGED_IN, timeout=5 * 60 * 1000)


def ask_code(prompt: str) -> str:
    return input(f"{prompt}: ").strip()


def answer_challenge(page, cfg: Config) -> None:
    """Handle the text prompts X can show after the username or password step."""
    box = page.locator(SEL_TEXT_CHALLENGE)
    if not box.count():
        return
    prompt_text = page.locator(SEL_PRIMARY).first.inner_text() if page.locator(SEL_PRIMARY).count() else ""
    prompt_text = (prompt_text or page.inner_text("body")).lower()

    if "phone" in prompt_text and "username" in prompt_text:
        answer = cfg.username or ask_code("X asks for your phone number or username")
    elif cfg.totp_secret and ("authentication" in prompt_text or "code" in prompt_text):
        import pyotp
        answer = pyotp.TOTP(cfg.totp_secret).now()
        print("Entering 2FA code from X_TOTP_SECRET.")
    else:
        answer = ask_code("X asks for a verification / 2FA code (check your app, SMS or email)")
    box.fill(answer)
    page.keyboard.press("Enter")
    page.wait_for_timeout(3000)


def login(page, cfg: Config) -> None:
    if is_logged_in(page):
        print("Already logged in (saved session).")
        return
    if not (cfg.username and cfg.password):
        page.goto(LOGIN_URL)
        wait_for_manual_login(page)
        print("Logged in.")
        return

    print("Logging in with the credentials from .env...")
    page.goto(LOGIN_URL)
    try:
        page.fill(SEL_USERNAME, cfg.username, timeout=20000)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2500)
        answer_challenge(page, cfg)  # "enter your phone or username" check
        page.fill(SEL_PASSWORD, cfg.password, timeout=20000)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
        for _ in range(2):  # 2FA, then possibly an email confirmation code
            answer_challenge(page, cfg)
        page.wait_for_selector(SEL_LOGGED_IN, timeout=20000)
        print("Logged in.")
    except Exception:
        # Unknown screen (CAPTCHA, push approval, changed layout...): hand over.
        print("Automatic login didn't finish. Complete it yourself in the browser.")
        wait_for_manual_login(page)
        print("Logged in.")


# --- Muting -------------------------------------------------------------------

def current_muted(page) -> set[str]:
    page.goto(MUTED_LIST_URL, wait_until="domcontentloaded")
    page.wait_for_selector(SEL_PRIMARY, timeout=20000)
    page.wait_for_timeout(2500)
    # Scroll so long lists fully load.
    last = -1
    for _ in range(30):
        height = page.evaluate("document.body.scrollHeight")
        if height == last:
            break
        last = height
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(800)
    text = page.locator(SEL_PRIMARY).first.inner_text()
    return {normalize(line) for line in text.splitlines() if line.strip()}


def set_checkbox(page, label: str, wanted: bool) -> None:
    """Set a checkbox or toggle switch (Home timeline is a checkbox,
    Notifications is a switch on the website)."""
    name = re.compile(label, re.I)
    for role in ("checkbox", "switch"):
        box = page.get_by_role(role, name=name)
        if box.count():
            if box.first.is_checked() != wanted:
                box.first.click()
            return
    raise RuntimeError(f"couldn't find the '{label}' setting on the page")


def pick_radio(page, pattern: re.Pattern) -> None:
    radio = page.get_by_role("radio", name=pattern)
    if radio.count():
        radio.first.check()
    else:
        page.get_by_text(pattern).first.click()


def add_keyword(page, cfg: Config, keyword: str) -> None:
    page.goto(ADD_MUTED_URL, wait_until="domcontentloaded")
    field = page.locator(SEL_KEYWORD_INPUT)
    if not field.count():
        field = page.locator(f"{SEL_PRIMARY} input[type='text']")
    field.first.wait_for(timeout=20000)
    field.first.fill(keyword)

    set_checkbox(page, "home timeline", cfg.home_timeline)
    set_checkbox(page, "notifications", cfg.notifications)
    if cfg.notifications:
        pick_radio(page, FROM_LABELS[cfg.mute_from])
    pick_radio(page, DURATION_LABELS[cfg.duration])

    save = page.get_by_role("button", name=re.compile(r"^save$", re.I))
    save.first.click()
    page.wait_for_url(re.compile(r"/settings/muted_keywords"), timeout=15000)


# --- Main -----------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="print the plan without opening a browser")
    parser.add_argument("--login-only", action="store_true", help="log in, save the session and stop")
    args = parser.parse_args()

    cfg = load_config()
    keywords = load_keywords(cfg.keywords_file)

    print(f"{len(keywords)} keywords from {cfg.keywords_file.name}")
    where = [n for n, on in (("Home timeline", cfg.home_timeline), ("Notifications", cfg.notifications)) if on]
    print(f"Mute in: {', '.join(where)} | from: {cfg.mute_from} | duration: {cfg.duration}")
    print("Login: " + ("credentials from .env" if cfg.username and cfg.password else "manual, in the browser")
          + (" + TOTP from .env" if cfg.totp_secret else ""))

    if args.dry_run:
        for kw in keywords:
            print(f"  would mute: {kw}")
        return 0

    from playwright.sync_api import sync_playwright

    added, failed = [], []
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(cfg.profile_dir), headless=False, viewport={"width": 1280, "height": 900}
        )
        page = context.pages[0] if context.pages else context.new_page()
        try:
            login(page, cfg)
            if args.login_only:
                print(f"Session saved to {cfg.profile_dir.name}/.")
                return 0

            existing = current_muted(page)
            todo = [kw for kw in keywords if normalize(kw) not in existing]
            print(f"{len(keywords) - len(todo)} already muted, {len(todo)} to add.")

            for i, kw in enumerate(todo, 1):
                try:
                    add_keyword(page, cfg, kw)
                    added.append(kw)
                    print(f"  [{i}/{len(todo)}] muted: {kw}")
                except Exception as exc:  # keep going; report at the end
                    failed.append(kw)
                    print(f"  [{i}/{len(todo)}] FAILED: {kw} ({type(exc).__name__}: {str(exc).splitlines()[0]})")
                pause(cfg)
        finally:
            context.close()

    print(f"\nDone. Added {len(added)}, failed {len(failed)}.")
    if failed:
        print("Failed keywords (add these by hand at x.com/settings/muted_keywords):")
        for kw in failed:
            print(f"  {kw}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
