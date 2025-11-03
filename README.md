[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.md)
[![ru](https://img.shields.io/badge/lang-ru-yellow.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.ru.md)

# Florentine Abbot

A utility designed to automate and optimize the scanning workflow using [VueScan](https://www.hamrick.com) by Ed Hamrick.

## Features

- **Automatic calculation of optimal scanning DPI** based on photo and output requirements.
- **Batch processing**: interactive, single calculation, or folder-based workflows.
- **Flexible template system** for file naming and metadata, including EXIF extraction.
- **Workflow automation**: run VueScan with generated settings, move and rename output files, extract EXIF metadata.
- **Comprehensive logging** for all workflow steps.
- **Command-line interface** with argument validation and help.
- **Plugin system**: easily extend workflows by adding new plugins (see below).

## Main Utilities

- `scan_batcher/cli.py` — main CLI entry point (used for the `scan-batcher` command).
- `scan_batcher/batch.py` — batch and interactive DPI calculation logic.
- `scan_batcher/calculator.py` — DPI calculation algorithms.
- `scan_batcher/parser.py` — command-line argument parsing and validation.
- `scan_batcher/recorder.py` — logging utility.
- `scan_batcher/workflow.py` — base class for all workflow plugins.
- `scan_batcher/workflows/__init__.py` — plugin registration and discovery.
- `scan_batcher/workflows/vuescan/workflow.py` — workflow automation for VueScan.
- `scan_batcher/exifer.py` — EXIF metadata extraction and parsing.

## Template System

Templates are used in settings and file names to inject dynamic values.

**Template format:**

```
{<name>[:length[:align[:pad]]]}
```

- `name` — template variable name  
- `length` — total length (optional)  
- `align` — alignment (`<`, `>`, `^`; optional)  
- `pad` — padding character (optional)  

## Supported Template Variables

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

## Usage

Run the main workflow:

```sh
scan-batcher --workflow <path_to_ini> --engine vuescan --batch scan --min-dpi 300 --max-dpi 4800 --dpis 600 1200 2400 4800
```

The program will **interactively prompt** you for the photo and image dimensions during execution.

For a full list of arguments and options, use:

```sh
scan-batcher --help
```

## Command Line Arguments

### Available Arguments
- `-b, --batch` - Batch mode: scan (interactive), calculate (single calculation), or process (folder processing). Default: scan
- `-w, --workflow` - Path to the workflow configuration file (INI format) for batch processing
- `-t, --templates` - List of template key-value pairs for file naming or metadata, e.g. `-t year=2024 author=Smith`
- `-e, --engine` - Scan engine to use for processing (default: vuescan)
- `-mnd, --min-dpi` - Minimum allowed DPI value for scanning (optional)
- `-mxd, --max-dpi` - Maximum allowed DPI value for scanning (optional)
- `-d, --dpis` - List of supported DPI resolutions by the scanner, separated by space, e.g., `100 300 1200`
- `-r, --rounding` - Rounding strategy: `mx` (maximum), `mn` (minimum), `nr` (nearest). Default: nr

## Examples

### Interactive DPI calculation (scan mode)
```sh
scan-batcher --workflow examples/workflow.ini --batch scan --dpis 300 600 1200 2400
```
*The program will prompt you to enter photo dimensions interactively.*

### Single DPI calculation (calculate mode)
```sh
scan-batcher --workflow examples/workflow.ini --batch calculate --min-dpi 300 --max-dpi 4800 --dpis 600 1200 2400 4800 --rounding nr
```
*The program will prompt you to enter photo and image dimensions, then exit after one calculation.*

### Process files from folder
```sh
scan-batcher --workflow examples/workflow.ini --batch process /path/to/scanned/files --templates author="John Doe" project="Family Archive"
```
*Process existing files without interactive input.*

## Logging

All workflow steps and errors are logged to a file with the same name as the script and `.log` extension.

## Installation

### Prerequisites
- Python 3.8 or higher
- VueScan software (for scanning operations)

### Install from source

To install the package locally from the source directory, use:

```sh
pip install .
```

This will install all required dependencies and make the `scan-batcher` CLI command available in your system.

> **Note:**  
> It is recommended to use a [virtual environment](https://docs.python.org/3/library/venv.html) for installation and development.

### Development installation

For development with editable installation:

```sh
pip install -e .
```

To upgrade an existing installation, use:

```sh
pip install --upgrade .
```

---

For more details, see the [README.ru.md](README.ru.md) (in Russian).
