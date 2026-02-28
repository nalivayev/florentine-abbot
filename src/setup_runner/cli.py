"""
setup-runner CLI entry point.
"""

import sys

from setup_runner.runner import MacOSRunner, LinuxRunner, WindowsRunner, Runner


def main() -> int:
    _map: dict[str, type[Runner]] = {
        "win32":  WindowsRunner,
        "darwin": MacOSRunner,
    }
    return _map.get(sys.platform, LinuxRunner)()()


if __name__ == "__main__":
    raise SystemExit(main())
