# Changelog

## 1.3.0 - 2026-09-27

- Added `portbroker cwd --name <service>` to print the working directory recorded for a reservation.
- Added JSON output for `portbroker cwd`.
- Updated the dashboard service cards to show recorded working directories and copyable `cd` commands.
- Changed the dashboard footer to display the running portbroker version from `/api/ports`.

## 1.2.0 - 2026-05-27

- Merged the standalone `portbroker-dashboard` application into `portbroker`.
- Replaced the inline basic dashboard with the polished disk-served dashboard asset.
- Added grouped dashboard responses and guarded `POST /api/kill/<pid>` support.
- Added `portbroker install-skill` for Claude Code, Codex, and OpenCode.
- Added the one-line user installer for the CLI, dashboard, and skill templates.
