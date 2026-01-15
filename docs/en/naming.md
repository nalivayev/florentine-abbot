# Rules for the Storage of Digital Photographs in a Personal Archive

## Contents
- **Introduction**
- **Part 0: Quick Start**
- **Part 1: File Naming Rules**
- **Part 2: Storage Architecture**
- **Part 3: Archive Operation in Practice**
- **Part 4: Frequently Asked Questions (FAQ)**

---

## Introduction

Storing photos haphazardly with names like `IMG_1234.JPG` or `Scan001.tiff` makes an archive practically useless. Finding a specific shot is difficult, and the context of the photo — the date and event — is forgotten over time.

This guide describes naming and organization rules that turn chaos into an ordered structure. The goal of these rules is to make the archive understandable, easy to search, and durable, so that it remains accessible even decades from now.

**What you get by following these rules:**

*   **Order:** You'll never lose a photo in a pile of files again.
*   **Accessibility:** Fast and logical search by dates and categories.
*   **Preservation:** The context of each photo (who, what, where, when) will be known not only to you, but also preserved in the file's metadata.
*   **Continuity:** The archive will likely remain understandable even in 20, 30, or 50 years.

You can start simple using the rules from the **"Quick Start"**, and gradually move to the full format. After reading all three parts of the guide, you will have a complete understanding.

---

## Part 0. Quick Start

### Purpose of this chapter

Without reading the entire guide, quickly learn the basic principles and get started. You'll get a working approach that you can later refine.

### Getting started

#### Basic format: `YYYY.MM.DD.X.GGG.NNNN.A.extension`

| Component | Meaning | Examples |
|:-|:-|:-|
| **YYYY.MM.DD** | Shooting date | `1960.06.15` (exact) <br> `1975.08.00` (year and month known) <br> `1985.00.00` (year only known) |
| **X** | Date modifier | `E` - exact date <br> `C` - approximate date |
| **GGG** | Photo category | `FAM` - family <br> `TRV` - travel |
| **NNNN** | Sequential number | `0001`, `0002`, `0003`... |
| **A** | Scan side | `A` - obverse (front), always `A` for digital photos |

> **Important about obverse and reverse:** For scanned analog photos, use `A` for the front side and `R` for the back (if there are inscriptions, stamps). For digital photos, always use `A`.

#### Examples to start immediately

- Family portrait, exactly June 15, 1960 → `1960.06.15.E.FAM.0001.A.tiff`
- Landscape from a trip, circa 1985 → `1985.00.00.C.TRV.0001.A.jpg`
- A friend's photo, circa August 1975 → `1975.08.00.C.FRD.0001.A.tiff`
- Wedding, date unknown → `0000.00.00.A.WED.0001.A.tiff`
- Back of an old photo with inscriptions → `1960.06.15.E.FAM.0001.R.tiff`

**Main rule: START.** It's better to name a file `1990.00.00.C.XXX.0001.A.tiff` than to leave `IMG_8547.JPG`.

### Category code cheat sheet

Create your own codes or use these ready-made ones:

| Code | Meaning | Usage examples |
|:-|:-|:-|
| **FAM** | Family | Family portraits, home events |
| **TRV** | Travel | Vacation, trips, excursions |
| **WED** | Wedding | Ceremonies, banquets |
| **FRD** | Friends | Meetings with friends, parties |
| **EVT** | Events | Holidays, concerts, sports events |
| **WRK** | Work | Work moments, colleagues |
| **SCH** | Study | School, university, graduation |
| **HOL** | Leisure | Vacation, holidays, weekends |
| **000** | General | If you don’t know where to assign |

### Startup algorithm

#### Step 1: Preparation
Choose 10–20 test photos from different events. Create a `TEST` folder for experiments.

#### Step 2: Analyze each photo
For each file determine:

1. **Date:** What is known? Year? Month? Day?
2. **Modifier:** Is it exact (`E`) or approximate (`C`)?
3. **Category:** Which theme does it belong to?
4. **Number:** Start at `0001` for each new category

#### Step 3: Renaming
Manually rename files using the template `YYYY.MM.DD.X.GGG.0001.A.tiff`

**Example process:**
- Was: `DSC_1234.JPG`
- Became: `1987.05.00.C.FAM.0001.A.jpg`

#### Step 4: Fill in metadata (REQUIRED STEP!)

This is even more important than the perfect name! Right-click the file → Properties → Details or Comment.

**In the "Description" field, enter ALL known information:**
- Who is depicted (names, relationships)
- What is happening (event, holiday)
- Where the date comes from ("from grandmother's words", "inscription on the back")
- Shooting location

**Example description:**
*"John Smith (grandfather) and Mary Smith (grandmother) in the backyard of their house on Maple St. The picture was taken approximately in the summer of 1975. Information from Aunt Emma."*

---

**Congratulations! You've just laid the foundation of your future professional archive.**

### What’s next? How the archive structure will grow with you

This simplified approach is not a dead end. It’s a full-fledged core that you will gradually extend as your archive and needs grow.

| When you need... | What to add | Example |
|:-|:-|:-|
| More detail | Subgroup (`SSS`) | `1960.06.15.E.FAM.**POR**.0001.A.tiff` |
| Photos with exact time appear | Time (`HH.NN.SS`) | `1960.06.15.**14.30.00**.E.FAM.0001.A.tiff` |
| Complex dating | Other modifiers | `1940.00.00.**B**.FAM.0001.A.tiff` |

**Key advantage:** You won't have to change the names of already created files! You'll simply start using a longer and more precise format for *new* photos. All your old files will sort perfectly together with the new ones.

### Frequently asked questions at the start

**Question 1:** Can I use Cyrillic characters in category codes?

**Answer:** NO. Only uppercase Latin letters (`A-Z`) and digits. This ensures compatibility across all devices for 20+ years.

**Question 2:** What if I'm not sure about the date?

**Answer:** Use the `C` (circa) modifier and specify in the description where the date came from.

**Question 3:** Do I need to create a complex folder structure right away?

**Answer:** NO. Start with a simple folder "MY_ARCHIVE". Add structure later, when you have 100+ files.

---

> **Tips:** 
- try applying the instructions to a few files; this will give you more understanding than just reading the recommendations.
- if you're ready, study the full naming rules in Part 1: working with file versions, automation, and professional storage structure.

---

## Part 1. File Naming Rules

This guide describes file naming rules for photographs in a digital archive. The rules are designed to ensure uniqueness, readability, logical sorting, and long-term preservation in accordance with FADGI (Federal Agencies Digital Guidelines Initiative) recommendations. It is suitable for images of any origin: digitized paper photographs (both black-and-white and color), as well as digital photographs.

File name format: `YYYY.MM.DD.HH.NN.SS.X.GGG.SSS.NNNN.tiff`, where:
- Used for all file versions (RAW, master copy, derivatives) with suffixes (e.g., `.RAW.tiff`, `.MSR.tiff`).
- `TIFF` format is mandatory for archival files; for derivatives `JPEG`, `PNG`, and others may be used.
- Components are separated by a period (`.`) for readability and compatibility with file systems (Windows, macOS, Linux).

### 1. File name structure
The file name consists of the following components:

| Component | Description | Format | Example |
|:-|:-|:-|:-|
| YYYY | Year the photo was taken (or an approximate year). | **4 digits** | 1950 |
| MM | Month of creation (or 00 if unknown). | **2 digits** (`01–12`) | 06 |
| DD | Day of creation (or 00 if unknown). | **2 digits** (`01–31`) | 15 |
| HH | Hour of creation (or 00 if unknown). | **2 digits** (`00–23`) | 12 |
| NN | Minutes of creation (or 00 if unknown). | **2 digits** (`00–59`) | 00 |
| SS | Seconds of creation (or 00 if unknown). | **2 digits** (`00–59`) | 00 |
| X | Date modifier (indicates the type of date). | **1 uppercase Latin letter:** `A`, `B`, `C`, `E`, `F` | E |
| GGG | Group (photo category). | **3 characters:** only uppercase Latin letters (`A-Z`) OR digits (`0-9`) | FAM, 001, S35 |
| SSS | Subgroup (refining the group). | **3 characters:** only uppercase Latin letters (`A-Z`) OR digits (`0-9`) | POR, 101, V96 |
| NNNN | Sequential number of the photo within the group/subgroup. | **4 digits** (`0001–9999`) | 0001 |
| A/R | Scan side (for analog photos). | **1 letter:** `A` (obverse/front) or `R` (reverse/back) | A |
| .tiff | File extension (for archival copies — TIFF without compression). | .tiff or .tif | .tiff |

**Full example file name**:
- `1950.06.15.12.00.00.E.FAM.POR.0001.A.tiff` — exact date (June 15, 1950, 12:00), family portrait, number 0001, obverse.
- `1950.06.15.12.00.00.E.FAM.POR.0001.R.tiff` — reverse of the same portrait.
- `1950.00.00.00.00.00.C.001.101.0002.A.tiff` — circa 1950, group 001, subgroup 101, number 0002, obverse.

### 2. Date modifier (X)
The modifier is an uppercase Latin letter indicating the type of date. It provides logical sorting (alphabetical order: A, B, C, E, F), corresponding to the sequence: "unknown" → "before" → "circa" → "exact" → "after".

| Letter | Meaning | Description | Usage example |
|:-|:-|:-|:-|
| A | Absent (unknown) | Date completely unknown. Used with a zero date (`0000.00.00.00.00.00`). | `0000.00.00.00.00.00.A.FAM.POR.0001.A.tiff` — date unknown. |
| B | Before | Photo was taken before the specified date (e.g., before 1950). Use if the upper bound is known. | `1950.00.00.00.00.00.B.FAM.POR.0002.A.tiff` — before 1950. |
| C | Circa | Approximate date (year, month, or day is known with uncertainty, but not exact). Use if the date is not exact and not "before" or "after". | `1950.00.00.00.00.00.C.FAM.POR.0003.A.tiff` — circa 1950. <br> `1950.06.00.00.00.00.C.001.101.0004.A.tiff` — circa June 1950. |
| E | Exact | Exact date (year, month, day, and possibly time are known). Use if the date is confirmed (e.g., written on the photo). | `1950.06.15.12.00.00.E.FAM.POR.0005.A.tiff` — June 15, 1950, 12:00. |
| F | aFter | Photo was taken after the specified date (e.g., after 1950). Use if the lower bound is known. | `1950.00.00.00.00.00.F.FAM.POR.0006.A.tiff` — after 1950. |

**Sorting**: Files are sorted first by date (`YYYY.MM.DD.HH.NN.SS`), then by letter (`A`, `B`, `C`, `E`, `F`), then by group, and so on, which produces:
- `0000.00.00.00.00.00.A...` (unknown, at the beginning).
- `1950.00.00.00.00.00.B...` (before 1950).
- `1950.00.00.00.00.00.C...` (circa 1950).
- `1950.06.15.12.00.00.E...` (exact).
- `1950.00.00.00.00.00.F...` (after 1950).

### 3. Rules for date and time (YYYY.MM.DD.HH.NN.SS)
#### Rules for the date (YYYY.MM.DD)
- Known date: Use real values (e.g., `1950.06.15.12.00.00` for an exact date with modifier `E`).
- Partial date: Replace unknown parts with zeros (e.g., `1950.00.00.00.00.00` for year only or `1950.06.00.00.00.00` for year and month; use with `C` for approximate dates).
- Unknown date: Always `0000.00.00.00.00.00.A` (modifier `A` is mandatory).
- Updating the date: If the date is specified more precisely (e.g., from `1950.00.00.00.00.00.C` to `1950.06.15.12.00.00.E`), rename the file and update the metadata.

#### Rules for time (HH.NN.SS)
- **Known time:** Use real values (e.g., `12.30.15`) if known (e.g., imprinted on the photo by the camera or recorded in diaries).
- **Unknown time in the file name:** **Always use `00.00.00`.** This ensures uniformity and indicates that the exact time is unknown.
- **Conditional time in metadata:** In the `DateTimeOriginal` field for exact dates (`E`) with unknown time, set `12:00:00`. For non-exact dates (`A`, `B`, `C`, `F`), leave the field empty. If the time is known, specify it up to seconds.

### 4. Group (GGG)
- Description: 3-character code denoting the main category of the photo. Used for broad grouping, e.g., by theme, collection, or album.
- Format: 3 characters (letters or digits, uppercase for letters).
- Examples:
  - Letter codes:
    - FAM (Family — family photos).
    - WED (Wedding).
    - TRV (Travel).
    - HIS (Historical events).
  - Numeric codes:
    - 001 (e.g., for the first album or collection).
    - 002 (for the second album or collection).
- Usage: To ensure archive uniformity, choose one type of codes and use it consistently for all groups.
  - Letter codes (e.g., `FAM`, `TRV`) are suitable for descriptive categories.
  - Numeric codes (e.g., `001`, `002`) are ideal for numbering albums, boxes, or systematic collections.

#### Allowed characters and case
- Case: All letter codes must be in UPPERCASE.
- Allowed characters:
  - Latin letters: `A-Z`
  - Digits: `0-9`
- Not allowed: Cyrillic, spaces, hyphens, underscores, special characters.

#### Important:
- Observing uppercase is important for cross-platform compatibility (Windows/macOS/Linux) and to prevent duplicate files.
- When using codes, always use the same number of digits or letters. 
- For numeric codes, use the same number of digits with leading zeros (001, 002, ... 010, 011, ... 099, 100). This ensures proper alphabetical sorting in file managers. For example, `010` will be sorted after `009`, not after `002`.

### 5. Subgroup (SSS)
- Description: 3-character code refining the category set by the group. Helps organize within the group, e.g., by photo type or album subcategory.
- Format: 3 characters (letters or digits, uppercase for letters).
- Examples:
  - Letter codes:
    - POR (Portrait).
    - GRP (Group photo).
    - LND (Landscape).
    - EVT (Event).
  - Numeric codes:
    - 101 (e.g., for the first series within an album).
    - 102 (for the second series within an album).
- Usage: The type of codes for the subgroup must match the type chosen for the group.
  - Letter codes (e.g., `POR`, `LND`) describe the photo type.
  - Numeric codes (e.g., `101`, `102`) are ideal for details within numbered collections.

### Allowed characters and case
The rules completely match those for the group (GGG):
- Case: UPPERCASE (uppercase Latin letters)
- Allowed characters: `A-Z`, `0-9`
- Code type must match the type chosen for the group.

#### Important:
- As with groups, when using subgroup codes always use the same number of digits or letters.
- For numeric codes, use the same number of digits with leading zeros to ensure correct sorting.

**Recommendation**: Mixing letter and numeric formats for groups and subgroups within a single archive is acceptable. Choose one approach and use it across the entire archive. This gives systematization and predictability.

### 6. Sequential number (NNNN)
- 4-character identifier, unique within the subgroup.
- The simplest option is numeric. Start from `0001` for each new `SSS`.

### 7. Scanning side suffixes (for analog photographs)

- **`A`** — obverse (front side)
- **`R`** — reverse (back side)

*Examples:*
- `1950.06.15.12.00.00.E.FAM.POR.0001.A.tiff`
- `1950.06.15.12.00.00.E.FAM.POR.0001.R.tiff`

**Note**
- The date and time components in the filename (`YYYY.MM.DD.HH.NN.SS`) always reflect the event (original creation), not the scanning date.
- For an obverse/reverse pair, use the same event date, time, and date modifier; only the `A`/`R` suffix differs.
- The scanning date is stored in metadata, not in the file name.

### 8. File version suffixes

- **RAW copy**: `.RAW.tiff` (raw scan, TIFF without compression).
- **Master copy**: `.MSR.tiff` (minimally processed archival version, TIFF without compression).
- **Derivative files**:
  - `.WEB.jpg` (low resolution, 72 dpi, 80% compression for the web).
  - `.PRT.jpg` (high resolution, 300 dpi, 100% quality for print).
- Example: `1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff`, `1950.00.00.00.00.00.C.001.101.0002.R.RAW.tiff`.

### 9. Metadata and Automation

A file name ensures uniqueness and sorting, but it’s the metadata that carries the meaning, history, and context of the photograph. Filling out metadata is a mandatory step in the archiving process.

Tag filling can be automated. Data for field values can be extracted from filename components, set in general archive settings, or passed via processing script parameters.

Since the filename already contains all necessary chronological information in a structured form, the process of filling technical fields (dates) is recommended to be **automated** using specialized tools. Descriptive fields are filled manually.

#### Field Mapping Rules

Below describes how file name components and known information should be reflected in standard metadata fields (EXIF, IPTC, XMP).

**1. Dates (Date/Time)**
The logic for filling date fields depends on the date modifier in the file name:

*   **Digitization Date (`Exif.Photo.DateTimeDigitized`):**
    *   This field records the date and time when the photograph was scanned or digitized.
    *   **Automated process:** If the scanning software (e.g., VueScan) writes a `CreateDate` tag but does not set `DateTimeDigitized`, the archiving tools should automatically copy `CreateDate` to `DateTimeDigitized`.
    *   **Preservation:** If `DateTimeDigitized` is already set (e.g., by future versions of scanning software), it should not be overwritten.
    *   **Format:** `YYYY:MM:DD HH:MM:SS` (full timestamp from the scanning session).

*   **Original Date - Exact Dates (Modifier `E`):**
    *   `Exif.Photo.DateTimeOriginal`: The full date and time (`YYYY:MM:DD HH:MM:SS`) from the filename is written. This is the primary field for most software and represents when the original photograph was taken.
    *   `XMP-photoshop:DateCreated`: The full timestamp is written (`YYYY-MM-DDTHH:MM:SS`).

*   **Original Date - Non-Exact Dates (Modifiers `A`, `B`, `C`, `F`):**
    *   `Exif.Photo.DateTimeOriginal`: **Remains empty**. The EXIF standard requires an exact date and does not support partial values. Writing fictitious values (like `01.01`) distorts historical truth.
    *   `XMP-photoshop:DateCreated`: A partial date is written as far as it is known (`YYYY` or `YYYY-MM`). This allows professional software to correctly display the year or month.

**2. Description / Caption**
*   This is the most important field for manual filling.
*   **Content:** Who is depicted, what is happening, information source (e.g., "inscription on the back").
*   **For non-exact dates:** A text explanation of the date is mandatory here (e.g., "Circa 1950", "Before 1940").

**3. Identifiers**
*   It is recommended to generate and write a unique identifier (UUID) into the `XMP-dc:Identifier` and `XMP-xmp:Identifier` fields. This allows for unambiguous identification of the file even after renaming.

**4. Authorship and Rights**
For archive protection and attribution, it is recommended to fill in authorship and rights fields:

*   `XMP-dc:Creator`: Creator of the digital copy or archive author (e.g., `John Doe`).
*   `XMP-photoshop:Credit`: Who holds the credit for the image (e.g., `Doe Family Archive`).
*   `XMP-dc:Rights`: Rights information (e.g., `Public Domain` or `All Rights Reserved`).
*   `XMP-xmpRights:UsageTerms`: Usage terms (e.g., `Free to use with attribution`).
*   `XMP-dc:Source`: Original source (e.g., `Box 42`, `Grandma's Album`).

#### Summary Table of Examples

| Modifier | Exif.Photo.DateTimeOriginal | Exif.Photo.DateTimeDigitized | XMP-photoshop:DateCreated | Description (Example) |
|:-|:-|:-|:-|:-|
| **`A` (Absent)** | *(empty)* | `2025:11:29 14:00:21` | *(empty)* | `Unknown date. Graduation party. Digitized: 2025-11-29.` |
| **`B` (Before)** | *(empty)* | `2025:11:29 14:00:21` | `1940` | `Approximate date: before 1940. Digitized: 2025-11-29.` |
| **`C` (Circa)** | *(empty)* | `2025:11:29 14:00:21` | `1950` | `Approximate date: circa 1950. Digitized: 2025-11-29.` |
| **`C` (Circa)** | *(empty)* | `2025:11:29 14:00:21` | `1950-06` | `Approximate date: circa June 1950. Digitized: 2025-11-29.` |
| **`C` (Circa)** | *(empty)* | `2025:11:29 14:00:21` | `1950-06-15` | `Approximate date: circa June 15, 1950. Digitized: 2025-11-29.` |
| **`E` (Exact)** | `1950:06:15 12:30:45` | `2025:11:29 14:00:21` | `1950-06-15T12:30:45` | `Exact date and time: June 15, 1950, 12:30:45. Date imprinted on the photo. Digitized: 2025-11-29.` |
| **`F` (aFter)** | *(empty)* | `2025:11:29 14:00:21` | `1960` | `Approximate date: after 1960. Digitized: 2025-11-29.` |

**Note:** `DateTimeDigitized` should always be filled with the actual scanning/digitization timestamp (copied from `CreateDate` if not already set by scanning software).

### 10. Examples

- Unknown date: `0000.00.00.00.00.00.A.FAM.POR.0001.A.tiff` — family portrait, unknown date, obverse.
- Before a date: `1940.00.00.00.00.00.B.HIS.EVT.0002.A.tiff` — historical event, before 1940, obverse.
- Approximate date: `1950.00.00.00.00.00.C.001.101.0003.R.tiff` — circa 1950, album 1, series 101, reverse.
- Exact date: `1950.06.15.12.00.00.E.FAM.POR.0004.A.tiff` — family portrait, exactly June 15, 1950, 12:00, obverse.
- After a date: `1960.00.00.00.00.00.F.TRV.LND.0005.A.tiff` — landscape from a trip, after 1960, obverse.

### 11. FADGI Compliance

The naming rules are designed in accordance with the recommendations of FADGI (Federal Agencies Digital Guidelines Initiative) to ensure the long-term preservation of digital materials.

**Main principles of compliance:**

- **File formats:** Using `TIFF` without compression for archival copies (RAW, Master) meets long-term storage requirements. `ZIP` or `LZW` compression is acceptable.
- **Name uniqueness:** The combination of the date, modifier (`A`, `B`, `C`, `E`, `F`), group, subgroup, serial number, and side suffixes ensures global uniqueness of each file.
- **Readability:** The structured format is intuitive for both humans and automated systems.
- **Logical sorting:** The sequence of components ensures correct chronological organization in line with archival principles.
- **Semantic integrity:** The file name contains key metadata (event date), which aligns with the principle of content priority over technical attributes.
- **Independence from software:** The naming rules are not tied to any specific software or operating system.

> **References to standards and guidelines** see **Appendix A**.

### 12. Recommendations

- **Use `A`, `B`, `C`, `E`, `F`**: This ensures the desired sorting order (`A`, `B`, `C`, `E`, `F`).
- **Flexibility of groups and subgroups**: Choose letter (e.g., `FAM.POR`) or numeric (e.g., `001.101`) codes depending on the archive structure. Numeric codes are convenient for large collections or automation.
- **Metadata**: Duplicate information in metadata:
  - `0000.00.00.00.00.00.A` → `Description: Date absent`.
  - `1950.00.00.00.00.00.B` → `Description: Date approximate: before 1950`.
  - `1950.00.00.00.00.00.C` → `Description: Date approximate: circa 1950`.
  - `1950.06.15.12.07.25.E` → `DateTimeOriginal: 1950:06:15 12:07:25`, `Description: Date exact: 1950-06-15 12:07:25`.
  - `1950.00.00.00.00.00.F` → `Description: Date approximate: after 1950`.


### 13. Summary

These naming rules (`YYYY.MM.DD.HH.NN.SS.[A|B|C|E|F].GGG.SSS.NNNN.[A|R].SUF.EXT`) provide logical sorting (`A`, `B`, `C`, `E`, `F`) corresponding to the sequence: unknown → before → circa → exact → after. Groups and subgroups, highlighted in separate sections, can be letter-based (e.g., `FAM.POR`) or numeric (e.g., `001.101`), adding flexibility for large archives or automation.

---

## Part 2. Storage Architecture

### 1. Philosophy: from file to structure

The naming rules described in Part 1 are the core of the archive. They ensure uniqueness and logical order at the level of individual files. The storage architecture is the overlay that organizes these files into an intuitive directory hierarchy for easy navigation, management, and manual browsing.

**Key principle:** The directory structure should be simple, predictable, and cross-platform. It does not need to literally repeat all components of the file name, but it must provide an obvious link "year → date → specific file" and not interfere with the operation of professional tools.

### 2. Top level: multiple archives

You can keep multiple independent archives on the same filesystem.

It is recommended to allocate a common root directory (e.g., `PHOTO_ARCHIVES/`) and create separate folders for each archive:

```
PHOTO_ARCHIVES/
    0001.Family_Johnson/
    0002.Tech_Photos/
    0003.Personal_Author/
```

The `NNNN.Name` pattern provides:

* a numeric archive identifier (`NNNN`), convenient for scripts;
* a human-readable label (`Name`) understandable without documentation;
* ASCII-only names without Cyrillic or special characters, important for cross-platform compatibility.

The examples below use a single archive, `0001.Family_Johnson/`.

### 3. Chronological hierarchy inside an archive

Within a specific archive, a simple chronological structure is used: top-level year folders, and within each year — folders for individual dates.

Example structure for one archive:

```
PHOTO_ARCHIVES/
    0001.Family_Johnson/
        0000/
            0000.00.00/
        1930/
            1930.00.00/
        1945/
            1945.06.15/
        1960/
            1960.00.00/
        2024/
            2024.06.15/
```

### 4. File roles in a date folder

For each date (`YYYY.MM.DD`), all files are divided by roles. The role is encoded in the suffix (`SUF` in the format):

* `RAW` — raw scans / original digital negatives (`.RAW.tiff`, `.ARW`, etc.);
* `MSR` — master copy (archival master TIFF without compression);
* `PRV` — lightweight versions for quick viewing (preview, JPEG);
* `PRT` — files prepared for printing;
* auxiliary files required to reproduce the master copy from RAW (logs, profiles, development settings, etc.) use the same prefix as the corresponding RAW/MSR with a different extension.

**Important rule for the date folder:**

* the root of `YYYY.MM.DD/` contains only files with the `PRV` role — the primary access layer for viewing;
* the `SOURCES/` folder stores digital source materials: RAW, master copies, and all auxiliary files necessary for reproducibility;
* the `DERIVATIVES/` folder stores derived files (print versions, web copies, additional edited TIFF/JPEG, project files, etc.) that can be regenerated from `SOURCES/` if needed.

This guarantees that when browsing the archive in a file manager, the user sees only lightweight, viewable copies, while the technical storage layer remains separate, structured, and fully reproducible.

### 5. Recommended structure of a date folder

The following structure is recommended for each date:

```
PHOTO_ARCHIVES/
    0001.Family_Johnson/
        1945/
            1945.06.15/
                1945.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg
                1945.06.15.12.00.00.E.FAM.POR.0002.A.PRV.jpg
                SOURCES/
                    1945.06.15.12.00.00.E.FAM.POR.0001.A.RAW.tiff
                    1945.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff
                    1945.06.15.12.00.00.E.FAM.POR.0001.A.RAW.vuescan.log
                    1945.06.15.12.00.00.E.FAM.POR.0001.target.icc
                    1945.06.15.12.00.00.E.FAM.POR.0002.A.RAW.tiff
                    1945.06.15.12.00.00.E.FAM.POR.0002.A.MSR.tiff
                DERIVATIVES/
                    1945.06.15.12.00.00.E.FAM.POR.0001.A.PRT.jpg
```

Here:

* `SOURCES/` — folder with digital source materials for this date: RAW, master copies, and all auxiliary files required to reproduce the master copy from RAW;
* `DERIVATIVES/` — folder for derived files (print versions, web copies, additional edits, project files, etc.) that can be recreated from the source materials if needed;
* PRV files are located in the root of the date folder and represent the primary access layer.

**Path examples:**

* Exact date, master copy:
    * file: `1945.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff`
    * path: `PHOTO_ARCHIVES/0001.Family_Johnson/1945/1945.06.15/SOURCES/1945.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff`

* Approximate date (year only known):
    * file: `1930.00.00.00.00.00.C.HIS.000.0005.A.RAW.tiff`
    * path: `PHOTO_ARCHIVES/0001.Family_Johnson/1930/1930.00.00/SOURCES/1930.00.00.00.00.00.C.HIS.000.0005.A.RAW.tiff`

* Completely unknown date:
    * file: `0000.00.00.00.00.00.A.UNK.000.0001.A.MSR.tiff`
    * path: `PHOTO_ARCHIVES/0001.Family_Johnson/0000/0000.00.00/SOURCES/0000.00.00.00.00.00.A.UNK.000.0001.A.MSR.tiff`

### 6. Quick viewing (PRV)

All files in the root of `YYYY.MM.DD/` are lightweight viewing versions (`PRV`).

A PRV file is the **best currently available viewing copy**:

* if a master copy (`MSR`) has not yet been produced, it is acceptable to create `PRV` directly from `RAW` (for example via batch conversion);
* once an `MSR` exists, PRV files can (and ideally should) be regenerated **from the master copy**, reusing the same `*.PRV.jpg` name.

**Recommendations for PRV files:**

* format: JPEG (for maximum compatibility);
* resolution: typically 150–300 DPI;
* long side length: 1600–2400 pixels (depends on use case and storage);
* file name retains the full naming structure but with the `.PRV.jpg` suffix.

**Example:** `1945.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg`

This allows you to open any date in a file manager and quickly browse all images without touching heavy RAW/MSR files.

### 7. Special date cases (B, F, unknown dates)

Special modifiers (`B`, `F`, `A`) do not affect the folder structure and are reflected only in file names:

* `B` (Before) — "before the specified date";
* `F` (aFter) — "after the specified date";
* `A` (Absent) — date completely unknown.

Placement rules:

* for `1930.00.00.00.00.00.C...` — folder `1930/1930.00.00/`;
* for `1950.00.00.00.00.00.B...` — folder `1950/1950.00.00/`;
* for `1960.00.00.00.00.00.F...` — folder `1960/1960.00.00/`;
* for `0000.00.00.00.00.00.A...` — folder `0000/0000.00.00/`.

Thus, the modifier defines only the semantics of the date and the sorting of names, but does not complicate the directory layout.

### 8. FADGI compatibility (for folder structure)

The proposed architecture is aligned with FADGI recommendations and common digital repository practice:

* **Separation by file roles.** RAW files and master copies (`MSR`) are physically separated from derivatives (`PRV`, `PRT`), matching the principle of keeping originals and derivatives distinct.
* **Logical organization by event date.** Grouping by event date rather than processing date preserves the historical context of materials.
* **Simplicity and predictability.** A single `Archive/Year/Date/` pattern simplifies automation (scripts, tools) and manual navigation.
* **Independence from fonds/series structure.** Traditional archival levels (fonds/series/file/item) can be represented in metadata and external catalogues without being hard-coded into file paths.

### 9. Recommendations for managing the structure

1. **Use batch renaming and automatic layout.** Scripts or programs can derive the correct year and date from the file name and automatically place the file into the appropriate `SOURCES/` folder for that date.
2. **Control path length.** Ensure the full file path does not exceed filesystem limits (e.g., 260 characters in Windows). Use short names for archive root folders.
3. **Be consistent.** Once you adopt this structure, use it for all archives. This ensures uniformity and predictability over many years.



---

## Part 3. Archive Operation in Practice

### 1. Typical workflows

#### Scenario 1: Digitizing a new album

1. Preparation:
    * Create a temporary `INCOMING/` folder at the archive root.
    * Scan all photos from the album to uncompressed TIFF, saving them to `INCOMING/`.
    * Pre-name files for convenience (e.g., `Album5_001.tiff`).

2.  **Research and assigning names:**
    *   Study each photo: determine the date (exact or approximate), choose the group (`GGG`) and subgroup (`SSS`).
    *   Assign names to files according to the rules from Part 1 using batch renaming.
    *   **Example:** Source `Album5_001.tiff` → `1968.07.00.00.00.00.C.FAM.VAC.0001.A.RAW.tiff`

3. Filling metadata:
    * Open each file in a metadata editor (e.g., Adobe Bridge).
    * Fill the `Description` field with all known information.
    * For exact dates (`E`), fill in `Exif.Photo.DateTimeOriginal`.

4. Organizing into the structure:
    * Using batch tools or a file manager, move files from `INCOMING/` to corresponding folders according to the architecture from Part 2.
    * Example: `1968.07.00.00.00.00.C.FAM.VAC.0001.A.RAW.tiff` → `.../1968/1968.07.00/SOURCES/1968.07.00.00.00.00.C.FAM.VAC.0001.A.RAW.tiff`

5. Creating derivative copies:
    * From Master copies, create files for WEB, PRT, and PRV.
    * Distribute them into corresponding folders within the day.

#### Scenario 2: Batch renaming digital photos

1. Preparation:
    * Copy photos from the camera to the `INCOMING/` folder.
    * Make sure the camera date and time are set correctly.

2. Automatic renaming:
    * Use Adobe Bridge ("Tools" → "Batch Rename").
    * In the settings, specify:
        * Text: `.#!`
        * Creation date (EXIF): `YYYY.MM.DD.HH.NN.SS`
        * Text: `.E.` (modifier for exact date)
        * Text: `[GGG].[SSS].` (set manually for the entire series)
        * Sequential number: Start from `0001`
    * Result: `IMG_1234.JPG` → `2024.12.25.15.05.10.E.VAC.ALP.0001.A.jpg`

3. Post-processing:
    * Manually verify and adjust names if necessary.
    * Fill in metadata, especially the `Description` field.
    * Place files within the archive structure.

#### Scenario 3: Clarifying a date and batch renaming

1. Discovering new information:
    * An exact date was found for the photo `1950.00.00.00.00.00.C.FAM.000.0045.A.tiff` — June 15, 1950.

2. Renaming:
    * Use software that supports batch template-based renaming (e.g., Advanced Renamer, Total Commander).
    * Set a replacement rule:
        * Find: `1950.00.00.00.00.00.C`
        * Replace: `1950.06.15.12.00.00.E` (set time to 12:00:00 if unknown)
    * Result: `1950.00.00.00.00.00.C.FAM.000.0045.A.tiff` → `1950.06.15.12.00.00.E.FAM.000.0045.A.tiff`

3. Updating metadata and structure:
    * Update the `Exif.Photo.DateTimeOriginal` field in the file.
    * In the `Description` field add: "Date clarified on 2025-01-10 from circa 1950 to exact 1950-06-15 based on the inscription on the back of the original."
    * Move the file to the new folder: from `.../1950/1950.00.00/` to `.../1950/1950.06.15/`.

#### Scenario 4: Searching photos in the archive

1. Chronological search:
    * Use the folder structure. To find photos for July 1968, go to `.../1968/1968.07.00/` (PRV files `*.PRV.jpg` will be in the date folder root).

2. Thematic search:
    * Use the operating system’s search.
    * Example search in Windows: In the Explorer search field enter: `*.PRV.jpg description:="John Smith"`

3. Search by technical parameters:
    * Use cataloging programs (Adobe Bridge, Lightroom).
    * Create collections by keywords, ratings, or other metadata.

### 2. Software and tools

#### For batch renaming:
*   **Adobe Bridge** (cross-platform, powerful tool with metadata support)
*   **Advanced Renamer** (Windows, free, powerful and flexible)
*   **NameChanger** (macOS, simple and effective)
*   **Renamer** (Windows, Russian interface)

#### For metadata management (EXIF, IPTC, XMP):
*   **Adobe Bridge** (integrated metadata work)
*   **ExifTool** (command line, maximum power and automation)
*   **Exif Pilot** (Windows, GUI for ExifTool)
*   **Metadata++** (Windows, free viewer and editor)

#### For viewing and cataloging:
*   **Adobe Bridge/Lightroom** (professional suite)
*   **XnView MP** (cross-platform, free for non-commercial use, supports many formats)
*   **FastStone Image Viewer** (Windows, fast and convenient)

#### Example script for ExifTool (advanced level):

```bash
# Example: Rename all JPG files in the current folder using the date from EXIF
exiftool -d "%Y.%m.%d.%H.%M.%S" '-filename<${DateTimeOriginal}.E.${Model;tr/ /_/}.${SubSecTimeOriginal}.%e' -ext jpg .

**Note:** ExifTool scripts require precise understanding of the syntax and testing on file copies. For most batch renaming tasks, graphical tools are sufficient.
```
### 3. Rules for maintaining order

1. Regular procedures:
    * Quarterly: Check archive integrity (absence of corrupted files).
    * When adding new materials: Immediately apply the full processing cycle — naming, metadata, placement in the structure.
    * Once a year: Make a full backup and check the relevance of the tools.

2.  **Backup (3-2-1 rule):**
    *   **3** copies of data
    *   **2** different media types (e.g., HDD + cloud)
    *   **1** copy in a remote location

    **Example strategy:**
    *   **Working copy:** On the main computer.
    *   **Local backup:** On an external hard drive, updated weekly.
    *   **Remote copy:** In cloud storage (Backblaze, Yandex Disk, Google Drive) or on a drive in another building.

### 4. Conclusion. Your archive as historical heritage

An archive created according to these rules is not just a collection of files. It is a **structured digital heritage** with several key properties:

*   **Durability:** Standardized names and structure will be clear even 50 years from now.
*   **Independence:** The archive is not tied to specific software and can be read on any operating system.
*   **Context:** Rich metadata preserves the history of each photo for future generations.
*   **Scalability:** The rules will work for 100 photos and for 100,000 photos.

Starting small — with the proper naming of a few files — you lay the foundation for a professional archival fund whose value will only increase over time.

---

## Part 4. Frequently Asked Questions (FAQ)

### About file naming

**Question 1:** Why use the date the photograph (event) was taken in the file name rather than the scanning date?

**Answer:** This is a fundamental requirement for archival storage in accordance with **FADGI** and other international standards (such as **Dublin Core**).

* **Meaning and context:** The event date is key meta-information that defines the historical and cultural context of the object. The file name is the first and basic level of description.
* **Logical sorting:** Using the event date allows photos to be arranged chronologically, rather than in the order of their scanning (processing).
* **Immutability:** The event date is an immutable attribute. The digitization date is technical information that should be stored in the appropriate metadata fields of the digital image (e.g., in the `DateTimeDigitized` field). Separating this data prevents confusion and guarantees the file name will not have to be changed when migrating the archive to new media or storage systems.

**Conclusion:** The digitization date is important, but its place is in the file metadata, not in its name.

**Question 2:** The file name becomes very long. Can it be shortened? 

**Answer:** Yes, the rules allow reasonable simplification to improve usability, **if it does not violate uniqueness and sorting logic**.

The main principle: **the first seven components (`YYYY.MM.DD.HH.NN.SS.X`), and in some cases four (`YYYY.MM.DD.X`), are the foundation for sorting and must retain their structure.** If a date part is **totally absent** throughout the entire archive, you can omit it at the level of the **entire archive**.

**The most common case — absence of time:**

* **If the shooting time is unknown for ALL photos in the archive,** you can agree to omit the `HH.NN.SS` components.
* **Simplified format:** `YYYY.MM.DD.X.GGG.SSS.NNNN.A.tiff`
* **Example:**  
  * Full format: `1950.06.15.12.00.00.E.FAM.POR.0001.A.tiff`  
  * Simplified format: `1950.06.15.E.FAM.POR.0001.A.tiff`

**Important warnings and recommendations:**

1. **You cannot omit individual components selectively.** The decision to omit the time (or other parts) must be made for the entire archive in order to preserve uniformity.
2. **All other components are mandatory.** The date modifier (`X`), group (`GGG`), subgroup (`SSS`), sequential number (`NNNN`), and side suffixes (`A/R`) are critical for ensuring uniqueness and organization of files. They cannot be omitted.
3. **Accounting in metadata.** In the `Exif.Photo.DateTimeOriginal` field of metadata, for exact dates with modifier `E`, the time from the filename is recorded. For dates with modifiers `B`, `C`, `F`, the field remains empty, as indicated in section 9.
4. **A decision for the future.** If you decide to omit time, but later a photo with known time appears in the archive, you will have to either abandon the simplification and rename all files by adding `.00.00.00`, or add time only for this file, breaking uniformity. The first option is preferable.

**Conclusion:** Simplifying the format is possible, but should be approached **very** carefully. The full format is the most reliable and consistent with FADGI best practices, as it is sufficiently universal.

**Question 3:** Why not remove the time from the file name by default? After all, for old photos it is almost always `00.00.00`, and this would shorten the name.

**Answer:** This seems logical for archives from the 19th or early 20th century, but for later periods it creates problems.
1. **Cameras with date imprinting (Quartz Date):** In the 1980s-2000s, cameras that imprinted the exact shooting time directly into the frame were very popular. For such shots, time is part of the exact date (`E`), and preserving it is critical for chronology.
2. **Digital photos:** Modern archives are mixed. A folder might contain a film scan from 1995 and a digital photo from 2005. Digital photos always have time. A unified `HH.NN.SS` standard allows storing them together without discrepancies in file names.
3. **Event chronology:** Even if the time is not imprinted, the order of events within a single day is often known (wedding: ransom, registry office, walk, banquet). Using conditional time (10.00.00, 11.00.00) allows arranging files in the correct order when sorting by name.

**Question 4:** How to batch-rename modern digital photos using the date from EXIF?  

**Answer:** The batch renaming process is easily automated with batch renaming software.

**Key points:**
- Use the shooting date from EXIF with the **`E` (Exact)** modifier
- Group (`GGG`) and subgroup (`SSS`) values are set manually for each photo series
- The sequential number starts at `0001` for each new subgroup
- For digital photos, ALWAYS include the `.A` suffix explicitly for consistency; omitting it is treated as a format error.

**Example result:**  
`IMG_1234.JPG` → `2024.12.25.15.05.10.E.VAC.ALP.0001.A.jpg`

**Detailed instructions for software and step-by-step scenarios** are in **Part 3. Archive Operation in Practice**.

**Question 5:** Why not use the standard ISO 8601 date/time format (e.g., `2025-01-15T12:00:00`) instead of components separated by dots (`2025.01.15.12.00.00`)?

**Answer:** This is a very logical question, but replacing it with ISO 8601 within these naming rules is undesirable for several fundamental reasons related to archival integrity, ease of processing, and the approach's philosophy.

1. Philosophy of “components,” not a “single date”.
   The key idea of the approach is not recording a single date-time value, but creating a set of separate, lexicographically sortable components. The dot (`.`) is an ideal separator for file systems, providing clear visual and machine separation of fields. This allows working independently with year, month, day, etc., as separate entities, which is critical for partially specified dates.

2. Elegant handling of unknown values.
   The approach allows indicating unknown parts of the date with sequences of zeros (`00`). The format `1950.00.00.00.00.00.C` is intuitive and easily sorted: all photos “circa 1950” will be grouped together. ISO 8601 has no standard way to denote “unknown month” or “unknown day.” Attempts to do so (e.g., `1950-00-00T00:00:00`) often lead to errors in date parsers and violate the standard, since `00` for month and day is not valid.

3. Trouble-free sorting in any environment.
   File names formed as `YYYY.MM.DD.HH.NN.SS` are guaranteed to be sorted in correct chronological order in any file manager (Windows Explorer, macOS Finder, ls in Linux) without any special software. ISO 8601 also sorts well, but using it in a file name, especially with the `T` character (e.g., `2025-01-15T12:00:00`), can cause inconveniences:
    * The `T` character may require escaping on the command line.
    * Some legacy or simple systems may incorrectly handle characters outside the basic alphabet.

4. Compatibility and human readability.
   The dot-separated format is more “flat” and universal. It doesn’t overload the file name with technical characters like `T` and `:`, which serve a service function in ISO but are redundant in a file name where structure is already set by the component’s position. This makes the file name slightly more compact and easier for a human to skim in a list.

5. Separation of responsibilities: file name vs. metadata.
   It’s important to remember that the main task of the file name in these rules is to ensure uniqueness and logical sorting. The full, standardized representation of date and time should be stored in the appropriate metadata fields (e.g., `Exif.Photo.DateTimeOriginal`), where ISO 8601 is ideal and widely supported. Thus, the approach gets the best of both worlds: a simple and reliable name for sorting and a strict standard in metadata.

Conclusion: Using dot-separated components is not a drawback but a deliberate architectural feature. It provides straightforward sorting, seamless handling of incomplete dates, and maximum compatibility, doing its narrow job better than ISO 8601 would as a file name.

**Question 6:** Why must codes use UPPERCASE Latin letters rather than lowercase or Cyrillic? Are there practical reasons beyond consistency?

**Answer:** Yes, this decision has deep practical justifications that go far beyond mere uniformity. Choosing UPPERCASE Latin letters is strategic for long-term archival preservation and is based on several key principles.

1. Historically established industry practices (Standard Practice):
   * In digital archiving, librarianship, and museum work (the GLAM domain — Galleries, Libraries, Archives, Museums), using uppercase Latin letters for identifiers and codes is a de facto standard. This is an established practice inherited from mainframes and early information systems, where such identifiers were the most reliable.
   * Adhering to this established approach provides immediate comprehensibility of your archive for professionals in digital preservation and ensures seamless compatibility with existing large collections and metadata.

2. Optimization for human perception (Human Readability):
   * Increased visual scannability: Blocks composed of UPPERCASE LETTERS (e.g., `.FAM.POR`) stand out more clearly from the numeric sequences of the date and number. This allows the eye to more quickly latch onto the photo category when viewing a long list of files.
   * Emphasizing significance: Uppercase letters are subconsciously perceived as official, permanent, and systematic. For service codes that are the key to organizing an archive, this is psychologically justified. Lowercase letters (`fam.por`) look less formal and may get lost in the overall flow of characters.
   * Modifier clarity: The single-letter date modifier `E` or `C`, written in uppercase, is visually accentuated and does not mix with the date components.

3. Maximum technical reliability (Technical Resilience):
   * “Lowest common denominator”: Although modern file systems and OSes have become smarter, an archive is created for decades. The risk of encountering an old, finicky, or specialized system (e.g., during data migration, in embedded systems, in command lines of older software versions) remains. Uppercase Latin letters are the simplest and most universally supported alphabet by all systems.
   * Reduced risk of errors: Using a single case completely eliminates the risk of duplicate files due to different spellings (e.g., `file.tiff` vs `FILE.TIFF` in case-sensitive systems), as well as errors in scripts and commands where case may matter.

4. International and inter-system compatibility (Global Compatibility):
   * The Latin alphabet (A-Z) is the universal standard in IT and international data exchange. Its use guarantees that the archive will be correctly processed and displayed anywhere in the world, on any operating system and in any software—from specialized archival systems to the simplest file managers. Cyrillic or other alphabets don’t offer such a guarantee.

Conclusion: The choice between uppercase and lowercase Latin letters is not just an aesthetic preference. Using UPPERCASE Latin letters is a conservative, time-tested, and safest choice for archival storage. It ensures continuity with existing professional practices, maximum human readability, unprecedented technical reliability, and global compatibility. While using lowercase letters is technically possible for consistency, it offers no substantial benefits but deprives the archive of the above critically important advantages for its longevity. It’s an investment in the future clarity and preservation of digital heritage.

**Question 7:** How should I choose Group (`GGG`) and Subgroup (`SSS`) codes so they remain robust and useful?

**Answer:** Use simple, stable, and scalable rules so codes don't require revision as the archive grows and remain understandable years later.

**Practical recommendations:**

1. Family → Type
    - `GGG` reflects a broad theme or collection ("where to file").
    - `SSS` refines the type within the theme ("what exactly").
    - Examples: `FAM.POR` (family → portrait), `TRV.LND` (travel → landscape), `EVT.GRP` (event → group photo).

2. Uppercase Latin letters or digits
    - Only `A-Z` and `0-9`, fixed length of 3 characters.
    - For numeric series use leading zeros: `001`, `002`, … `101`, `102`.

3. Stable code dictionaries
    - Compile a short list of allowed codes and keep it at the archive root (see section 7.4 “Document group codes”).
    - Example dictionary: `FAM, TRV, WED, HIS, DOC` for `GGG`; `POR, LND, GRP, EVT, TXT` for `SSS`.

4. Context matters
    - If the archive grows around albums/boxes — numeric `GGG.SSS` is convenient: `001.101` (album 1, series 101).
    - If the archive is thematic — letter codes are convenient: `FAM.POR`, `TRV.LND`.

5. Independence from folder names
    - Codes in the file name must remain correct even when moved to another folder. Don’t tie `GGG.SSS` to the current physical structure.

6. Avoid frequent renames
    - Don’t use overly specific codes that will need to change when the archive is rethought.
    - Prefer broader `GGG` with more detailed `SSS` rather than making both overly narrow.

**Mini‑cheatsheet:**

- Family album: `FAM.POR`, `FAM.GRP`, `FAM.EVT`
- Travel: `TRV.LND`, `TRV.GRP`, `TRV.CIT`
- Documents: `DOC.TXT`, `DOC.CRD` (cards), `DOC.LET` (letters)
- Album/series: `001.101`, `001.102`, `002.001`

**Primary recommendation: event-source-number scheme**

For mixed archives with photos from various events, a convenient scheme is:
- `GGG` = event number (e.g., `023` for "Family gathering, June 2024")
- `SSS` = source identifier (e.g., `007` — may represent a camera, phone, or photographer)
- `NNNN` = sequential photo number within this event and source

**Example:** `2024.06.15.14.30.00.E.023.007.0001.A.jpg`
- Event #23 (family gathering)
- Source #7 (for example, a particular camera or phone)
- Photo #1 from this source at this event

**Advantages:**
- Helps track the origin of each shot
- Convenient grouping: all photos from one event together, subdivided by source
- Flexibility: you decide what the source code represents (camera, phone, photographer)
- Simple expansion: new sources get new codes, existing files remain unchanged
- Universal: suitable for family archives, professional shoots, expeditions

**Alternative schemes:**
- **Thematic-type:** `FAM.POR` (if you have a single photographer and clear themes)
- **Album-series:** `001.101` (for systematic digitization of physical albums)
- **Location-type:** `CITY.STR` (City-Street) for geographic organization

Choose one scheme and apply it consistently throughout the archive. Mixed approaches are acceptable if well-documented.

This approach is compatible with the sorting and clarity requirements described in Part 1 (sections 4 and 5) and scales without breaking the logic.

### About architecture and navigation

**Question 1:** Won’t this structure create too many small folders?

**Answer:** Yes, this is inevitable for a large archive. However, that’s the goal — breaking a large archive into small, logically organized, and easily viewable parts. It’s much more convenient to view 20 day folders in a year folder than 10,000 files in a single folder.

**Question 2:** What if I want to find all photos of a particular person that are scattered across different years?

**Answer:** This structure is optimized for chronological navigation. For thematic search (by people, events, places) you should use:
1. Metadata: Entering names in the `Description` or `Keywords` fields allows searching via the operating system or photo viewers.
2. External tools: Cataloging programs (e.g., Adobe Lightroom) allow creating virtual collections independent of the physical file location.

**Question 3:** Can this structure be used for other types of media, such as scanned documents?

**Answer:** Yes, the approach is universal. For documents, define appropriate groups (`DOC` — documents, `LET` — letters, `NEW` — newspapers) and apply the same naming and organization principles based on the document’s creation date.

---

## Appendix A: References and Additional Resources

This section contains links to official standards, guidelines, and tools mentioned in the document, as well as additional materials for those who want to dive deeper into the topic of digital preservation.

### **1. Preservation Standards**

*   **FADGI (Federal Agencies Digital Guidelines Initiative)**
    *   *Official site:* [https://www.digitizationguidelines.gov/](https://www.digitizationguidelines.gov/)
    *   *"Technical Guidelines for Digitizing Cultural Heritage Materials":* [https://www.digitizationguidelines.gov/guidelines/digitize-technical.html](https://www.digitizationguidelines.gov/guidelines/digitize-technical.html)
    *   *Why it matters:* This is the direct guide upon which the philosophy of long-term preservation, format usage, and metadata in this instruction is based.

*   **ISO 19005 (PDF/A)**
    *   *Information from PDF Association:* [https://pdfa.org/resource/iso-19005-pdfa/](https://pdfa.org/resource/iso-19005-pdfa/)
    *   *Why it matters:* PDF/A is a standard for long-term preservation of electronic documents. Understanding its principles is useful for archiving documents accompanying scanned photos.

*   **Dublin Core Metadata Initiative (DCMI)**
    *   *Official site:* [https://www.dublincore.org/](https://www.dublincore.org/)
    *   *Why it matters:* This is one of the most common metadata sets for describing resources. Dublin Core principles are directly reflected in the metadata fields recommended for completion.

### **2. Software & Tools**

*   **ExifTool by Phil Harvey**
    *   *Official site:* [https://exiftool.org/](https://exiftool.org/)
    *   *Why it matters:* This is the "gold standard" and the most powerful tool for reading, writing, and editing metadata in almost any file format. Recommended for advanced users and automation.

*   **Summary table of software for batch renaming and metadata management**
    *   **Adobe Bridge:** [https://www.adobe.com/products/bridge.html](https://www.adobe.com/products/bridge.html)
    *   **Advanced Renamer (Windows):** [https://www.advancedrenamer.com/](https://www.advancedrenamer.com/)
    *   **NameChanger (macOS):** [https://mrrsoftware.com/namechanger/](https://mrrsoftware.com/namechanger/)
    *   **XnView MP (cross-platform viewing and conversion):** [https://www.xnview.com/en/xnviewmp/](https://www.xnview.com/en/xnviewmp/)
    *   **FastStone Image Viewer (Windows):** [https://www.faststone.org/FSViewerDetail.htm](https://www.faststone.org/FSViewerDetail.htm)

### **3. Further Reading**

*   **Library of Congress - Sustainability of Digital Formats**
    *   *Page about TIFF format:* [https://www.loc.gov/preservation/digital/formats/fdd/fdd000022.shtml](https://www.loc.gov/preservation/digital/formats/fdd/fdd000022.shtml)
    *   *Why it matters:* A detailed analysis of the TIFF format in terms of its suitability for long-term preservation.

*   **DPBestflow (Project of the Library of Congress)**
    *   *Official site:* [http://www.dpbestflow.org/](http://www.dpbestflow.org/)
    *   *Why it matters:* An excellent resource on all aspects of digital photography for archives and libraries.

*   **Digital Preservation Coalition (DPC)**
    *   *Official site:* [https://www.dpconline.org/](https://www.dpconline.org/)
    *   *Why it matters:* An international association dedicated to digital preservation issues. The site contains a huge amount of guides and news in this area.
