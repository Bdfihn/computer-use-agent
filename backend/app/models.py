from typing import Literal
from pydantic import BaseModel


class ActivityEvent(BaseModel):
    type: Literal["tool_call", "tool_result", "text", "error", "done", "status"]
    content: str


class SessionInfo(BaseModel):
    session_id: str
    viewer_url: str
