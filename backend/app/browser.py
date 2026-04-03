import asyncio
import base64
import os

from playwright.async_api import async_playwright, Browser, Page
from steel import Steel

DISPLAY_WIDTH = 900
DISPLAY_HEIGHT = 600

# Map xdotool-style key names (used by Claude's computer tool) to Playwright key names.
_KEY_MAP = {
    "ctrl": "Control", "shift": "Shift", "alt": "Alt",
    "super": "Meta", "win": "Meta",
    "return": "Enter", "esc": "Escape",
    "up": "ArrowUp", "down": "ArrowDown", "left": "ArrowLeft", "right": "ArrowRight",
}


def _normalize_key(key: str) -> str:
    parts = key.split("+")
    return "+".join(_KEY_MAP.get(p.lower(), p) for p in parts)


class BrowserManager:
    def __init__(self, steel_api_key: str) -> None:
        self._steel_api_key = steel_api_key
        self._client = Steel(steel_api_key=steel_api_key)
        self._session = None
        self._playwright = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    @property
    def session_id(self) -> str | None:
        return self._session.id if self._session else None

    @property
    def debug_url(self) -> str | None:
        return self._session.debug_url if self._session else None

    async def ensure_session(self) -> None:
        if self._session is not None:
            return

        self._session = await asyncio.to_thread(
            self._client.sessions.create,
            dimensions={"width": DISPLAY_WIDTH, "height": DISPLAY_HEIGHT},
            api_timeout=3600000,
        )

        cdp_url = (
            f"wss://connect.steel.dev"
            f"?apiKey={self._steel_api_key}"
            f"&sessionId={self._session.id}"
        )

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.connect_over_cdp(cdp_url)
        context = self._browser.contexts[0]
        self._page = await context.new_page()

    async def take_screenshot(self) -> str:
        assert self._page is not None, "No active page — call ensure_session() first"
        data = await self._page.screenshot(type="png")
        return base64.standard_b64encode(data).decode()

    async def execute_action(self, action: str, tool_input: dict) -> str:
        """Execute a computer_20251124 action. Returns base64 PNG screenshot."""
        assert self._page is not None, "No active page — call ensure_session() first"
        page = self._page

        if action == "screenshot":
            pass

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
            await page.keyboard.press(_normalize_key(tool_input["text"]))

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

        elif action == "wait":
            await asyncio.sleep(tool_input.get("duration", 1))

        elif action == "cursor_position":
            pass

        try:
            await page.wait_for_load_state("domcontentloaded", timeout=3000)
        except Exception:
            pass
        return await self.take_screenshot()

    async def cleanup(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        if self._session:
            await asyncio.to_thread(
                self._client.sessions.release, self._session.id
            )
            self._session = None
