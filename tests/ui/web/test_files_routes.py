"""Regression tests for ui.web files routes."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from common.constants import ARCHIVE_SYSTEM_DIR
from common.database import ArchiveDatabase, FILE_STATUS_ACTIVE, FILE_STATUS_NEW
from preview_maker.constants import PREVIEWS_DIR
from tile_cutter.constants import TILES_DIR
from ui.web.routes.files import DeleteItemsRequest, delete_items, get_file, list_files
from ui.web.routes.files.history import get_file_history
from ui.web.routes.files.metadata import get_file_metadata
from ui.web.routes.files.navigation import get_file_navigation
from ui.web.store import WebStore


class TestFilesRoutes:
    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def test_list_files_filters_by_collection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)

            preview_dir = archive_path / ARCHIVE_SYSTEM_DIR / PREVIEWS_DIR / "2024"
            preview_dir.mkdir(parents=True, exist_ok=True)
            (preview_dir / "scan.PRV.jpg").write_bytes(b"jpg")

            tile_dir = archive_path / ARCHIVE_SYSTEM_DIR / TILES_DIR / "2024" / "scan"
            tile_dir.mkdir(parents=True, exist_ok=True)
            (tile_dir / "meta.json").write_text("{}", encoding="utf-8")

            monkeypatch.setattr("ui.web.routes.files.get_archive_path", lambda: archive_path)
            monkeypatch.setattr("ui.web.routes.files.navigation.get_archive_path", lambda: archive_path)

            conn = database.get_conn()
            try:
                collection_a = conn.execute(
                    "INSERT INTO collections (type, name, created_at) VALUES (?, ?, ?)",
                    ("scan", "Family album", self._now()),
                ).lastrowid
                collection_b = conn.execute(
                    "INSERT INTO collections (type, name, created_at) VALUES (?, ?, ?)",
                    ("scan", "Other album", self._now()),
                ).lastrowid
                assert collection_a is not None
                assert collection_b is not None

                conn.execute(
                    "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
                    (int(collection_a), "2024/scan.tif", FILE_STATUS_ACTIVE, self._now()),
                )
                conn.execute(
                    "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
                    (int(collection_b), "2025/other.tif", FILE_STATUS_NEW, self._now()),
                )
                conn.commit()

                with WebStore(archive_path) as store:
                    payload = asyncio.run(
                        list_files(
                            collection_id=int(collection_a),
                            _user={"id": 1, "role": "admin"},
                            store=store,
                        )
                    )

                assert len(payload) == 1
                assert payload[0]["path"] == "2024/scan.tif"
                assert payload[0]["preview_url"] == "/system/previews/2024/scan.PRV.jpg"
                assert payload[0]["tile_base_url"] == "/system/tiles/2024/scan"
            finally:
                database.close_conn()

    def test_get_file_returns_base_file_payload(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)

            preview_dir = archive_path / ARCHIVE_SYSTEM_DIR / PREVIEWS_DIR / "2024"
            preview_dir.mkdir(parents=True, exist_ok=True)
            (preview_dir / "scan.PRV.jpg").write_bytes(b"jpg")

            tile_dir = archive_path / ARCHIVE_SYSTEM_DIR / TILES_DIR / "2024" / "scan"
            tile_dir.mkdir(parents=True, exist_ok=True)
            (tile_dir / "meta.json").write_text("{}", encoding="utf-8")

            monkeypatch.setattr("ui.web.routes.files.get_archive_path", lambda: archive_path)
            monkeypatch.setattr("ui.web.routes.files.navigation.get_archive_path", lambda: archive_path)

            conn = database.get_conn()
            try:
                collection_id = conn.execute(
                    "INSERT INTO collections (type, name, created_at) VALUES (?, ?, ?)",
                    ("scan", "Family album", self._now()),
                ).lastrowid
                assert collection_id is not None

                file_id = conn.execute(
                    "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
                    (int(collection_id), "2024\\scan.tif", FILE_STATUS_ACTIVE, self._now()),
                ).lastrowid
                assert file_id is not None

                conn.execute(
                    """
                    INSERT INTO file_metadata (
                        file_id, photo_year, photo_month, photo_day, photo_time,
                        date_accuracy, description, source, credit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (int(file_id), 2024, 3, 15, "10:30:00", "exact", "Portrait", "Album 3", "Family archive"),
                )
                conn.execute(
                    "INSERT INTO file_meta_gps (file_id, lat, lon, altitude) VALUES (?, ?, ?, ?)",
                    (int(file_id), 41.8902, 12.4924, 32.5),
                )
                conn.execute(
                    "INSERT INTO file_creators (file_id, position, name) VALUES (?, ?, ?)",
                    (int(file_id), 1, "Alice Example"),
                )
                conn.commit()

                with WebStore(archive_path) as store:
                    payload = asyncio.run(
                        get_file(
                            int(file_id),
                            _user={"id": 1, "role": "admin"},
                            store=store,
                        )
                    )

                assert payload["path"] == "2024/scan.tif"
                assert payload["status"] == FILE_STATUS_ACTIVE
                assert payload["collection_id"] == int(collection_id)
                assert payload["collection_name"] == "Family album"
                assert payload["preview_url"] == "/system/previews/2024/scan.PRV.jpg"
                assert payload["tile_base_url"] == "/system/tiles/2024/scan"
                assert payload["creators"] == ["Alice Example"]
            finally:
                database.close_conn()

    def test_get_file_returns_404_for_missing_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)

            monkeypatch.setattr("ui.web.routes.files.get_archive_path", lambda: archive_path)

            database.get_conn()
            try:
                with WebStore(archive_path) as store:
                    with pytest.raises(Exception) as exc_info:
                        asyncio.run(
                            get_file(
                                999,
                                _user={"id": 1, "role": "admin"},
                                store=store,
                            )
                        )
                assert getattr(exc_info.value, "status_code", None) == 404
            finally:
                database.close_conn()

    def test_get_file_metadata_returns_semantic_metadata(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)

            monkeypatch.setattr("ui.web.routes.files.get_archive_path", lambda: archive_path)
            monkeypatch.setattr("ui.web.routes.files.navigation.get_archive_path", lambda: archive_path)

            conn = database.get_conn()
            try:
                collection_id = conn.execute(
                    "INSERT INTO collections (type, name, created_at) VALUES (?, ?, ?)",
                    ("scan", "Family album", self._now()),
                ).lastrowid
                assert collection_id is not None

                file_id = conn.execute(
                    "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
                    (int(collection_id), "2024/scan.tif", FILE_STATUS_ACTIVE, self._now()),
                ).lastrowid
                assert file_id is not None

                conn.execute(
                    """
                    INSERT INTO file_metadata (
                        file_id, photo_year, photo_month, photo_day, photo_time,
                        date_accuracy, description, source, credit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (int(file_id), 2024, 3, 15, "10:30:00", "exact", "Portrait", "Album 3", "Family archive"),
                )
                conn.execute(
                    "INSERT INTO file_meta_gps (file_id, lat, lon, altitude) VALUES (?, ?, ?, ?)",
                    (int(file_id), 41.8902, 12.4924, 32.5),
                )
                conn.commit()

                with WebStore(archive_path) as store:
                    payload = asyncio.run(
                        get_file_metadata(
                            int(file_id),
                            _user={"id": 1, "role": "admin"},
                            store=store,
                        )
                    )

                assert payload is not None
                assert payload["description"] == "Portrait"
                assert payload["photo_time"] == "10:30:00"
                assert payload["gps"] == {"lat": 41.8902, "lon": 12.4924, "altitude": 32.5}
            finally:
                database.close_conn()

    def test_get_file_history_returns_history(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)

            monkeypatch.setattr("ui.web.routes.files.get_archive_path", lambda: archive_path)
            monkeypatch.setattr("ui.web.routes.files.navigation.get_archive_path", lambda: archive_path)

            conn = database.get_conn()
            try:
                collection_id = conn.execute(
                    "INSERT INTO collections (type, name, created_at) VALUES (?, ?, ?)",
                    ("scan", "Family album", self._now()),
                ).lastrowid
                assert collection_id is not None

                file_id = conn.execute(
                    "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
                    (int(collection_id), "2024/scan.tif", FILE_STATUS_ACTIVE, self._now()),
                ).lastrowid
                assert file_id is not None

                conn.execute(
                    "INSERT INTO file_history (file_id, action, recorded_at, software, changed, instance_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (int(file_id), "managed", self._now(), "content-importer test", "metadata", "iid-1"),
                )
                conn.commit()

                with WebStore(archive_path) as store:
                    payload = asyncio.run(
                        get_file_history(
                            int(file_id),
                            _user={"id": 1, "role": "admin"},
                            store=store,
                        )
                    )

                assert len(payload) == 1
                assert payload[0]["action"] == "managed"
                assert payload[0]["changed"] == "metadata"
            finally:
                database.close_conn()

    def test_get_file_navigation_returns_adjacent_viewable_files(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)

            first_tile_dir = archive_path / ARCHIVE_SYSTEM_DIR / TILES_DIR / "2024" / "001"
            first_tile_dir.mkdir(parents=True, exist_ok=True)
            (first_tile_dir / "meta.json").write_text("{}", encoding="utf-8")

            second_tile_dir = archive_path / ARCHIVE_SYSTEM_DIR / TILES_DIR / "2024" / "003"
            second_tile_dir.mkdir(parents=True, exist_ok=True)
            (second_tile_dir / "meta.json").write_text("{}", encoding="utf-8")

            monkeypatch.setattr("ui.web.routes.files.get_archive_path", lambda: archive_path)
            monkeypatch.setattr("ui.web.routes.files.navigation.get_archive_path", lambda: archive_path)

            conn = database.get_conn()
            try:
                collection_id = conn.execute(
                    "INSERT INTO collections (type, name, created_at) VALUES (?, ?, ?)",
                    ("scan", "Family album", self._now()),
                ).lastrowid
                assert collection_id is not None

                first_id = conn.execute(
                    "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
                    (int(collection_id), "2024/001.tif", FILE_STATUS_ACTIVE, self._now()),
                ).lastrowid
                middle_id = conn.execute(
                    "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
                    (int(collection_id), "2024/002.tif", FILE_STATUS_ACTIVE, self._now()),
                ).lastrowid
                third_id = conn.execute(
                    "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
                    (int(collection_id), "2024/003.tif", FILE_STATUS_ACTIVE, self._now()),
                ).lastrowid
                assert first_id is not None
                assert middle_id is not None
                assert third_id is not None
                conn.commit()

                with WebStore(archive_path) as store:
                    payload = asyncio.run(
                        get_file_navigation(
                            int(third_id),
                            collection_id=int(collection_id),
                            _user={"id": 1, "role": "admin"},
                            store=store,
                        )
                    )

                assert payload["prev_id"] == int(first_id)
                assert payload["next_id"] is None
            finally:
                database.close_conn()

    def test_delete_items_deletes_untracked_file_by_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)
            monkeypatch.setattr("ui.web.routes.files.get_archive_path", lambda: archive_path)

            physical_file = archive_path / "1925" / "1925.04.00" / "SOURCES" / "scan.RAW.tif"
            physical_file.parent.mkdir(parents=True, exist_ok=True)
            physical_file.write_bytes(b"raw")

            database.get_conn()
            try:
                with WebStore(archive_path) as store:
                    payload = asyncio.run(
                        delete_items(
                            DeleteItemsRequest(file_paths=["1925/1925.04.00/SOURCES/scan.RAW.tif"]),
                            _user={"id": 1, "role": "admin"},
                            store=store,
                        )
                    )

                assert payload["failed"] == []
                assert payload["deleted"] == [
                    {
                        "kind": "file",
                        "key": "file-path:1925/1925.04.00/SOURCES/scan.RAW.tif",
                        "path": "1925/1925.04.00/SOURCES/scan.RAW.tif",
                    }
                ]
                assert physical_file.exists() is False
            finally:
                database.close_conn()
