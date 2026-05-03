"""Regression tests for ui.web WebStore DB operations."""

from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from common.database import ArchiveDatabase, FILE_STATUS_NEW
from ui.web.store import WebStore


class TestStore:
    """Covers ui.web DB operations behind WebStore."""

    def setup_method(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.archive_path = Path(self.temp_dir.name)
        self.database = ArchiveDatabase(self.archive_path)
        self._stack = ExitStack()
        self.store = self._stack.enter_context(WebStore(self.archive_path))

    def teardown_method(self) -> None:
        self._stack.close()
        self.database.close_conn()
        self.temp_dir.cleanup()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def test_create_user_and_lookup_methods(self) -> None:
        role_id = self.store.get_role_id("admin")
        assert role_id is not None

        user_id = self.store.create_user(
            username="admin",
            password_hash="hashed-password",
            role_id=role_id,
            created_at=self._now(),
        )

        assert self.store.username_exists("admin") is True

        login_row = self.store.get_user_for_login("admin")
        assert login_row is not None
        assert login_row["id"] == user_id

        summary = self.store.get_user_summary("admin")
        assert summary is not None
        assert summary["role"] == "admin"

        user_row = self.store.get_user_by_id(user_id)
        assert user_row is not None
        assert user_row["id"] == user_id

    def test_session_lifecycle(self) -> None:
        role_id = self.store.get_role_id("admin")
        assert role_id is not None

        user_id = self.store.create_user(
            username="admin",
            password_hash="hashed-password",
            role_id=role_id,
            created_at=self._now(),
        )
        now = self._now()
        self.store.create_session(
            user_id=user_id,
            token_hash="token-hash",
            created_at=now,
            expires_at=now,
        )
        self.store.update_last_login(user_id, now)

        current_user = self.store.get_user_by_token_hash("token-hash")
        assert current_user is not None
        assert current_user["username"] == "admin"
        assert current_user["token_hash"] == "token-hash"

        summary = self.store.get_user_summary("admin")
        assert summary is not None
        assert summary["last_login_at"] == now

        self.store.delete_session(user_id, "token-hash")

        assert self.store.get_user_by_token_hash("token-hash") is None

    def test_list_users_and_delete_user(self) -> None:
        role_id = self.store.get_role_id("user")
        assert role_id is not None

        user_id = self.store.create_user(
            username="editor",
            password_hash="hashed-password",
            role_id=role_id,
            created_at=self._now(),
        )
        self.store.create_session(
            user_id=user_id,
            token_hash="session-hash",
            created_at=self._now(),
            expires_at=self._now(),
        )

        users = self.store.list_users()
        assert len(users) == 1
        assert users[0]["username"] == "editor"
        assert users[0]["role"] == "user"

        self.store.delete_user_sessions(user_id)
        self.store.delete_user(user_id)

        assert self.store.list_users() == []

    def test_collection_lifecycle_methods(self) -> None:
        collection = self.store.create_collection(
            collection_type="scan",
            name="Family album",
            created_at=self._now(),
        )

        collections = self.store.list_collections()
        assert len(collections) == 1
        assert collections[0]["name"] == "Family album"

        conn = self.database.get_conn()
        conn.execute(
            "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
            (collection["id"], "2024/scan.tif", FILE_STATUS_NEW, self._now()),
        )
        conn.commit()

        files = self.store.list_files(collection_id=int(collection["id"]))
        assert len(files) == 1
        assert files[0]["path"] == "2024/scan.tif"

        paths = self.store.list_file_paths(collection_id=int(collection["id"]))
        assert len(paths) == 1
        assert paths[0]["id"] == files[0]["id"]
        assert paths[0]["path"] == "2024/scan.tif"

    def test_collection_file_detail_reads_semantic_metadata_projection(self) -> None:
        collection = self.store.create_collection(
            collection_type="scan",
            name="Family album",
            created_at=self._now(),
        )

        conn = self.database.get_conn()
        cursor = conn.execute(
            "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
            (collection["id"], "2024/scan.tif", FILE_STATUS_NEW, self._now()),
        )
        assert cursor.lastrowid is not None
        file_id = int(cursor.lastrowid)

        conn.execute(
            """
            INSERT INTO file_metadata (
                file_id, photo_year, photo_month, photo_day, photo_time,
                date_accuracy, description, source, credit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (file_id, 2024, 3, 15, "10:30:00", "exact", "Portrait", "Album 3", "Family archive"),
        )
        conn.execute(
            "INSERT INTO file_meta_gps (file_id, lat, lon, altitude) VALUES (?, ?, ?, ?)",
            (file_id, 41.8902, 12.4924, 32.5),
        )
        conn.execute(
            "INSERT INTO file_creators (file_id, position, name) VALUES (?, ?, ?)",
            (file_id, 1, "Alice Example"),
        )
        conn.execute(
            "INSERT INTO file_history (file_id, action, recorded_at, software, changed, instance_id) VALUES (?, ?, ?, ?, ?, ?)",
            (file_id, "managed", self._now(), "content-importer test", "metadata", "iid-1"),
        )
        conn.commit()

        detail = self.store.get_file_detail(file_id)

        assert detail is not None
        assert detail["path"] == "2024/scan.tif"
        assert detail["description"] == "Portrait"
        assert detail["photo_time"] == "10:30:00"
        assert detail["gps_lat"] == 41.8902
        assert detail["gps_lon"] == 12.4924
        assert detail["gps_altitude"] == 32.5

        creators = self.store.list_file_creators(file_id)
        assert creators == ["Alice Example"]

        history = self.store.list_file_history(file_id)
        assert len(history) == 1
        assert history[0]["action"] == "managed"
        assert history[0]["changed"] == "metadata"

    def test_browse_files_uses_filesystem_with_db_overlay_for_tracked_files(self) -> None:
        sources_dir = self.archive_path / "1925" / "1925.04.00" / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)
        tracked_file = sources_dir / "1925.04.00.00.00.00.C.001.001.0001.A.RAW.tif"
        tracked_file.write_bytes(b"raw")
        loose_file = sources_dir / "1925.04.00.00.00.00.C.001.001.0002.A.RAW.tif"
        loose_file.write_bytes(b"raw2")

        collection = self.store.create_collection(
            collection_type="scan",
            name="Family album",
            created_at=self._now(),
        )
        conn = self.database.get_conn()
        cursor = conn.execute(
            "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
            (collection["id"], "1925\\1925.04.00\\SOURCES\\1925.04.00.00.00.00.C.001.001.0001.A.RAW.tif", FILE_STATUS_NEW, self._now()),
        )
        assert cursor.lastrowid is not None
        tracked_id = int(cursor.lastrowid)
        conn.commit()

        parent_payload = self.store.browse_files(str(self.archive_path), "1925/1925.04.00")
        child_payload = self.store.browse_files(str(self.archive_path), "1925/1925.04.00/SOURCES")
        tracked_payload = next(file for file in child_payload["files"] if file["path"].endswith("0001.A.RAW.tif"))
        loose_payload = next(file for file in child_payload["files"] if file["path"].endswith("0002.A.RAW.tif"))

        assert len(parent_payload["folders"]) == 1
        assert parent_payload["folders"][0]["name"] == "SOURCES"
        assert parent_payload["folders"][0]["path"] == "1925/1925.04.00/SOURCES"
        assert parent_payload["folders"][0]["empty"] is False
        assert parent_payload["folders"][0]["modified_at"] is not None
        assert child_payload["folders"] == []
        assert len(child_payload["files"]) == 2
        assert tracked_payload["path"] == "1925/1925.04.00/SOURCES/1925.04.00.00.00.00.C.001.001.0001.A.RAW.tif"
        assert tracked_payload["size_bytes"] == 3
        assert tracked_payload["modified_at"] is not None
        assert tracked_payload["id"] == tracked_id
        assert tracked_payload["collection_id"] == collection["id"]
        assert tracked_payload["collection_name"] == "Family album"
        assert tracked_payload["status"] == FILE_STATUS_NEW
        assert tracked_payload["imported_at"] is not None
        assert loose_payload["path"] == "1925/1925.04.00/SOURCES/1925.04.00.00.00.00.C.001.001.0002.A.RAW.tif"
        assert loose_payload["size_bytes"] == 4
        assert loose_payload["modified_at"] is not None
        assert "id" not in loose_payload
        assert "status" not in loose_payload
        assert "collection_id" not in loose_payload

