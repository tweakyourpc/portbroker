# portbroker

`portbroker` is a local CLI to allocate, claim, and track service ports for this homelab.

- Language/runtime: Python 3, standard library only
- Default registry: `~/.config/portbroker/ports.json`
- Lock file: `~/.config/portbroker/ports.lock` (uses `fcntl` file locking)
- Port checks: `ss -ltnp` (or `ss -lunp` for UDP), with `lsof -iTCP -sTCP:LISTEN` fallback when `ss` is unavailable
- Persistence marker: entries can be marked `persistent` to protect them from auto-cleanup

## Install

### Option A: system-wide (`/usr/local/bin`)

```bash
sudo install -m 0755 ./portbroker /usr/local/bin/portbroker
which portbroker
```

### Option B: user-local (`~/bin`)

```bash
mkdir -p "$HOME/bin"
install -m 0755 ./portbroker "$HOME/bin/portbroker"
export PATH="$HOME/bin:$PATH"
which portbroker
```

If your environment is restricted and cannot write `~/.config`, set one of:

```bash
export PORTBROKER_CONFIG_DIR="$PWD/.portbroker-config"
# or:
export PORTBROKER_REGISTRY="$PWD/.portbroker-config/ports.json"
```

## Commands

### Allocate

```bash
portbroker alloc --name NAME [--range 8700-8999] [--host 0.0.0.0] [--proto tcp] [--persistent|-p] [--meta key=value ...] [--cmd "run command"]
```

- Picks a free port and stores:
  - `name`, `port`, `host`, `proto`, `createdAt`, `updatedAt`, `cwd`, `cmd`, `meta`, `persistent`
- `--persistent` marks the reservation so cleanup will not free it
- Output: port number only (unless `--json`)
- If a `persistent` reservation already exists for that name, returns the same port

### Claim

```bash
portbroker claim --name NAME --port PORT [--host 0.0.0.0] [--proto tcp] [--persistent|-p] [--meta key=value ...] [--cmd "run command"]
```

- Reserves a specific free port
- `--persistent` marks the reservation so cleanup will not free it
- Output: port number only (unless `--json`)
- To mark an existing reservation persistent:
  - `portbroker claim --name NAME --port "$(portbroker get --name NAME)" --persistent`

### Get

```bash
portbroker get --name NAME
```

- Prints port only
- Exits nonzero if missing

### Free

```bash
portbroker free --name NAME
```

### List

```bash
portbroker list
portbroker list --json
```

- Table columns: `name`, `port`, `host`, `proto`, `persistent`, `cwd`, `createdAt`, `lastSeenPid`

### Cleanup

```bash
portbroker cleanup
portbroker cleanup --dry-run
portbroker cleanup --json
```

- Frees stale reservations that are not listening and not marked `persistent`
- Never frees `persistent` entries
- `persistent` entries are released only via explicit `portbroker free --name NAME`
- `--dry-run` shows what would be freed without modifying the registry

### Project Init (Node)

```bash
portbroker project-init --name NAME [--package-json package.json] [--start-cmd "node server.js"]
```

- Updates `scripts.start` in `package.json` to inject:
  - `PORT=$(portbroker get --name NAME 2>/dev/null || portbroker alloc --name NAME --persistent)`
- If `scripts.start` is missing, use `--start-cmd` to provide the underlying app command
- Idempotent: if portbroker logic is already present, no rewrite is performed

### Install Shell Helper

```bash
portbroker install-shell
portbroker install-shell --shell bash
portbroker install-shell --shell zsh
```

- Installs the `dev` helper by appending a `source` block into your shell rc file
- Default helper path:
  - `~/.config/portbroker/portbroker-shell.sh`
- Auto-detects shell from `$SHELL`, or use `--shell bash|zsh`
- For custom/testing targets, use `--rc-file PATH`

### Web Dashboard

```bash
PORT=$(portbroker get --name portbroker-dashboard 2>/dev/null || portbroker alloc --name portbroker-dashboard --persistent)
portbroker web --name portbroker-dashboard --port "$PORT" --persistent
```

- Runs a live dashboard on `0.0.0.0` by default
- HTML dashboard: `/`
- JSON feed: `/api/ports`
- Homelab identity endpoint: `/whoami`
- `--verbose` enables request logging
- If `--port` is omitted, `web` reuses the named reservation or allocates from `--range`

### Doctor

```bash
portbroker doctor
portbroker doctor --json
```

- Validates registry integrity
- Flags duplicate/bad entries
- Checks for active ports that appear owned by a different process (best effort with available process data)
- Suggests recovery actions

### Probe (optional)

```bash
portbroker probe --port PORT [--proto tcp]
portbroker probe --port PORT --json
```

- Shows what is listening on the port

## Homelab usage pattern

Use in scripts/commands without hardcoding ports:

```bash
PORT=$(portbroker alloc --name terminus-config)
CONFIG_HOST=0.0.0.0 CONFIG_PORT=$PORT npm run config-server
```

For npm projects, initialize once so `npm start` handles port assignment automatically:

```bash
portbroker project-init --name my-app
npm start
```

Optional shell helper (`bash`/`zsh`) for manual projects:

```bash
portbroker install-shell
dev my-app
```

- `dev my-app` runs `portbroker cleanup` silently in the background
- Then it runs `portbroker alloc --name my-app --persistent`, exports `PORT`, and starts `npm start`
- Override broker binary if needed: `export PORTBROKER_BIN=/usr/local/bin/portbroker`

For the dashboard itself:

```bash
PORT=$(portbroker get --name portbroker-dashboard 2>/dev/null || portbroker alloc --name portbroker-dashboard --persistent)
portbroker web --name portbroker-dashboard --port "$PORT" --persistent
```

## Quick smoke test

```bash
# allocate
PORT=$(portbroker alloc --name smoke-portbroker --range 8900-8910 --host 0.0.0.0 --cmd "python3 -m http.server")
echo "$PORT"
# expected: a single integer in [8900, 8910]

# get
portbroker get --name smoke-portbroker
# expected: same integer

# list
portbroker list
# expected: one row containing name=smoke-portbroker and that port

# cleanup preview
portbroker cleanup --dry-run
# expected: reports stale non-persistent entries only

# probe (may show unknown process/pid if kernel permissions are restricted)
portbroker probe --port "$PORT"

# doctor
portbroker doctor
# expected: healthy or warning-level notes

# free
portbroker free --name smoke-portbroker

# confirm missing (nonzero)
portbroker get --name smoke-portbroker
# expected: error + nonzero exit code
```
