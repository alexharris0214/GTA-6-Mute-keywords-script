# GTA 6 Mute Keywords Script

Avoid GTA 6 spoilers on X (Twitter). This script adds a list of GTA 6 spoiler
keywords to your **muted words**. After that, posts that mention them stop
showing up in your Home timeline, notifications and replies.

It works in **your normal browser, where you're already logged in**. It moves
your mouse and keyboard for you (with [PyAutoGUI](https://pyautogui.readthedocs.io/)),
so there's no password to enter and no automated login for X to block.

> **Account risk.** X's [automation rules](https://help.x.com/en/rules-and-policies/x-automation)
> discourage scripting the website. This script makes the same few clicks you
> would, at human speed, on your own settings page, with no login, posting or
> scraping. That's about as low-risk as automation gets, but **use it at your own
> risk.** If you'd rather not, add the words from [`keywords.txt`](keywords.txt)
> by hand under **Settings → Privacy and safety → Mute and block → Muted words**.

## What muting does (and doesn't do)

- It hides matching posts from your **Home timeline**, **notifications** and **replies**.
- It's case-insensitive, and muting `GTA6` also mutes `#GTA6`.
- **Muted posts still appear in Search, trending lists and DMs.** Avoid those until you've played.
- Notifications you turned on for specific accounts ignore muted words.

## Quick start

You need **Python 3.9 or newer** ([download](https://www.python.org/downloads/);
on Windows, tick **"Add python.exe to PATH"** in the installer) and **Git**
(or use **Code → Download ZIP** on GitHub and unzip it).

**Before you start:** log in to X in your normal browser.

### Mac

Open **Terminal** and run:

```bash
git clone https://github.com/alexharris0214/GTA-6-Mute-keywords-script.git
cd GTA-6-Mute-keywords-script
bash setup.sh
```

The first time, macOS has to let your terminal control the mouse. The script
opens **System Settings → Privacy & Security → Accessibility** for you: turn on
your terminal app (Terminal, iTerm, VS Code...), quit and reopen the terminal, then run:

```bash
.venv/bin/python mute_keywords.py
```

### Windows

Open **Command Prompt** or **PowerShell** and run (or double-click `setup.bat`
in the downloaded folder):

```bat
git clone https://github.com/alexharris0214/GTA-6-Mute-keywords-script.git
cd GTA-6-Mute-keywords-script
setup.bat
```

To run it again later:

```bat
.venv\Scripts\python mute_keywords.py
```

## What happens when it runs

**First run: about 30 seconds of your help.**

1. X's "add muted word" page opens in your browser. Arrange the windows so you
   can see the browser **and** the terminal, then press Enter in the terminal.
2. The terminal asks you to point at 4 spots, one at a time: the **address
   bar**, the **word box**, the **30 days** option and the **Save** button.
   Hover over each one; it's captured after a 5-second countdown.
3. The script fills in the first keyword and asks you to check the page.
   Make sure **Home timeline** is ticked, **Notifications** is on, and **From
   anyone** is selected. These are X's defaults, and the script doesn't change them.
   Press Enter.
4. **Hands off.** It adds the rest by itself. Then it re-reads your muted
   words list, retries anything missing, and prints a summary.

**Later runs: fully automatic.** The positions are saved in `calibration.json`.
Words you already have are skipped, so re-running is safe. With a 30-day mute,
run it again after a month to renew the mutes.

**Emergency stop:** move the mouse into any corner of the screen.

Don't move or resize the browser window between runs. If you do, or if clicks
land in the wrong place, run `mute_keywords.py --recalibrate`.

## Settings

Setup writes `.env` for you. You can also edit it by hand:

| Setting | Default | Meaning |
|---|---|---|
| `MUTE_DURATION` | `30d` | `30d`, `7d`, `24h` or `forever` (X calls it "Until you unmute the word"). |
| `PAGE_WAIT` | `4` | Seconds to wait for X pages to load. Raise it on a slow connection. |
| `DELAY_MIN`, `DELAY_MAX` | `1`, `3` | Random pause between keywords, in seconds. |
| `KEYWORDS_FILE` | `keywords.txt` | Which keyword list to use. |

Edit [`keywords.txt`](keywords.txt) to add or remove words, one per line.
Lines starting with `# ` (hash and space) are comments. Any phrase with
`GTA VI` or `GTA 6` is muted in both spellings automatically, so you only need
to write one. The default list targets story spoilers, not GTA 6 news in general.
Uncomment the lines at the bottom to hide all GTA 6 posts.

## Commands

Use `.venv/bin/python` on Mac or `.venv\Scripts\python` on Windows:

| Command | What it does |
|---|---|
| `mute_keywords.py` | Adds the keywords (calibrates on the first run). |
| `mute_keywords.py --recalibrate` | Picks the 4 screen spots again. |
| `mute_keywords.py --dry-run` | Lists the keywords. Touches nothing. |

## Troubleshooting

- **Nothing happens on a Mac:** the terminal app lacks Accessibility permission.
  Turn it on, then quit and reopen the terminal.
- **Clicks land in the wrong place:** run with `--recalibrate`, and keep the
  browser window where it was.
- **Keywords show `NOT SAVED`:** the page was probably slow. Set `PAGE_WAIT=6`
  in `.env` and run again; already-muted words are skipped.
- **X changed its settings page:** add the missing words by hand. The script
  lists them at the end.

## Files

- `mute_keywords.py`: the script.
- `keywords.txt`: the words to mute.
- `setup.sh` / `setup.bat`: one-step setup for Mac / Windows.
- `configure.py`: the setup questions (writes `.env`).
- `.env.example`: settings template (setup copies it to `.env`, which is git-ignored).
- `RESEARCH.md`: notes on how X muting, login and automation work.
