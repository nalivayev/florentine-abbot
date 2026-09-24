"""
Tests for the file filter of the Process batch.
"""

import os
from pathlib import Path

import pytest

from scan_batcher.batch import Process
from scan_batcher.logger import Logger


RAW = "2026.09.24.10.11.12.RAW.tif"
MSR = "2026.09.24.10.11.12.MSR.tif"
NOTES = "notes"

CASE_INSENSITIVE = os.path.normcase("A") == "a"


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    """
    Create a folder holding a raw, a master and a file with no extension.
    """
    for name in (RAW, MSR, NOTES):
        (tmp_path / name).touch()
    return tmp_path


@pytest.mark.parametrize(
    "file_filter, expected",
    [
        ("*.tif", {RAW, MSR}),
        (".tif", {RAW, MSR}),
        ("RAW.tif", {RAW}),
        ("*.RAW.tif", {RAW}),
        ("*.*", {RAW, MSR}),
        ("raw.tif", {RAW} if CASE_INSENSITIVE else set()),
    ],
)
def test_filter(logger: Logger, folder: Path, file_filter: str, expected: set[str]) -> None:
    """
    A filter is either a glob or an ending of the name; case follows the platform.
    """
    batch = Process(logger, folder, file_filter)
    assert {item["filename"] for item in batch} == expected


@pytest.mark.parametrize("file_filter, warnings", [("*.xyz", 1), ("*.tif", 0)])
def test_empty_selection_warns(
    logger: Logger, folder: Path, monkeypatch: pytest.MonkeyPatch, file_filter: str, warnings: int
) -> None:
    """
    A filter that selects nothing is reported rather than passed over in silence.
    """
    calls: list[str] = []
    monkeypatch.setattr(logger, "warning", lambda msg, *args, **kwargs: calls.append(msg))
    Process(logger, folder, file_filter)
    assert len(calls) == warnings
