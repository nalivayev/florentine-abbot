import json
import shutil
import subprocess
import atexit
import threading
from pathlib import Path
from typing import Any, Sequence

from common.constants import EXIFTOOL_LARGE_FILE_TIMEOUT


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
        # Add -charset utf8 to properly handle UTF-8 encoded arguments
        # IMPORTANT: -charset utf8 must appear BEFORE -@ - so that exiftool knows
        # the input stream (stdin) is UTF-8 encoded.
        cmd = [executable, "-stay_open", "True", "-charset", "utf8", "-@", "-"]
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

    def _kill_process_and_signal(self, process: subprocess.Popen, event: threading.Event) -> None:
        """Kill process and set event flag. Used as Timer callback."""
        event.set()
        try:
            process.kill()
        except Exception:
            pass

    def _run(self, args: Sequence[str], timeout: float = EXIFTOOL_LARGE_FILE_TIMEOUT) -> str:
        """Run exiftool with arguments using the shared persistent process."""
        # Check for newlines in args which break -stay_open protocol
        if any("\n" in str(arg) for arg in args):
             return self._run_one_off(args, timeout=timeout)

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

                # Timeout handling via Event
                timeout_event = threading.Event()
                timer = threading.Timer(
                    timeout, 
                    self._kill_process_and_signal, 
                    args=(process, timeout_event)
                )
                timer.start()

                try:
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
                    
                    if timeout_event.is_set():
                        raise RuntimeError(f"Exiftool operation timed out after {timeout} seconds")
                    
                    if not line and process.poll() is not None:
                         raise RuntimeError("Exiftool process died unexpectedly during execution")

                    return "".join(output_lines)
                finally:
                    timer.cancel()
                
        except Exception:
            # Fallback to one-off if persistent process fails
            return self._run_one_off(args, timeout=timeout)

    def _run_one_off(self, args: Sequence[str], timeout: float | int | None = None) -> str:
        import tempfile
        
        # Check if any args contain newlines (multiline values)
        has_multiline = any("\n" in str(arg) for arg in args if str(arg).startswith("-") and "=" in str(arg))
        
        if not has_multiline:
            # Simple case: no multiline values, use standard argfile approach
            cmd = [self.executable, "-charset", "utf8", "-@", "-"]
            input_str = "\n".join(str(arg) for arg in args)
            
            try:
                result = subprocess.run(
                    cmd,
                    input=input_str,
                    capture_output=True,
                    text=True,
                    check=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                )
                return result.stdout
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(f"Exiftool failed: {exc.stderr}") from exc
        
        # Complex case: has multiline values
        # Use temporary files for multiline tag values with -TAG<=file syntax
        temp_files = []
        processed_args = []
        
        try:
            for arg in args:
                arg_str = str(arg)
                if arg_str.startswith("-") and "=" in arg_str and "\n" in arg_str:
                    # Extract tag and value
                    tag_part, value_part = arg_str.split("=", 1)
                    # Create temp file with the value
                    temp_file = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt")
                    temp_file.write(value_part)
                    temp_file.close()
                    temp_files.append(temp_file.name)
                    # Use -TAG<=file syntax
                    processed_args.append(f"{tag_part}<={temp_file.name}")
                else:
                    processed_args.append(arg_str)
            
            # Now use argfile with the processed args
            cmd = [self.executable, "-charset", "utf8", "-@", "-"]
            input_str = "\n".join(processed_args)
            
            try:
                result = subprocess.run(
                    cmd,
                    input=input_str,
                    capture_output=True,
                    text=True,
                    check=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                )
                return result.stdout
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(f"Exiftool failed: {exc.stderr}") from exc
        finally:
            # Clean up temp files
            for temp_file_path in temp_files:
                try:
                    Path(temp_file_path).unlink()
                except Exception:
                    pass

    def _read_json(self, file_path: Path, args: Sequence[str] | None = None) -> dict[str, Any]:
        """Read metadata as JSON.

        Internal helper used by :meth:`read` to fetch raw JSON output
        from exiftool and decode it into a Python dictionary.
        """
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

    def read(self, file_path: Path, tag_names: list[str], exclude_patterns: list[str] | None = None, include_patterns: list[str] | None = None) -> dict[str, Any]:
        """Read specific metadata tags.
        
        Args:
            file_path: Path to the image file.
            tag_names: List of tag names to read (e.g., ['XMP-exif:DateTimeDigitized', 'ExifIFD:CreateDate']).
                      Empty list means read all tags.
            exclude_patterns: Optional list of tag name patterns to exclude (prefix or substring match).
                             E.g., ['XMP-xmpMM:History'] will exclude tags starting with this prefix.
            include_patterns: Optional list of tag name prefixes to include.
                             E.g., ['XMP-', 'EXIF:', 'ExifIFD:'] will only include tags starting with these prefixes.
                             If not provided, all tags are included (subject to exclusions).
            
        Returns:
            Dictionary with tag names as keys and their values.
        """
        args = ["-G1"]  # Use -G1 to get group prefixes in output
        for tag_name in tag_names:
            args.append(f"-{tag_name}")
        
        data = self._read_json(file_path, args)
        
        # Extract only the requested tags (exiftool returns full group:tag format)
        result = {}
        for key, value in data.items():
            # Skip non-tag fields
            if key in ["SourceFile", "ExifTool"]:
                continue
            
            # Apply inclusion filter if provided (prefix match)
            if include_patterns:
                if not any(key.startswith(pattern) for pattern in include_patterns):
                    continue
            
            # Apply exclusion filters if provided (prefix match)
            if exclude_patterns:
                if any(key.startswith(pattern) for pattern in exclude_patterns):
                    continue
            
            # Normalize line endings: exiftool on Windows returns \r\n, but we write \n
            if isinstance(value, str):
                value = value.replace('\r\n', '\n')
            result[key] = value
        
        return result

    def write(self, file_path: Path, tags: dict[str, Any], overwrite_original: bool = True, timeout: int | None = None) -> bool:
        """Write metadata tags.
        
        Args:
            file_path: Path to the file.
            tags: Dictionary of tag names and values to write.
            overwrite_original: Whether to overwrite the original file.
            timeout: Timeout in seconds for large files (uses one-off mode if set).
            
        Returns:
            True if successful.
        """
        # Skip if no tags to write
        if not tags:
            return True
            
        args = []
        
        if overwrite_original:
            args.append("-overwrite_original")
            
        for tag, value in tags.items():
            if value is None:
                continue
            # Handle list values (e.g., Creator as multiple authors)
            # exiftool expects: -TAG=value1 -TAG=value2 ...
            if isinstance(value, list):
                for item in value:
                    if item is not None:
                        args.append(f"-{tag}={item}")
            else:
                args.append(f"-{tag}={value}")
        
        args.append(str(file_path))
        
        # Use one-off mode with timeout for large files to avoid hangs
        if timeout is not None:
            self._run_one_off(args, timeout=timeout)
        else:
            self._run(args) # Uses default timeout (EXIFTOOL_LARGE_FILE_TIMEOUT = 600s)

        # If no exception was raised, consider the write successful
        return True

# Register cleanup
atexit.register(Exifer._stop_all)
