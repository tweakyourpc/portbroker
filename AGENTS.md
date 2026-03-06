# Portbroker Agent Skill Guide

Use this repository as a Codex/CLI agent skill so every server launch goes through named port allocation.

## Skill intent

`portbroker` prevents port conflicts when multiple agents/projects run concurrently by allocating ports from a shared local registry.

## What to put in a skill file

Include rules like this in your agent skill/instructions:

- Always allocate or fetch a named port before starting any HTTP/TCP service.
- Never hard-code common ports (`3000`, `8000`, `8080`, etc.).
- Default bind host is `0.0.0.0` unless user requested loopback-only.
- For any new HTTP service, implement `GET /whoami` returning:
  - `service`, `version`, `pid`, `startedAt`, `host`, `port`
- Use `portbroker list` and `ss -ltnp` when diagnosing conflicts.

## Exact command pattern agents should run

```bash
# 1) Reserve/fetch the service port
PORT=$(portbroker get --name <service-name> 2>/dev/null || portbroker alloc --name <service-name> --host 0.0.0.0 --persistent)

# 2) Start the service on that port
# (example)
HOST=0.0.0.0 PORT="$PORT" <start-command>

# 3) Verify reservation state
portbroker list

# 4) Verify live listener (optional but recommended)
ss -ltnp | rg ":$PORT\\b"
```

## Dashboard command for agent ops

```bash
PORT=$(portbroker get --name portbroker-dashboard 2>/dev/null || portbroker alloc --name portbroker-dashboard --persistent)
portbroker web --name portbroker-dashboard --host 0.0.0.0 --port "$PORT" --persistent
```

Check:

- `GET /api/ports` for machine-readable port state
- `GET /whoami` for dashboard service identity

## Agent instruction snippet

Use this exact snippet in task prompts:

```text
Before starting any server, run:
PORT=$(portbroker get --name <service-name> 2>/dev/null || portbroker alloc --name <service-name> --host 0.0.0.0 --persistent)
Start the server with HOST=0.0.0.0 and PORT=$PORT.
Do not hard-code ports.
If adding an HTTP service, include GET /whoami returning {service, version, pid, startedAt, host, port}.
```
