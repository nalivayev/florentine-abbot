"""Database models for Archive Keeper."""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Enum, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum

class Base(DeclarativeBase):
    pass

class FileStatus(enum.Enum):
    OK = "ok"
    MISSING = "missing"
    CORRUPTED = "corrupted"
    MODIFIED = "modified"

class AuditEventType(enum.Enum):
    ADDED = "added"
    MOVED = "moved"
    RENAMED = "renamed"
    MODIFIED = "modified"
    CORRUPTED_DETECTED = "corrupted_detected"
    MISSING_DETECTED = "missing_detected"
    RECOVERED = "recovered"

class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String, unique=True, index=True)  # Relative path in archive
    name: Mapped[str] = mapped_column(String, index=True)
    hash: Mapped[str] = mapped_column(String(64), index=True)  # SHA-256
    size: Mapped[int] = mapped_column(BigInteger)
    mtime: Mapped[float] = mapped_column()  # Timestamp
    
    status: Mapped[FileStatus] = mapped_column(Enum(FileStatus), default=FileStatus.OK)
    last_checked_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    metadata_entries: Mapped[list["FileMetadata"]] = relationship(back_populates="file", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="file", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<File(path={self.path}, status={self.status})>"

class FileMetadata(Base):
    __tablename__ = "file_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"))
    key: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[str] = mapped_column(String)

    file: Mapped["File"] = relationship(back_populates="metadata_entries")

    def __repr__(self) -> str:
        return f"<Metadata(key={self.key}, value={self.value})>"

class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_id: Mapped[int | None] = mapped_column(ForeignKey("files.id"), nullable=True)
    event_type: Mapped[AuditEventType] = mapped_column(Enum(AuditEventType))
    details: Mapped[str | None] = mapped_column(String)
    old_value: Mapped[str | None] = mapped_column(String)
    new_value: Mapped[str | None] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    file: Mapped["File"] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(event={self.event_type}, time={self.timestamp})>"
