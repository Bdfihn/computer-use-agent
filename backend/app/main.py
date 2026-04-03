import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.browser import BrowserManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.browser = BrowserManager(steel_api_key=os.environ["STEEL_API_KEY"])
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


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/session/start")
async def session_start():
    browser: BrowserManager = app.state.browser
    await browser.ensure_session()
    return {"session_id": browser.session_id, "viewer_url": browser.viewer_url}
