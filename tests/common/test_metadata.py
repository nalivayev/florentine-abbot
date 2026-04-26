"""Tests for the reusable semantic metadata provider."""

from common.constants import (
    TAG_XMP_DC_CREATOR,
    TAG_XMP_DC_DESCRIPTION,
    TAG_XMP_DC_RIGHTS,
    TAG_XMP_DC_SOURCE,
    TAG_XMP_PHOTOSHOP_CREDIT,
    TAG_XMP_XMPRIGHTS_MARKED,
    TAG_XMP_XMPRIGHTS_USAGE_TERMS,
)
from common.metadata import ArchiveMetadata, DEFAULT_METADATA_CONFIG


class TestArchiveMetadata:
    def test_default_config_is_empty_for_writes(self) -> None:
        values = ArchiveMetadata().get_metadata_values()

        assert values == {}

    def test_multilingual_fields_write_default_and_language_variants(self) -> None:
        metadata = {
            "languages": {
                "ru-RU": {
                    "default": True,
                    "description": "Русское описание",
                    "rights": "Все права защищены",
                    "terms": "Только для личного использования",
                },
                "en-US": {
                    "description": "English description",
                    "rights": "All rights reserved",
                    "terms": "Personal use only",
                },
            },
        }

        values = ArchiveMetadata(metadata=metadata).get_metadata_values()

        assert values[TAG_XMP_DC_DESCRIPTION] == "Русское описание"
        assert values[f"{TAG_XMP_DC_DESCRIPTION}-ru-RU"] == "Русское описание"
        assert values[f"{TAG_XMP_DC_DESCRIPTION}-en-US"] == "English description"
        assert values[TAG_XMP_DC_RIGHTS] == "Все права защищены"
        assert values[f"{TAG_XMP_XMPRIGHTS_USAGE_TERMS}-en-US"] == "Personal use only"

    def test_non_multilingual_fields_use_default_language_only(self) -> None:
        metadata = {
            "languages": {
                "ru-RU": {
                    "default": True,
                    "creator": ["Иван Иванов", "Петр Петров"],
                    "source": "Коробка 3",
                    "credit": "Семейный архив",
                    "marked": True,
                },
                "en-US": {
                    "creator": ["Ivan Ivanov"],
                    "source": "Box 3",
                    "credit": "Family Archive",
                    "marked": False,
                },
            },
        }

        values = ArchiveMetadata(metadata=metadata).get_metadata_values()

        assert values[TAG_XMP_DC_CREATOR] == ["Иван Иванов", "Петр Петров"]
        assert values[TAG_XMP_DC_SOURCE] == "Коробка 3"
        assert values[TAG_XMP_PHOTOSHOP_CREDIT] == "Семейный архив"
        assert values[TAG_XMP_XMPRIGHTS_MARKED] == "True"
        assert f"{TAG_XMP_DC_CREATOR}-en-US" not in values
        assert f"{TAG_XMP_DC_SOURCE}-en-US" not in values
        assert f"{TAG_XMP_PHOTOSHOP_CREDIT}-en-US" not in values

    def test_creator_string_is_split_by_lines(self) -> None:
        metadata = {
            "languages": {
                "ru-RU": {
                    "default": True,
                    "creator": "Alice\nBob",
                },
            },
        }

        values = ArchiveMetadata(metadata=metadata).get_metadata_values()

        assert values[TAG_XMP_DC_CREATOR] == ["Alice", "Bob"]

    def test_default_config_shape_keeps_expected_languages(self) -> None:
        assert "languages" in DEFAULT_METADATA_CONFIG
        assert "ru-RU" in DEFAULT_METADATA_CONFIG["languages"]
        assert "en-US" in DEFAULT_METADATA_CONFIG["languages"]

    def test_returns_default_language_semantic_values(self) -> None:
        metadata = {
            "languages": {
                "ru-RU": {
                    "default": True,
                    "description": "Описание",
                    "creator": ["Иван Иванов", "Мария Иванова"],
                    "source": "Альбом 3",
                    "credit": "Семейный архив",
                },
                "en-US": {
                    "description": "Description",
                    "creator": ["John Smith"],
                    "source": "Album 3",
                    "credit": "Family archive",
                },
            },
        }

        values = ArchiveMetadata(metadata=metadata).get_default_language_values()

        assert values["description"] == "Описание"
        assert values["creator"] == ["Иван Иванов", "Мария Иванова"]
        assert values["source"] == "Альбом 3"
        assert values["credit"] == "Семейный архив"