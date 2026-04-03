import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agent import run_agent_loop
from app.browser import BrowserManager
from app.models import ActivityEvent


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.browser = BrowserManager(steel_api_key=os.environ["STEEL_API_KEY"])
    app.state.conversation = []
    app.state.connections = set()
    yield
    await app.state.browser.cleanup()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000"), "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def broadcast(event: ActivityEvent) -> None:
    data = event.model_dump_json()
    dead = set()
    for ws in app.state.connections:
        try:
            await ws.send_text(data)
        except Exception:
            dead.add(ws)
    app.state.connections -= dead


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/session/start")
async def session_start():
    browser: BrowserManager = app.state.browser
    await browser.ensure_session()
    return {"session_id": browser.session_id, "debug_url": browser.debug_url}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app.state.connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        app.state.connections.discard(websocket)


class ChatRequest(BaseModel):
    message: str


@app.post("/chat", status_code=202)
async def chat(req: ChatRequest):
    asyncio.create_task(run_agent_loop(
        user_message=req.message,
        conversation=app.state.conversation,
        browser=app.state.browser,
        broadcast=broadcast,
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
    ))
    return {"status": "accepted"}
