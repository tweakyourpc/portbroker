# portbroker usage

`portbroker` is a standard-library Python CLI for named local port reservations, listener checks, and a live dashboard.

- Default registry: `~/.config/portbroker/ports.json`
- Lock file: `~/.config/portbroker/ports.lock`
- Listener checks: `ss`, with `lsof` fallback for TCP where available
- Persistent reservations are retained until explicitly freed

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/tweakyourpc/portbroker/main/install.sh | sh
```

The installer places the CLI in `~/.local/bin`, installs the dashboard asset and skill templates under `~/.local/share/portbroker`, and runs `portbroker install-skill` for detected coding agents.

For a checkout-based installation:

```bash
install -m 0755 ./portbroker "$HOME/.local/bin/portbroker"
mkdir -p "$HOME/.local/share/portbroker/skills"
install -m 0644 dashboard.html "$HOME/.local/share/portbroker/dashboard.html"
install -m 0644 skills/*.md "$HOME/.local/share/portbroker/skills/"
```

Set `PORTBROKER_CONFIG_DIR` or `PORTBROKER_REGISTRY` to relocate the local registry for tests or restricted environments.

## Reservation commands

### Allocate or reuse a name

```bash
PORT="$(portbroker alloc --name my-app --persistent)"
```

`alloc` stores `name`, `port`, `host`, `proto`, timestamps, working directory, optional command and metadata, and persistence state. Existing names retain their assigned port.

Optional flags:

```bash
portbroker alloc --name api-server --range 8700-8999 --host 0.0.0.0 --proto tcp --persistent --meta group=backend --cmd "python3 -m http.server"
```

### Claim a chosen available port

```bash
portbroker claim --name dev-proxy --port "$PORT" --persistent
```

### Read, list, or free reservations

```bash
portbroker get --name my-app
portbroker list
portbroker list --json
portbroker free --name my-app
```

### Clean and diagnose

```bash
portbroker cleanup --dry-run
portbroker cleanup
portbroker doctor
portbroker probe --port "$PORT"
```

`cleanup` does not remove persistent reservations. `doctor` reports invalid entries and likely listener ownership drift without changing the registry.

## Coding agent integration

```bash
portbroker install-skill
portbroker install-skill --agents claude-code,codex,opencode
portbroker install-skill --agents codex --dry-run
```

When no `--agents` value is supplied, the command detects installed supported agents from their normal configuration directories. Installation is marker-based and idempotent.

| Agent | Destination |
| --- | --- |
| Claude Code | `~/.claude/skills/portbroker.md` |
| Codex | `~/.codex/AGENTS.md` |
| OpenCode | `~/.config/opencode/AGENTS.md` |

## Project helpers

For an npm application, inject named port setup into its start command:

```bash
portbroker project-init --name my-app
```

For an optional interactive shell helper:

```bash
portbroker install-shell
```

This installs a `dev my-app` convenience function that allocates a persistent named port, exports `PORT`, and runs `npm start`.

## Dashboard

```bash
PORT="$(portbroker get --name portbroker-dashboard 2>/dev/null || portbroker alloc --name portbroker-dashboard --persistent)"
portbroker web --host 0.0.0.0 --port "$PORT" --persistent
```

The dashboard serves the bundled polished UI, correlates reservations with active listeners, and groups entries when `meta.group` is present. The kill control sends `SIGTERM` only when a requested PID is currently verified as a listener on a registered endpoint.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Dashboard UI |
| `GET` | `/api/ports` | Reservation groups and live listener state |
| `GET` | `/api/health` | Health status |
| `GET` | `/whoami` | Service identity and bind details |
| `POST` | `/api/kill/<pid>` | Guarded termination of a verified active listener |

## Smoke test

```bash
PORT="$(portbroker alloc --name test-app --persistent)"
portbroker get --name test-app
portbroker list
portbroker cleanup --dry-run
portbroker doctor
portbroker free --name test-app
```
