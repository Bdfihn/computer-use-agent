# CLAUDE.md

## Core Principles
- Doing it right is better than doing it fast. You are not in a rush. NEVER skip steps or take shortcuts.
- Prefers direct, honest feedback over diplomacy.
- Speak up about bad ideas, don't just go along with them.

## Git Workflow
- After every meaningful change, commit. Don't let work pile up uncommitted.
- Never commit broken code — one commit per completed task that the user has verified as completed. Before comitting, ask the user to test the feature you built. 
- Check for committed code before starting any new plan.
- Always use `git add .` instead of staging individual files. If there was an unexpected change, understand it and write the commit message accordingly.
- ALWAYS ask before pushing. NEVER push without confirming with the user first.

## Rules
- Use Context7 to verify latest stable library versions before adding to package.json.
- When working with libraries, frameworks, and APIs, use Context7 to fetch up-to-date documentation.
- Write tests that verify real observable behavior — inputs in, outputs out. Avoid tests that just assert mocks were called in the right order. All tests must pass before committing.
- The tests should not just check input/output. The tests should actually read into and make accessible the internal logic, which is what's actually important to audit. 
- When creating or modifying ignore files, audit the actual file tree, don't guess.
- Before solving any unknown (token limits, PDF parsing edge cases, etc.), run a spike first. Don't pre-solve problems you don't know you have.
- Never add comments about changes or history. Comments explain WHAT or WHY, never "improved", "better", "new", or what used to be there. 
- Match surrounding code style - consistency within a file and repository trumps external standards. 
- Don't reengineer everything from scratch. Study what already exists. Search the codebase for existing utility functions, service patterns, UI components, depending on what you're working on. 
- Confirm before selecting which LLM model to use, and before setting model parameters. I care a lot about model selection and configuration. 
- The user wants to review each and every line of code -- when implementing, implement in bite sized chunks that are readable, testable, and auditable. 
- Work in abstraction. It's easier and cleaner to execute things in one place and implement them in another.

## Environment & Shell
- Host OS: Windows 11
- Primary Shell: PowerShell / CMD
- Container OS: Linux (Alpine)
- Everything runs in Docker. There is no Node, npm, or anything else installed on the host machine. All commands must be run inside the container

## Docs
- After resolving a blocker or correcting a mistake, append an entry to `docs/lessons-learned.md` before moving on.
- Refer to and maintain `docs/status.md` to understand and update current state, what's implemented, and what's next.
- Append significant architectural decisions (tradeoff made, alternatives rejected, why) to `docs/decisions.md`. Implementation details don't qualify.
- Keep all docs concise and current. Overwrite stale content rather than letting files grow indefinitely.

## Project Specifics

### Why
A personal browser agent interface for supervised web automation. The user watches a live browser, sees what the agent is doing in real time, and directs it via chat. The point is transparency and control — not unattended automation. When ambiguous decisions come up, ask: does this keep the human informed and in control?

### What
**Stack:**
- **Frontend:** Next.js / React — three-pane UI: live browser view, agent activity log, chat input
- **Backend:** FastAPI — runs the agent loop, manages WebSocket connections, streams browser state to the UI
- **Browser:** Steel — manages the browser session (anti-bot, CAPTCHA, fingerprinting). Playwright connects to the Steel session via CDP and is the actual control interface
- **Agent:** Claude API — receives screenshots + conversation history, emits tool calls (click, type, navigate, scroll, screenshot), responds in chat

**Major components:**
- Agent loop (FastAPI async task): send screenshot → get tool call or text → execute via Playwright → feed result back → repeat
- WebSocket server: streams screenshot frames and agent activity events to the frontend
- Three-pane React UI: live `<img>` updated on each frame, scrolling activity log, chat input

**Structural decisions:**
- Steel over raw Playwright: needed for anti-bot/CAPTCHA handling even in supervised sessions. Playwright still present as the control layer — Steel just sits underneath.
- Sliding window for context management: sessions won't be deep enough to need summarization. Just drop oldest turns when approaching the limit.
- Headed browser always: the entire point of the UI is seeing the real browser. Headless is never appropriate here.

### How
- Steel session must be created before Playwright connects. On session start, create a Steel session, then connect Playwright via `connect_over_cdp` using the Steel WSS URL.
- Screenshots are taken after each agent action, not on a fixed polling interval. This keeps the UI in sync with what the agent actually did.
- Coordinate space: screenshots sent to Claude are at the browser's native resolution. If the UI scales them down for display, click coordinates from the user's UI must be translated back before passing to Playwright.
- Steel's session viewer URL is available immediately on session create — useful for debugging or as a fallback viewer during development before the custom stream is built.
- Two API keys required: `ANTHROPIC_API_KEY` and `STEEL_API_KEY`.
- Confirm model selection and parameters with the user before any Claude API call configuration.