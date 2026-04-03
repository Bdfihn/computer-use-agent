# Lessons Learned

## Steel debug URL: always embed with `?interactive=false`

`interactive=true` is the default, meaning the embedded iframe gives live mouse/keyboard control into the same browser the agent is controlling. With both the user's browser and Playwright acting on the same page simultaneously, actions interfere — clicks from mouse-overs in the iframe fight the agent's Playwright actions. Always embed with `?interactive=false`. The user is the observer; the agent is the actor. Intervention goes through chat.

## Screenshots must wait for page load: add `wait_for_load_state` before each screenshot

After actions that trigger navigation (pressing Enter in address bar, clicking links), Playwright's `page.screenshot()` fires immediately and captures a blank or mid-load page. Wrap `await page.wait_for_load_state("domcontentloaded", timeout=3000)` in a try/except before every screenshot in `execute_action`. The timeout prevents hanging on non-navigation actions.

## Key names: Claude uses xdotool format, Playwright expects its own format

Claude's `computer_20251124` tool emits xdotool-style key names (`ctrl`, `super`, `return`). Playwright rejects these with "Unknown key". Map them in `browser.py` before passing to `page.keyboard.press()`. Common mappings: `ctrl→Control`, `super→Meta`, `return→Enter`, `up→ArrowUp`. Also tell Claude via system prompt to use Playwright format directly, which reduces the failure surface further.

## Claude needs a system prompt describing the browser environment

Without a system prompt, Claude assumes it's on a generic desktop OS and tries things like `ctrl+End` to scroll or `super` to open a launcher. The system prompt must explicitly state: Chrome on Linux, navigate by clicking the address bar, use Playwright key names, don't try to open terminals.

## Steel session URLs — use `debug_url`, not `session_viewer_url`

Steel sessions expose two URL fields. `session_viewer_url` points to the Steel dashboard viewer and cannot be embedded in an iframe (X-Frame-Options blocks it). `debug_url` is the correct field for embedding — it streams via WebRTC at 25 fps and accepts `?interactive=true` to enable remote input. Always use `session.debug_url` when embedding a session in any UI context.
