[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.md)
[![ru](https://img.shields.io/badge/lang-ru-yellow.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.ru.md)

# Florentine Abbot

Florentine Abbot is a project dedicated to the scanning and digital organization of home photo archives. 

> **⚠️ Project Status**: Currently, only the **Scan Batcher** utility is packaged and ready for use. Additional modules (`file_organizer`, `archive_keeper`) are in development and not yet fully tested or documented.

## Scanning (Scan Batcher)

A utility designed to automate and optimize the scanning workflow using [VueScan](https://www.hamrick.com) by Ed Hamrick.

### Why this matters 

VueScan is powerful, but its flexibility becomes a liability at scale: hundreds of settings across different tabs are easy to change by accident or miss.

Florentine Abbot addresses this with canonical INI profiles and a scripted workflow that deliver:
- **Predictability** — the same settings for every scan
- **Reproducibility** — the ability to repeat the process exactly, even months later
- **Standardization** — a single workflow shared by the team
- **Automation** — fewer manual steps and less chance of human error

### Features

- **Automatic calculation of optimal scanning DPI** based on photo and output requirements.
- **Batch processing**: interactive, single calculation, or folder-based workflows.
- **Flexible template system** for file naming and metadata, including EXIF extraction.
- **Workflow automation**: run VueScan with generated settings, move and rename output files, extract EXIF metadata.
- **Comprehensive logging** for all workflow steps.
- **Command-line interface** with argument validation and help.
- **Plugin system**: easily extend workflows by adding new plugins.

### Requirements

- Python 3.10+
- [ExifTool](https://exiftool.org/) must be installed and available in PATH.

### Usage

Run the main workflow:

```sh
scan-batcher --workflow <path_to_ini> --engine vuescan --batch scan --min-dpi 300 --max-dpi 4800 --dpis 600 1200 2400 4800
```

The program will **interactively prompt** you for the photo and image dimensions during execution.

On Windows PowerShell, the syntax is the same. For values with spaces, use quotes:

```powershell
scan-batcher --workflow .\examples\workflow.ini --batch scan --dpis 300 600 1200 2400 --templates author="John Doe" project="Family Archive"
```

For a full list of arguments and options, use:

```sh
scan-batcher --help
```

#### Command Line Arguments

- `-b, --batch` - Batch mode: scan (interactive), calculate (single calculation), or process (folder processing). Default: scan
- `-w, --workflow` - Path to the workflow configuration file (INI format) for batch processing
- `-t, --templates` - List of template key-value pairs for file naming or metadata, e.g. `-t year=2024 author=Smith`
- `-e, --engine` - Scan engine to use for processing (default: vuescan)
- `-mnd, --min-dpi` - Minimum allowed DPI value for scanning (optional)
- `-mxd, --max-dpi` - Maximum allowed DPI value for scanning (optional)
- `-d, --dpis` - List of supported DPI resolutions by the scanner, separated by space, e.g., `100 300 1200`
- `-r, --rounding` - Rounding strategy: `mx` (maximum), `mn` (minimum), `nr` (nearest). Default: nr. Internally uses `RoundingStrategy` enum

#### Examples

**Interactive DPI calculation (scan mode)**
```sh
scan-batcher --workflow examples/workflow.ini --batch scan --dpis 300 600 1200 2400
```
*The program will prompt you for photo dimensions interactively.*

**Single DPI calculation (calculate mode)**
```sh
scan-batcher --workflow examples/workflow.ini --batch calculate --min-dpi 300 --max-dpi 4800 --dpis 600 1200 2400 4800 --rounding nr
```
*The program will prompt for photo and image dimensions, then exit after one calculation.*

**Process files from folder**
```sh
scan-batcher --workflow examples/workflow.ini --batch process /path/to/scanned/files --templates author="John Doe" project="Family Archive"
```
*Process existing files without interactive input.*

### Template System

Templates are used in settings and file names to inject dynamic values.

**Template format:**

```
{<name>[:length[:align[:pad]]]}
```

- `name` — template variable name  
- `length` — total length (optional)  
- `align` — alignment (`<`, `>`, `^`; optional)  
- `pad` — padding character (optional)  

#### Supported Template Variables

- `user_name` — operating system user name  
- `digitization_year` — year of digitization (from EXIF or file modification time)  
- `digitization_month` — month of digitization  
- `digitization_day` — day of digitization  
- `digitization_hour` — hour of digitization  
- `digitization_minute` — minute of digitization  
- `digitization_second` — second of digitization  
- `scan_dpi` — DPI value selected or calculated during the batch or interactive workflow  
- ...plus any additional variables provided via command-line (`--templates key=value`) or batch templates

**Note:**  
If EXIF metadata is missing, date/time variables are filled with the file's modification time.

**Example:**
```
{digitization_year:8:>:0}
```

## Automatic Organization (Archive Organizer)

A tool to automatically organize scanned files based on their filenames. It extracts metadata from the filename (date, modifiers) and moves the file into a structured folder hierarchy (`YYYY.M/YYYY.MM.DD.M/SUFFIX`). It also writes this metadata into the file's EXIF/XMP tags.

### Usage

**Batch Mode (process existing files):**
```sh
archive-organizer "D:\Scans\Inbox"
```

**Watch Mode (daemon):**
```sh
archive-organizer "D:\Scans\Inbox" --watch
```

**With Metadata:**
```sh
archive-organizer "D:\Scans\Inbox" --creator "John Doe" --rights "All Rights Reserved"
```

## Archive Integrity (Archive Keeper)

A tool to ensure the long-term integrity of your digital archive. It scans your archive folder, calculates SHA-256 hashes of all files, and stores them in a SQLite database. On subsequent runs, it detects:
- **New files** (Added)
- **Modified files** (Content changed)
- **Moved files** (Same content, different path)
- **Missing files** (Deleted or moved outside)
- **Corrupted files** (Bit rot detection)

### Usage

```sh
archive-keeper "D:\Archive\Photos"
```

This will create `archive.db` and populate it with the current state of the archive. Subsequent runs will compare the file system against this database.

## Technical Details

### Main Utilities

- `scan_batcher/cli.py` — main CLI entry point (used for the `scan-batcher` command).
- `archive_keeper/cli.py` — CLI for the `archive-keeper` tool.
- `file_organizer/cli.py` — CLI for the `archive-organizer` tool.
- `scan_batcher/batch.py` — batch and interactive DPI calculation logic.
- `scan_batcher/calculator.py` — DPI calculation algorithms.
- `scan_batcher/parser.py` — command-line argument parsing and validation.
- `scan_batcher/recorder.py` — logging utility.
- `scan_batcher/constants.py` — centralized constants and enumerations (e.g., `RoundingStrategy`).
- `scan_batcher/workflow.py` — base class for all workflow plugins.
- `scan_batcher/workflows/__init__.py` — plugin registration and discovery.
- `scan_batcher/workflows/vuescan/workflow.py` — workflow automation for VueScan.
- `scan_batcher/exifer.py` — EXIF metadata extraction and parsing.

### Installation

#### Prerequisites
- Python 3.10 or higher
- VueScan software (for scanning operations)

#### Install from source

To install the package locally from the source directory, use:

```sh
pip install .
```

This will install all required dependencies and make the `scan-batcher` CLI command available in your system.

> **Note:**  
> It is recommended to use a [virtual environment](https://docs.python.org/3/library/venv.html) for installation and development.

#### Development installation

For development with editable installation:

```sh
pip install -e .
```

To upgrade an existing installation, use:

```sh
pip install --upgrade .
```

### Logging

All utilities write logs to a centralized location:

**Default location:**
- Linux/macOS: `~/.florentine-abbot/logs/`
- Windows: `C:\Users\<username>\.florentine-abbot\logs\`

**Log files:**
- `scan_batcher.log` — Scan Batcher activity
- `file_organizer.log` — File Organizer/Archive Organizer activity
- `archive_keeper.log` — Archive Keeper activity

**Custom log location:**

You can override the default location using either:

**1. CLI parameter (highest priority):**
```sh
scan-batcher --log-dir /custom/logs --workflow examples/workflow.ini
file-organizer --log-dir /custom/logs /path/to/scans
archive-keeper --log-dir /custom/logs /path/to/archive
```

**2. Environment variable:**
```sh
# Linux/macOS
export FLORENTINE_LOG_DIR=/var/log/florentine-abbot
scan-batcher --workflow examples/workflow.ini

# Windows PowerShell
$env:FLORENTINE_LOG_DIR = "D:\Logs\florentine-abbot"
scan-batcher --workflow examples\workflow.ini
```

**Priority order:**
1. `--log-dir` CLI parameter (per-command override)
2. `FLORENTINE_LOG_DIR` environment variable (session/system-wide)
3. Default: `~/.florentine-abbot/logs/`

This is useful for:
- **Development**: Quick override with `--log-dir /tmp/debug`
- **Daemon mode**: Set via ENV in systemd unit files
- **Docker**: Configure via `ENV` in Dockerfile
- **Centralized logging**: Point all tools to shared location

**Log features:**
- Unified timestamp format: `YYYY.MM.DD HH:MM:SS.mmm`
- Automatic rotation (10 MB per file, 5 backup copies)
- Console output + file logging
- Module name and log level in each entry

## Documentation

- Documentation index: [docs/README.md](docs/README.md)
- File naming guide (EN): [docs/en/naming.md](docs/en/naming.md)

---

For more details, see the [README.ru.md](README.ru.md) (in Russian).
