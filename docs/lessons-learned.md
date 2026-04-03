# Lessons Learned

## Steel session URLs — use `debug_url`, not `session_viewer_url`

Steel sessions expose two URL fields. `session_viewer_url` points to the Steel dashboard viewer and cannot be embedded in an iframe (X-Frame-Options blocks it). `debug_url` is the correct field for embedding — it streams via WebRTC at 25 fps and accepts `?interactive=true` to enable remote input. Always use `session.debug_url` when embedding a session in any UI context.
