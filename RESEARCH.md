# Research notes: muting keywords on X

Researched 2026-11-13. Main source: X Help Center, "How to use advanced muting options"
(https://help.x.com/en/using-x/advanced-x-mute-options).

## How muted words work

- You can mute words, phrases, @usernames, emojis and hashtags.
- Muting is **case-insensitive** ("GTA6" also mutes "gta6").
- Muting a word also mutes its hashtag ("gta6" also mutes "#gta6").
- Punctuation inside a phrase is allowed. Trailing punctuation isn't needed.
- Muting `@account` hides posts that *mention* that account. It does not mute the account itself.
- It works in every language X supports.
- **Entries are added one at a time.** The script will repeat the add flow once per keyword.

## Where muting applies

- Home timeline, Notifications (including push, SMS and email), and replies to posts.
- **Muted posts still show up in Search.** No setting changes this, so the README should warn about it.
- Notifications you opted into for accounts you follow ignore muted words.
- Each entry has two toggles: **Home timeline** and **Notifications**. Turn both on for spoiler protection.
- "From anyone" or "From people you don't follow" only affects notifications. Use "From anyone".

## Duration (TTL)

- Options: **Forever** (the default), **24 hours**, **7 days**, **30 days**. There are no custom durations.
- Recommendation: make it configurable and default to `forever`. Spoilers keep circulating for weeks
  after launch, and the user can unmute later.
- With a timed mute, the script would need to run again to renew it. The script must skip
  words that are already muted, so re-running is safe.

## Web UI path

- Settings → Privacy and safety → Mute and block → Muted words → **+** (add).
  The direct URL is `https://x.com/settings/muted_keywords`, and the add form is at
  `/settings/add_muted_keyword`. Check both against the live site, because X changes its DOM often.

## Is there an API instead?

- The official X API v2 only supports **muting accounts** (`/2/users/:id/muting`).
  It has **no documented endpoint for muted keywords**.
- One blog post describes an undocumented v1.1 `mutes/keywords/create.json` endpoint. It's
  unofficial and fragile, so I don't recommend it.
- So browser automation is the only practical way to script this.

## Login and 2FA

- If the account has 2FA turned on (authenticator app, SMS, security key or push approval), X asks for it at
  every new login. The script should **not** try to get around it, because 2FA is the account's security.
- X may also ask for an **email or phone confirmation code** on logins from new devices or locations,
  or show an "unusual activity" challenge, even with 2FA off. Logins from new automated
  browsers trigger this often.
- Login with only a username and password works only when 2FA is off *and* X shows no challenge.
  Don't rely on it.
- Supported approaches, from most to least robust:
  1. **Manual login in a persistent browser profile.** The script opens a visible browser, the user logs in
     themselves and completes any 2FA, and the session is saved to a local profile folder. Later runs reuse
     it, so no password goes in `.env` at all.
  2. **`.env` username and password, with a pause for codes.** The script fills in the username and password,
     then waits for the user to type any 2FA or confirmation code in the terminal.
  3. **Optional `X_TOTP_SECRET` in `.env`** for users with an authenticator app. The script generates the
     6-digit code with `pyotp`. Storing the TOTP secret next to the password weakens 2FA,
     so make this opt-in and explain the tradeoff.
- CAPTCHAs or Arkose challenges must be completed by the user in the visible browser. Never solve them automatically.

## Terms of service risk (important for users)

- X's automation rules say that **non-API automation, such as scripting the website, may lead to permanent
  account suspension**.
  (https://help.x.com/en/rules-and-policies/x-automation)
- This tool runs one short, low-volume task on the user's own account settings, with no
  posting, scraping or engagement. That's the lowest-risk kind of automation, but it is still
  against the rules. The README must say so plainly, and users run it at their own risk.
- Ways to reduce risk: a visible (non-headless) browser, human-like delays between entries, no repeated
  logins (reuse the session), and only adding keywords that aren't already muted.
- A no-automation fallback: also ship the keyword list as plain text, so users can add the words manually.

## Tooling choice

- **Playwright (Python)** is preferred over Selenium. It has built-in auto-waiting, persistent browser contexts
  for saving the session, and simpler setup (`playwright install chromium`).

## Open questions to check on the live site

- The maximum number of muted words per account. X doesn't publish a limit, so test with the full list.
- The maximum characters per entry. The help page only says "up to the max character count".
- Current selectors for the add-muted-word form and its toggles.
