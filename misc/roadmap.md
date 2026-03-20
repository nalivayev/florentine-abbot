# Roadmap

## Ideas and future plans

### Metadata synchronization across master and derivatives

When a daemon (face-detector, future colorizer, etc.) updates metadata on a master file,
existing derivatives may become stale.

**Current stance:** all derivatives are treated as regenerable. When master metadata
changes, derivatives should be re-created from scratch. This is acceptable as long as
all derivative-producing operations are cheap (e.g. preview generation).

**Open question:** how to handle "expensive" derivatives — ones that took significant
time or manual effort to produce (e.g. manual retouching, long-running colorization).
These cannot simply be discarded and re-created.

**Distinguishing generated vs. manual derivatives via metadata:**

Derivatives can potentially be classified by inspecting their XMP metadata:

- *Indirect approach:* check the last `xmpMM:History` entry — if `softwareAgent` is a
  known daemon (`preview-maker`, `face-detector`, etc.), the file is auto-generated and
  safe to regenerate. Unreliable: third-party tools may not write History at all.

- *Explicit approach:* daemons write a dedicated tag when creating a derivative
  (e.g. a custom field `fa:generated = true`). Reliable, but requires a convention
  agreed upon by all daemons from the start.

**Candidate approaches for sync itself:**
- Mark derivatives as `generated` / `manual` — only regenerate `generated` ones
- For metadata-only changes, propagate tags to derivatives without re-creating content
- Accept staleness and let the user decide when to regenerate

**When to revisit:** when the first "expensive" derivative-producing tool is introduced.

---

### End-user distribution (Windows-first)

Currently the project requires programming skills to install and run. The target audience
is ordinary users with no command-line experience.

**Target UX:** a system tray application — user installs, configures watched folders via
a settings dialog, and forgets about it. Daemons run silently in the background.

**Required components:**
- System tray UI (`pystray` + `customtkinter`)
- Settings dialog (watched folders, daemon on/off toggles)
- Standalone Windows bundle (`PyInstaller` + bundled `exiftool`)
- Installer (Inno Setup → `.exe`)
- macOS / Linux packaging in the future

**Why not now:** this is effectively a second project on top of the existing one, roughly
equal in scope. Core functionality must be stable first.

**Incremental steps that move toward this goal:**
- Keep business logic decoupled from CLI (already done — organizer/maker classes are
  independent of `cli.py`)
- Maintain clean, file-based configuration (no manual JSON editing required at runtime)
- Ensure all daemons are startable/stoppable programmatically (needed for tray control)

**When to revisit:** when core tools (file-organizer, preview-maker, face-detector) are
stable and feature-complete.

---

### UI / Web: system messages in the log panel

When a daemon stops or crashes, add a formatted message to the log buffer in the same
format as the daemon's own output.

**Requires:** a `Logger` instance in `DaemonManager` with a custom handler that writes
formatted lines into `self._logs[name]`, so stop/crash events appear inline with the
daemon's output.

**When to revisit:** when daemon lifecycle events need to be visible in the log panel.

---

### file-organizer: `sort` subcommand (lightweight mode without pipeline)

Analogous to `preview-maker convert` — a low-level subcommand that sorts files by
filename structure without requiring the full pipeline (no scan-batcher upstream,
no metadata writing).

**Motivation:** useful for ad-hoc sorting, testing routing rules, and importing files
from outside the normal scan-batcher → file-organizer flow.

**Key design question:** unlike `preview-maker convert`, file organization is inherently
project-specific (filename parsing and destination routing both depend on Formatter and
Router). There is no "pure" equivalent to `Converter`. The `sort` mode is therefore
not a separate low-level class but rather `FileOrganizer` with optional pipeline stages
disabled.

**Proposed approach:**
- Extend `FileOrganizer` with flags: `skip_id_check` (no DocumentID/InstanceID required)
  and `no_metadata` (skip EXIF/XMP writing)
- Move metadata writing out of `FileProcessor.process()` into `FileOrganizer` so that
  the flag controls it at the orchestration level
- `FileProcessor` is reduced to filename parsing + validation only (or merged into
  `FileOrganizer` entirely)
- CLI: `file-organizer sort --input <path> --output <path>` with no `--config` required
  beyond project config (Formatter/Router are always needed for routing)

**Prerequisite:** move metadata writing from `FileProcessor` up to `FileOrganizer`
(clean separation of concerns, independently useful).

**When to revisit:** after metadata writing is moved to `FileOrganizer`.

---

### UI / Web: user management

Create, disable and delete users through the web admin interface.

**Requires:** `GET/POST/PATCH /api/v1/users` endpoints, a page under `/admin`.

**When to revisit:** once the auth layer is stable.

---

### UI / Web: password reset via CLI

A CLI command `florentine-web reset-password --username <name>` to restore access
without deleting the database.

**Motivation:** if the admin forgets their password, the only current option is to delete
`florentine.db` and go through setup again, destroying all users and sessions.

**When to revisit:** on demand.

---

### UI / Web: naming presets in the setup wizard

Step 2 of the setup wizard — choosing a folder structure template for the archive.

**Proposed presets:** `Year/Month`, `Year/Month/Day`, `Year`, custom template.
Presets write a corresponding `routes.json` to the config directory.

**Problem:** the current Router uses complex XMP-based routing, which is hard to
represent as simple presets without a dedicated "simple mode".

**When to revisit:** when the routing system is simplified or a separate simple routing
mode is introduced.

---

### UI / Web: photo gallery

Browsing the archive through the web interface.

**Core features:**
- Thumbnail grid (PRV files)
- Single photo viewer via Leaflet `CRS.Simple`
- Filtering by date, tags
- Virtual scrolling for large archives

**When to revisit:** once the admin section and setup wizard are stable.
