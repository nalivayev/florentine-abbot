"""Tests for ImageOrganizer."""

import stat
from pathlib import Path

from common.constants import TAG_XMP_XMPMM_INSTANCE_ID
from common.exifer import Exifer
from common.tagger import Tagger
from common.tags import KeyValueTag, Tag
from content_importer.image_organizer import ImageOrganizer
from tests.common.test_utils import create_test_image


class TestImageOrganizer:

    def test_copy_places_file_at_dest(self, tmp_path: Path) -> None:
        src = tmp_path / "source" / "file.tif"
        src.parent.mkdir()
        src.write_bytes(b"data")
        dest = tmp_path / "archive" / "2024" / "file.tif"

        organizer = ImageOrganizer()
        report = organizer.organize([(src, dest, [])], copy_mode=True)

        assert report.succeeded == 1
        assert report.failed == 0
        assert dest.exists()
        assert src.exists()  # source kept in copy mode

    def test_move_deletes_source(self, tmp_path: Path) -> None:
        src = tmp_path / "source" / "file.tif"
        src.parent.mkdir()
        src.write_bytes(b"data")
        dest = tmp_path / "archive" / "file.tif"

        organizer = ImageOrganizer()
        organizer.organize([(src, dest, [])], copy_mode=False)

        assert dest.exists()
        assert not src.exists()

    def test_dest_already_exists_returns_error(self, tmp_path: Path) -> None:
        src = tmp_path / "file.tif"
        src.write_bytes(b"source")
        dest = tmp_path / "dest.tif"
        dest.write_bytes(b"existing")

        organizer = ImageOrganizer()
        report = organizer.organize([(src, dest, [])], copy_mode=True)

        assert report.succeeded == 0
        assert report.failed == 1
        assert report.results[0].error is not None
        assert "already exists" in report.results[0].error

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        src = tmp_path / "file.tif"
        src.write_bytes(b"data")
        dest = tmp_path / "a" / "b" / "c" / "file.tif"

        organizer = ImageOrganizer()
        report = organizer.organize([(src, dest, [])], copy_mode=True)

        assert report.succeeded == 1
        assert dest.exists()

    def test_protect_makes_dest_readonly(self, tmp_path: Path) -> None:
        src = tmp_path / "file.tif"
        src.write_bytes(b"data")
        dest = tmp_path / "out" / "file.tif"

        organizer = ImageOrganizer()
        organizer.organize([(src, dest, [])], copy_mode=True, protect=True)

        mode = dest.stat().st_mode
        assert not (mode & stat.S_IWUSR), "dest should be read-only"

    def test_no_tmp_file_left_on_success(self, tmp_path: Path) -> None:
        src = tmp_path / "file.tif"
        src.write_bytes(b"data")
        dest = tmp_path / "out" / "file.tif"

        organizer = ImageOrganizer()
        organizer.organize([(src, dest, [])], copy_mode=True)

        tmp = dest.with_suffix(".tif.tmp")
        assert not tmp.exists()

    def test_multiple_files_in_one_call(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "src"
        dst_dir = tmp_path / "dst"
        src_dir.mkdir()
        dst_dir.mkdir()

        mapping: list[tuple[Path, Path, list[Tag]]] = []
        for i in range(3):
            src = src_dir / f"file{i}.tif"
            src.write_bytes(f"data{i}".encode())
            mapping.append((src, dst_dir / f"file{i}.tif", []))

        organizer = ImageOrganizer()
        report = organizer.organize(mapping, copy_mode=True)

        assert report.succeeded == 3
        assert report.total == 3

    def test_writes_tags_to_dest(self, tmp_path: Path, require_exiftool: None) -> None:
        """Tags are written to the destination file (requires ExifTool)."""
        src = tmp_path / "source.tif"
        create_test_image(src)
        dest = tmp_path / "out" / "dest.tif"

        new_id = "xmp.iid:test-instance-123"
        tags: list[Tag] = [KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID, new_id)]

        organizer = ImageOrganizer()
        report = organizer.organize([(src, dest, tags)], copy_mode=True)

        assert report.succeeded == 1

        exifer = Exifer()
        tagger = Tagger(dest, exifer=exifer)
        tagger.begin()
        tagger.read(KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID))
        result = tagger.end() or {}
        assert result[TAG_XMP_XMPMM_INSTANCE_ID] == new_id
