# Systematizing the Storage of Digital Photographs in a Personal Archive

## Contents
- **Introduction**
- **Part 0: Quick Start**
- **Part 1: File Naming System**
- **Part 2: Storage Architecture**
- **Part 3: Archive Operation in Practice**

---

## Introduction

Imagine you're looking for a particular family photograph taken sometime in the 1980s. Instead of scrolling through thousands of files with meaningless names like `IMG_1234.JPG` or `Scan001.tiff`, you simply open the folder "1980.C" and find the needed photo within minutes.

This guide helps you achieve exactly that result. We're not just suggesting you "rename files." We offer a philosophy and a ready-made system to turn your collection of digital photographs into a thoughtful, convenient, and long-lasting archive.

What you get by adopting this system:

*   Order: You'll never lose a photo in a pile of files again.
*   Accessibility: Fast and logical search by dates and categories.
*   Preservation: The context of each photo (who, what, where, when) is safely preserved not only in your memory but also in the file's metadata.
*   Continuity: The archive will likely remain understandable—to you and to software—in 20, 30, or even 50 years.

You can start simple using the rules from the Quick Start in the first part and gradually move to the full format. Going through all three parts of the guide will give you complete control over the archive.

---

## Cheat Sheet

### Full filename format
```
YYYY.MM.DD.HH.NN.SS.X.GGG.SSS.NNNN.extension
```

### Simplified format (without time)
```
YYYY.MM.DD.X.GGG.NNN.[A|R].extension
```

### Component definitions
| Component | Description | Format |
|:-|:-|:-|
| YYYY | Year | 4 digits (or 0000 if unknown) |
| MM | Month | 2 digits (01–12, or 00) |
| DD | Day | 2 digits (01–31, or 00) |
| HH | Hour | 2 digits (00–23) |
| NN | Minutes | 2 digits (00–59) |
| SS | Seconds | 2 digits (00–59) |
| X | Date modifier | 1 letter: Absent, Before, Circa, Exact, aFter |
| GGG | Group | 3 characters (A-Z or 0-9) |
| SSS | Subgroup | 3 characters (A-Z or 0-9) |
| NNNN | Sequential number | 4 digits (0001–9999) |
| A/R | Scan side | 1 letter: A — obverse (front), R — reverse (back) |

### Date modifiers (X)
| Letter | Meaning | When to use |
|:-|:-|:-|
| **A** | Absent | Date completely unknown (`0000.00.00.00.00.00.A`) |
| **B** | Before | Before the specified date (e.g., before 1950) |
| **C** | Circa | Approximate date (around the specified year/month) |
| **E** | Exact | Exact date (all components known) |
| **F** | aFter | After the specified date |

### Version suffixes
- `.RAW.tiff` — raw scan
- `.MSR.tiff` — Master copy (minimally processed)
- `.WEB.jpg` — for the web (72 dpi, 80% compression)
- `.PRT.jpg` — for print (300 dpi, no compression)
- `.VIEW.jpg` — for quick viewing

### Required metadata fields
1. **Description** — everything known about the photo (who, what, where, when, source)
2. **DateTimeOriginal** — filled only for modifier **E** (format: `YYYY:MM:DD HH:NN:SS`)
3. **Copyright** — archive rights holder
4. **Creator** — who created the digital copy
5. **Artist** — author of the original (if known)

### Examples
```
1950.06.15.12.00.00.E.FAM.POR.0001.A.tiff    # Exact date, family portrait, obverse
1950.00.00.00.00.00.C.FAM.POR.0002.A.tiff    # Circa 1950, obverse
0000.00.00.00.00.00.A.FAM.POR.0003.A.tiff    # Date unknown, obverse
1950.06.15.E.FAM.001.A.tiff                    # Simplified format (no time), obverse
```

---

## Part 0. Quick Start

### Purpose of this chapter

Without reading the entire guide, learn the basics in 15 minutes and get to work. You'll get a working system that you can later refine without renaming files again.

> Important: This is not a simplified but a fully functional core of the system. All files created by these rules will be compatible with the full format.

### Your first renamed file

Forget the complex format. Your goal is to learn to use 4 key components:

#### Basic format: `YYYY.MM.DD.X.GGG.NNN.A.extension`

| Component | Meaning | Examples |
|:-|:-|:-|
| **YYYY.MM.DD** | Shooting date | `1960.06.15` (exact) <br> `1975.08.00` (year and month known) <br> `1985.00.00` (year only known) |
| **X** | Date modifier | `E` - exact date <br> `C` - approximate date |
| **GGG** | Photo category | `FAM` - family <br> `TRV` - travel |
| **NNN** | Sequential number | `001`, `002`, `003`... |
| **A** | Scan side | `A` - obverse (front), always `A` for digital photos |

> **Important about obverse and reverse:** For scanned analog photos, use `A` for the front side and `R` for the back (if there are inscriptions, stamps). For digital photos, always use `A`.

#### Examples to start immediately

- Family portrait, exactly June 15, 1960 → `1960.06.15.E.FAM.001.A.tiff`
- Landscape from a trip, circa 1985 → `1985.00.00.C.TRV.001.A.jpg`
- A friend's photo, circa August 1975 → `1975.08.00.C.FRD.001.A.tiff`
- Wedding, date unknown → `0000.00.00.A.WED.001.A.tiff`
- Back of an old photo with inscriptions → `1960.06.15.E.FAM.001.R.tiff`

Main rule: START. It's better to name a file `1990.00.00.C.XXX.001.A.tiff` than to leave `IMG_8547.JPG`.

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
4. **Number:** Start at `001` for each new category

#### Step 3: Renaming
Manually rename files using the template `YYYY.MM.DD.X.GGG.001.A.tiff`

Example process:
- Was: `DSC_1234.JPG`
- Became: `1987.05.00.C.FAM.001.A.jpg`

#### Step 4: Fill in metadata (REQUIRED STEP!)

This is even more important than the perfect name! Right-click the file → Properties → Details or Comment.

In the "Description" field, enter ALL known information:
- Who is depicted (names, relationships)
- What is happening (event, holiday)
- Where the date comes from ("from grandmother’s words", "inscription on the back")
- Shooting location

Example description:
"Ivan Petrov (grandfather) and Maria Petrova (grandmother) in the garden of the house on Lenin St. The picture was taken approximately in the summer of 1975. Information from Aunt Anna."

---

Congratulations! You’ve just laid the foundation of your future professional archive.

### What’s next? How the system will grow with you

This simplified system is not a dead end. It’s a full-fledged core that you will gradually extend as your archive and needs grow.

| When you need... | What to add | Example |
|:-|:-|:-|
| More detail | Subgroup (`SSS`) | `1960.06.15.E.FAM.**POR**.001.A.tiff` |
| File count exceeded 999 | 4-digit number | `1960.06.15.E.FAM.001.**0001**.A.tiff` |
| Photos with exact time appear | Time (`HH.NN.SS`) | `1960.06.15.**14.30.00**.E.FAM.001.A.tiff` |
| Complex dating | Other modifiers | `1940.00.00.**B**.FAM.001.A.tiff` |

Key advantage: You won’t have to change the names of already created files! You’ll simply start using a longer and more precise format for new photos. All your old files will sort perfectly together with the new ones.

### Frequently asked questions at the start

Question 1: Can I use Cyrillic characters in category codes?

Answer: NO. Only uppercase Latin letters (`A-Z`) and digits. This ensures compatibility across all devices for 20+ years.

Question 2: What if I’m not sure about the date?

Answer: Use the `C` (circa) modifier and specify in the description where the date came from.

Question 3: Do I need to create a complex folder structure right away?

Answer: NO. Start with a simple folder "MY_ARCHIVE". Add structure later, when you have 100+ files.

---

> Tips: 
- try applying the instructions to a few files; this will give you more understanding than just reading the recommendations.
- if you’re ready, study the full naming system in Part 1: working with file versions, automation, and professional storage structure.

---

## Part 1. File Naming System

This guide describes a file naming system for photographs in a digital archive. The system is designed to ensure uniqueness, readability, logical sorting, and long-term preservation in accordance with FADGI (Federal Agencies Digital Guidelines Initiative) recommendations. It is suitable for images of any origin: digitized paper photographs (both black-and-white and color), as well as digital photographs.

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
| NNNN | Sequential number within the group/subgroup. | **4 digits** (`0001–9999`) | 0001 |
| A/R | Scan side (for analog photos). | **1 letter:** `A` (obverse/front) or `R` (reverse/back) | A |
| .tiff | File extension (for archival copies — TIFF without compression). | .tiff or .tif | .tiff |

Full example file name:
- `1950.06.15.12.00.00.E.FAM.POR.0001.A.tiff` — exact date (June 15, 1950, 12:00), family portrait, number 0001, obverse.
- `1950.00.00.00.00.00.C.001.101.0002.A.tiff` — circa 1950, group 001, subgroup 101, number 0002, obverse.
- `1950.06.15.12.00.00.E.FAM.POR.0001.R.tiff` — reverse of the same portrait.

### 2. Date modifier (X)
The modifier is an uppercase Latin letter indicating the type of date. It provides logical sorting (alphabetical order: A, B, C, E, F), corresponding to the sequence: "unknown" → "before" → "circa" → "exact" → "after".

| Letter | Meaning | Description | Usage example |
|:-|:-|:-|:-|
| A | Absent (unknown) | Date completely unknown. Used with a zero date (`0000.00.00.00.00.00`). | `0000.00.00.00.00.00.A.FAM.POR.0001.A.tiff` — date unknown. |
| B | Before | Photo was taken before the specified date (e.g., before 1950). Use if the upper bound is known. | `1950.00.00.00.00.00.B.FAM.POR.0002.A.tiff` — before 1950. |
| C | Circa | Approximate date (year, month, or day is known with uncertainty, but not exact). Use if the date is not exact and not "before" or "after". | `1950.00.00.00.00.00.C.FAM.POR.0003.A.tiff` — circa 1950. <br> `1950.06.00.00.00.00.C.001.101.0004.A.tiff` — circa June 1950. |
| E | Exact | Exact date (year, month, day, and possibly time are known). Use if the date is confirmed (e.g., written on the photo). | `1950.06.15.12.00.00.E.FAM.POR.0005.A.tiff` — June 15, 1950, 12:00. |
| F | aFter | Photo was taken after the specified date (e.g., after 1950). Use if the lower bound is known. | `1950.00.00.00.00.00.F.FAM.POR.0006.A.tiff` — after 1950. |

Sorting: Files are sorted first by date (`YYYY.MM.DD.HH.NN.SS`), then by letter (`A`, `B`, `C`, `E`, `F`), then by group, and so on, which produces:
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
- Known time: Use real values (e.g., `12.30.15`).
- Unknown time in the file name: Always use `00.00.00`. This ensures uniformity and indicates that the exact time is unknown.
- Conditional time in metadata: In the `DateTimeOriginal` field for exact dates (`E`) with unknown time, set `12:00:00`. For non-exact dates (`A`, `B`, `C`, `F`), leave the field empty.

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
- Always use the same number of digits or letters.
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

Recommendation: Mixing letter and numeric formats for groups and subgroups within a single archive is acceptable. Choose one approach and use it across the entire archive. This gives systematization and predictability.

### 6. Sequential number (NNNN)
- 4-character identifier, unique within the subgroup.
- The simplest option is numeric. Start from `0001` for each new `SSS`.

### 7. Scanning side suffixes (for analog photographs)

- `A` — obverse (front side)
- `R` — reverse (back side)

Examples:
- `1950.06.15.12.00.00.E.FAM.POR.0001.A.tiff`
- `1950.06.15.12.00.00.E.FAM.POR.0001.R.tiff`

### 8. File version suffixes

- RAW copy: `.RAW.tiff` (raw scan, TIFF without compression).
- Master copy: `.MSR.tiff` (minimally processed archival version, TIFF without compression).
- Derivative files:
  - `.WEB.jpg` (low resolution, 72 dpi, 80% compression for the web).
  - `.PRT.jpg` (high resolution, 300 dpi, 100% quality for print).
- Example: `1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff`, `1950.00.00.00.00.00.C.001.101.0002.R.RAW.tiff`.

### 9. Metadata: Filling the file with meaning

A file name ensures uniqueness and sorting, but it’s the metadata that carries the meaning, history, and context of the photograph. Filling out metadata is a mandatory step in the archiving process. Use tools like Adobe Bridge, ExifTool, etc., to work with metadata.

#### Required fields for TIFF files

1. `Description` / `Caption` / `XPComment` (Description)
    * This is the most important field. Enter all known information here:
        * Who is depicted: Names of people, their family relationships (e.g., "Ivan Petrov (grandfather), Maria Petrova (grandmother). Sitting on a bench in the garden at 10 Lenin St.").
        * What is happening: Event, holiday (e.g., "Celebrating a silver wedding").
        * Origin of the photo: Information source (e.g., "Inscription on the back of the original", "From Aunt Anna’s words", "Determined by the model of the car in the background").
        * History of changes: (e.g., "Date clarified on 2024-01-12 from circa 1950 to exact 1950-06-15 based on an album found with dates").
        * Link to other files: For the obverse, indicate the existence of a reverse (e.g., "Inscriptions on the back: see file 1950.06.15.E.FAM.POR.0001.R.MSR.tiff").

2. `DateTimeOriginal` (Date and time of shooting)
    * For modifier `E` (Exact): Enter the exact date in the format `YYYY:MM:DD HH:NN:SS`. If the time is unknown, set `12:00:00`.
    * For modifiers `A` (Absent), `B` (Before), `C` (Circa), `F` (After): Leave the field empty.

3. `Copyright` (Copyright)
    * Specify the archive rights holder. Example: `© Ivanov Family Archive. Scan © 2025, A.A. Ivanov.`

4. `Creator` (Creator of the digital copy)
    * Your name or the name of the organization that performed the scanning.

5. `Artist` (Author of the original)
    * If the photographer is known. Example: `Photo studio "Luch"`.

6. Technical metadata (often added by the scanner or software automatically, but must be checked)
    * `XResolution` / `YResolution`: Resolution (e.g., `600 dpi`).
    * `Software`: Program used for scanning.
    * `Model`: Scanner model.
    * `DateTimeDigitized` (Digitization date): Date and time the digital copy was created (e.g., `2025:09:18 14:30:00`).

#### Mapping the date modifier to metadata fields

| Modifier | DateTimeOriginal (Example) | Description (Example) |
|:-|:-|:-|
| `A` (Absent) | (empty) | `Unknown date. In the photo: graduation party. On the back of the original, the inscription: "In memory of school".` |
| `B` (Before) | (empty) | `Approximate date: before 1940. Determined by clothing style. In the photo: parents’ wedding.` |
| `C` (Circa) | (empty) | `Approximate date: circa 1950. Determined by the date on the cinema poster in the background.` |
| `E` (Exact) | `1950:06:15 12:00:00` | `Exact date: June 15, 1950. The exact date is written in ink on the back of the original.` |
| `F` (aFter) | (empty) | `Approximate date: after 1960. The photo was taken after moving into the new house, which was purchased in 1960.` |

### 10. Examples

- Unknown date: `0000.00.00.00.00.00.A.FAM.POR.0001.A.tiff` — family portrait, unknown date, obverse.
- Before a date: `1940.00.00.00.00.00.B.HIS.EVT.0002.A.tiff` — historical event, before 1940, obverse.
- Approximate date: `1950.00.00.00.00.00.C.001.101.0003.R.tiff` — circa 1950, album 1, series 101, reverse.
- Exact date: `1950.06.15.12.00.00.E.FAM.POR.0004.A.tiff` — family portrait, exactly June 15, 1950, 12:00, obverse.
- After a date: `1960.00.00.00.00.00.F.TRV.LND.0005.A.tiff` — landscape from a trip, after 1960, obverse.

### 11. FADGI Compliance

The naming system is designed in accordance with the recommendations of FADGI (Federal Agencies Digital Guidelines Initiative) to ensure the long-term preservation of digital materials.

Main principles of compliance:

- File formats: Using uncompressed `TIFF` for archival copies (RAW, Master) meets long-term storage requirements. `ZIP` or `LZW` compression is acceptable.
- Name uniqueness: The combination of the date, modifier (`A`, `B`, `C`, `E`, `F`), group, subgroup, serial number, and side suffixes ensures global uniqueness of each file.
- Readability: The structured format is intuitive for both humans and automated systems.
- Logical sorting: The sequence of components ensures correct chronological organization in line with archival principles.
- Semantic integrity: The file name contains key metadata (event date), which aligns with the principle of content priority over technical attributes.
- Independence from software: The naming system is not tied to any specific software or operating system.

> **References to standards and guidelines** see **Appendix A**.

### 12. Recommendations

- Use `A`, `B`, `C`, `E`, `F`: This ensures the desired sorting order (`A`, `B`, `C`, `E`, `F`).
- Flexibility of groups and subgroups: Choose letter (e.g., `FAM.POR`) or numeric (e.g., `001.101`) codes depending on the archive structure. Numeric codes are convenient for large collections or automation.
- Metadata: Duplicate information in metadata:
  - `0000.00.00.00.00.00.A` → `Description: Date absent`.
  - `1950.00.00.00.00.00.B` → `Description: Date approximate: before 1950`.
  - `1950.00.00.00.00.00.C` → `Description: Date approximate: circa 1950`.
  - `1950.06.15.12.07.25.E` → `DateTimeOriginal: 1950:06:15 12:07:25`, `Description: Date exact: 1950-06-15 12:07:25`.
  - `1950.00.00.00.00.00.F` → `Description: Date approximate: after 1950`.
- Case and characters: Strictly use UPPERCASE Latin letters (`A-Z`) and digits (`0-9`) for components `X`, `GGG`, `SSS`. This ensures:
  - Cross-OS compatibility
  - Predictable sorting
  - No conflicts due to different case

### 13. Frequently asked questions about file naming

Question 1: Why use the date the photograph (event) was taken in the file name rather than the scanning date?

Answer: This is a fundamental requirement for archival storage in accordance with FADGI and other international standards (such as Dublin Core).

- Meaning and context: The event date is key meta-information that defines the historical and cultural context of the object. The file name is the first and basic level of description.
- Logical sorting: Using the event date allows photos to be arranged chronologically, rather than in the order of their scanning (processing).
- Immutability: The event date is an immutable attribute. The digitization date is technical information that should be stored in the appropriate metadata fields of the digital image (e.g., in the `DateTimeDigitized` field). Separating this data prevents confusion and guarantees the file name will not have to be changed when migrating the archive to new media or storage systems.

Conclusion: The digitization date is important, but its place is in the file metadata, not in its name.

Question 2: The file name becomes very long. Can it be shortened?

Answer: Yes, the system allows reasonable simplification to improve usability if it does not violate uniqueness and sorting logic.

The main principle: the first seven components (`YYYY.MM.DD.HH.NN.SS.X`), and in some cases four (`YYYY.MM.DD.X`), are the foundation for sorting and must retain their structure. If a date part is totally absent throughout the entire archive, you can omit it at the level of the entire system.

The most common case — absence of time:

- If the shooting time is unknown for ALL photos in the archive, you can agree to omit the `HH.NN.SS` components.
- Simplified format: `YYYY.MM.DD.X.GGG.SSS.NNNN.A.tiff`
- Example:
  - Full format: `1950.06.15.12.00.00.E.FAM.POR.0001.A.tiff`
  - Simplified format: `1950.06.15.E.FAM.POR.0001.A.tiff`

Important warnings and recommendations:

1. You cannot omit individual components selectively. The decision to omit the time (or other parts) must be made for the entire archive to preserve uniformity.
2. All other components are mandatory. The date modifier (`X`), group (`GGG`), subgroup (`SSS`), sequential number (`NNNN`), and side suffixes (`A/R`) are critical for ensuring uniqueness and organization of files. They cannot be omitted.
3. Accounting in metadata. In the `DateTimeOriginal` field of metadata, if the time is unknown, specify `12:00:00` (for exact dates with modifier `E`) or `00:00:00` (for dates with modifiers `B`, `C`, `F`), as indicated in section 9.
4. A decision for the future. If you decide to omit time, but later a photo with known time appears in the archive, you will have to either abandon the simplification and rename all files by adding `.00.00.00`, or add time only for this file, breaking uniformity. The first option is preferable.

Conclusion: Simplifying the format is possible, but should be approached very carefully. The full format is the most reliable and consistent with FADGI best practices, as it is sufficiently universal.

Question 3: How to batch-rename modern digital photos using the date from EXIF?

Answer: The batch renaming process is easily automated with batch renaming software.

Key points:
- Use the shooting date from EXIF with the `E` (Exact) modifier
- Group (`GGG`) and subgroup (`SSS`) values are set manually for each photo series
- The sequential number starts at `0001` for each new subgroup
- For digital photos, ALWAYS include the `.A` suffix explicitly for consistency; omitting it is treated as a format error.

Example result:
`IMG_1234.JPG` → `2024.12.25.15.05.10.E.VAC.ALP.0001.A.jpg`

Detailed instructions for software and step-by-step scenarios are in Part 3. Archive Operation in Practice.

Question 4: Why not use the standard ISO 8601 date/time format (e.g., `2025-01-15T12:00:00`) instead of components separated by dots (`2025.01.15.12.00.00`)?

Answer: This is a very logical question, but replacing it with ISO 8601 within this naming system is undesirable for several fundamental reasons related to archival integrity, ease of processing, and the system’s philosophy.

1. Philosophy of “components,” not a “single date”.
   The key idea of the system is not recording a single date-time value, but creating a set of separate, lexicographically sortable components. The dot (`.`) is an ideal separator for file systems, providing clear visual and machine separation of fields. This allows working independently with year, month, day, etc., as separate entities, which is critical for partially specified dates.

2. Elegant handling of unknown values.
   The system allows indicating unknown parts of the date with sequences of zeros (`00`). The format `1950.00.00.00.00.00.C` is intuitive and easily sorted: all photos “circa 1950” will be grouped together. ISO 8601 has no standard way to denote “unknown month” or “unknown day.” Attempts to do so (e.g., `1950-00-00T00:00:00`) often lead to errors in date parsers and violate the standard, since `00` for month and day is not valid.

3. Trouble-free sorting in any environment.
   File names formed as `YYYY.MM.DD.HH.NN.SS` are guaranteed to be sorted in correct chronological order in any file manager (Windows Explorer, macOS Finder, ls in Linux) without any special software. ISO 8601 also sorts well, but using it in a file name, especially with the `T` character (e.g., `2025-01-15T12:00:00`), can cause inconveniences:
    * The `T` character may require escaping on the command line.
    * Some legacy or simple systems may incorrectly handle characters outside the basic alphabet.

4. Compatibility and human readability.
   The dot-separated format is more “flat” and universal. It doesn’t overload the file name with technical characters like `T` and `:`, which serve a service function in ISO but are redundant in a file name where structure is already set by the component’s position. This makes the file name slightly more compact and easier for a human to skim in a list.

5. Separation of responsibilities: file name vs. metadata.
   It’s important to remember that the main task of the file name in this system is to ensure uniqueness and logical sorting. The full, standardized representation of date and time should be stored in the appropriate metadata fields (e.g., `DateTimeOriginal`), where ISO 8601 is ideal and widely supported. Thus, the system gets the best of both worlds: a simple and reliable name for sorting and a strict standard in metadata.

Conclusion: Using dot-separated components is not a drawback but a deliberate architectural feature. It provides straightforward sorting, seamless handling of incomplete dates, and maximum compatibility, doing its narrow job better than ISO 8601 would as a file name.

Question 5: Why must codes use UPPERCASE Latin letters rather than lowercase or Cyrillic? Are there practical reasons beyond consistency?

Answer: Yes, this decision has deep practical justifications that go far beyond mere uniformity. Choosing UPPERCASE Latin letters is strategic for long-term archival preservation and is based on several key principles.

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

### 14. Summary

This naming system (`YYYY.MM.DD.HH.NN.SS.[A|B|C|E|F].GGG.SSS.NNNN.[A|R].SUF.EXT`) provides logical sorting (`A`, `B`, `C`, `E`, `F`) corresponding to the sequence: unknown → before → circa → exact → after. Groups and subgroups, highlighted in separate sections, can be letter-based (e.g., `FAM.POR`) or numeric (e.g., `001.101`), adding flexibility for large archives or automation.

---

## Part 2. Storage Architecture

### 1. Philosophy: from file to structure

The naming system described in Part 1 is the core of the archive. It ensures uniqueness and logical order at the level of individual files. The storage architecture is the overlay that organizes these files into an intuitive directory hierarchy for easy navigation, management, and manual browsing.

Key principle: The directory structure mirrors the file naming system, creating a direct and predictable link between the file name and its place in the archive. This allows working with the archive without specialized software, using only a file manager.

### 2. Recommended directory hierarchy

The structure is built according to the principle `Archive/YYYY.X/YYYY.MM.DD.X/<suffix>/`.

```
├─── ARCHIVE/                 // For example, "0001.Ivanov Family Archive"
│  ├─── YYYY.X/               // Year folder with modifier
│  │  ├─── YYYY.MM.DD.X/      // Day folder with modifier
│  │  │  ├── RAW/             // Raw scans
│  │  │  ├── MSR/             // Master copies
│  │  │  ├── WEB/             // Web versions
│  │  │  ├── PRT/             // Print versions
│  │  │  ├── VIEW/            // Quick viewing files (often copies from WEB or PRT)
```

Important rule: Folders are created reactively, only when at least one file appears for them. This eliminates empty directories.

### 3. Practical organization examples

**Example 1: Photo with exact date**
- File: `1945.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff`
- Path: `.../1945.E/1945.06.15.E/MSR/1945.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff`

**Example 2: Photo with approximate date (only year known)**
- File: `1930.00.00.00.00.00.C.HIS.000.0005.A.RAW.tiff`
- Path: `.../1930.C/1930.00.00.C/RAW/1930.00.00.00.00.00.C.HIS.000.0005.A.RAW.tiff`

**Example 3: Photo with approximate date (year and month known)**
- File: `1955.08.00.00.00.00.C.TRV.LND.0003.A.WEB.jpg`
- Path: `.../1955.C/1955.08.00.C/WEB/1955.08.00.00.00.00.C.TRV.LND.0003.A.WEB.jpg`

### 4. Special cases (B, F, unknown dates)

For files with modifiers `B` (Before) and `F` (After), a special folder `0000` is used, because there is no exact year to bind them to.

**Example 4: Photo "before 1950"**
- File: `1950.00.00.00.00.00.B.FAM.000.0002.A.tiff`
- Path: `.../0000.B/1950.00.00.B/MSR/1950.00.00.00.00.00.B.FAM.000.0002.A.MSR.tiff`
- Logic: All files "before some date" are grouped in the `0000.B` folder, inside — by approximate year.

**Example 5: Photo "after 1960"**
- File: `1960.00.00.00.00.00.F.TRV.000.0001.A.tiff`
- Path: `.../0000.F/1960.00.00.F/RAW/1960.00.00.00.00.00.F.TRV.000.0001.A.RAW.tiff`

**Example 6: Photo with completely unknown date**
- File: `0000.00.00.00.00.00.A.UNK.000.0001.A.tiff`
- Path: `.../0000.A/0000.00.00.A/MSR/0000.00.00.00.00.00.A.UNK.000.0001.A.MSR.tiff`

### 5. Quick viewing and derivative files

The `VIEW/` folder in the day structure is intended for files optimized for quick viewing on any device.

Recommendations for the `VIEW` folder:
- Use JPEG for broad compatibility.
- Resolution can be set within 150–300 DPI.
- Long side size — 1600–2400 pixels.
- The file name should retain the full naming structure but with the `.VIEW.jpg` suffix.

Example: `1945.06.15.12.00.00.E.FAM.POR.0001.A.VIEW.jpg`

This folder allows opening any day of the archive and quickly viewing all its photos without the need to load heavy Master or RAW files.

### 6. FADGI compatibility (for folder structure)

The proposed architecture matches the spirit of FADGI recommendations:
- Separation by versions: Clear separation into RAW, Master, and Derivatives (WEB, PRT, VIEW) corresponds to the principle of separating originals and derivative copies.
- Logical organization: Grouping by event date, not processing date, ensures historical and archival integrity.
- Predictability: A standardized structure facilitates data migration and process automation.

### 7. Recommendations for managing the structure

1. Use batch renaming and organization. Tools like Adobe Bridge, Total Commander, or specialized scripts will help automatically distribute files into folders according to their names.
2. Control path length. Ensure the full file path does not exceed file system limits (e.g., 260 characters in Windows). Use short names for the archive root folder.
3. Be consistent. Having adopted this structure, use it for the entire archive. This will ensure uniformity and predictability over many years.
4. Document group codes. Keep a simple text file or spreadsheet with decoding of the `GGG` and `SSS` codes at the root of the archive.

### 8. Frequently asked questions about architecture and navigation

Question 1: Won’t this structure create too many small folders?

Answer: Yes, this is inevitable for a large archive. However, that’s the goal — breaking a large archive into small, logically organized, and easily viewable parts. It’s much more convenient to view 20 day folders in a year folder than 10,000 files in a single folder.

Question 2: What if I want to find all photos of a particular person that are scattered across different years?

Answer: This structure is optimized for chronological navigation. For thematic search (by people, events, places) you should use:
1. Metadata: Entering names in the `Description` or `Keywords` fields allows searching via the operating system or photo viewers.
2. External tools: Cataloging programs (e.g., Adobe Lightroom) allow creating virtual collections independent of the physical file location.

Question 3: Can this structure be used for other types of media, such as scanned documents?

Answer: Yes, the system is universal. For documents, define appropriate groups (`DOC` — documents, `LET` — letters, `NEW` — newspapers) and apply the same naming and organization principles based on the document’s creation date.

---

## Part 3. Archive Operation in Practice

### 1. Typical workflows

Scenario 1: Digitizing a new album

1. Preparation:
    * Create a temporary `INCOMING/` folder at the archive root.
    * Scan all photos from the album to uncompressed TIFF, saving them to `INCOMING/`.
    * Pre-name files for convenience (e.g., `Album5_001.tiff`).

2. Research and assigning names:
    * Study each photo: determine the date (exact or approximate), choose the group (`GGG`) and subgroup (`SSS`).
    * Assign names to files according to the system from Part 1 using batch renaming.
    * Example: Source `Album5_001.tiff` → `1968.07.00.00.00.00.C.FAM.VAC.0001.A.RAW.tiff`

3. Filling metadata:
    * Open each file in a metadata editor (e.g., Adobe Bridge).
    * Fill the `Description` field with all known information.
    * For exact dates (`E`), fill in `DateTimeOriginal`.

4. Organizing into the structure:
    * Using batch tools or a file manager, move files from `INCOMING/` to corresponding folders according to the architecture from Part 2.
    * Example: `1968.07.00.00.00.00.C.FAM.VAC.0001.A.RAW.tiff` → `/1968.C/1968.07.00.C/RAW/`

5. Creating derivative copies:
    * From Master copies, create files for WEB, PRT, and VIEW.
    * Distribute them into corresponding folders within the day.

Scenario 2: Batch renaming digital photos

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

Scenario 3: Clarifying a date and batch renaming

1. Discovering new information:
    * An exact date was found for the photo `1950.00.00.00.00.00.C.FAM.000.0045.A.tiff` — June 15, 1950.

2. Renaming:
    * Use software that supports batch template-based renaming (e.g., Advanced Renamer, Total Commander).
    * Set a replacement rule:
        * Find: `1950.00.00.00.00.00.C`
        * Replace: `1950.06.15.12.00.00.E` (set time to 12:00:00 if unknown)
    * Result: `1950.00.00.00.00.00.C.FAM.000.0045.A.tiff` → `1950.06.15.12.00.00.E.FAM.000.0045.A.tiff`

3. Updating metadata and structure:
    * Update the `DateTimeOriginal` field in the file.
    * In the `Description` field add: "Date clarified on 2025-01-10 from circa 1950 to exact 1950-06-15 based on the inscription on the back of the original."
    * Move the file to the new folder: from `/1950.C/1950.00.00.C/` to `/1950.E/1950.06.15.E/`.

Scenario 4: Searching photos in the archive

1. Chronological search:
    * Use the folder structure. To find photos for July 1968, go to `/1968.C/1968.07.00.C/VIEW/`.

2. Thematic search:
    * Use the operating system’s search.
    * Example search in Windows: In the Explorer search field enter: `*.VIEW.jpg description:="Ivan Petrov"`

3. Search by technical parameters:
    * Use cataloging programs (Adobe Bridge, Lightroom).
    * Create collections by keywords, ratings, or other metadata.

### 2. Software and tools

For batch renaming:
* Adobe Bridge (cross-platform, powerful tool with metadata support)
* Advanced Renamer (Windows, free, powerful and flexible)
* NameChanger (macOS, simple and effective)
* Renamer (Windows, Russian interface)

For metadata management (EXIF, IPTC, XMP):
* Adobe Bridge (integrated metadata work)
* ExifTool (command line, maximum power and automation)
* Exif Pilot (Windows, GUI for ExifTool)
* Metadata++ (Windows, free viewer and editor)

For viewing and cataloging:
* Adobe Bridge/Lightroom (professional suite)
* XnView MP (cross-platform, free for non-commercial use, supports many formats)
* FastStone Image Viewer (Windows, fast and convenient)

Example script for ExifTool (advanced level):

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

2. Backup (3-2-1 rule):
    * 3 copies of data
    * 2 different media types (e.g., HDD + cloud)
    * 1 copy in a remote location

    Example strategy:
    * Working copy: On the main computer.
    * Local backup: On an external hard drive, updated weekly.
    * Remote copy: In cloud storage (Backblaze, Yandex Disk, Google Drive) or on a drive in another building.

### 4. Conclusion. Your archive as historical heritage

An archive created according to this system is not just a collection of files. It is a structured digital heritage with several key properties:

*   Durability: Standardized names and structure will be clear even 50 years from now.
*   Independence: The archive is not tied to specific software and can be read on any operating system.
*   Context: Rich metadata preserves the history of each photo for future generations.
*   Scalability: The system will work for 100 photos and for 100,000 photos.

Starting small — with the proper naming of a few files — you lay the foundation for a professional archival fund whose value will only increase over time.

---

## Appendix A: Links and additional resources

This section contains links to official standards, guides, and tools mentioned in the document, as well as additional materials for those who want to dive deeper into digital preservation.

1. Preservation standards and guidelines

* FADGI (Federal Agencies Digital Guidelines Initiative)
    * Official site: https://www.digitizationguidelines.gov/
    * Technical Guidelines for Digitizing Cultural Heritage Materials: https://www.digitizationguidelines.gov/guidelines/digitize-technical.html
    * Why it matters: This is the direct guidance on which the philosophy of long-term preservation, use of formats and metadata in this guide is based.

* ISO 19005 (PDF/A)
    * Information from the PDF Association: https://pdfa.org/resource/iso-19005-pdfa/
    * Why it matters: PDF/A is a standard for long-term preservation of electronic documents. Understanding its principles is useful for archiving documents accompanying scanned photos.

* Dublin Core Metadata Initiative (DCMI)
    * Official site: https://www.dublincore.org/
    * Why it matters: This is one of the most common metadata sets for describing resources. The principles of Dublin Core are directly reflected in the metadata fields recommended for filling out.

2. Software & Tools

* ExifTool by Phil Harvey
    * Official site: https://exiftool.org/
    * Why it matters: This is the "gold standard" and the most powerful tool for reading, writing, and editing metadata in almost any file format. Recommended for advanced users and automation.

* Summary table of batch renaming and metadata tools
    * Adobe Bridge: https://www.adobe.com/products/bridge.html
    * Advanced Renamer (Windows): https://www.advancedrenamer.com/
    * NameChanger (macOS): https://mrrsoftware.com/namechanger/
    * XnView MP (cross-platform viewer and converter): https://www.xnview.com/en/xnviewmp/
    * FastStone Image Viewer (Windows): https://www.faststone.org/FSViewerDetail.htm

3. Further reading

* Library of Congress - Sustainability of Digital Formats
    * Page on the TIFF format: https://www.loc.gov/preservation/digital/formats/fdd/fdd000022.shtml
    * Why it matters: The most detailed analysis of the TIFF format in terms of its suitability for long-term preservation.

* DPBestflow (Project of the Library of Congress)
    * Official site: http://www.dpbestflow.org/
    * Why it matters: An excellent resource on all aspects of digital photography for archives and libraries.

* Digital Preservation Coalition (DPC)
    * Official site: https://www.dpconline.org/
    * Why it matters: An international association engaged in digital preservation issues. The site contains a vast number of guides and news in this area.
