# portbroker

`portbroker` is a lightweight named port registry for homelab and AI agent environments.

- Python standard library only (no external dependencies)
- Single-file CLI tool for deterministic port allocation and reuse
- Built for multi-project, concurrent CLI agent workflows

## Why this exists (AI agent skill first)

`portbroker` was designed to be used as a Codex/CLI agent skill so agents automatically allocate ports without conflicts across multiple concurrent projects.

Instead of hard-coding `3000`, `8000`, etc., agents should always request a named reservation first, then start services with that port.

## Install

```bash
chmod +x portbroker && sudo install -m 0755 portbroker /usr/local/bin/portbroker
```

## Core commands

Use named allocations so a service keeps a stable port identity.

```bash
# alloc: reserve a free port for a name
PORT=$(portbroker alloc --name my-service --host 0.0.0.0 --persistent)
echo "$PORT"

# get: read an existing reservation
portbroker get --name my-service

# list: show all reservations
portbroker list

# probe: inspect listeners on a specific port
portbroker probe --port "$PORT"

# doctor: validate registry health
portbroker doctor

# free: release a reservation
portbroker free --name my-service

# cleanup: remove stale non-persistent reservations
portbroker cleanup
```

## Dashboard (`web`)

Start the dashboard with a named reservation:

```bash
PORT=$(portbroker get --name portbroker-dashboard 2>/dev/null || portbroker alloc --name portbroker-dashboard --persistent)
portbroker web --name portbroker-dashboard --host 0.0.0.0 --port "$PORT" --persistent
```

The dashboard shows live reservation and listener state, including service name, port, host/proto, status, process metadata, persistence, and timestamps.

Endpoints:

- `GET /` dashboard UI
- `GET /api/ports` JSON view of tracked ports and listener state
- `GET /whoami` service identity (`service`, `version`, `pid`, `startedAt`, `host`, `port`)

## Dev shell helper (`portbroker-shell.sh`)

The helper script is at `scripts/portbroker-shell.sh`.

Source it in your shell:

```bash
source /path/to/portbroker-tool-src/scripts/portbroker-shell.sh
```

Then run:

```bash
dev my-app
```

`dev` will run `portbroker cleanup` in the background, reserve a persistent named port, export `PORT`, and start `npm start`.

## systemd user service (persistent dashboard)

Create `~/.config/systemd/user/portbroker-dashboard.service`:

```ini
[Unit]
Description=Portbroker Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/portbroker web --name portbroker-dashboard --host 0.0.0.0 --persistent
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
```

Enable and start:

```bash
systemctl --user daemon-reload
systemctl --user enable --now portbroker-dashboard.service
systemctl --user status portbroker-dashboard.service
```

## Privacy

Registry data is local only: `~/.config/portbroker/ports.json`.

It contains project names, assigned ports, and working directory paths. Do not share this file.

## More usage

See [USAGE.md](USAGE.md) for full command details.
