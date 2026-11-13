# GTA 6 Mute Keywords Script

Avoid GTA 6 spoilers on X (Twitter). This script opens a browser, logs in to your
account, and adds a list of GTA 6 keywords to your **muted words**. After that,
posts that mention them stop showing up in your Home timeline, notifications and replies.

> **Read this first: account risk.** X's [automation rules](https://help.x.com/en/rules-and-policies/x-automation)
> say that scripting the website, instead of using the official API, can get an
> account suspended. X's API has no endpoint for muted words, so this tool has to
> use browser automation. It keeps the risk low: one short run, a visible
> browser, random pauses, and no posting or scraping. **But use it at your own
> risk.** If you'd rather not, copy the words from [`keywords.txt`](keywords.txt)
> into **Settings → Privacy and safety → Mute and block → Muted words** by hand.

## What muting does (and doesn't do)

- It hides matching posts from your **Home timeline**, **notifications** and **replies**.
- It's case-insensitive, and muting `GTA6` also mutes `#GTA6`.
- **Muted posts still appear in Search, trending lists and in DMs.** Avoid those until you've played.
- Notifications you turned on for specific accounts ignore muted words.

## Setup

You need Python 3.9 or newer.

```bash
git clone https://github.com/alexharris0214/GTA-6-Mute-keywords-script.git
cd GTA-6-Mute-keywords-script
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Then edit `.env` (all optional):

| Setting | Default | Meaning |
|---|---|---|
| `X_USERNAME`, `X_PASSWORD` | blank | Leave blank to log in by hand in the browser (recommended). |
| `X_TOTP_SECRET` | blank | Your authenticator app's secret key, if you want the script to type 2FA codes. Opt-in: storing it next to your password weakens 2FA. |
| `MUTE_DURATION` | `forever` | `forever`, `24h`, `7d` or `30d` (the only options X offers). |
| `MUTE_HOME_TIMELINE` | `true` | Mute in the Home timeline. |
| `MUTE_NOTIFICATIONS` | `true` | Mute in notifications. |
| `MUTE_FROM` | `anyone` | For notifications: `anyone` or `not_following`. |
| `DELAY_MIN`, `DELAY_MAX` | `2`, `5` | Random seconds between keywords. |

Edit [`keywords.txt`](keywords.txt) to add or remove words, one per line.
Lines starting with `# ` (hash and space) are comments. Any phrase with
`GTA VI` or `GTA 6` is muted in both spellings automatically, so you only need
to write one. The default list targets story spoilers, not GTA 6 news in general.
Uncomment the lines at the bottom to hide all GTA 6 posts.

## Run it

```bash
python mute_keywords.py --dry-run   # show the plan, no browser
python mute_keywords.py             # add the keywords
```

The first run opens Chrome:

- **No credentials in `.env`:** log in yourself in that window, including any 2FA.
  The script waits up to 5 minutes, then carries on.
- **Credentials in `.env`:** the script fills them in. If X asks for a 2FA or
  email code, type it in the terminal (or set `X_TOTP_SECRET`). If X shows
  anything it doesn't recognise, such as a CAPTCHA or a push approval, finish
  it in the browser and the script continues.

Your session is saved in `.browser-profile/`, so later runs skip the login.
Running it again is safe: words that are already muted are skipped. With a
timed `MUTE_DURATION`, run it again to renew the mutes.

`python mute_keywords.py --login-only` just logs in and saves the session.

## About 2FA

The script **does not get around 2FA**, and it shouldn't. If your account has 2FA,
you approve each new login yourself, either in the browser or by typing the code.
Even without 2FA, X often asks for an email code when an account logs in from a
new browser, so plan to be at the keyboard for the first run.

## Troubleshooting

- **A keyword says FAILED:** X probably changed its page layout. The URLs and
  selectors are at the top of [`mute_keywords.py`](mute_keywords.py). Failed
  words are listed at the end so you can add them by hand.
- **Logged out unexpectedly:** delete `.browser-profile/` and run again.

## Files

- `mute_keywords.py`: the script.
- `keywords.txt`: the words to mute.
- `.env.example`: settings template (copy to `.env`, which is git-ignored).
- `RESEARCH.md`: notes on how X muting, login and 2FA work.
