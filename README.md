[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/nalivayev/florentine-abbot/blob/master/README.md)
[![ru](https://img.shields.io/badge/lang-ru-yellow.svg)](https://github.com/nalivayev/florentine-abbot/blob/master/README.ru.md)
[![by](https://img.shields.io/badge/lang-by-green.svg)](https://github.com/nalivayev/florentine-abbot/blob/master/README.by.md)

# Scan Batcher

Scan Batcher is a project dedicated to the scanning of home photo archives.

## Scanning

A utility for automating and stabilizing the scanning workflow using external scanning software (for example, [VueScan](https://www.hamrick.com) by Ed Hamrick).

### Why this matters 

Modern scanning applications are powerful and flexible, but at scale their rich settings often turn into a problem: hundreds of options across multiple tabs are easy to change accidentally or forget to update.

Scan Batcher addresses this with canonical INI profiles and a scripted workflow that provide:
- **Predictability** — the same settings for every scan run
- **Reproducibility** — the ability to repeat the process exactly, even months later
- **Standardization** — a single, shared workflow for the whole team
- **Automation** — fewer manual steps and less room for human error

### Features

- **Automatic calculation of optimal scanning DPI** based on photo characteristics and output requirements.
- **Batch processing**: interactive, single calculation, or folder-based workflows.
- **Flexible template system** for file naming and metadata, including EXIF extraction.
- **Workflow automation**: run the selected scan engine (e.g. VueScan) with generated settings, move and rename output files, extract EXIF metadata.
- **Comprehensive logging** for all workflow steps.
- **Command-line interface** with argument validation and help.
- **Plugin / engine system**: extend workflows by adding new scan engines or plugins.

### Requirements

- Python 3.10+
- [ExifTool](https://exiftool.org/) must be installed and available in PATH.
- At least one supported scanning engine (by default, the project provides integration with VueScan).

### Usage

Run the main workflow (example with VueScan as the engine):

```sh
scan-batcher --workflow <path_to_ini> --engine vuescan --batch scan --min-dpi 300 --max-dpi 4800 --dpis 600 1200 2400 4800
```

The program will **interactively prompt** you for the photo and image dimensions during execution.
On Windows PowerShell, the syntax is the same. For values with spaces, use quotes:

```powershell
scan-batcher --workflow .\examples\workflow.ini --engine vuescan --batch scan --dpis 300 600 1200 2400 --templates author="John Doe" project="Family Archive"
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

### Key modules

- `scan_batcher/cli.py` — main CLI entry point (`scan-batcher` command).
- `scan_batcher/batch.py` — batch and interactive DPI calculation logic.
- `scan_batcher/calculator.py` — DPI calculation algorithms.
- `scan_batcher/parser.py` — command-line argument parsing and validation.
- `scan_batcher/constants.py` — centralized constants and enumerations (e.g., `RoundingStrategy`).
- `scan_batcher/workflow.py` — base class for all workflow plugins.
- `scan_batcher/workflows/__init__.py` — plugin registration and discovery.
- `scan_batcher/workflows/vuescan/workflow.py` — workflow automation for VueScan.

## Technical Details

### Shared modules

Used across the project:

- `common/logger.py` — unified logging subsystem.
- `common/tagger.py` — batch XMP/EXIF read/write abstraction over exiftool.
- `common/exifer.py` — EXIF metadata extraction and processing.
- `common/constants.py` — project-wide tag names, MIME type mapping, and XMP history action constants.

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

Logs are written to a centralized location:

**Default location:**
- Linux/macOS: `~/.scan-batcher/logs/`
- Windows: `C:\Users\<username>\.scan-batcher\logs\`

**Log file:**
- `scan_batcher.log` — Scan Batcher activity

**Custom log location:**

You can override the default location using either:

**1. CLI parameter (highest priority):**
```sh
scan-batcher --log-path /custom/logs --workflow examples/workflow.ini
```

**2. Environment variable:**
```sh
# Linux/macOS
export SCAN_BATCHER_LOG_DIR=/var/log/scan-batcher
scan-batcher --workflow examples/workflow.ini

# Windows PowerShell
$env:SCAN_BATCHER_LOG_DIR = "D:\Logs\scan-batcher"
scan-batcher --workflow examples\workflow.ini
```

**Priority order:**
1. `--log-path` CLI parameter (per-command override)
2. `SCAN_BATCHER_LOG_DIR` environment variable (session/system-wide)
3. Default: `~/.scan-batcher/logs/`

This is useful for:
- **Development**: Quick override with `--log-path /tmp/debug`
- **Docker**: Configure via `ENV` in Dockerfile

**Log features:**
- Unified timestamp format: `YYYY.MM.DD HH:MM:SS.mmm`
- Automatic rotation (10 MB per file, 5 backup copies)
- Console output + file logging
- Module name and log level in each entry

## Architecture & Standards

The project implements to some extent approaches from the **OAIS (Open Archival Information System)** reference model, developed by the **[Consultative Committee for Space Data Systems (CCSDS)](https://public.ccsds.org/)** — a standard for long-term data preservation used by archives and libraries.

OAIS is published as:
- **[CCSDS 650.0-M-3](https://public.ccsds.org/Pubs/650x0m3.pdf)** (Pink Book, 2019) — current version, freely available
- **[ISO 14721:2025](https://www.iso.org/standard/87471.html)** — formal international standard (identical to CCSDS 650.0-M-3 in content)


For image digitization, the project also relies on recommendations from the **[Federal Agencies Digital Guidelines Initiative (FADGI)](https://www.digitizationguidelines.gov/)**:
- **[Technical Guidelines for Digitizing Cultural Heritage Materials, 3rd Edition](https://www.digitizationguidelines.gov/guidelines/FADGITechnicalGuidelinesforDigitizingCulturalHeritageMaterials_ThirdEdition_05092023.pdf)** (May 2023)

For metadata encoding and preservation, the project uses **[XMP (Extensible Metadata Platform)](https://www.adobe.com/devnet/xmp.html)**:
- **[ISO 16684-1:2019](https://www.iso.org/standard/75163.html)** — Extensible metadata platform (XMP) — Part 1: Data model, serialization and core properties
- **[XMP Specification Part 2: Additional Properties](https://github.com/adobe/xmp-docs/tree/master/XMPSpecifications)** (Adobe) — extended namespaces including XMP Media Management (xmpMM) for file history tracking

## Documentation

- Documentation index: [docs/README.md](docs/README.md)
- File naming guide (EN): [docs/en/naming.md](docs/en/naming.md)
- Scanning workflow (EN): [docs/en/scanning.md](docs/en/scanning.md)

---

For more details, see the [README.ru.md](README.ru.md) (in Russian).
