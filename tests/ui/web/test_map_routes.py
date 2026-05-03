"""Regression tests for ui.web map routes."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from common.database import ArchiveDatabase
from ui.web.routes.map import list_map_files
from ui.web.store import WebStore


class TestMapRoutes:
    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def test_list_map_files_returns_only_files_with_gps(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)

            conn = database.get_conn()
            try:
                collection_id = conn.execute(
                    "INSERT INTO collections (type, name, created_at) VALUES (?, ?, ?)",
                    ("scan", "Family album", self._now()),
                ).lastrowid
                assert collection_id is not None

                file_with_gps_id = conn.execute(
                    "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
                    (int(collection_id), "2024/scan-geo.tif", "active", self._now()),
                ).lastrowid
                file_without_gps_id = conn.execute(
                    "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
                    (int(collection_id), "2024/scan-no-geo.tif", "active", self._now()),
                ).lastrowid
                assert file_with_gps_id is not None
                assert file_without_gps_id is not None

                conn.execute(
                    "INSERT INTO file_meta_gps (file_id, lat, lon, altitude) VALUES (?, ?, ?, ?)",
                    (int(file_with_gps_id), 45.920278, 63.342222, None),
                )
                conn.execute(
                    """
                    INSERT INTO file_metadata (
                        file_id, photo_year, photo_month, photo_day, photo_time,
                        date_accuracy, description, source, credit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(file_with_gps_id),
                        2024,
                        3,
                        15,
                        "10:30:00",
                        "exact",
                        "Portrait",
                        "Album 3",
                        "Family archive",
                    ),
                )
                conn.commit()

                with WebStore(archive_path) as store:
                    payload = asyncio.run(
                        list_map_files(
                            _user={"id": 1, "role": "admin"},
                            store=store,
                        )
                    )

                assert len(payload) == 1
                assert payload[0]["id"] == int(file_with_gps_id)
                assert payload[0]["collection_id"] == int(collection_id)
                assert payload[0]["collection_name"] == "Family album"
                assert payload[0]["path"] == "2024/scan-geo.tif"
                assert payload[0]["gps"] == {
                    "lat": 45.920278,
                    "lon": 63.342222,
                    "altitude": None,
                }
            finally:
                database.close_conn()