"""
Tests for ArchiveMetadata configuration provider.
"""


from common.constants import DEFAULT_TAGS
from common.logger import Logger

from tests.common.fake_archive_metadata import FakeArchiveMetadata


class TestGetConfigurableTags:
    """
    Tests for get_configurable_tags method.
    """

    def test_returns_default_tags_when_no_config(self) -> None:
        """
        Returns default tags when no tags.json loaded.
        """
        am = FakeArchiveMetadata(metadata_tags=None)
        
        tags = am.get_configurable_tags()
        
        assert tags == list(DEFAULT_TAGS.values())

    def test_returns_custom_tags_from_config(self) -> None:
        """
        Returns tags from custom configuration.
        """
        custom_tags = {
            "description": "XMP-dc:Description",
            "custom_field": "XMP-custom:Field",
        }
        am = FakeArchiveMetadata(metadata_tags=custom_tags)
        
        tags = am.get_configurable_tags()
        
        assert "XMP-dc:Description" in tags
        assert "XMP-custom:Field" in tags


class TestGetMetadataValues:
    """
    Tests for get_metadata_values method.
    """

    def test_returns_empty_dict_when_no_config(self) -> None:
        """
        Returns empty dict when no metadata.json loaded.
        """
        am = FakeArchiveMetadata(metadata_config=None)
        
        values = am.get_metadata_values()
        
        assert values == {}

    def test_returns_empty_dict_when_no_languages(self) -> None:
        """
        Returns empty dict when config has no languages key.
        """
        am = FakeArchiveMetadata(metadata_config={"other_key": "value"})
        
        values = am.get_metadata_values()
        
        assert values == {}

    def test_returns_empty_dict_when_languages_empty(self) -> None:
        """
        Returns empty dict when languages is empty.
        """
        logger = Logger("test", console=False)
        am = FakeArchiveMetadata(metadata_config={"languages": {}}, logger=logger)
        
        values = am.get_metadata_values(logger=logger)
        
        assert values == {}

    def test_returns_values_for_single_language(self) -> None:
        """
        Returns correct values for single language config.
        """
        metadata_config = {
            "languages": {
                "en-US": {
                    "default": True,
                    "description": "Test description",
                    "creator": "John Doe",
                    "rights": "© 2026",
                }
            }
        }
        am = FakeArchiveMetadata(metadata_config=metadata_config)
        
        values = am.get_metadata_values()
        
        # Default language gets base tag
        assert values["XMP-dc:Description"] == "Test description"
        assert values["XMP-dc:Creator"] == ["John Doe"]  # Creator is list
        assert values["XMP-dc:Rights"] == "© 2026"
        
        # Also gets language-specific variants
        assert values["XMP-dc:Description-en-US"] == "Test description"
        assert values["XMP-dc:Creator-en-US"] == ["John Doe"]
        assert values["XMP-dc:Rights-en-US"] == "© 2026"

    def test_returns_values_for_multiple_languages(self) -> None:
        """
        Returns correct values with language variants.
        """
        metadata_config = {
            "languages": {
                "en-US": {
                    "default": True,
                    "description": "English description",
                    "rights": "© 2026",
                },
                "ru-RU": {
                    "description": "Русское описание",
                    "rights": "© 2026 (RU)",
                }
            }
        }
        am = FakeArchiveMetadata(metadata_config=metadata_config)
        
        values = am.get_metadata_values()
        
        # Default language (en-US) gets base tags
        assert values["XMP-dc:Description"] == "English description"
        assert values["XMP-dc:Rights"] == "© 2026"
        
        # Language-specific variants for both languages
        assert values["XMP-dc:Description-en-US"] == "English description"
        assert values["XMP-dc:Description-ru-RU"] == "Русское описание"
        assert values["XMP-dc:Rights-en-US"] == "© 2026"
        assert values["XMP-dc:Rights-ru-RU"] == "© 2026 (RU)"

    def test_fallback_to_first_language_when_no_default(self) -> None:
        """
        Uses first language as default when none marked.
        """
        metadata_config = {
            "languages": {
                "ru-RU": {
                    "description": "Первый язык",
                },
                "en-US": {
                    "description": "Second language",
                }
            }
        }
        am = FakeArchiveMetadata(metadata_config=metadata_config)
        
        values = am.get_metadata_values()
        
        # First language becomes default
        assert values["XMP-dc:Description"] == "Первый язык"

    def test_creator_as_list(self) -> None:
        """
        Creator field is normalized to list.
        """
        metadata_config = {
            "languages": {
                "en-US": {
                    "default": True,
                    "creator": ["Alice", "Bob"],
                }
            }
        }
        am = FakeArchiveMetadata(metadata_config=metadata_config)
        
        values = am.get_metadata_values()
        
        assert values["XMP-dc:Creator"] == ["Alice", "Bob"]
        assert values["XMP-dc:Creator-en-US"] == ["Alice", "Bob"]

    def test_creator_string_converted_to_list(self) -> None:
        """
        Single creator string is converted to list.
        """
        metadata_config = {
            "languages": {
                "en-US": {
                    "default": True,
                    "creator": "Single Author",
                }
            }
        }
        am = FakeArchiveMetadata(metadata_config=metadata_config)
        
        values = am.get_metadata_values()
        
        assert values["XMP-dc:Creator"] == ["Single Author"]

    def test_skips_empty_values(self) -> None:
        """
        Empty values are not included in result.
        """
        metadata_config = {
            "languages": {
                "en-US": {
                    "default": True,
                    "description": "",  # empty
                    "rights": "© 2026",
                }
            }
        }
        am = FakeArchiveMetadata(metadata_config=metadata_config)
        
        values = am.get_metadata_values()
        
        assert "XMP-dc:Description" not in values
        assert "XMP-dc:Description-en-US" not in values
        assert values["XMP-dc:Rights"] == "© 2026"

    def test_uses_custom_tags_mapping(self) -> None:
        """
        Uses custom tags mapping from tags.json.
        """
        custom_tags = {
            "description": "Custom:Description",
            "rights": "Custom:Rights",
        }
        metadata_config = {
            "languages": {
                "en-US": {
                    "default": True,
                    "description": "Test",
                    "rights": "© 2026",
                }
            }
        }
        am = FakeArchiveMetadata(metadata_config=metadata_config, metadata_tags=custom_tags)
        
        values = am.get_metadata_values()
        
        assert values["Custom:Description"] == "Test"
        assert values["Custom:Rights"] == "© 2026"
        assert "XMP-dc:Description" not in values  # Not using default tag
