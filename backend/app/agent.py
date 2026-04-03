import anthropic

from app.browser import BrowserManager, DISPLAY_WIDTH, DISPLAY_HEIGHT
from app.models import ActivityEvent

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 16000
SLIDING_WINDOW_SIZE = 10

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

    await broadcast(ActivityEvent(type="status", content="Agent started"))

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

    try:
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

            if response.stop_reason == "max_tokens":
                await broadcast(ActivityEvent(type="status", content="Max tokens reached, stopping"))
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

    except Exception as exc:
        await broadcast(ActivityEvent(type="error", content=f"Agent loop error: {exc}"))

    await broadcast(ActivityEvent(type="done", content=""))
