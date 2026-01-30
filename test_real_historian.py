#!/usr/bin/env python3
"""Test script for XMP Historian on a real image file."""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from common.historian import XMPHistorian, XMP_ACTION_EDITED
from common.exifer import Exifer


def main():
    # Path to the real file
    file_path = Path(r"D:\temp\1925.04.00.00.00.00.C.001.001.0001.A.RAW.tif")

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    # Create historian
    historian = XMPHistorian()

    # Add a history entry
    when = datetime.now(timezone.utc)
    software_agent = "Florentine Abbot/test-script 1.0.0"

    print(f"Adding history entry to {file_path}")
    success = historian.append_entry(
        file_path=file_path,
        action=XMP_ACTION_EDITED,
        software_agent=software_agent,
        when=when,
        changed="/metadata",
        parameters="Test entry for historian validation"
    )

    if success:
        print("History entry added successfully.")
    else:
        print("Failed to add history entry.")
        return

    # Now read back using exiftool directly
    print("\nReading history using exiftool:")
    exifer = Exifer()
    result = exifer.read(file_path, ["XMP-xmpMM:History"])
    print(f"Raw result from exifer.read: {result}")

    if result and "XMP-xmpMM:History" in result:
        history = result["XMP-xmpMM:History"]
        print("XMP-xmpMM:History:")
        if isinstance(history, list):
            for i, entry in enumerate(history):
                print(f"  Entry {i+1}: {entry}")
        else:
            print(f"  {history}")
    else:
        print("No history found or failed to read.")

    # Also try reading all XMP tags
    print("\nTrying to read all XMP-xmpMM tags:")
    all_result = exifer.read(file_path, ["XMP-xmpMM:all"])
    print(f"All XMP-xmpMM: {all_result}")

    # Also run exiftool command to show structured XMP History
    print("\n" + "="*50)
    print("Structured XMP History using exiftool -XMP -b:")
    import subprocess
    try:
        cmd = ["exiftool", "-XMP", "-b", str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=False, timeout=30)
        if result.returncode == 0:
            xmp_data = result.stdout.decode('utf-8', errors='ignore')
            # Look for xmpMM:History
            if "<xmpMM:History>" in xmp_data:
                start = xmp_data.find("<xmpMM:History>")
                end = xmp_data.find("</xmpMM:History>") + len("</xmpMM:History>")
                history_xml = xmp_data[start:end]
                print(history_xml)
            else:
                print("xmpMM:History not found in XMP data.")
                print("XMP data preview:")
                print(xmp_data[:1000])
        else:
            print(f"Error: {result.stderr.decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"Failed to run exiftool: {e}")


if __name__ == "__main__":
    main()