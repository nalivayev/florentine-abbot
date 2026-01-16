[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.md)
[![ru](https://img.shields.io/badge/lang-ru-yellow.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.ru.md)

# Florentine Abbot

Florentine Abbot is a project dedicated to the scanning and digital organization of home photo archives.

## Architecture & Standards

Florentine Abbot attempts to implement core concepts of the **Open Archival Information System (OAIS)** reference model (ISO 14721), a standard widely used by national archives and libraries (NASA, Library of Congress) for long-term data preservation.

The system adapts these concepts for personal archiving:

- **Ingest (`Scan Batcher`)**: The process of receiving data, quality control (validation), and preparation for storage. It scans, checks, and batches the content.
- **Archival Storage (`File Organizer`)**: The long-term preservation component. It moves data to the "Masters" storage (`2_Masters`), assigning immutable identifiers and creating **Archival Information Packages (AIP)**.
- **Access (`Preview Maker`)**: The access component. Archives do not serve original Master files to users to prevent damage or loss. Instead, they create "user copies" (previews, PDFs, lower-res JPEGs). This module generates **Dissemination Information Packages (DIP)**.

This architecture ensures that the "Masters" remain untouched and secure while providing convenient access through lightweight derivatives.

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

## Automatic Organization (File Organizer)

> **⚠️ Status**: In development. Not yet fully tested or documented.

A tool to automatically organize scanned files based on their filenames. It extracts metadata from the filename (date, modifiers, role suffix) and moves each file into a working `processed/` tree with the layout:

- `processed/YYYY/YYYY.MM.DD/` — per-date folder (root of the date tree)
- `processed/YYYY/YYYY.MM.DD/SOURCES/` — RAW, master (`MSR`) and related technical files
- `processed/YYYY/YYYY.MM.DD/DERIVATIVES/` — derivatives such as WEB, PRT and other outputs
- `processed/YYYY/YYYY.MM.DD/` — `*.PRV.jpg` files for quick browsing (preview/access copies) stored directly in the date folder

The same date information is also written into the file's EXIF/XMP tags. For detailed rules and examples, see `docs/en/naming.md` (Parts 2 and 3).

### Usage

**Batch Mode (process existing files):**
```sh
file-organizer "D:\Scans\Inbox"
```

**Daemon Mode (continuous monitoring):**
```sh
file-organizer "D:\Scans\Inbox" --daemon
```

**With Metadata (using JSON config):**
1. Run `file-organizer` once without `--config` to generate a default config file based on `config.template.json`.
2. Open the created JSON file (typically under the user config directory) and fill in fields such as `creator`, `credit`, `rights`, `usage_terms`, `source`.
3. Use `--config` to point to this file explicitly if needed:

```sh
file-organizer "D:\Scans\Inbox" --config "D:\Configs\file-organizer.json"
```

## Preview Maker (PRV Generator)

> **⚠️ Status**: In development. Not yet fully tested or documented.

For existing structured archives, a helper tool can generate `PRV` preview JPEGs from `RAW`/`MSR` sources.

- Scans under a root path for `SOURCES/` folders
- For each structured filename with suffix `RAW` or `MSR`:
	- prefers `MSR` over `RAW` when both exist for the same base name;
	- writes a preview `*.PRV.jpg` into the date folder (parent of `SOURCES/`).
- Existing `PRV` files are kept unless `--overwrite` is specified.

Metadata for previews is derived from the corresponding master files:
- contextual EXIF/XMP fields (description, creator, rights, source, etc.) are copied from the `RAW`/`MSR` master;
- each `PRV` receives its own identifier;
- an explicit relation tag links the `PRV` back to its master.

**Batch Mode (generate previews for archive):**
```sh
preview-maker --path "D:\Archive\PHOTO_ARCHIVES" --max-size 2000 --quality 80
```

**With Overwrite:**
```sh
preview-maker --path "D:\Archive\PHOTO_ARCHIVES" --max-size 2400 --quality 85 --overwrite
```

Logging follows the same convention as other tools:
- default logs: `~/.florentine-abbot/logs/preview_maker.log`
- override directory via `--log-path` or `FLORENTINE_LOG_DIR`.

## Archive Integrity (Archive Keeper)

> **⚠️ Status**: In development. Not yet fully tested or documented. Not included in the installable package; run from source.

A tool to ensure the long-term integrity of your digital archive. It scans your archive folder, calculates SHA-256 hashes of all files, and stores them in a SQLite database. On subsequent runs, it detects:
- **New files** (Added)
- **Modified files** (Content changed)
- **Moved files** (Same content, different path)
- **Missing files** (Deleted or moved outside)
- **Corrupted files** (Bit rot detection)

### Usage

Run the tool directly from the source tree using the module entry point:

```sh
python -m archive_keeper.cli "D:\Archive\Photos"
```

This will create `archive.db` and populate it with the current state of the archive. Subsequent runs will compare the file system against this database.

## Technical Details

### Main Utilities

- `scan_batcher/cli.py` — main CLI entry point (used for the `scan-batcher` command).
- `archive_keeper/cli.py` — CLI for the `archive-keeper` tool.
- `file_organizer/cli.py` — CLI for the `file-organizer` tool.
- `preview_maker/cli.py` — CLI for the `preview-maker` tool.
- `preview_maker/maker.py` — core implementation for Preview Maker (PRV generation logic).
- `scan_batcher/batch.py` — batch and interactive DPI calculation logic.
- `scan_batcher/calculator.py` — DPI calculation algorithms.
- `scan_batcher/parser.py` — command-line argument parsing and validation.
- `common/logger.py` — unified logging subsystem used by all tools.
- `scan_batcher/constants.py` — centralized constants and enumerations (e.g., `RoundingStrategy`).
- `scan_batcher/workflow.py` — base class for all workflow plugins.
- `scan_batcher/workflows/__init__.py` — plugin registration and discovery.
- `scan_batcher/workflows/vuescan/workflow.py` — workflow automation for VueScan.
- `common/exifer.py` — EXIF metadata extraction and parsing shared across tools.
 - `common/archive_metadata.py` — centralized archival metadata policy for masters and derivatives.
 - `file_organizer/organizer.py` — batch workflow for organizing files into the `processed/` tree.
 - `file_organizer/processor.py` — per-file processing logic (parsing, validation, EXIF/XMP writing, moving files).
 - `file_organizer/monitor.py` — filesystem monitor (daemon mode) built on top of watchdog and `FileProcessor`.

### Installation

#### Prerequisites
- Python 3.10 or higher
- VueScan software (for scanning operations)

#### Install from source

To install the package locally from the source directory, use:

```sh
pip install .
```

This will install all required dependencies and make the main CLI commands available in your system:

- `scan-batcher`
- `file-organizer`
- `preview-maker`

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
- `file_organizer.log` — File Organizer (`file-organizer`) activity
- `archive_keeper.log` — Archive Keeper activity
 - `preview_maker.log` — Preview Maker (`preview-maker`) activity

**Custom log location:**

You can override the default location using either:

**1. CLI parameter (highest priority):**
```sh
scan-batcher --log-path /custom/logs --workflow examples/workflow.ini
file-organizer --log-path /custom/logs /path/to/scans
archive-keeper --log-path /custom/logs /path/to/archive
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
1. `--log-path` CLI parameter (per-command override)
2. `FLORENTINE_LOG_DIR` environment variable (session/system-wide)
3. Default: `~/.florentine-abbot/logs/`

This is useful for:
- **Development**: Quick override with `--log-path /tmp/debug`
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
- Scanning workflow (EN): [docs/en/scanning.md](docs/en/scanning.md)
- Digital workflow for born-digital photos (EN): [docs/en/digital_workflow.md](docs/en/digital_workflow.md)

---

For more details, see the [README.ru.md](README.ru.md) (in Russian).
