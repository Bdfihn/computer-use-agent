# Lessons Learned

## Use Steel's computer API for all input actions, not Playwright directly

Playwright's `page.mouse.click()` and `page.keyboard.press()` do not work with Steel's headful sessions. Input must go through `steel.sessions.computer(session_id, action=..., ...)`. Playwright is still needed to connect via CDP and call `context.new_page()` (which makes the session appear in the live viewer), but all mouse/keyboard/scroll actions use the Steel computer API. Key names are passed as a list: `keys=["Control", "l"]`, not a joined string.

## `interactive=true` is required for the Steel computer API to work

`interactive=false` blocks all remote input including the Steel computer API. The agent uses `sessions.computer()` to send actions — this requires `interactive=true` on the debug URL. Embed with `${debugUrl}?interactive=true`.

## Steel debug URL: use `debug_url`, not `session_viewer_url`

`session_viewer_url` points to the Steel dashboard and cannot be embedded (X-Frame-Options blocks it). `debug_url` is the embeddable URL — streams via WebRTC at 25 fps. Always use `session.debug_url`.

## Key names for Steel computer API: list of strings, normalized from xdotool aliases

Claude's `computer_20251124` tool emits xdotool-style combos like `"ctrl+l"`. Steel's `press_key` expects a list: `["Control", "l"]`. Normalize with a map (`ctrl→Control`, `super→Meta`, `return→Enter`, etc.) and split on `+` before passing to the API.

## Claude needs a system prompt describing the browser environment

Without a system prompt, Claude assumes a generic desktop OS and tries xdotool shortcuts, opens terminals, etc. The system prompt must state: Chrome on Linux, navigate by focusing the address bar with `Control+l`, type URL, press `Enter` — and that a blank screen at startup is normal.

## Always create a new page on session start — don't reuse existing pages

Use `context.new_page()`, not `context.pages[0]`. Reusing the initial page causes the session to not be recorded correctly in the Steel live viewer.

## Restore `api_timeout=3600000` on session create

Steel's default session timeout is 5 minutes. Without `api_timeout=3600000`, sessions die mid-task. Always pass it explicitly.
