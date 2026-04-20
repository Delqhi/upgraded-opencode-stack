# SKILL: new-google-login

> **Description:** Robust Google Account Login via Chrome Native Profile Menu + CDP Attach
> **Version:** 1.1.0
> **Scope:** opencode

## What this skill does
This skill provides an extremely robust way to log into Google accounts in Chrome.

- **Standalone mode:** macOS AppleScript + keyboard emulation against the native Chrome profile menu.
- **Attach mode:** direct CDP attach to an already-running Chrome debug session (used by the Token-Refresh-Service).

It avoids fragile Google DOM selectors and handles the common blockers: search-engine popup, cookie consent, sync dialogs, and nodriver-launched Chrome sessions.

## Usage
When an agent needs to log into a Google account, they can invoke this skill to execute the robust login flow.

```bash
python3 ~/.config/opencode/skills/new-google-login/login.py --email "email@domain.com" --password "pass123" --port 7654 --profile-dir "/tmp/fresh_profile"
python3 ~/.config/opencode/skills/new-google-login/login.py --email "email@domain.com" --password "pass123" --port 7654 --profile-dir "/tmp/fresh_profile" --attach
```

## How it works

### Standalone flow
1. Launches Chrome on `about:blank`.
2. Uses `--disable-search-engine-choice-screen` to kill the EU popup block.
3. Focuses the address bar (`Cmd+L`), then uses `Tab` and `Space` to open the native profile menu.
4. Uses `Tab` and `Space` to click the "Sign in" / "Turn on sync" button.
5. In the Google Login window, it types email, submits, types password, submits.

### Attach flow
1. Reuses the nodriver-launched Chrome session on the given debug port.
2. Attaches via CDP and opens `accounts.google.com/ServiceLogin` directly.
3. Types email/password through Chrome DevTools instead of AppleScript.
4. Returns success/failure to the Token-Refresh-Service without needing a Chrome restart.

## Robust Fallbacks implemented
- Avoids cookie consent entirely by starting on `about:blank`
- Includes multiple Tab cycles in case UI extensions are present
- Contains timing fallbacks
