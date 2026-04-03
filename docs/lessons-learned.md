# Lessons Learned

## Key names: Claude uses xdotool format, Playwright expects its own format

Claude's `computer_20251124` tool emits xdotool-style key names (`ctrl`, `super`, `return`). Playwright rejects these with "Unknown key". Map them in `browser.py` before passing to `page.keyboard.press()`. Common mappings: `ctrl→Control`, `super→Meta`, `return→Enter`, `up→ArrowUp`. Also tell Claude via system prompt to use Playwright format directly, which reduces the failure surface further.

## Claude needs a system prompt describing the browser environment

Without a system prompt, Claude assumes it's on a generic desktop OS and tries things like `ctrl+End` to scroll or `super` to open a launcher. The system prompt must explicitly state: Chrome on Linux, navigate by clicking the address bar, use Playwright key names, don't try to open terminals.

## Steel session URLs — use `debug_url`, not `session_viewer_url`

Steel sessions expose two URL fields. `session_viewer_url` points to the Steel dashboard viewer and cannot be embedded in an iframe (X-Frame-Options blocks it). `debug_url` is the correct field for embedding — it streams via WebRTC at 25 fps and accepts `?interactive=true` to enable remote input. Always use `session.debug_url` when embedding a session in any UI context.
