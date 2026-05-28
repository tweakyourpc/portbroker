# Show HN: portbroker — stop AI coding agents from hijacking each other's dev ports

I built `portbroker` after getting burned by concurrent local dev sessions fighting over familiar ports like `3000`, `8000`, and `8080`. One agent starts a server, another session or my own dev server is already there, and suddenly the browser or verification step is talking to the wrong process.

`portbroker` is a stdlib-only Python CLI and dashboard for stable named port reservations. Agents get a short instruction: allocate or fetch a named port before starting a service, bind to `0.0.0.0`, and expose `/whoami` for HTTP services.

What's still missing is native support in the coding agents themselves. A small reservation API in Claude Code, Codex, Cursor, OpenCode, and similar tools would be better than relying on project instructions.

## Draft first comment

Minimal reproduction:

```bash
# terminal A
python3 -m http.server 3000
# terminal B, in another AI coding session
python3 -m http.server 3000
# one process wins; the other session or browser tab can point at the wrong server
```

Related native-support requests:

- Anthropic Claude Code: https://github.com/anthropics/claude-code/issues/34385
- OpenAI Codex: https://github.com/openai/codex/issues/16483

If this has happened to you, the useful signal is an incident report: agent name, what you were running, what the agent was doing, and what got hijacked.
