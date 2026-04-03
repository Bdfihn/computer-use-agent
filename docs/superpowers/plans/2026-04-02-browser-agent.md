# Browser Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a three-pane browser agent UI where the user watches a live Steel session, sees real-time agent activity, and directs the Claude-powered agent via chat.

**Architecture:** FastAPI backend manages a Steel browser session (connected via Playwright CDP), runs the Claude agent loop using the `computer_20251124` built-in tool, and streams activity events to the React frontend via WebSocket. The frontend embeds Steel's session viewer URL directly in an iFrame — no screenshot streaming to the frontend.

**Tech Stack:** Python 3.12, FastAPI, Playwright (CDP only — no local browser), Anthropic SDK (`claude-sonnet-4-6` + `computer_20251124` beta), Steel REST API, Next.js 15, React, TypeScript, Tailwind CSS, Docker Compose

---

## File Map

| File | Responsibility |
|------|---------------|
| `docker-compose.yml` | Two services: backend (8000) + frontend (3000), shared .env |
| `.env.example` | Template: ANTHROPIC_API_KEY, STEEL_API_KEY |
| `.gitignore` | .env, __pycache__, .next, node_modules |
| `backend/Dockerfile` | python:3.12-slim, pip install, no Playwright browser binaries |
| `backend/requirements.txt` | fastapi, uvicorn, playwright, anthropic, httpx, python-dotenv |
| `backend/app/__init__.py` | Empty |
| `backend/app/models.py` | `ActivityEvent`, `SessionInfo` Pydantic models |
| `backend/app/browser.py` | `BrowserManager`: Steel session lifecycle, Playwright CDP connect, `execute_action()`, `take_screenshot()` |
| `backend/app/agent.py` | `run_agent_loop()`, `apply_sliding_window()`, Claude API with computer_20251124 |
| `backend/app/main.py` | FastAPI app, `ConnectionManager`, all routes: GET /health, GET /session, POST /chat, WS /ws |
| `frontend/Dockerfile` | node:20-alpine, npm ci, npm run dev |
| `frontend/package.json` | next, react, react-dom, typescript, tailwindcss |
| `frontend/next.config.js` | Minimal config |
| `frontend/tsconfig.json` | Strict mode, path alias @/ → src/ |
| `frontend/src/app/layout.tsx` | Root HTML shell, full-height body |
| `frontend/src/app/page.tsx` | Three-column layout, viewerUrl + agentBusy state, wires all panes |
| `frontend/src/components/BrowserPane.tsx` | iFrame embedding Steel viewer URL; "No active session" fallback |
| `frontend/src/components/ActivityLog.tsx` | Scrolling event feed, auto-scroll to bottom |
| `frontend/src/components/useActivityLog.ts` | WebSocket hook: events[], connected, agentBusy |
| `frontend/src/components/ChatInput.tsx` | Controlled textarea, POST /chat, disabled when agentBusy |

---

## Task 1: Docker + Backend Skeleton

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `backend/Dockerfile`
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py` (health endpoint only)

- [ ] **Step 1: Use Context7 to get latest stable versions**

Look up: `fastapi`, `uvicorn`, `playwright` (Python), `anthropic`, `httpx`, `python-dotenv`. Populate exact versions in requirements.txt.

- [ ] **Step 2: Create `backend/requirements.txt`**

```
fastapi==<latest>
uvicorn[standard]==<latest>
playwright==<latest>
anthropic==<latest>
httpx==<latest>
python-dotenv==<latest>
```

- [ ] **Step 3: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

Note: no `playwright install` — we use CDP to connect to Steel's cloud browser, not a local one.

- [ ] **Step 4: Create `backend/app/__init__.py`**

Empty file.

- [ ] **Step 5: Create `backend/app/main.py` (health only)**

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Use Context7 to get latest stable Next.js + React versions**

Look up: `next`, `react`, `react-dom`, `@types/react`, `@types/react-dom`, `typescript`, `tailwindcss`, `postcss`, `autoprefixer`.

- [ ] **Step 7: Create `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

CMD ["npm", "run", "dev"]
```

- [ ] **Step 8: Create `frontend/package.json`**

```json
{
  "name": "browser-agent-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "<latest>",
    "react": "<latest>",
    "react-dom": "<latest>"
  },
  "devDependencies": {
    "@types/node": "<latest>",
    "@types/react": "<latest>",
    "@types/react-dom": "<latest>",
    "typescript": "<latest>",
    "tailwindcss": "<latest>",
    "postcss": "<latest>",
    "autoprefixer": "<latest>"
  }
}
```

- [ ] **Step 9: Create `frontend/next.config.js`**

```js
/** @type {import('next').NextConfig} */
const nextConfig = {};

module.exports = nextConfig;
```

- [ ] **Step 10: Create `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 11: Create `frontend/tailwind.config.js`**

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
```

- [ ] **Step 12: Create `frontend/postcss.config.js`**

```js
module.exports = {
  plugins: { tailwindcss: {}, autoprefixer: {} },
};
```

- [ ] **Step 13: Create `docker-compose.yml`**

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      - FRONTEND_ORIGIN=http://localhost:3000
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    env_file: .env
    environment:
      - NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    depends_on:
      - backend
```

Note: `NEXT_PUBLIC_*` vars are browser-side — they point to `localhost:8000` because the browser (not the container) makes these requests.

- [ ] **Step 14: Create `.env.example`**

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
STEEL_API_KEY=your_steel_api_key_here
```

- [ ] **Step 15: Create `.gitignore`**

Audit the actual file tree first, then create:

```
.env
__pycache__/
*.pyc
.next/
node_modules/
```

- [ ] **Step 16: Build both containers**

```bash
docker compose build
```

Expected: both images build without errors.

- [ ] **Step 17: Bring up backend and verify health**

```bash
docker compose up backend -d
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 18: Commit**

```bash
git init
git add .
git commit -m "scaffold: Docker Compose, backend skeleton with /health, frontend scaffold"
```

---

## Task 2: Pydantic Models

**Files:**
- Create: `backend/app/models.py`

- [ ] **Step 1: Create `backend/app/models.py`**

```python
from typing import Literal
from pydantic import BaseModel


class ActivityEvent(BaseModel):
    type: Literal["tool_call", "tool_result", "text", "error", "done"]
    content: str


class SessionInfo(BaseModel):
    session_id: str
    viewer_url: str
```

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "feat: add Pydantic models ActivityEvent and SessionInfo"
```

---

## Task 3: Browser Layer

**Files:**
- Create: `backend/app/browser.py`

No unit tests — this module is entirely coupled to external services (Steel API, Playwright CDP). It is verified manually in Task 5 as part of the first end-to-end chat flow.

- [ ] **Step 1: Use Context7 to fetch Steel API docs**

Look up: Steel session create endpoint, request/response shape, `sessionViewerUrl` and `websocketUrl` field names, session release endpoint.

- [ ] **Step 2: Create `backend/app/browser.py`**

```python
import base64
import httpx
from playwright.async_api import async_playwright, Browser, Page

STEEL_API_BASE = "https://api.steel.dev/v1"
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 800


class BrowserManager:
    def __init__(self, steel_api_key: str) -> None:
        self._steel_api_key = steel_api_key
        self._session_id: str | None = None
        self._viewer_url: str | None = None
        self._cdp_url: str | None = None
        self._playwright = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    @property
    def session_id(self) -> str | None:
        return self._session_id

    @property
    def viewer_url(self) -> str | None:
        return self._viewer_url

    async def ensure_session(self) -> None:
        if self._session_id is not None:
            return
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{STEEL_API_BASE}/sessions",
                headers={"Steel-Api-Key": self._steel_api_key},
                json={"sessionTimeout": 3600000},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        self._session_id = data["id"]
        self._viewer_url = data["sessionViewerUrl"]
        self._cdp_url = data["websocketUrl"]

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.connect_over_cdp(self._cdp_url)
        context = self._browser.contexts[0]
        self._page = context.pages[0] if context.pages else await context.new_page()
        await self._page.set_viewport_size({"width": DISPLAY_WIDTH, "height": DISPLAY_HEIGHT})

    async def take_screenshot(self) -> str:
        assert self._page is not None, "No active page — call ensure_session() first"
        data = await self._page.screenshot(type="png")
        return base64.standard_b64encode(data).decode()

    async def execute_action(self, action: str, tool_input: dict) -> str:
        """Execute a computer_20251124 action. Returns base64 PNG screenshot."""
        assert self._page is not None, "No active page — call ensure_session() first"
        page = self._page

        if action == "screenshot":
            pass  # just capture below

        elif action == "left_click":
            x, y = tool_input["coordinate"]
            await page.mouse.click(x, y)

        elif action == "right_click":
            x, y = tool_input["coordinate"]
            await page.mouse.click(x, y, button="right")

        elif action == "double_click":
            x, y = tool_input["coordinate"]
            await page.mouse.dblclick(x, y)

        elif action == "middle_click":
            x, y = tool_input["coordinate"]
            await page.mouse.click(x, y, button="middle")

        elif action == "type":
            await page.keyboard.type(tool_input["text"])

        elif action == "key":
            await page.keyboard.press(tool_input["text"])

        elif action == "mouse_move":
            x, y = tool_input["coordinate"]
            await page.mouse.move(x, y)

        elif action == "scroll":
            x, y = tool_input["coordinate"]
            direction = tool_input.get("scroll_direction", "down")
            distance = tool_input.get("scroll_distance", 3)
            delta_y = distance * 100 if direction == "down" else (-distance * 100 if direction == "up" else 0)
            delta_x = distance * 100 if direction == "right" else (-distance * 100 if direction == "left" else 0)
            await page.mouse.move(x, y)
            await page.mouse.wheel(delta_x, delta_y)

        elif action == "left_click_drag":
            sx, sy = tool_input["start_coordinate"]
            ex, ey = tool_input["coordinate"]
            await page.mouse.move(sx, sy)
            await page.mouse.down()
            await page.mouse.move(ex, ey)
            await page.mouse.up()

        elif action == "cursor_position":
            pass  # just capture below

        return await self.take_screenshot()

    async def cleanup(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        if self._session_id:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{STEEL_API_BASE}/sessions/{self._session_id}",
                    headers={"Steel-Api-Key": self._steel_api_key},
                    timeout=10,
                )
            self._session_id = None
            self._viewer_url = None
            self._cdp_url = None
```

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "feat: add BrowserManager — Steel session lifecycle and Playwright CDP action execution"
```

---

## Task 4: Agent Loop

**Files:**
- Create: `backend/app/agent.py`

- [ ] **Step 1: Use Context7 to fetch Anthropic SDK docs**

Look up: `client.beta.messages.create`, `betas` parameter for computer-use-2025-11-24, `computer_20251124` tool declaration shape, response content block types (ToolUseBlock, TextBlock), `stop_reason` values.

- [ ] **Step 2: Create `backend/app/agent.py`**

```python
import anthropic
from app.browser import BrowserManager, DISPLAY_WIDTH, DISPLAY_HEIGHT
from app.models import ActivityEvent

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8096
SLIDING_WINDOW_SIZE = 20

COMPUTER_TOOL = {
    "type": "computer_20251124",
    "name": "computer",
    "display_width_px": DISPLAY_WIDTH,
    "display_height_px": DISPLAY_HEIGHT,
}


def apply_sliding_window(conversation: list, max_size: int = SLIDING_WINDOW_SIZE) -> None:
    """Trim conversation in-place to the most recent max_size turns."""
    if len(conversation) > max_size:
        del conversation[:-max_size]


async def run_agent_loop(
    user_message: str,
    conversation: list,
    browser: BrowserManager,
    broadcast,
    anthropic_api_key: str,
) -> None:
    client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)

    screenshot = await browser.take_screenshot()
    conversation.append({
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": screenshot},
            },
            {"type": "text", "text": user_message},
        ],
    })

    while True:
        apply_sliding_window(conversation)

        response = await client.beta.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            tools=[COMPUTER_TOOL],
            messages=conversation,
            betas=["computer-use-2025-11-24"],
        )

        conversation.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    await broadcast(ActivityEvent(type="text", content=block.text))
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                action = block.input.get("action", "unknown")
                await broadcast(ActivityEvent(
                    type="tool_call",
                    content=f"{action} {block.input}",
                ))

                try:
                    result_screenshot = await browser.execute_action(action, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": result_screenshot,
                                },
                            }
                        ],
                    })
                    await broadcast(ActivityEvent(type="tool_result", content=f"{action} completed"))
                except Exception as exc:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": [{"type": "text", "text": f"Error: {exc}"}],
                        "is_error": True,
                    })
                    await broadcast(ActivityEvent(type="error", content=f"{action} failed: {exc}"))

            conversation.append({"role": "user", "content": tool_results})

    await broadcast(ActivityEvent(type="done", content=""))
```

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "feat: add agent loop with computer_20251124 tool, sliding window context management"
```

---

## Task 5: Routes + WebSocket (main.py complete)

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Replace `backend/app/main.py` with full implementation**

```python
import asyncio
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agent import run_agent_loop
from app.browser import BrowserManager
from app.models import ActivityEvent, SessionInfo


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.remove(ws)

    async def broadcast(self, event: ActivityEvent) -> None:
        payload = event.model_dump_json()
        for ws in list(self._connections):
            try:
                await ws.send_text(payload)
            except Exception:
                pass


ws_manager = ConnectionManager()
browser: BrowserManager = None  # set in lifespan
conversation: list = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global browser
    browser = BrowserManager(steel_api_key=os.environ["STEEL_API_KEY"])
    yield
    await browser.cleanup()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/session", response_model=SessionInfo)
async def get_session():
    if browser._session_id is None:
        raise HTTPException(status_code=404, detail="No active session")
    return SessionInfo(
        session_id=browser._session_id,
        viewer_url=browser._viewer_url,
    )


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):
    await browser.ensure_session()
    asyncio.create_task(
        run_agent_loop(
            user_message=request.message,
            conversation=conversation,
            browser=browser,
            broadcast=ws_manager.broadcast,
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        )
    )
    return {"status": "started"}
```

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "feat: add full FastAPI routes — /health, /session, /chat, WebSocket /ws"
```

---

## Task 6: Frontend Shell

**Files:**
- Create: `frontend/src/app/globals.css`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx` (static three-pane skeleton)

- [ ] **Step 1: Create `frontend/src/app/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html,
body {
  height: 100%;
  margin: 0;
  padding: 0;
}
```

- [ ] **Step 2: Create `frontend/src/app/layout.tsx`**

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Browser Agent",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full bg-gray-950 text-gray-100">{children}</body>
    </html>
  );
}
```

- [ ] **Step 3: Create `frontend/src/app/page.tsx`**

```tsx
"use client";

export default function Home() {
  return (
    <main className="flex h-full divide-x divide-gray-800">
      <div className="flex-1 bg-gray-900 flex items-center justify-center text-gray-500">
        Browser pane
      </div>
      <div className="w-80 flex flex-col bg-gray-950">
        <div className="flex-1 p-4 text-gray-500">Activity log</div>
      </div>
      <div className="w-80 flex flex-col bg-gray-950">
        <div className="flex-1 p-4 text-gray-500">Chat input</div>
      </div>
    </main>
  );
}
```

- [ ] **Step 4: Bring up frontend, verify layout renders**

```bash
docker compose up frontend -d
```

Open http://localhost:3000 — expect three visible panes.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: Next.js frontend shell with three-pane layout"
```

---

## Task 7: Activity Log

**Files:**
- Create: `frontend/src/components/useActivityLog.ts`
- Create: `frontend/src/components/ActivityLog.tsx`

- [ ] **Step 1: Create `frontend/src/components/useActivityLog.ts`**

```ts
"use client";

import { useEffect, useRef, useState } from "react";

export interface ActivityEvent {
  type: "tool_call" | "tool_result" | "text" | "error" | "done";
  content: string;
}

export function useActivityLog() {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [agentBusy, setAgentBusy] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const url = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
    const ws = new WebSocket(`${url}/ws`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      setAgentBusy(false);
    };
    ws.onmessage = (e) => {
      const event = JSON.parse(e.data) as ActivityEvent;
      setEvents((prev) => [...prev, event]);
      if (event.type === "done" || event.type === "error") {
        setAgentBusy(false);
      }
    };

    return () => ws.close();
  }, []);

  const markBusy = () => setAgentBusy(true);

  return { events, connected, agentBusy, markBusy };
}
```

- [ ] **Step 2: Create `frontend/src/components/ActivityLog.tsx`**

```tsx
"use client";

import { useEffect, useRef } from "react";
import { ActivityEvent } from "./useActivityLog";

const EVENT_COLORS: Record<ActivityEvent["type"], string> = {
  tool_call: "text-blue-400",
  tool_result: "text-gray-400",
  text: "text-green-400",
  error: "text-red-400",
  done: "text-gray-600",
};

interface ActivityLogProps {
  events: ActivityEvent[];
  connected: boolean;
}

export default function ActivityLog({ events, connected }: ActivityLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b border-gray-800 text-xs text-gray-500 flex items-center gap-2">
        <span className={connected ? "text-green-500" : "text-red-500"}>●</span>
        Activity
      </div>
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1 font-mono text-xs">
        {events
          .filter((e) => e.type !== "done")
          .map((event, i) => (
            <div key={i} className={EVENT_COLORS[event.type]}>
              <span className="text-gray-600">[{event.type}]</span> {event.content}
            </div>
          ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Update `frontend/src/app/page.tsx` to mount ActivityLog with props**

```tsx
"use client";

import ActivityLog from "@/components/ActivityLog";
import { useActivityLog } from "@/components/useActivityLog";

export default function Home() {
  const { events, connected } = useActivityLog();

  return (
    <main className="flex h-full divide-x divide-gray-800">
      <div className="flex-1 bg-gray-900 flex items-center justify-center text-gray-500">
        Browser pane
      </div>
      <div className="w-80 flex flex-col bg-gray-950">
        <ActivityLog events={events} connected={connected} />
      </div>
      <div className="w-80 flex flex-col bg-gray-950">
        <div className="flex-1 p-4 text-gray-500">Chat input</div>
      </div>
    </main>
  );
}
```

- [ ] **Step 4: Verify in browser**

Reload http://localhost:3000 — activity pane shows "● Activity" header with disconnected/connected indicator.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: ActivityLog component with WebSocket hook and auto-scroll"
```

---

## Task 8: Chat Input

**Files:**
- Create: `frontend/src/components/ChatInput.tsx`
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: Create `frontend/src/components/ChatInput.tsx`**

```tsx
"use client";

import { KeyboardEvent, useState } from "react";

interface ChatInputProps {
  agentBusy: boolean;
  onSend: (message: string) => Promise<void>;
}

export default function ChatInput({ agentBusy, onSend }: ChatInputProps) {
  const [message, setMessage] = useState("");

  const submit = async () => {
    const trimmed = message.trim();
    if (!trimmed || agentBusy) return;
    setMessage("");
    await onSend(trimmed);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="flex flex-col h-full p-3 gap-2">
      <div className="px-1 py-1 text-xs text-gray-500 border-b border-gray-800">
        Chat
      </div>
      <textarea
        className="flex-1 bg-gray-900 border border-gray-700 rounded p-2 text-sm text-gray-100
                   placeholder-gray-600 resize-none focus:outline-none focus:border-gray-500
                   disabled:opacity-40"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={agentBusy}
        placeholder={agentBusy ? "Agent is working…" : "Send a message (Enter to send)"}
      />
      <button
        className="px-4 py-2 bg-blue-600 text-white text-sm rounded
                   hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed"
        onClick={submit}
        disabled={agentBusy || !message.trim()}
      >
        {agentBusy ? "Working…" : "Send"}
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Update `frontend/src/app/page.tsx` to wire ChatInput + shared agentBusy**

```tsx
"use client";

import ActivityLog from "@/components/ActivityLog";
import ChatInput from "@/components/ChatInput";
import { useActivityLog } from "@/components/useActivityLog";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function Home() {
  const { events, connected, agentBusy, markBusy } = useActivityLog();

  const handleSend = async (message: string) => {
    markBusy();
    await fetch(`${BACKEND}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  };

  return (
    <main className="flex h-full divide-x divide-gray-800">
      <div className="flex-1 bg-gray-900 flex items-center justify-center text-gray-500">
        Browser pane
      </div>
      <div className="w-80 flex flex-col bg-gray-950">
        <ActivityLog events={events} connected={connected} />
      </div>
      <div className="w-80 flex flex-col bg-gray-950">
        <ChatInput agentBusy={agentBusy} onSend={handleSend} />
      </div>
    </main>
  );
}
```

- [ ] **Step 3: Verify in browser**

Reload http://localhost:3000 — chat pane renders with textarea and Send button.

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "feat: ChatInput component, wire agentBusy state from shared useActivityLog hook"
```

---

## Task 9: Browser Pane

**Files:**
- Create: `frontend/src/components/BrowserPane.tsx`
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: Create `frontend/src/components/BrowserPane.tsx`**

```tsx
"use client";

interface BrowserPaneProps {
  viewerUrl: string | null;
}

export default function BrowserPane({ viewerUrl }: BrowserPaneProps) {
  if (!viewerUrl) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-2 text-gray-600 text-sm">
        <span className="text-2xl">⬡</span>
        <span>Send a message to start the browser session</span>
      </div>
    );
  }

  return (
    <iframe
      src={viewerUrl}
      className="w-full h-full border-none"
      title="Live browser session"
    />
  );
}
```

- [ ] **Step 2: Update `frontend/src/app/page.tsx` to fetch viewer URL after first chat**

```tsx
"use client";

import { useRef, useState } from "react";
import ActivityLog from "@/components/ActivityLog";
import BrowserPane from "@/components/BrowserPane";
import ChatInput from "@/components/ChatInput";
import { useActivityLog } from "@/components/useActivityLog";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function Home() {
  const { events, connected, agentBusy, markBusy } = useActivityLog();
  const [viewerUrl, setViewerUrl] = useState<string | null>(null);
  const sessionFetched = useRef(false);

  const handleSend = async (message: string) => {
    markBusy();
    await fetch(`${BACKEND}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!sessionFetched.current) {
      sessionFetched.current = true;
      const res = await fetch(`${BACKEND}/session`);
      if (res.ok) {
        const data = await res.json();
        setViewerUrl(data.viewer_url);
      }
    }
  };

  return (
    <main className="flex h-full divide-x divide-gray-800">
      <div className="flex-1 bg-gray-900">
        <BrowserPane viewerUrl={viewerUrl} />
      </div>
      <div className="w-80 flex flex-col bg-gray-950">
        <ActivityLog events={events} connected={connected} />
      </div>
      <div className="w-80 flex flex-col bg-gray-950">
        <ChatInput agentBusy={agentBusy} onSend={handleSend} />
      </div>
    </main>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "feat: BrowserPane embeds Steel viewer URL on first chat"
```

---

## Task 10: Docs + Status

**Files:**
- Create: `docs/lessons-learned.md`
- Create: `docs/status.md`
- Create: `docs/decisions.md`

- [ ] **Step 1: Create `docs/status.md`**

```markdown
# Status

## Implemented
- Docker Compose: two containers (backend port 8000, frontend port 3000)
- Backend: Steel session lifecycle, Playwright CDP connection, all computer_20251124 actions
- Backend: Agent loop with claude-sonnet-4-6, sliding window (20 turns), WebSocket broadcast
- Backend: Routes — GET /health, GET /session, POST /chat, WS /ws
- Frontend: Three-pane layout (browser iFrame, activity log, chat input)
- Frontend: WebSocket hook with agentBusy state
- Frontend: Steel viewer URL loaded on first chat message

## Known Gaps
- No error recovery if Steel session drops mid-task
- No session restart UX (requires container restart)
- No system prompt — Claude gets raw user message + screenshot

## Next
- Add system prompt to agent.py
- Test with real Steel + Anthropic credentials
```

- [ ] **Step 2: Create `docs/decisions.md`**

```markdown
# Decisions

## Steel viewer URL instead of screenshot streaming (2026-04-02)
Steel provides a hosted session viewer URL at session creation time. Embedding this in an iFrame eliminates all screenshot streaming infrastructure on the frontend path. Trade-off: UI is dependent on Steel's viewer staying available; no custom rendering or overlays possible. Alternatives rejected: base64 PNG streaming over WebSocket (adds latency, bandwidth, and complexity for no benefit in supervised mode).

## computer_20251124 built-in tool instead of custom tool definitions (2026-04-02)
The built-in computer use tool gives Claude a standardized action vocabulary (left_click, type, scroll, etc.) with no custom tool schema maintenance. Trade-off: tied to Anthropic's tool versioning; action set is fixed. Alternative rejected: custom tool definitions would require reimplementing the same action set with more maintenance burden.

## Single Steel session per backend lifetime (2026-04-02)
Session is auto-created on first /chat call and persists until the container stops. No explicit start/end UX. Appropriate for a personal single-user tool. Alternative rejected: per-conversation sessions would add UI complexity with no benefit for solo use.

## Flat backend structure — no routers/ directory (2026-04-02)
All routes in main.py. For a project with ~4 endpoints, a routers/ directory is premature abstraction. Revisit if the route count grows significantly.
```

- [ ] **Step 3: Create `docs/lessons-learned.md`**

```markdown
# Lessons Learned

(Append entries here when blockers are resolved or mistakes corrected.)
```

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "docs: add status, decisions, lessons-learned"
```

---

## End-to-End Verification Checklist

Before calling this complete, run through:

- [ ] `docker compose build` — both images build clean
- [ ] `docker compose up` — both containers start, no crash loops
- [ ] `curl http://localhost:8000/health` → `{"status":"ok"}`
- [ ] Open http://localhost:3000 — three panes render
- [ ] Type a message, press Send — POST /chat returns 200
- [ ] Activity pane shows WebSocket events in real time
- [ ] Browser pane shows Steel viewer iFrame after first message
- [ ] Agent completes task, `[done]` event received, Send button re-enables
- [ ] `docker compose down` — Steel session released cleanly (check Steel dashboard)
