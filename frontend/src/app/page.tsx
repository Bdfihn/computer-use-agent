"use client";

import { useState, useEffect, useRef } from "react";

const API = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

type ActivityEvent = { type: string; content: string };
type PageState = "idle" | "loading" | "ready";

const EVENT_COLORS: Record<string, string> = {
  user: "text-blue-400",
  text: "text-green-400",
  tool_call: "text-yellow-400",
  tool_result: "text-gray-400",
  error: "text-red-400",
  status: "text-purple-400",
  done: "text-gray-600",
};

export default function Page() {
  const [pageState, setPageState] = useState<PageState>("idle");
  const [error, setError] = useState("");
  const [debugUrl, setDebugUrl] = useState("");
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [events]);

  async function startSession() {
    setPageState("loading");
    setError("");
    try {
      const res = await fetch(`${API}/session/start`, { method: "POST" });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const { debug_url } = await res.json();
      setDebugUrl(debug_url);

      const ws = new WebSocket(`${WS_URL}/ws`);
      ws.onmessage = (e) => {
        const event: ActivityEvent = JSON.parse(e.data);
        setEvents((prev) => [...prev, event]);
        if (event.type === "done") setBusy(false);
      };
      wsRef.current = ws;
      setPageState("ready");
    } catch (err) {
      setError(String(err));
      setPageState("idle");
    }
  }

  async function sendMessage() {
    if (!input.trim() || busy) return;
    const message = input.trim();
    setInput("");
    setBusy(true);
    setEvents((prev) => [...prev, { type: "user", content: message }]);
    await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  }

  if (pageState !== "ready") {
    return (
      <main className="flex h-screen flex-col items-center justify-center gap-3">
        <button
          onClick={startSession}
          disabled={pageState === "loading"}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg font-medium transition-colors"
        >
          {pageState === "loading" ? "Starting session…" : "Start Session"}
        </button>
        {error && <p className="text-red-400 text-sm">{error}</p>}
      </main>
    );
  }

  return (
    <div className="flex h-screen">
      <iframe
        src={`${debugUrl}?interactive=false`}
        className="flex-1 border-0"
        allow="clipboard-read; clipboard-write"
      />

      <div className="w-80 flex flex-col border-l border-gray-800">
        <div
          ref={logRef}
          className="flex-1 overflow-y-auto p-3 space-y-1 font-mono text-xs"
        >
          {events.length === 0 && (
            <p className="text-gray-600">Activity will appear here…</p>
          )}
          {events.map((e, i) => (
            <div key={i} className={EVENT_COLORS[e.type] ?? "text-gray-300"}>
              <span className="text-gray-600">[{e.type}]</span>{" "}
              {e.content}
            </div>
          ))}
        </div>

        <div className="p-3 border-t border-gray-800 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            disabled={busy}
            placeholder="Tell the agent what to do…"
            className="flex-1 bg-gray-900 rounded px-3 py-2 text-sm outline-none disabled:opacity-50 placeholder-gray-600"
          />
          <button
            onClick={sendMessage}
            disabled={busy || !input.trim()}
            className="px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded text-sm transition-colors"
          >
            {busy ? "…" : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}
