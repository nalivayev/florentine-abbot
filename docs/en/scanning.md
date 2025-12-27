# Guide to Digitizing Paper Photo Archives

## Table of Contents
- **Introduction**
- **Part 0: Quick Start**
- **Part 1: Preparation**
- **Part 2: Technical Scanning Parameters**
- **Part 3: Scanning Process**
- **Part 4: Working with Special Materials**
- **Part 5: Frequently Asked Questions (FAQ)**

---

## Introduction

Digitizing a paper archive is not just "converting paper to digital." It is creating a digital twin of history that must outlive the original. Paper yellows, fades, and crumbles. A digital copy, made correctly, will remain unchanged forever.

The main mistake beginners make is scanning for viewing on a phone or posting on social media, often in low, compressed quality. In 5-10 years, when you want to print a photo or restore it, you will have to scan it again. But the originals may not survive by then.

**Goal of this guide:** To teach you to scan **once and for all**. To make a so-called "Master Copy," from which you can then do anything: publish to social networks, print photobooks, or restore in Photoshop.

> **Important:** This guide is dedicated exclusively to digitizing analog media (paper photos, film). If you need to organize an archive of photos taken with a digital camera or phone ("born-digital"), use the `digital_workflow.md` guide.

---

## Part 0. Quick Start

### Goal of this chapter
To get a guaranteed high-quality result without diving into technical details. If you just want to start — use these settings.

### Recommended Settings

In your scanning software (Epson Scan, VueScan, SilverFast, or standard utility), set the following parameters:

| Parameter | Value | Why? |
|:-|:-|:-|
| **Mode / Type** | **24-bit Color** | Even for black and white photos! This preserves paper tones and stains, which is important for history and restoration. |
| **Resolution (DPI)** | **600 dpi** | Optimal balance. Allows enlarging the photo by 2 times when printing without loss of quality. |
| **File Format** | **TIFF** | Uncompressed (or LZW compression). No JPEG for the archive! JPEG degrades the image with every save. |
| **Enhancements** | **OFF ALL*** | Turn off "Dust Removal," "Color Restoration," "Sharpening." It is better to do this manually later. (*See exceptions in Part 2.5*). |

### Start Algorithm

1.  **Wipe the scanner glass** with a lint-free cloth.
2.  **Place the photo** on the glass, centering it. The vertical axis of the photo should align with the vertical axis of the scanner glass.
3.  **Click "Preview".**
4.  **Select the scan area**, capturing a bit of the background (scanner backing) around the photo.
5.  **Click "Scan".**
6.  **Save the file** using the naming rules from the `naming.md` instructions (e.g., `1985.05.09.E.FAM.001.A.RAW.tiff`).

---

## Part 1. Preparation

Scanning quality depends largely not only on the scanner but also on cleanliness. A speck of dust on grandma's face will turn into a mole or scar on the digital copy, removing which will take you 10 minutes in Photoshop. It's easier to spend 1 minute cleaning before scanning.

### 1. Workplace Equipment
*   **Scanner:**
    *   **Ideal:** Flatbed scanner (Epson Perfection V-series, Canon LiDE, etc.).
    *   **Acceptable:** MFP (Multifunction Printer) with a flatbed module, if it allows setting 600 DPI resolution and saving to TIFF format.
    *   **Not Recommended:** Sheet-fed scanners — risk of mechanical damage to fragile photos.
    *   **Alternative if no scanner:** Re-photographing with a modern camera with good lighting.
*   **Gloves:** Cotton white gloves (sold in photo stores or pharmacies). Finger grease is the main enemy of emulsion.
*   **Cleaning:**
    *   Air blower (photographic).
    *   Soft brush (squirrel or synthetic).
    *   Microfiber cloth for glass.

### 2. Photo Preparation
1.  **Sorting:** Sort photos by year or event *before* scanning. This will simplify file naming.
2.  **Cleaning:**
    *   Blow off dust with the blower.
    *   Gently brush off stuck particles.
    *   **NEVER** wipe photos with wet wipes or water. The emulsion may dissolve.
3.  **Analysis:** The back of the photo will always need to be scanned (in accordance with FADGI recommendations).

---

## Part 2. Technical Scanning Parameters

### 1. Resolution (DPI / PPI)
DPI (Dots Per Inch) determines detail. The higher the DPI, the more pixels in the final file.

| Original Size | Recommended DPI | Result |
|:-|:-|:-|
| **Standard Photo (10x15 cm)** | **600 dpi** | Optimal choice. Allows A4 printing or cropping faces. |
| **Small Photo (3x4 cm, passport)** | **1200 dpi** | Necessary to pull details from a tiny snapshot. |
| **Large Photo (A4 and larger)** | **300-400 dpi** | Sufficient to preserve 1:1 scale. |
| **Slides and Negatives** | **2400-4800 dpi** | Transparent materials require much higher values. |

> **Rule:** It is better to scan with excess (600 dpi) than to regret the lack of detail later. Disk space is getting cheaper with technology, but history is priceless.

### 2. Color Depth (Bit Depth)
*   **24-bit Color (8 bits per channel):** Standard for most tasks. Sufficient for quality storage and printing.
*   **48-bit Color (16 bits per channel):** Professional format. File weighs 2 times more.
    *   *When to use:* If the photo is heavily faded, damaged, and will require *extreme* color correction and restoration in Photoshop. 48 bits give a safety margin for "pulling" shadows and colors without "banding" appearing.

### 3. File Format
*   **TIFF (uncompressed or LZW):** The only true choice for the Master Copy. Preserves every pixel exactly as the scanner saw it.
*   **JPEG:** Lossy format. Use JPEG only for the `WEB` or `VIEW` folder (copies for viewing), but not for the archive.
*   **PNG:** Acceptable as it is lossless compression, but TIFF is the industry standard for archives and supports metadata better.

---

## Part 2.5. Advanced Techniques and Nuances (For Perfectionists)

If you want to get the maximum out of your scanner, simply pressing the "Scan" button is not enough. Here are the nuances that distinguish a professional from an amateur.

### 1. Digital ICE (Hardware Dust Removal)
Many scanners (Epson, Nikon) have a Digital ICE feature. This is not just a software filter. The scanner uses an infrared beam to detect physical defects (dust, scratches) on the surface.
*   **When to turn ON:** For color negatives and slides. This saves hours of retouching.
*   **When to turn OFF:**
    *   **Black and White Film (Silver Halide):** Silver in the emulsion blocks the IR beam, and the scanner will perceive the entire image as a defect, turning it into a "mess".
    *   **Paper Photos:** Most flatbed scanners do NOT support Digital ICE for reflective materials. If your scanner supports it — test it. Often it significantly softens the image and creates artifacts on the edges. It is better to spend time cleaning with a blower.

### 2. Histogram and Levels
The scanner's automatic exposure often makes mistakes, turning black into gray or "blowing out" highlights into white.
*   **What to do:** In Professional Mode, open the "Histogram" or "Levels" tool.
*   **Setting:** You will see a "mountain" of data. Move the black triangle (Black Point) to the start of the mountain's rise on the left, and the white one (White Point) to the end of the descent on the right.
*   **Important:** Leave a small gap (clipping) so as not to cut off details in the deepest shadows and brightest highlights. It is better to get a slightly faded image (easy to fix) than a high-contrast one with lost information (impossible to return).

### 3. Descreening
If you are scanning a clipping from a newspaper, magazine, or a postcard printed typographically, you will see a grid of dots (screen). When scanning, this creates moiré (patterned ripples).
*   **Solution:** Turn on the "Descreening" option.
*   **Nuance:** This function slightly blurs the image. Choose the setting corresponding to the print type (Newspaper - 85 lpi, Magazine - 133 lpi, Art Print - 175 lpi).

### 4. Color Management (ICC Profiles)
For archival storage, it is important not only to preserve pixels but also to understand what these pixels mean.
*   **Embed ICC Profile:** Always check this box.
*   **Profile Choice:**
    *   **sRGB:** Safe choice. Colors will look the same on all screens.
    *   **Adobe RGB (1998):** Wider color gamut. Good for future printing and professional processing, but on ordinary monitors, colors may look dull without proper software configuration. For a "Master Copy," Adobe RGB is preferable if you understand how to work with it.

---

## Part 3. Scanning Process

### Step 1: Placement
Place the photo on the glass face down (towards the glass). **Position the photo in the center of the scanner's working area**, not pressing it against the edges. The optics of flatbed scanners provide the best sharpness and minimal geometric distortion in the central zone of the glass.

**Alignment:**

Although FADGI recommends aligning by the physical edges of the print to preserve the document's authenticity, for digitizing personal photos **it is better to align by the image content** — horizon, buildings, vertical portrait lines.

**Why:** This ensures correct geometry and eliminates the need for software rotation, which always leads to interpolation and, consequently, loss of sharpness. To preserve maximum quality, it is better to place the photo straight right away.

### Step 2: Preview and Cropping
Always do a Preview. Set the scan frame (Crop) so that a **white border (2-3 mm)** remains around the photo.
*   *Why:* This guarantees that you haven't cut off the edge of the image. Also, the jagged edge of old photos is part of their charm and history.

### Step 3: Scanning
Click Scan. Do not touch the scanner or table during the process. Vibrations reduce sharpness.

### Step 4: Check
Open the resulting file at 100% scale.
*   Is there any blurriness?
*   Are there dust specks, hairs, or other artifacts on the image?
*   Are color and contrast rendered correctly?

If you find a problem — eliminate the cause (wipe the glass, remove the dust speck from the photo, place it straighter) and rescan.

### Step 5: Reverse Side
**Always scan the reverse side**, regardless of the presence of inscriptions.
*   This can provide additional information to researchers (e.g., about the photo paper used and its quality). This complies with FADGI recommendations.
*   Use the same settings.
*   In the file name, indicate the suffix `.R` (Reverse), for example: `...001.R.tiff`.

### Step 6: File Versions and Metadata

After scanning, you have a **RAW version** (`...RAW.tiff`) — an unprocessed scan with all defects. This is the archival original.

**Further processing:**
1.  **Master version** (`...MSR.tiff`) is created from RAW after minimal correction: rotation, cropping, basic color correction.
2.  **Derivative files** (`...WEB.jpg`, `...PRT.jpg`) — for publication and printing.

**Important:** Immediately after scanning, fill in the file metadata (description, date, copyright) according to the `naming.md` instructions.

### Step 7: Physical Scanning Mark

After successfully scanning and checking the file, it is recommended to make a mark on the original. This records the fact of digitization, the date, and the person responsible, preventing duplicate work in the future.

*   **What to write:** Status, initials, and date. For example: `scan. NKB 2025.04.01`.
*   **Where:** In the bottom left or right corner on the **reverse side**.
*   **With what:** This is a critically important point. Use only a **high-quality graphite pencil**.

    **Pencil Requirements:**
    1.  **Chemical Neutrality (pH-neutral):** The ideal choice is special **Archival Pencils**. They are guaranteed to be acid-free and free of impurities that could cause the paper to yellow over time at the inscription site.
        *   *Examples:* **General's Photo Graphite** (specifically for photos), **Staedtler Mars Lumograph** (high-quality graphite), **Faber-Castell 9000**.
        *   Ordinary graphite is inert, but cheap pencils may contain harmful binders.
    2.  **Hardness:** The optimal choice is **H** or **HB**.
        *   *Why:* An **H** pencil produces a clear, durable line that does not smudge during storage or stain adjacent prints. **HB** is an acceptable universal option.
        *   *Caution:* Avoid soft pencils (**B, 2B** and softer) — they can "dust" and leave dirty marks.
        *   *Technique:* When using H, write **without pressure**, with light touches, so as not to indent the paper.
    3.  **Sharpening:** The pencil should be sharpened, but not "needle-sharp". Slightly blunt the tip on scrap paper.
    
    **Prohibited:**
    *   **Pens (ballpoint, gel, fountain):** Ink is a chemical that penetrates the paper. In 10-20 years, the inscription may appear as a mirror spot on the front side (especially on thin photo paper).
    *   **Markers and felt-tip pens:** Contain solvents that can damage the structure of the photo paper.

---

## Part 4. Working with Special Materials

### Embossed Paper ("Silk", "Fabric")
Photos from the 70s-90s were often printed on textured paper. When scanning, this texture creates strong noise ("snow").
*   **Solution 1 (Software):** Scan as is, remove texture with special plugins (e.g., FFT filters).
*   **Solution 2 (Physical):** Scan the photo twice, rotating it 180 degrees. Then combine the two layers in Photoshop with 50% transparency. The shadow from the texture will fall from the other side and compensate for itself.

### Photos in Albums (Glued)
If the photo is glued "tightly," do not try to tear it off — you will tear it.
*   If the album fits in the scanner — scan the entire page (DPI 600-800), then cut into separate files.
*   If the album is thick and the scanner lid does not close — cover it with a sheet of black paper and press down with your hand (gently!). Or use re-photographing with a camera (see separate guide).

### Glossy Photos and Newton Rings

**Any** photos with a glossy or semi-glossy surface (including Polaroid, photo lab prints on glossy paper) can create "Newton Rings" when scanning — rainbow concentric patterns in places of tight contact with the scanner glass. This is a physical effect of light interference.

**Solution:**
*   Try to lift the photo slightly above the glass by placing a thin paper frame (0.5-1 mm thick) around the edges.
*   Or use anti-Newton glass (if your scanner supports it).
*   As a last resort — remove the artifact via software in post-processing.

**Note on Polaroid:** Polaroid shots additionally often have chemical streaks inside the image itself — this is normal and part of the shot's history. Do not try to remove them.

---

## Part 5. Frequently Asked Questions (FAQ)

**Question 1:** Why should I place the photo in the center of the scanner, and not in the corner like paper in a copier?

**Answer:** Because of optical distortions.
The scanner lens is designed like a camera lens: it gives the sharpest and most geometrically correct image in the center. Closer to the edges of the glass, the following may appear:
*   **Loss of sharpness:** Details become blurry.
*   **Chromatic aberration:** Colored halos on high-contrast edges.
*   **Geometric distortion:** Straight lines may bend slightly.

Although modern scanners compensate for this via software, you can't cheat physics. For archival quality, always use the "sweet spot" in the center of the glass.

**Question 2:** I re-photographed photos with a phone or digital camera. Why can't this be considered a Master Copy?

**Answer:**
A Master Copy is not just a picture, it is a **reliable digital document** suitable for restoration and printing. A "handheld" shot (even with a good camera) usually does not meet this standard for three reasons:

1.  **Geometry:** A camera lens always produces distortion, and the slightest tilt turns a rectangular photo into a trapezoid. A scanner rigidly fixes the original plane parallel to the sensor, preserving the correct geometry of the shot.
2.  **Light and Glare:** When shooting, it is difficult to avoid glare on glossy paper, shadows from hands, or uneven lighting. A scanner has a calibrated, uniform light source.
3.  **Processing and Compression:** Phones and cameras often save photos in JPEG (lossy compression) and apply automatic "enhancers" (noise reduction, sharpening) that destroy the natural texture of the paper and fine facial details.

*Re-photographing can only become a Master Copy when using a tripod, macro lens, special lighting, and shooting in RAW, but technically this is more difficult than scanning.*

---

## Appendix A: Checklist Before Starting a Session

1.  [ ] Table is clean, there is space for "Processed" and "In Progress" stacks.
2.  [ ] Scanner glass is wiped and streak-free.
3.  [ ] Gloves are on.
4.  [ ] Software settings checked:
    *   [ ] TIFF
    *   [ ] 600 DPI
    *   [ ] 24-bit Color
    *   [ ] Auto-corrections: OFF
5.  [ ] Folder for saving selected (e.g., `D:\Scans\Temp_Input`).
6.  [ ] Naming scheme selected (or temporary: `Scan_001`, `Scan_002` for later renaming).
7.  [ ] Remember to scan the reverse side of every photo.

---

> **Tip:** Scanning is a meditative process. Turn on an audiobook or podcast. Don't try to do everything in one evening. 50 high-quality scanned photos are better than 500 done haphazardly.
