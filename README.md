[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.md)
[![ru](https://img.shields.io/badge/lang-ru-yellow.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.ru.md)
[![by](https://img.shields.io/badge/lang-by-green.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.by.md)

# Florentine Abbot

Florentine Abbot is a project dedicated to the scanning and digital organization of home photo archives.

## Architecture & Standards

The project implements to some extent approaches from the **OAIS (Open Archival Information System)** reference model, developed by the **[Consultative Committee for Space Data Systems (CCSDS)](https://public.ccsds.org/)** — a standard for long-term data preservation used by archives and libraries.

OAIS is published as:
- **[CCSDS 650.0-M-3](https://public.ccsds.org/Pubs/650x0m3.pdf)** (Pink Book, 2019) — current version, freely available
- **[ISO 14721:2025](https://www.iso.org/standard/87471.html)** — formal international standard (identical to CCSDS 650.0-M-3 in content)

The project implements three functional blocks of OAIS:

- **Ingest** is implemented in `scan-batcher` and `file-organizer` — scanning automation, structured filename parsing, and metadata validation
- **Archival Storage** is implemented in `file-organizer` and `archive-keeper` — file organization, UUID assignment, XMP/EXIF metadata writing, and SHA-256 integrity control
- **Access** is implemented in `preview-maker` — generation of lightweight JPEG images from master files

For image digitization, the project also relies on recommendations from the **[Federal Agencies Digital Guidelines Initiative (FADGI)](https://www.digitizationguidelines.gov/)**:
- **[Technical Guidelines for Digitizing Cultural Heritage Materials, 3rd Edition](https://www.digitizationguidelines.gov/guidelines/FADGITechnicalGuidelinesforDigitizingCulturalHeritageMaterials_ThirdEdition_05092023.pdf)** (May 2023)

For metadata encoding and preservation, the project uses **[XMP (Extensible Metadata Platform)](https://www.adobe.com/devnet/xmp.html)**:
- **[ISO 16684-1:2019](https://www.iso.org/standard/75163.html)** — Extensible metadata platform (XMP) — Part 1: Data model, serialization and core properties
- **[XMP Specification Part 2: Additional Properties](https://github.com/adobe/xmp-docs/tree/master/XMPSpecifications)** (Adobe) — extended namespaces including XMP Media Management (xmpMM) for file history tracking

## Scanning (Scan Batcher)

A utility for automating and stabilizing the scanning workflow using external scanning software (for example, [VueScan](https://www.hamrick.com) by Ed Hamrick).

### Why this matters 

Modern scanning applications are powerful and flexible, but at scale their rich settings often turn into a problem: hundreds of options across multiple tabs are easy to change accidentally or forget to update.

Florentine Abbot addresses this with canonical INI profiles and a scripted workflow that provide:
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

## Automatic Organization (File Organizer)

> **⚠️ Status**: In development. Not yet fully tested or documented.

A tool to automatically organize scanned files based on their filenames. It extracts metadata from the filename (date, modifiers, role suffix) and moves each file into an archive tree with the default layout:

- `{output}/{year}/{year}.{month}.{day}/` — per-date folder (configurable via `formats.json`)
- `{output}/{year}/{year}.{month}.{day}/SOURCES/` — RAW, master (`MSR`) and related technical files
- `{output}/{year}/{year}.{month}.{day}/DERIVATIVES/` — derivatives such as WEB, PRT and other outputs
- `{output}/{year}/{year}.{month}.{day}/` — `*.PRV.jpg` files for quick browsing (preview/access copies) stored directly in the date folder

The archive structure is fully customizable through `formats.json` (see [Customizing Path and Filename Formats](#customizing-path-and-filename-formats-formatsjson) below).

The same date information is also written into the file's EXIF/XMP tags. For detailed rules and examples, see `docs/en/naming.md` (Parts 2 and 3).

### Usage

File Organizer provides two subcommands: `batch` (one-shot) and `watch` (daemon).

Both require `--input` (source/inbox folder) and `--output` (archive root). Input and output must not overlap.

**Batch Mode (process existing files):**
```sh
file-organizer batch --input "D:\Scans\Inbox" --output "D:\Archive"
```

**Batch Mode with recursive scan:**
```sh
file-organizer batch --input "D:\Scans\Inbox" --output "D:\Archive" -r
```

**Daemon Mode (watch for new files):**
```sh
file-organizer watch --input "D:\Scans\Inbox" --output "D:\Archive"
```

**Copy mode (keep source files):**
```sh
file-organizer batch --input "D:\Scans\Inbox" --output "D:\Archive" --copy
```

**With Metadata (using JSON config):**
1. Run `file-organizer` once without `--config` to generate a default config file based on `config.template.json`.
2. Open the created JSON file (typically under the user config directory) and edit the `metadata.languages` section. Each key under `languages` is a BCP‑47 language code (for example, `"ru-RU"`, `"en-US"`) with a block of human‑readable fields:

	 ```jsonc
	 "metadata": {
		 "languages": {
			 "ru-RU": {
				 "default": true,
				 "creator": ["Имя Фамилия", "Соавтор"],
				 "credit": "Название архива или коллекции",
				 "description": [
					 "Краткое описание серии или набора снимков.",
					 "Можно в несколько строк."
				 ],
				 "rights": "Строка про права и ограничения.",
				 "terms": "Условия использования (если нужны).",
				 "source": "Физический источник: коробка, альбом и т.п."
			 },
			 "en-US": {
				 "default": false,
				 "creator": ["Name Surname", "Co-author"],
				 "credit": "Archive or collection name",
				 "description": [
					 "Short description of the series or image set.",
					 "Can span multiple lines."
				 ],
				 "rights": "Rights and restrictions text.",
				 "terms": "Usage terms (if needed).",
				 "source": "Physical source: box, album, etc."
			 }
		 }
	 }
	 ```

	 One language block should have `"default": true`; its values are also written into the plain XMP fields (x‑default). The `creator` field is taken from the default language block and written once as a list of names; all other text fields (`description`, `credit`, `rights`, `terms`, `source`) are written per language.

3. Use `--config` to point to this file explicitly if needed:

```sh
file-organizer "D:\Scans\Inbox" --config "D:\Configs\file-organizer.json"
```

### Advanced Configuration

**Customizing Metadata Fields (`tags.json`):**

By default, File Organizer uses a standard set of XMP tags for metadata fields (`description`, `credit`, `rights`, `terms`, `source`). You can override these mappings by creating a `tags.json` file in the configuration folder:

```json
{
  "description": "XMP-dc:Description",
  "credit": "XMP-photoshop:Credit",
  "rights": "XMP-dc:Rights",
  "terms": "XMP-xmpRights:UsageTerms",
  "source": "XMP-dc:Source"
}
```

You can add custom fields by specifying new `"field_name": "XMP-namespace:TagName"` pairs. Then add that field to your language blocks in the config, and it will automatically be written to images with language variants.

**Customizing File Routing (`routes.json`):**

File routing rules are shared between `file-organizer` and `preview-maker`. Configuration files are located in:
- Windows: `%APPDATA%\florentine-abbot\routes.json`, `tags.json`, and `formats.json`
- Linux/macOS: `~/.config/florentine-abbot/routes.json`, `tags.json`, and `formats.json`

By default, files are organized as follows:
- `RAW`, `MSR` → `SOURCES/`
- `PRV` → date folder root (`.`)
- all others → `DERIVATIVES/`

You can override this logic by creating a `routes.json` file:

```json
{
  "RAW": "SOURCES",
  "MSR": "SOURCES",
  "PRV": ".",
  "COR": "MASTERS",
  "EDT": "EXPORTS"
}
```

Values:
- `"SOURCES"`, `"DERIVATIVES"`, or any folder name — create a subfolder under the date folder (e.g., `{year}/{year}.{month}.{day}/SOURCES/`)
- `"."` — place file directly in the date folder root

**Customizing Templates (`formats.json`):**

You can customize how incoming filenames are parsed and how archive paths/filenames are formatted. Create a `formats.json` file in your config directory:

```json
{
  "source_filename_template": "{year}.{month}.{day}.{hour}.{minute}.{second}.{modifier}.{group}.{subgroup}.{sequence}.{side}.{suffix}.{extension}",
  "archive_path_template": "{year:04d}/{year:04d}.{month:02d}.{day:02d}",
  "archive_filename_template": "{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
}
```

- `source_filename_template` — defines expected structure of incoming filenames. Each `{field}` becomes a regex capture group for parsing. Fields not present in the template receive default values and are not validated.
- `archive_path_template` — folder structure in the archive storage.
- `archive_filename_template` — normalized filename (without extension) in archive.

Available fields:
- Date/time: `{year}`, `{month}`, `{day}`, `{hour}`, `{minute}`, `{second}`
- Components: `{modifier}`, `{group}`, `{subgroup}`, `{sequence}`, `{side}`, `{suffix}`, `{extension}`

Format specifiers (standard Python formatting, for archive templates):
- `{year:04d}` — 4 digits with leading zeros (0000, 2024)
- `{month:02d}` — 2 digits with leading zero (01, 12)
- `{sequence:04d}` — 4 digits with leading zeros (0001, 0042)

Source filename template examples:
- Default: `"{year}.{month}.{day}.{hour}.{minute}.{second}.{modifier}.{group}.{subgroup}.{sequence}.{side}.{suffix}.{extension}"`
- Without time: `"{year}.{month}.{day}.{modifier}.{group}.{subgroup}.{sequence}.{side}.{suffix}.{extension}"`
- Underscore-separated: `"{year}_{month}_{day}_{modifier}_{group}_{sequence}.{extension}"`

Archive template examples:
- Flat structure: `"archive_path_template": "{year:04d}.{month:02d}.{day:02d}"`
- By month: `"archive_path_template": "{year:04d}/{year:04d}.{month:02d}"`
- By group: `"archive_path_template": "{group}/{year:04d}/{year:04d}.{month:02d}.{day:02d}"`
- Compact filename: `"archive_filename_template": "{year:04d}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}_{group}_{suffix}"`
- ISO-style: `"archive_filename_template": "{year:04d}-{month:02d}-{day:02d}_{hour:02d}-{minute:02d}-{second:02d}_{modifier}_{group}_{subgroup}_{sequence:04d}_{side}_{suffix}"`

All configuration files are optional. If absent, built-in defaults are used. These settings affect both file organization (`file-organizer`) and preview generation (`preview-maker`).

### Key modules

- `file_organizer/cli.py` — CLI (`batch`, `watch` subcommands).
- `file_organizer/organizer.py` — core batch workflow and per-file orchestration.
- `file_organizer/processor.py` — per-file filename parsing, validation, and metadata writing.
- `file_organizer/watcher.py` — daemon mode via watchdog, delegates to `FileOrganizer`.
- `file_organizer/metadata.py` — `ArchiveMetadata`: multilingual XMP field resolution.
- `file_organizer/constants.py` — default metadata configuration (`DEFAULT_METADATA`).
- `file_organizer/config.py` — config loading from `file-organizer/config.json`.

## Preview Maker (PRV Generator)

> **⚠️ Status**: In development. Not yet fully tested or documented.

The Preview Maker uses the same routing configuration (`routes.json`) as the File Organizer to locate master files and determine where to place preview images.

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

Image parameters (size, format, quality) are defined in the configuration file (`config.json`), not on the command line. Multi-format output is supported: JPEG, PNG, WebP, TIFF.

Preview Maker provides three subcommands: `batch` (one-shot), `watch` (daemon), and `convert` (single file).

**Batch Mode (generate previews for archive):**
```sh
preview-maker batch --path "D:\Archive\PHOTO_ARCHIVES"
```

**Batch Mode with overwrite:**
```sh
preview-maker batch --path "D:\Archive\PHOTO_ARCHIVES" --overwrite
```

**Daemon Mode (watch for new master files):**
```sh
preview-maker watch --path "D:\Archive\PHOTO_ARCHIVES"
```

**Process a single file (no metadata, no database orchestration):**
```sh
preview-maker process --file "D:\Archive\PHOTO_ARCHIVES\1950\1950.06.15\SOURCES\1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff" --output "D:\Temp\1950.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg"
```

Logging follows the same convention as other tools:
- default logs: `~/.florentine-abbot/logs/preview_maker.log`
- override directory via `--log-path` or `FLORENTINE_LOG_DIR`.

### Key modules

- `preview_maker/cli.py` — CLI (`batch`, `process`, `watch` subcommands).
- `preview_maker/maker.py` — preview orchestration for batch and daemon modes.
- `preview_maker/processor.py` — low-level single-file preview processing (resize + format write) without metadata or DB logic.
- `preview_maker/constants.py` — format maps, default sizes, and format aliases.
- `preview_maker/watcher.py` — daemon mode via watchdog, delegates to `Maker`.

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

### Key modules

- `archive_keeper/cli.py` — CLI entry point (`archive-keeper` command).
- `archive_keeper/keeper.py` — batch orchestration for archive integrity reconciliation.
- `archive_keeper/processor.py` — SHA-256 checksum calculation for one file.
- `archive_keeper/store.py` — DB boundary for archive lifecycle state transitions.
- `archive_keeper/watcher.py` — polling daemon wrapper over `Keeper`.

## Face Recognition (Face Recognizer)

> **⚠️ Status**: In development. Not yet fully tested or documented. Not included in the installable package; run from source.

A tool for automated face detection and identity clustering across a photo archive. It recursively scans a directory tree for images, detects faces using a pluggable detection backend, stores embeddings in a SQLite database, and clusters them into identity domains using DBSCAN.

- **Pluggable detector backends** — built-in support for InsightFace; additional detectors can be registered via entry points.
- **Incremental processing** — already-processed files are skipped unless `--overwrite` is specified.
- **Identity clustering** — DBSCAN groups detected face embeddings across images into identity domains.
- **Visualization** — draws bounding boxes on a JPEG preview for manual verification.

### Requirements

Optional dependencies are required. Install with the `face-insightface` extra from source:

```sh
pip install -e .[face-insightface]
```

### Usage

Run from the source tree using the module entry point:

**Scan for faces and cluster:**
```sh
python -m face_recognizer.cli batch --path "D:\Archive\PHOTO_ARCHIVES"
```

**Skip clustering:**
```sh
python -m face_recognizer.cli batch --path "D:\Archive\PHOTO_ARCHIVES" --no-cluster
```

**Re-process already indexed files:**
```sh
python -m face_recognizer.cli batch --path "D:\Archive\PHOTO_ARCHIVES" --overwrite
```

**Detect faces in one file (no database orchestration):**
```sh
python -m face_recognizer.cli process --file "D:\Archive\2024\photo.jpg"
```

**Preview detected faces on an image:**
```sh
python -m face_recognizer.cli preview --file "D:\Archive\2024\photo.jpg"
```

**Daemon mode:**
```sh
python -m face_recognizer.cli watch
```

For a full list of arguments:

```sh
python -m face_recognizer.cli --help
```

### Key modules

- `face_recognizer/cli.py` — CLI (`batch`, `process`, `preview`, `watch` subcommands).
- `face_recognizer/recognizer.py` — face-recognition orchestration for batch and daemon modes.
- `face_recognizer/detector.py` — detector plugin contract and registry.
- `face_recognizer/classes.py` — shared recognizer settings and data types.
- `face_recognizer/processor.py` — low-level single-file face detection without DB orchestration.
- `face_recognizer/store.py` — SQLite persistence for face embeddings.
- `face_recognizer/clusterer.py` — DBSCAN-based identity clustering.
- `face_recognizer/previewer.py` — visualization of detected faces on image previews.
- `face_recognizer/watcher.py` — polling daemon wrapper over `Recognizer`.

## Setup (Setup Runner)

A one-time interactive configuration tool. Run it once after installation to set up paths and generate configuration files for all daemons.

### What it does

- **Checks ExifTool** — verifies the dependency is installed; offers automatic installation via winget (Windows) or Homebrew (macOS), or prints manual instructions.
- **Configures paths** — asks for the inbox folder (where new scans arrive) and the archive root (where organized files go), and creates them if needed.
- **Writes daemon configs** — generates `config.json` for `file-organizer`, `preview-maker`, `tile-cutter`, and `face-recognizer`.
- **Creates a desktop shortcut** — places a shortcut to the web dashboard (`http://127.0.0.1:8000/`) on the desktop (Windows, macOS, Linux).
- **Optionally launches the web dashboard** — starts `florentine-web` immediately after setup.

### Usage

```sh
setup-runner
```

Config files are written to:
- Windows: `%APPDATA%\florentine-abbot\`
- Linux/macOS: `~/.config/florentine-abbot/`

### Key modules

- `setup_runner/cli.py` — CLI entry point (`setup-runner` command).
- `setup_runner/runner.py` — interactive setup logic; platform subclasses for Windows, macOS, Linux.

## Technical Details

### Shared modules

Used by all tools:

- `common/logger.py` — unified logging subsystem.
- `common/naming.py` — shared filename parser and validator.
- `common/router.py` — configurable file routing (filename pattern → subfolder mapping).
- `common/formatter.py` — customizable archive path and filename formatting.
- `common/tagger.py` — batch XMP/EXIF read/write abstraction over exiftool.
- `common/exifer.py` — EXIF metadata extraction and processing.
- `common/constants.py` — project-wide tag names, action constants, and default configurations.

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
- `florentine-web`
- `setup-runner`

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
- `face_recognizer.log` — Face Recognizer activity

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
