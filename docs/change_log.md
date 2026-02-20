# Change Log (Recent)

This log summarizes the most recent changes in the repository, with commit IDs, dates, and key files touched. Use it to quickly reconstruct context across devices.

## Commits

### [Pending] — 2026-02-20
refactor: subcommands CLI, composition watchers, DRY, daemon mode for preview-maker
- Added: `src/file_organizer/watcher.py`, `src/preview_maker/watcher.py`
- Deleted: `src/file_organizer/monitor.py`
- Modified: `src/file_organizer/cli.py`, `src/file_organizer/organizer.py`, `src/file_organizer/__init__.py`, `src/preview_maker/cli.py`, `src/preview_maker/maker.py`, `src/preview_maker/__init__.py`, `tests/file_organizer/test_organizer.py`, `tests/preview_maker/test_maker.py`, `tests/test_pipeline.py`, `tests/test_manual_pipeline.py`, `README.md`, `README.ru.md`, `docs/change_log.md`
- Features:
  - **file-organizer subcommands**: `file-organizer batch --input --output` and `file-organizer watch --input --output`; `--output` is required, input/output overlap validation via `is_relative_to()`
  - **preview-maker subcommands**: `preview-maker batch --path` and `preview-maker watch --path`
  - **Composition pattern**: `FileWatcher` and `PreviewWatcher` are thin wrappers around `FileOrganizer`/`PreviewMaker` respectively; all per-file logic delegated via `process_single_file()` / `should_process()`
  - **DRY refactoring**: extracted `process_single_file()` in both organizer and maker; eliminated ~130 lines of duplicated code from old monitor.py
  - **Rename**: `monitor.py` → `watcher.py`, `FileMonitor` → `FileWatcher`
  - 105 tests passing, 1 deselected (manual)

### [Pending] — 2026-01-22
feat: add extensible configuration for metadata tags and suffix routing
- Added: `src/file_organizer/tags.template.json`, `src/file_organizer/routes.template.json`, `tests/file_organizer/test_processor.py`
- Modified: `src/common/archive_metadata.py`, `src/common/config_utils.py`, `src/common/constants.py`, `src/file_organizer/config.py`, `src/file_organizer/organizer.py`, `src/file_organizer/processor.py`, `tests/file_organizer/test_organizer.py`, `tests/test_pipeline.py`, `pyproject.toml`, `README.md`, `README.ru.md`, `docs/change_log.md`
- Features:
  - Optional `tags.json` for customizing metadata field to XMP tag mapping
  - Optional `routes.json` for customizing file suffix routing rules
  - Both configs fall back to hardcoded defaults if files missing
  - Added `load_optional_config()` utility function
  - Refactored routing logic to use concrete folder names (SOURCES, DERIVATIVES, .)
  - 7 new routing tests in `test_processor.py`
  - All 72 tests passing

### 4bdda45 — 2026-01-15 22:55 (+03:00)
docs(en/digital_workflow): expand Part 5 to mirror RU — RAW vs DNG guidance, PRV folder, example structure
- Modified: `docs/en/digital_workflow.md`

### fb30acb — 2026-01-16 17:40 (+03:00)
Document PreviewMaker metadata and ArchiveMetadata
- Modified: `README.md`, `README.ru.md`

### f156640 — 2026-01-16 17:36 (+03:00)
Centralize archive metadata and integrate PreviewMaker
- Added: `src/common/archive_metadata.py`, `tests/preview_maker/test_preview_maker.py`
- Modified: `src/file_organizer/processor.py`, `src/preview_maker/maker.py`, `tests/test_pipeline.py`
- Deleted: `tests/file_organizer/test_preview_maker.py`

### 45676d6 — 2026-01-16 15:28 (+03:00)
Refactor file organizer & preview maker workflows; shared naming/validator
- Added: `src/common/constants.py`, `src/common/naming.py`, `src/file_organizer/__main__.py`, `src/file_organizer/organizer.py`, `src/preview_maker/maker.py`
- Modified: `README.md`, `README.ru.md`, `src/file_organizer/__init__.py`, `src/file_organizer/cli.py`, `src/file_organizer/monitor.py`, `src/file_organizer/processor.py`, `src/file_organizer/validator.py`, `src/preview_maker/__init__.py`, `src/preview_maker/__main__.py`, `src/preview_maker/cli.py`, `src/scan_batcher/parser.py`, multiple `tests/*`
- Deleted: `src/file_organizer/parser.py`, `src/file_organizer/preview_maker.py`, `src/preview_maker/core.py`

### 468465c — 2026-01-16 10:50 (+03:00)
Update README for preview_maker and archive_keeper
- Modified: `README.md`, `README.ru.md`

### 225f0bc — 2026-01-15 22:41 (+03:00)
docs(ru/naming): clarify filename date/time come from event; A/R pair shares event timestamp; scan date in metadata
- Modified: `docs/ru/naming.md`

### 2008cc6 — 2026-01-15 18:46 (+03:00)
Refactor preview maker into standalone package
- Added: `src/preview_maker/__init__.py`, `src/preview_maker/__main__.py`, `src/preview_maker/cli.py`, `src/preview_maker/core.py`
- Modified: `pyproject.toml`, `src/file_organizer/cli.py`, `src/file_organizer/preview_maker.py`, `tests/file_organizer/test_preview_maker.py`

### de6fd16 (tag: v1.0.5) — 2026-01-15 17:58 (+03:00)
Rename File Organizer CLI and update docs
- Modified: `README.md`, `README.ru.md`, `docs/en/scanning.md`, `docs/ru/scanning.md`, `pyproject.toml`

### 46cfd52 — 2026-01-15 16:23 (+03:00)
Add preview maker utility and update archive workflow docs
- Modified: `README.md`, `README.ru.md`, `docs/en/digital_workflow.md`, `docs/en/naming.md`, `docs/en/scanning.md`, `docs/ru/digital_workflow.md`, `docs/ru/naming.md`, `docs/ru/scanning.md`, `pyproject.toml`, `src/file_organizer/processor.py`, `tests/file_organizer/test_integration.py`, `tests/test_pipeline.py`
- Added: `src/file_organizer/preview_maker.py`, `tests/file_organizer/test_preview_maker.py`

### 1c5f28b — 2026-01-15 12:56 (+03:00)
refactor(storage): rename ARTEFACTS to DERIVATIVES
- Modified: `README.md`, `README.ru.md`, `docs/en/naming.md`, `docs/ru/naming.md`, `src/file_organizer/processor.py`, `tests/file_organizer/test_exiftool_compliance.py`, `tests/file_organizer/test_integration.py`, `tests/test_pipeline.py`

---

Tip: If you need to run tests, start with fast ones:
- `tests/file_organizer/test_leap_year.py` (date edge cases)
- `tests/test_pipeline.py` (pipeline expectations)
- `tests/preview_maker/test_preview_maker.py` (PreviewMaker)

Then run the full suite when ready.