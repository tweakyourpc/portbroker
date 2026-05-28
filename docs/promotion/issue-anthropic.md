# Claude Code should reserve dev ports before starting local servers

```bash
# terminal A
python3 -m http.server 3000
# terminal B, in another AI coding session
python3 -m http.server 3000
# one process wins; the other session or browser tab can point at the wrong server
```

Claude Code can run in parallel with a human dev server or another agent session. When both reach for the same familiar port, the result is confusing: the browser tab, callback URL, or agent verification step may now be talking to the wrong local service.

## Current workaround

`portbroker` is a stdlib-only Python CLI that gives each local service a stable named reservation before it binds.

```bash
curl -fsSL https://raw.githubusercontent.com/tweakyourpc/portbroker/main/install.sh | sh
PORT="$(portbroker get --name my-app 2>/dev/null || portbroker alloc --name my-app --host 0.0.0.0 --persistent)"
HOST=0.0.0.0 PORT="$PORT" npm start
```

The workaround is useful, but it depends on agent instructions and shell discipline. Native agent support would be more reliable.

## Proposed native fix

Expose a small typed API the agent runtime can call before starting any HTTP/TCP service:

```ts
allocate_port({name, scope}) -> {port, fd?}
```

Suggested fields:

- `name`: stable service name, usually inferred from project and command intent.
- `scope`: workspace, repo, session, or user.
- `port`: assigned port the tool command should use.
- `fd`: optional pre-bound socket/file descriptor for runtimes that can avoid time-of-check/time-of-use races.

The important behavior is not a particular port range. It is that Claude Code coordinates named local services across concurrent sessions instead of independently guessing `3000`, `8000`, or `8080`.
