"""Archive Keeper batch orchestration for archive integrity reconciliation."""

from pathlib import Path

from archive_keeper.processor import KeeperProcessor
from archive_keeper.store import KeeperStore
from common.database import FILE_STATUS_MODIFIED
from common.logger import Logger


class Keeper:
    """Batch-mode archive integrity reconciler."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        self._processor = KeeperProcessor(logger)

    def execute(self, *, path: Path) -> None:
        """Run one integrity pass for the archive at *path*."""
        if not path.exists():
            raise ValueError(f"Archive path does not exist: {path}")

        self.poll(path)

    def poll(self, archive_path: Path) -> None:
        """Run one archive-keeper daemon cycle against the archive database."""
        if not archive_path.exists():
            raise ValueError(f"Archive path does not exist: {archive_path}")

        with KeeperStore(archive_path) as store:
            self._recover_missing(store, archive_path)
            self._checksum_new_files(store, archive_path)
            self._promote_to_active(store, archive_path)
            self._detect_missing(store, archive_path)

    def _recover_missing(self, store: KeeperStore, archive_path: Path) -> None:
        """Reset files marked as missing that have reappeared on disk."""
        for record in store.list_missing_files():
            file_path = archive_path / record.rel_path
            if file_path.exists():
                self._logger.info(f"File recovered, resetting to new: {record.rel_path}")
                store.requeue_recovered_file(record.file_id)

    def _checksum_new_files(self, store: KeeperStore, archive_path: Path) -> None:
        """Calculate checksums for new files that don't have one yet."""
        for record in store.list_new_files_without_checksum():
            file_path = archive_path / record.rel_path
            if not file_path.exists():
                continue
            try:
                checksum = self._processor.process(file_path)
                store.update_checksum(record.file_id, checksum)
                self._logger.info(f"Checksum calculated: {record.rel_path}")
            except Exception as e:
                self._logger.error(f"Failed to calculate checksum for {record.rel_path}: {e}")

    def _promote_to_active(self, store: KeeperStore, archive_path: Path) -> None:
        """Promote ready new/modified files to active."""
        for record in store.list_activation_candidates():
            task_counts = store.get_task_counts(record.file_id)

            if task_counts.pending == 0 and task_counts.total > 0:
                if record.status == FILE_STATUS_MODIFIED:
                    file_path = archive_path / record.rel_path
                    if not file_path.exists():
                        self._logger.warning(
                            f"Modified file missing before activation: {record.rel_path}"
                        )
                        continue
                    try:
                        checksum = self._processor.process(file_path)
                        store.mark_active(record.file_id, checksum=checksum)
                        self._logger.info(
                            f"Checksum refreshed for modified file: {record.rel_path}"
                        )
                    except Exception as e:
                        self._logger.error(
                            f"Failed to refresh checksum for {record.rel_path}: {e}"
                        )
                        continue
                else:
                    if record.checksum is None:
                        self._logger.warning(
                            f"New file has no checksum yet, keeping status 'new': {record.rel_path}"
                        )
                        continue
                    store.mark_active(record.file_id)

    def _detect_missing(self, store: KeeperStore, archive_path: Path) -> None:
        """Mark active files that are no longer on disk as missing."""
        for record in store.list_active_files():
            file_path = archive_path / record.rel_path
            if not file_path.exists():
                self._logger.warning(f"File missing: {record.rel_path}")
                store.mark_missing(record.file_id)
