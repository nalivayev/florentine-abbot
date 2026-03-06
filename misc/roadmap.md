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
