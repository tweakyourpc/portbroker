import json
import os
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "portbroker"


class PortbrokerCLITest(unittest.TestCase):
    def env(self, home: Path) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["PORTBROKER_CONFIG_DIR"] = str(home / "config")
        return env

    def run_cli(self, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            cwd=ROOT,
            env=self.env(home),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_install_skill_explicit_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            first = self.run_cli(home, "install-skill", "--agents", "codex,claude-code")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn("Summary: 2 installed", first.stdout)
            codex = home / ".codex" / "AGENTS.md"
            claude = home / ".claude" / "skills" / "portbroker.md"
            self.assertTrue(codex.exists())
            self.assertTrue(claude.exists())

            second = self.run_cli(home, "install-skill", "--agents", "codex,claude-code")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("Summary: 0 installed, 2 already installed", second.stdout)
            self.assertEqual(codex.read_text(encoding="utf-8").count("# managed by portbroker install-skill"), 1)

    def test_install_skill_auto_detect_and_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".config" / "opencode").mkdir(parents=True)
            result = self.run_cli(home, "install-skill", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Would install: opencode", result.stdout)
            self.assertFalse((home / ".config" / "opencode" / "AGENTS.md").exists())

    def test_alloc_and_get_reuse_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            alloc = self.run_cli(home, "alloc", "--name", "test-app", "--range", "28970-28990")
            self.assertEqual(alloc.returncode, 0, alloc.stderr)
            get = self.run_cli(home, "get", "--name", "test-app")
            self.assertEqual(get.returncode, 0, get.stderr)
            self.assertEqual(get.stdout.strip(), alloc.stdout.strip())

    def test_cwd_returns_recorded_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            alloc = self.run_cli(home, "alloc", "--name", "test-app", "--range", "28970-28990")
            self.assertEqual(alloc.returncode, 0, alloc.stderr)
            cwd = self.run_cli(home, "cwd", "--name", "test-app")
            self.assertEqual(cwd.returncode, 0, cwd.stderr)
            self.assertEqual(cwd.stdout.strip(), str(ROOT))

            cwd_json = self.run_cli(home, "cwd", "--name", "test-app", "--json")
            self.assertEqual(cwd_json.returncode, 0, cwd_json.stderr)
            self.assertEqual(json.loads(cwd_json.stdout), {"name": "test-app", "cwd": str(ROOT)})

    def test_cwd_errors_when_working_directory_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            registry = home / "config" / "ports.json"
            registry.parent.mkdir(parents=True)
            registry.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "entries": {
                            "missing-cwd": {"port": 28991, "host": "0.0.0.0", "proto": "tcp", "cwd": ""}
                        },
                    }
                ),
                encoding="utf-8",
            )
            cwd = self.run_cli(home, "cwd", "--name", "missing-cwd")
            self.assertEqual(cwd.returncode, 1)
            self.assertIn("has no working directory recorded", cwd.stderr)

    def test_grouped_snapshot_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            registry = home / "config" / "ports.json"
            registry.parent.mkdir(parents=True)
            registry.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "entries": {
                            "api-server": {"port": 28991, "host": "0.0.0.0", "proto": "tcp", "meta": {"group": "backend"}},
                            "dev-proxy": {"port": 28992, "host": "0.0.0.0", "proto": "tcp", "meta": {}},
                        },
                    }
                ),
                encoding="utf-8",
            )
            env = self.env(home)
            code = (
                "import json,runpy; "
                "m=runpy.run_path('portbroker'); "
                "m['safe_listeners_by_key']=lambda entries: ({}, None); "
                "print(json.dumps(m['build_dashboard_snapshot']('portbroker-dashboard','test')))"
            )
            result = subprocess.run(["python3", "-c", code], cwd=ROOT, env=env, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            snapshot = json.loads(result.stdout)
            self.assertEqual([group["key"] for group in snapshot["groups"]], ["backend", "ungrouped"])
            self.assertEqual(len(snapshot["ports"]), 2)
            self.assertEqual(snapshot["issues"], [])

    def test_snapshot_skips_invalid_entries_and_reports_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            registry = home / "config" / "ports.json"
            registry.parent.mkdir(parents=True)
            registry.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "entries": {
                            "api-server": {"port": 28991, "host": "0.0.0.0", "proto": "tcp", "meta": "bad-meta"},
                            "broken-api": {"port": "not-a-port", "host": "0.0.0.0", "proto": "tcp"},
                        },
                    }
                ),
                encoding="utf-8",
            )
            env = self.env(home)
            code = (
                "import json,runpy; "
                "m=runpy.run_path('portbroker'); "
                "m['safe_listeners_by_key']=lambda entries: ({}, None); "
                "print(json.dumps(m['build_dashboard_snapshot']('portbroker-dashboard','test')))"
            )
            result = subprocess.run(["python3", "-c", code], cwd=ROOT, env=env, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            snapshot = json.loads(result.stdout)
            self.assertEqual([port["name"] for port in snapshot["ports"]], ["api-server"])
            self.assertEqual(snapshot["summary"]["total"], 1)
            self.assertEqual({issue["name"] for issue in snapshot["issues"]}, {"api-server", "broken-api"})
            self.assertTrue(any(issue["level"] == "error" for issue in snapshot["issues"]))
            self.assertTrue(any(issue["level"] == "warning" for issue in snapshot["issues"]))

    def test_alloc_existing_name_moves_from_unverified_listener(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            first = self.run_cli(home, "alloc", "--name", "test-app", "--range", "28970-28972")
            self.assertEqual(first.returncode, 0, first.stderr)
            original_port = int(first.stdout.strip())

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                listener.bind(("127.0.0.1", original_port))
                listener.listen(1)

                second = self.run_cli(home, "alloc", "--name", "test-app", "--range", "28970-28972")

            self.assertEqual(second.returncode, 0, second.stderr)
            replacement_port = int(second.stdout.strip())
            self.assertNotEqual(replacement_port, original_port)

            registry = json.loads((home / "config" / "ports.json").read_text(encoding="utf-8"))
            self.assertEqual(registry["entries"]["test-app"]["port"], replacement_port)


if __name__ == "__main__":
    unittest.main()
