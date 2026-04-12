"""
Daemon process manager.

Reads watch paths from each daemon's config.json, launches them as
subprocesses using the installed CLI scripts, and tracks their lifecycle.
"""

import json
import subprocess
import sys
import threading
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from common.config_utils import get_config_dir, get_archive_path


class DaemonStatus(str, Enum):
    STOPPED        = "stopped"
    RUNNING        = "running"
    CRASHED        = "crashed"        # exited without us calling stop()
    NOT_CONFIGURED = "not_configured"


@dataclass
class DaemonDescriptor:
    name: str          # CLI name, e.g. "file-organizer"
    label: str         # Display label
    description: str


@dataclass
class DaemonState:
    descriptor: DaemonDescriptor
    status: DaemonStatus
    watch_path: str | None = None
    output_path: str | None = None  # file-organizer only
    error: str | None = None


class DaemonManager:
    """
    Manages background daemon subprocesses.

    Reads paths from each daemon's config.json (watch.path / watch.output).
    Uses the installed CLI scripts to launch subprocesses.
    Thread-safe: all mutations protected by a lock.
    """

    _DESCRIPTORS = [
        DaemonDescriptor(
            name="preview-maker",
            label="Preview Maker",
            description="Watches archive for new masters and generates PRV previews.",
        ),
        DaemonDescriptor(
            name="tile-cutter",
            label="Tile Cutter",
            description="Watches archive for new masters and generates image tile pyramids.",
        ),
        DaemonDescriptor(
            name="archive-keeper",
            label="Archive Keeper",
            description="Monitors archive integrity: checksums, missing files, lifecycle tracking.",
        ),
    ]

    MAX_LOG_LINES = 500

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._processes: dict[str, subprocess.Popen[bytes] | None] = {
            d.name: None for d in self._DESCRIPTORS
        }
        # Daemons we explicitly stopped — distinguishes clean stop from crash.
        self._stopped_by_us: set[str] = set()
        # Daemons that exited on their own → maps name to last stderr output.
        self._crashed: dict[str, str] = {}
        # Per-daemon log buffers (stdout + stderr combined).
        self._logs: dict[str, list[str]] = {d.name: [] for d in self._DESCRIPTORS}

    def _read_output(self, name: str, proc: "subprocess.Popen[bytes]") -> None:
        """Read combined stdout+stderr line by line into the log buffer."""
        try:
            for raw in proc.stdout:
                line = raw.decode(errors="replace").rstrip()
                with self._lock:
                    buf = self._logs[name]
                    buf.append(line)
                    if len(buf) > self.MAX_LOG_LINES:
                        del buf[:len(buf) - self.MAX_LOG_LINES]
        except Exception:
            pass

    def get_logs(self, name: str) -> list[str]:
        """Return a snapshot of the log buffer for *name*."""
        with self._lock:
            return list(self._logs.get(name, []))

    def _find_script(self, name: str) -> str:
        """
        Return the full path to an installed CLI script.

        Looks in the same directory as sys.executable (venv Scripts/ on
        Windows, bin/ on Unix) before falling back to the bare name.
        """
        scripts_dir = Path(sys.executable).parent
        for ext in ("", ".exe", ".cmd"):
            candidate = scripts_dir / f"{name}{ext}"
            if candidate.exists():
                return str(candidate)
        return name  # let the OS resolve via PATH

    def _load_config(self, name: str) -> dict[str, Any]:
        config_path = get_config_dir() / name / "config.json"
        if not config_path.exists():
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    def _build_cmd(self, name: str, config: dict[str, Any]) -> list[str] | None:
        """Build the subprocess argv for a daemon, or None if not configured."""
        watch = config.get("watch", {})
        script = self._find_script(name)

        if name == "preview-maker":
            if get_archive_path() is None:
                return None
            return [script, "watch"]

        if name == "tile-cutter":
            if get_archive_path() is None:
                return None
            return [script, "watch"]

        if name == "archive-keeper":
            if get_archive_path() is None:
                return None
            return [script, "watch"]

        return None

    def _poll(self, name: str) -> None:
        """
        Check whether the stored process has exited. Must be called with
        self._lock held. Moves the daemon to _crashed if it died on its own.
        """
        proc = self._processes.get(name)
        if proc is not None and proc.poll() is not None:
            stderr = ""
            if proc.stderr:
                try:
                    stderr = proc.stderr.read().decode(errors="replace").strip()
                except Exception:
                    pass
            self._processes[name] = None
            if name not in self._stopped_by_us:
                self._crashed[name] = stderr or f"Exited with code {proc.returncode}"

    def all(self) -> list[DaemonState]:
        """Return current state for every daemon."""
        states: list[DaemonState] = []
        for d in self._DESCRIPTORS:
            config = self._load_config(d.name)
            watch = config.get("watch", {})
            watch_path = watch.get("path") or None
            output_path = watch.get("output") or None

            cmd = self._build_cmd(d.name, config)
            if cmd is None:
                states.append(DaemonState(
                    descriptor=d,
                    status=DaemonStatus.NOT_CONFIGURED,
                    watch_path=watch_path,
                    output_path=output_path,
                ))
                continue

            with self._lock:
                self._poll(d.name)
                running = self._processes.get(d.name) is not None
                crash_msg = self._crashed.get(d.name)

            if running:
                status, error = DaemonStatus.RUNNING, None
            elif crash_msg is not None:
                status = DaemonStatus.CRASHED
                error = crash_msg
            else:
                status, error = DaemonStatus.STOPPED, None

            states.append(DaemonState(
                descriptor=d,
                status=status,
                watch_path=watch_path,
                output_path=output_path,
                error=error,
            ))

        return states

    def start(self, name: str) -> None:
        """Launch the daemon subprocess. No-op if already running."""
        config = self._load_config(name)
        cmd = self._build_cmd(name, config)
        if cmd is None:
            raise ValueError(f"Daemon {name!r} is not configured or has no watch mode")

        with self._lock:
            self._poll(name)
            if self._processes.get(name) is not None:
                return  # already running
            self._stopped_by_us.discard(name)
            self._crashed.pop(name, None)
            self._logs[name] = []
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self._processes[name] = proc
            threading.Thread(
                target=self._read_output, args=(name, proc), daemon=True
            ).start()

    def stop(self, name: str) -> None:
        """Terminate the daemon subprocess. No-op if already stopped."""
        with self._lock:
            self._poll(name)
            self._stopped_by_us.add(name)
            self._crashed.pop(name, None)
            proc = self._processes.get(name)
            if proc is None:
                return
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            self._processes[name] = None


# Module-level singleton shared across all requests (single-worker uvicorn).
manager = DaemonManager()
