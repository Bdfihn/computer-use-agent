import asyncio

from playwright.async_api import async_playwright, Browser
from steel import Steel

DISPLAY_WIDTH = 900
DISPLAY_HEIGHT = 600

_KEY_MAP = {
    "ctrl": "Control", "shift": "Shift", "alt": "Alt",
    "super": "Meta", "win": "Meta",
    "return": "Enter", "esc": "Escape",
    "up": "ArrowUp", "down": "ArrowDown", "left": "ArrowLeft", "right": "ArrowRight",
}


def _normalize_keys(combo: str) -> list[str]:
    """Split a key combo like 'Control+l' into ['Control', 'l'], normalizing aliases."""
    return [_KEY_MAP.get(p.lower(), p) for p in combo.split("+")]


class BrowserManager:
    def __init__(self, steel_api_key: str) -> None:
        self._steel_api_key = steel_api_key
        self._client = Steel(steel_api_key=steel_api_key)
        self._session = None
        self._playwright = None
        self._browser: Browser | None = None

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
        await context.new_page()  # side effect: registers the page so Steel records the session in the live viewer

    def _computer(self, **kwargs):
        """Synchronous call to Steel computer API."""
        return self._client.sessions.computer(self._session.id, **kwargs)

    async def take_screenshot(self) -> str:
        assert self._session is not None
        resp = await asyncio.to_thread(self._computer, action="take_screenshot")
        return resp.base64_image

    async def execute_action(self, action: str, tool_input: dict) -> str:
        """Execute a computer_20251124 action via Steel computer API. Returns base64 PNG."""
        assert self._session is not None

        if action in ("screenshot", "cursor_position"):
            pass  # no action needed; fall through to take_screenshot()

        elif action == "left_click":
            x, y = tool_input["coordinate"]
            await asyncio.to_thread(self._computer, action="click_mouse", button="left", coordinates=[x, y])

        elif action == "right_click":
            x, y = tool_input["coordinate"]
            await asyncio.to_thread(self._computer, action="click_mouse", button="right", coordinates=[x, y])

        elif action == "double_click":
            x, y = tool_input["coordinate"]
            await asyncio.to_thread(self._computer, action="click_mouse", button="left", coordinates=[x, y], num_clicks=2)

        elif action == "middle_click":
            x, y = tool_input["coordinate"]
            await asyncio.to_thread(self._computer, action="click_mouse", button="middle", coordinates=[x, y])

        elif action == "type":
            await asyncio.to_thread(self._computer, action="type_text", text=tool_input["text"])

        elif action == "key":
            keys = _normalize_keys(tool_input["text"])
            await asyncio.to_thread(self._computer, action="press_key", keys=keys)

        elif action == "mouse_move":
            x, y = tool_input["coordinate"]
            await asyncio.to_thread(self._computer, action="move_mouse", coordinates=[x, y])

        elif action == "scroll":
            x, y = tool_input["coordinate"]
            direction = tool_input.get("scroll_direction", "down")
            distance = tool_input.get("scroll_distance", 3)
            delta_y = distance * 100 if direction == "down" else (-distance * 100 if direction == "up" else 0)
            delta_x = distance * 100 if direction == "right" else (-distance * 100 if direction == "left" else 0)
            await asyncio.to_thread(self._computer, action="scroll", coordinates=[x, y], delta_x=delta_x, delta_y=delta_y)

        elif action == "left_click_drag":
            sx, sy = tool_input["start_coordinate"]
            ex, ey = tool_input["coordinate"]
            await asyncio.to_thread(self._computer, action="drag_mouse", path=[[sx, sy], [ex, ey]])

        elif action == "wait":
            await asyncio.sleep(tool_input.get("duration", 1))

        return await self.take_screenshot()

    async def cleanup(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        if self._session:
            await asyncio.to_thread(self._client.sessions.release, self._session.id)
            self._session = None
