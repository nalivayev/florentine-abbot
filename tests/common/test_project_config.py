"""Tests for common.project_config — ProjectConfig singleton."""

import json
from pathlib import Path

from common.project_config import ProjectConfig
from common.constants import DEFAULT_CONFIG, DEFAULT_ROUTES, DEFAULT_SOURCE_FILENAME_TEMPLATE


class TestSingletonLifecycle:
    """Verify initialize / instance contract."""

    def test_initialize_returns_instance(self):
        cfg = ProjectConfig.instance(data=DEFAULT_CONFIG)
        assert cfg is ProjectConfig.instance()

    def test_initialize_replaces_previous(self):
        first = ProjectConfig.instance(data={"a": 1})
        second = ProjectConfig.instance(data={"b": 2})
        assert ProjectConfig.instance() is second
        assert ProjectConfig.instance() is not first


class TestInMemoryData:
    """Initialize with explicit data dict (no file I/O)."""

    def test_empty_data_uses_defaults(self):
        cfg = ProjectConfig.instance(data={})
        assert cfg.formats == {}
        assert cfg.routes == {}
        assert cfg.data.get("metadata") is None

    def test_custom_formats(self):
        cfg = ProjectConfig.instance(data={
            "formats": {
                "source_filename_template": "{year}_{month}_{day}.{extension}",
                "archive_path_template": "{year:04d}",
                "archive_filename_template": "{year:04d}_{month:02d}",
            }
        })
        assert cfg.formats["source_filename_template"] == "{year}_{month}_{day}.{extension}"
        assert cfg.formats["archive_path_template"] == "{year:04d}"
        assert cfg.formats["archive_filename_template"] == "{year:04d}_{month:02d}"

    def test_custom_routes(self):
        rules = [["*.TIFF", "MASTERS"], ["*", "OTHER"]]
        cfg = ProjectConfig.instance(data={
            "routes": {"rules": rules}
        })
        assert cfg.routes == {"rules": rules}

    def test_metadata_tags_and_languages(self):
        tags = {
            "description": "XMP-dc:Description",
            "creator": "XMP-dc:Creator",
        }
        langs = {
            "en-US": {"default": True, "creator": ["Test"]},
            "ru-RU": {"creator": ["Тест"]},
        }
        cfg = ProjectConfig.instance(data={
            "metadata": {"tags": tags, "languages": langs}
        })
        assert cfg.data.get("metadata", {})["tags"] == tags
        assert cfg.data.get("metadata", {})["languages"] == langs

    def test_raw_data(self):
        raw = {"formats": {"archive_path_template": "X"}, "custom": 42}
        cfg = ProjectConfig.instance(data=raw)
        assert cfg.data is raw
        assert cfg.data["custom"] == 42


class TestFileLoading:
    """Load from a JSON file on disk."""

    def test_loads_from_file(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        content = {
            "formats": {
                "source_filename_template": "{year}.{extension}",
            },
            "routes": {
                "rules": [["*", "ALL"]],
            },
            "metadata": {
                "tags": {
                    "description": "XMP-dc:Description",
                },
                "languages": {"en-US": {"default": True}},
            },
        }
        config_file.write_text(json.dumps(content), encoding="utf-8")

        cfg = ProjectConfig.instance(config_path=config_file)
        assert cfg.formats["source_filename_template"] == "{year}.{extension}"
        assert cfg.routes == {"rules": [["*", "ALL"]]}
        assert cfg.data.get("metadata", {})["tags"] == {"description": "XMP-dc:Description"}
        assert cfg.data.get("metadata", {})["languages"] == {"en-US": {"default": True}}

    def test_missing_file_creates_from_defaults(self, tmp_path: Path):
        config_file = tmp_path / "nonexistent" / "config.json"
        cfg = ProjectConfig.instance(config_path=config_file)
        # File should have been created
        assert config_file.exists()
        # Config should have meaningful defaults
        assert cfg.formats.get(
            "source_filename_template", DEFAULT_SOURCE_FILENAME_TEMPLATE
        ) == DEFAULT_SOURCE_FILENAME_TEMPLATE

    def test_invalid_json_falls_back_to_defaults(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        config_file.write_text("{ not valid json !!!", encoding="utf-8")

        cfg = ProjectConfig.instance(config_path=config_file)
        assert cfg.formats.get(
            "source_filename_template", DEFAULT_SOURCE_FILENAME_TEMPLATE
        ) == DEFAULT_SOURCE_FILENAME_TEMPLATE
        assert cfg.routes == DEFAULT_ROUTES

    def test_partial_config_fills_missing_with_defaults(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        content = {
            "formats": {
                "archive_path_template": "{year:04d}",
            }
        }
        config_file.write_text(json.dumps(content), encoding="utf-8")

        cfg = ProjectConfig.instance(config_path=config_file)
        # Provided value used
        assert cfg.formats["archive_path_template"] == "{year:04d}"
        # Missing values fall back to defaults
        assert "source_filename_template" not in cfg.formats
        assert "archive_filename_template" not in cfg.formats
        assert cfg.routes == {}
