"""
Florentine Abbot — Setup Wizard.

Run once before first use to configure paths and create config files:

    python scripts/setup.py
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Installer(ABC):
    """
    Base wizard.  Handles shared steps: I/O, paths, config writing, dashboard.
    Platform subclasses override the exiftool-related methods.
    """

    _DAEMON_NAMES = ("file-organizer", "preview-maker", "face-detector")

    def __init__(self) -> None:
        if sys.platform == "win32":
            self.config_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "florentine-abbot"
        else:
            self.config_dir = Path.home() / ".config" / "florentine-abbot"

    def _ask(self, prompt: str, default: str | None = None) -> str:
        if default:
            full = f"  {prompt} [{default}]: "
        else:
            full = f"  {prompt}: "
        while True:
            try:
                answer = input(full).strip()
            except EOFError:
                if default is not None:
                    return default
                raise SystemExit("\nAborted.")
            if answer:
                return answer
            if default is not None:
                return default
            print("  (required — please enter a value)")

    def _ask_yn(self, prompt: str, default: bool = True) -> bool:
        hint = "Y/n" if default else "y/N"
        try:
            answer = input(f"  {prompt} [{hint}]: ").strip().lower()
        except EOFError:
            return default
        if not answer:
            return default
        return answer in ("y", "yes")

    def _load_json(self, path: Path) -> dict[str, Any]:
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    def _save_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        print(f"  Saved: {path}")

    def _load_template(self, module: str) -> dict[str, Any]:
        path = Path(__file__).resolve().parent.parent / "src" / module / "config.template.json"
        return self._load_json(path) if path.exists() else {}

    def _merge_watch(self, existing: dict[str, Any], template: dict[str, Any],
                     watch_update: dict[str, Any]) -> dict[str, Any]:
        """Start from template, overlay existing settings, then apply watch_update."""
        result = dict(template)
        result.update({k: v for k, v in existing.items() if k != "watch"})
        result["watch"] = {**template.get("watch", {}), **existing.get("watch", {}), **watch_update}
        return result

    def _ensure_dir(self, path_str: str, label: str) -> None:
        p = Path(path_str)
        if p.exists():
            return
        print(f"\n  Directory does not exist: {p}")
        if self._ask_yn(f"Create {label} directory?", default=True):
            p.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {p}")
        else:
            print("  Skipped — make sure to create it before starting the daemon.")

    def _configure_daemon(self, daemon: str, module: str, watch_update: dict[str, Any]) -> None:
        path = self.config_dir / daemon / "config.json"
        data = self._merge_watch(self._load_json(path) if path.exists() else {},
                                 self._load_template(module),
                                 watch_update)
        self._save_json(path, data)

    def _exiftool_ok(self) -> bool:
        return subprocess.run(["exiftool", "-ver"], capture_output=True).returncode == 0

    @abstractmethod
    def _step_exiftool(self) -> bool:
        """Check / install exiftool. Returns False if setup should abort."""

    def _step_paths(self) -> tuple[str, str] | None:
        """
        Ask for inbox/archive paths.
        Returns (inbox, archive), or None if the user chose not to reconfigure.
        """
        existing = [
            name for name in self._DAEMON_NAMES
            if (self.config_dir / name / "config.json").exists()
        ]
        if existing:
            print(f"  Found existing configs: {', '.join(existing)}")
            if not self._ask_yn("Reconfigure?", default=False):
                print("\n  Nothing changed. Exiting.")
                return None
            print()

        print("  Enter your archive paths:")
        print()
        inbox   = self._ask("Inbox folder  (where new scans arrive)")
        archive = self._ask("Archive root  (where organized files go)")
        print()

        self._ensure_dir(inbox,   "inbox")
        self._ensure_dir(archive, "archive root")
        print()

        return inbox, archive

    def _step_write_configs(self, inbox: str, archive: str) -> None:
        print("  Writing configuration files...")
        self._configure_daemon("file-organizer", "file_organizer", {"path": inbox, "output": archive})
        self._configure_daemon("preview-maker",  "preview_maker",  {"path": archive})
        self._configure_daemon("face-detector",  "face_detector",  {"path": archive})
        print()

    def _step_launch_dashboard(self) -> int:
        script = shutil.which("florentine-web") or "florentine-web"
        if self._ask_yn("Start the web dashboard now?", default=True):
            print(f"\n  Launching {script} ...")
            print("  Open http://127.0.0.1:8000/ in your browser.")
            print("  Press Ctrl+C to stop.\n")
            try:
                subprocess.run([script])
            except KeyboardInterrupt:
                pass
            except FileNotFoundError:
                print(f"\n  Could not find '{script}'.")
                print("  Install the package first:  pip install -e .[web]")
                return 1
        else:
            print(f"  To start later, run:  {script}")
        return 0

    def __call__(self) -> int:
        print()
        print("=" * 54)
        print("   Florentine Abbot — Setup Wizard")
        print("=" * 54)
        print()
        print(f"  Config directory: {self.config_dir}")
        print()

        if not self._step_exiftool():
            return 1
        print()

        result = self._step_paths()
        if result is None:
            return 0
        inbox, archive = result

        self._step_write_configs(inbox, archive)

        print("  Setup complete.")
        print()
        print(f"  Inbox:   {inbox}")
        print(f"  Archive: {archive}")
        print()

        return self._step_launch_dashboard()


class WindowsInstaller(Installer):
    """Windows: installs exiftool via winget or direct download."""

    def _reg_append_path(self, hive: int, subkey: str, directory: str) -> None:
        import winreg
        key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ | winreg.KEY_WRITE)
        try:
            current, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current = ""
        parts = [p.strip() for p in current.split(";") if p.strip()]
        if directory.lower() not in [p.lower() for p in parts]:
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ,
                              ";".join(parts + [directory]))
        winreg.CloseKey(key)

    def _add_to_path(self, directory: str) -> None:
        """Add directory to Windows PATH via registry; HKLM first, HKCU fallback."""
        import winreg
        try:
            self._reg_append_path(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                directory,
            )
            os.environ["PATH"] = os.environ.get("PATH", "") + ";" + directory
            print(f"  [OK] Added to system PATH (all users): {directory}")
            return
        except PermissionError:
            pass  # not admin — fall through to user PATH
        except Exception as e:
            print(f"  Warning: could not write system PATH: {e}")

        try:
            self._reg_append_path(winreg.HKEY_CURRENT_USER, "Environment", directory)
            os.environ["PATH"] = os.environ.get("PATH", "") + ";" + directory
            print(f"  [OK] Added to user PATH: {directory}")
            print("       (New terminal windows will pick this up automatically.)")
        except Exception as e:
            print(f"  [!!] Could not update PATH: {e}")
            print(f"       Add manually: {directory}")

    def _try_install(self) -> bool:
        if shutil.which("winget"):
            print("  Trying winget...")
            result = subprocess.run(
                ["winget", "install", "--id", "OliverBetz.ExifTool", "-e", "--silent"],
                capture_output=True,
            )
            if result.returncode == 0:
                if self._exiftool_ok():
                    print("  [OK] Installed via winget")
                    return True
                print("  [OK] Installed via winget (restart your terminal to update PATH)")
                return True

        print()
        install_dir = self._ask("Install directory", default=r"C:\Program Files\ExifTool")
        install_path = Path(install_dir)

        print()
        print("  Downloading from exiftool.org...")
        try:
            with urllib.request.urlopen("https://exiftool.org/", timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"  Could not reach exiftool.org: {e}")
            return False

        match = re.search(r'href="(exiftool-[\d.]+_64\.zip)"', html)
        if not match:
            match = re.search(r'href="(exiftool-[\d.]+\.zip)"', html)
        if not match:
            print("  Could not find a download link on exiftool.org")
            return False

        zip_name = match.group(1)
        url = f"https://exiftool.org/{zip_name}"
        print(f"  Downloading {url} ...")

        try:
            with tempfile.TemporaryDirectory() as tmp:
                zip_path = Path(tmp) / zip_name
                urllib.request.urlretrieve(url, str(zip_path))

                with zipfile.ZipFile(zip_path) as zf:
                    exe_entries = [n for n in zf.namelist() if n.lower().endswith(".exe")]
                    if not exe_entries:
                        print("  No .exe found in the archive")
                        return False

                    install_path.mkdir(parents=True, exist_ok=True)
                    target = install_path / "exiftool.exe"
                    # The exe ships as "exiftool(-k).exe"; rename on extraction.
                    with zf.open(exe_entries[0]) as src, open(target, "wb") as dst:
                        dst.write(src.read())

            print(f"  [OK] Installed to {target}")
            self._add_to_path(str(install_path))
            return self._exiftool_ok()

        except PermissionError:
            print(f"  Permission denied writing to {install_path}")
            print("  Choose a directory you own, or run the wizard as administrator.")
            return False
        except Exception as e:
            print(f"  Download failed: {e}")
            return False

    def _step_exiftool(self) -> bool:
        print("  Checking dependencies...")
        print()
        if self._exiftool_ok():
            print("  [OK] exiftool found")
            return True

        print("  [!!] exiftool not found")
        print()

        if self._ask_yn("Install exiftool automatically?", default=True):
            if self._try_install() and self._exiftool_ok():
                return True
            print("  Automatic install failed.")
            print()

        print("  Manual install options (Windows):")
        print("    winget install --id OliverBetz.ExifTool -e")
        print("    choco install exiftool")
        print("    scoop install exiftool")
        print("    Or download from https://exiftool.org/ (Windows Executable),")
        print("    rename exiftool(-k).exe → exiftool.exe, place on PATH.")
        print()
        return self._ask_yn("Continue setup without exiftool?", default=False)


class MacOSInstaller(Installer):
    """macOS: installs exiftool via Homebrew."""

    def _step_exiftool(self) -> bool:
        print("  Checking dependencies...")
        print()
        if self._exiftool_ok():
            print("  [OK] exiftool found")
            return True

        print("  [!!] exiftool not found")
        print()

        if self._ask_yn("Install exiftool automatically?", default=True) and shutil.which("brew"):
            print("  Installing via Homebrew...")
            result = subprocess.run(["brew", "install", "exiftool"])
            if result.returncode == 0 and self._exiftool_ok():
                return True
            print("  Automatic install failed.")
            print()

        print("  Install via Homebrew:  brew install exiftool")
        print()
        return self._ask_yn("Continue setup without exiftool?", default=False)


class LinuxInstaller(Installer):
    """Linux: no auto-install, prints package manager instructions."""

    def _step_exiftool(self) -> bool:
        print("  Checking dependencies...")
        print()
        if self._exiftool_ok():
            print("  [OK] exiftool found")
            return True

        print("  [!!] exiftool not found")
        print()
        print("  Install via your package manager:")
        print("    sudo apt install libimage-exiftool-perl   # Debian/Ubuntu")
        print("    sudo dnf install perl-Image-ExifTool      # Fedora")
        print()
        return self._ask_yn("Continue setup without exiftool?", default=False)


def main() -> int:
    _map: dict[str, type[Installer]] = {
        "win32":  WindowsInstaller,
        "darwin": MacOSInstaller,
    }
    return _map.get(sys.platform, LinuxInstaller)()()


if __name__ == "__main__":
    raise SystemExit(main())
