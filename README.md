# computer-use-agent

Supervised browser automation. Watch a live browser, direct it via chat. The agent uses Claude's computer use API to control the browser.

## Stack

- **Backend**: FastAPI, Steel (browser sessions), Playwright (CDP), Claude API
- **Frontend**: Next.js, Tailwind

## Setup

1. Copy `.env.example` to `.env` and fill in your keys:

```
STEEL_API_KEY=...
ANTHROPIC_API_KEY=...
```

2. Start everything:

```
docker compose up
```

3. Open `http://localhost:3000`, click **Start Session**, then type instructions in the chat.

## Requirements

Docker and Docker Compose. 
