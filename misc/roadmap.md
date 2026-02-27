# Roadmap

## Ideas and future plans

### Universal file routing

Currently `Router` is tightly coupled to a specific filename format — it extracts a
suffix token (`RAW`, `MSR`, `PRV`) via `FilenameParser` and uses it to determine the
target subfolder. Files with arbitrary names cannot be routed.

The goal is a routing scheme based on generic criteria — file extension, glob pattern,
or a priority-ordered list of rules — so that any file can be organized regardless of
its naming convention.

**Why not now:** Too many components depend on `FilenameParser` and the specific filename
format: `Router`, `FileProcessor`, `Formatter`, `preview_maker`. A proper fix requires
reworking the entire pipeline.

**When to revisit:** After the current filename/format architecture stabilises.

---

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
