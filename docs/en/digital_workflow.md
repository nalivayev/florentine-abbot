# Guide to Digital Photo Workflow (Born-Digital)

## Table of Contents
- **Introduction**
- **Part 1: Import and Initial Safety**
- **Part 2: Culling**
- **Part 3: Naming and Organization**
- **Part 4: Metadata**
- **Part 5: Storage Formats**

---

## Introduction

Working with photos taken on a digital camera or phone ("born-digital") is fundamentally different from scanning.
In scanning, we fight to get maximum quality from an analog source.
In digital photography, the source is already perfect (it's the RAW file from the camera), and the archivist's main enemies here are **chaos, duplicates, and loss of context**.

This guide will help turn the stream of files from a flash drive into a structured archive.

---

## Part 1. Import and Initial Safety

### Main Rule: Backup First, Then Sort
Never start renaming, deleting, or processing photos directly on the memory card.

1.  **Copying:** Copy all files from the memory card to the `INCOMING` folder on your computer.
2.  **Second Copy:** If the shoot is important, immediately copy this folder to an external drive.
3.  **Only now** can you clear the memory card and start working with the `INCOMING` folder.

---

## Part 2. Culling

Digital shooting encourages taking thousands of shots. Keeping them all means burying the best shots in trash.

### "Traffic Light" Method
Review imported photos and assign them labels (flags or colors in your software):

*   🔴 **Reject:** Technical defects (blur, closed eyes), accidental shots, exact duplicates. **Delete ruthlessly.**
*   🟡 **Keep:** Good shots documenting the event. They will go into the archive.
*   🟢 **Select:** The best 5-10 shots of the event. They will go to print, social media, and the `VIEW` folder.

> **Tip:** If you have 10 similar shots of one subject, keep 1 best and 1 backup. The other 8 are trash that will take up your time and disk space in 10 years.

---

## Part 3. Naming and Organization

For digital photos, we use the same naming rules as for scans (`naming.md`), but with important nuances.

### 1. Automation via EXIF
Unlike scans, a digital photo already knows its creation date and time. Use this!

**Renaming Template:**
`YYYY.MM.DD.HH.NN.SS.E.[GGG].[SSS].NNNN.A.ext`

*   **YYYY.MM.DD.HH.NN.SS** — taken automatically from EXIF (Date Time Original).
*   **E** — always `E` (Exact), since the date is exact.
*   **[GGG].[SSS]** — group and subgroup code you set manually for the entire series (e.g., `FAM.VAC` for vacation).
*   **NNNN** — sequential number (counter).
*   **A** — always `A` (since a digital file has no "reverse").

### 2. Example Process (in Adobe Bridge / Lightroom)
1.  Select all chosen photos of the series.
2.  Open the "Batch Rename" tool.
3.  Set the template: `{Date Created}.E.FAM.VAC.{Sequence Number, 4}.A`
4.  Click "Rename".

**Was:** `DSC_0543.ARW`, `DSC_0544.ARW`
**Became:** `2024.06.15.14.30.22.E.FAM.VAC.0001.A.ARW`, `2024.06.15.14.30.25.E.FAM.VAC.0002.A.ARW`

---

## Part 4. Metadata

The filename ensures uniqueness, but context lives in metadata.

### Mandatory Minimum
For digital photos, filling in metadata is easier since it can be copied to a group of files.

1.  **Description:**
    *   Select all photos of the event.
    *   Write a general description: *"Trip to Lake Baikal. View of Shaman Rock."*
    *   For portraits, add people's names individually.
2.  **Keywords:**
    *   Add tags: `Baikal`, `Nature`, `2024`, `Family`.
3.  **Copyright:**
    *   Set up automatic addition of your copyright upon import.

---

## Part 5. Storage Formats

In digital photography, there is no concept of "Master Copy" in the same sense as in scanning. Here there is **Source (RAW)** and **Result (Export)**.

### 1. Source (RAW)
This is your "digital negative".
*   **Formats:** Original RAW (`.CR2`, `.NEF`, `.ARW`) or converted `.DNG`.
*   **Action:** Store forever. Do not edit the file itself (edits are stored in a sidecar `.xmp` file or catalog database).

### 2. Export (Result)
These are files for use (printing, viewing).
*   **Format:** JPEG (High Quality) or TIFF (for printing).
*   **Action:** Generate on demand from RAW. Can be deleted if the RAW is preserved.
