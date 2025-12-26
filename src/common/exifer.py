import json
import shutil
import subprocess
import atexit
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Sequence

from scan_batcher.constants import EXIF_DATE_FORMAT, EXIF_DATETIME_FORMAT


class Exifer:
    """
    Utility class for extracting and converting EXIF metadata from images.

    Provides methods for reading specific tags and writing metadata using exiftool.
    Optimized to use a shared persistent exiftool process (via -stay_open) to avoid
    process creation overhead for each operation.
    """
    
    # Shared state for persistent processes
    _processes: dict[str, subprocess.Popen] = {}
    _locks: dict[str, threading.Lock] = {}
    _global_lock = threading.Lock()

    def __init__(self, executable: str = "exiftool"):
        self.executable = executable
        if not shutil.which(self.executable):
             raise FileNotFoundError(f"Exiftool executable '{self.executable}' not found in PATH.")

    @classmethod
    def _get_process(cls, executable: str) -> subprocess.Popen:
        """Get or create a persistent exiftool process for the given executable."""
        with cls._global_lock:
            if executable not in cls._locks:
                cls._locks[executable] = threading.Lock()
                
        # Double-checked locking optimization not strictly needed here due to GIL, 
        # but good practice. We just use the lock for the specific executable.
        with cls._locks[executable]:
            if executable not in cls._processes or cls._processes[executable].poll() is not None:
                cls._start_process(executable)
            return cls._processes[executable]

    @classmethod
    def _start_process(cls, executable: str) -> None:
        """Start a new exiftool process in stay_open mode."""
        cmd = [executable, "-stay_open", "True", "-@", "-"]
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1  # Line buffered
            )
            cls._processes[executable] = process
            # Register cleanup only once per executable
            # (atexit handles duplicates fine, but let's be clean)
            pass 
        except Exception as e:
            raise RuntimeError(f"Failed to start exiftool: {e}")

    @classmethod
    def _stop_all(cls) -> None:
        """Stop all running exiftool processes."""
        for executable, process in cls._processes.items():
            if process.poll() is None:
                try:
                    if process.stdin:
                        process.stdin.write("-stay_open\nFalse\n")
                        process.stdin.flush()
                    process.communicate(timeout=2)
                except (IOError, OSError, subprocess.TimeoutExpired):
                    process.kill()
                    process.communicate()
        cls._processes.clear()

    def _run(self, args: Sequence[str]) -> str:
        """Run exiftool with arguments using the shared persistent process."""
        # Check for newlines in args which break -stay_open protocol
        if any("\n" in str(arg) for arg in args):
             return self._run_one_off(args)

        try:
            process = self._get_process(self.executable)
            
            # We need to lock usage of the process so multiple threads don't interleave commands
            with self._locks[self.executable]:
                # Re-check if process died while waiting for lock
                if process.poll() is not None:
                    process = self._get_process(self.executable) # Restart
                
                stdin = process.stdin
                stdout = process.stdout
                
                if not stdin or not stdout:
                    raise RuntimeError("Exiftool process streams are not available")

                # Write args
                for arg in args:
                    stdin.write(str(arg) + "\n")
                
                stdin.write("-execute\n")
                stdin.flush()
                
                # Read output
                output_lines = []
                while True:
                    line = stdout.readline()
                    if not line:
                        break 
                    if line.strip() == "{ready}":
                        break
                    output_lines.append(line)
                    
                return "".join(output_lines)
                
        except Exception:
            # Fallback to one-off if persistent process fails
            return self._run_one_off(args)

    def _run_one_off(self, args: Sequence[str]) -> str:
        cmd = [self.executable] + list(args)
        try:
            # Use utf-8 encoding and ignore errors to be safe with weird metadata
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="replace"
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Exiftool failed: {e.stderr}") from e
        except Exception as e:
            raise RuntimeError(f"Error running exiftool: {e}") from e

    def read_json(self, file_path: Path, args: Sequence[str] | None = None) -> dict[str, Any]:
        """Read metadata as JSON."""
        cmd_args = ["-json"]
        if args:
            cmd_args.extend(args)
        cmd_args.append(str(file_path))
        
        output = self._run(cmd_args)
        try:
            data = json.loads(output)
            if not data:
                return {}
            return data[0]
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse exiftool output: {e}") from e

    def read(self, file_path: Path, tag_names: list[str]) -> dict[str, Any]:
        """Read specific metadata tags.
        
        Args:
            file_path: Path to the image file.
            tag_names: List of tag names to read (e.g., ['XMP-exif:DateTimeDigitized', 'ExifIFD:CreateDate']).
            
        Returns:
            Dictionary with tag names as keys and their values.
        """
        args = ["-G1"]  # Use -G1 to get group prefixes in output
        for tag_name in tag_names:
            args.append(f"-{tag_name}")
        
        data = self.read_json(file_path, args)
        
        # Extract only the requested tags (exiftool returns full group:tag format)
        result = {}
        for key, value in data.items():
            # Skip non-tag fields
            if key in ["SourceFile", "ExifTool"]:
                continue
            result[key] = value
        
        return result

    def write(self, file_path: Path, tags: dict[str, Any], overwrite_original: bool = True) -> None:
        """Write metadata tags."""
        args = ["-overwrite_original"] if overwrite_original else []
        for tag, value in tags.items():
            if value is None:
                continue
            args.append(f"-{tag}={value}")
        
        args.append(str(file_path))
        self._run(args)

# Register cleanup
atexit.register(Exifer._stop_all)
