"""Regression tests for ui.web config routes."""

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from ui.web.routes.config import MetadataSettings, config_metadata_get, config_metadata_save


class TestConfigRoutes:
    def test_metadata_get_returns_default_languages(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPDATA", str(tmp_path))

        data = asyncio.run(config_metadata_get(_user={"id": 1, "role": "admin"}))

        assert "languages" in data
        assert "ru-RU" in data["languages"]
        assert data["languages"]["ru-RU"]["default"] is True
        assert "en-US" in data["languages"]

    def test_metadata_post_persists_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPDATA", str(tmp_path))
        payload: dict[str, Any] = {
            "languages": {
                "ru-RU": {
                    "default": True,
                    "description": "Описание",
                    "creator": ["Иван Иванов"],
                    "rights": "Все права защищены",
                    "source": "Коробка 4",
                    "credit": "Семейный архив",
                    "terms": "Личное использование",
                    "marked": "True",
                },
                "en-US": {
                    "description": "Description",
                    "creator": ["Ivan Ivanov"],
                    "rights": "All rights reserved",
                    "source": "Box 4",
                    "credit": "Family Archive",
                    "terms": "Personal use only",
                    "marked": "",
                },
            },
        }

        response = asyncio.run(
            config_metadata_save(
                MetadataSettings(**payload),
                _user={"id": 1, "role": "admin"},
            )
        )

        assert response == {"ok": True}

        metadata_path = tmp_path / "florentine-abbot" / "metadata.json"
        assert metadata_path.exists()

        saved = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert saved["languages"]["ru-RU"]["description"] == "Описание"
        assert saved["languages"]["en-US"]["credit"] == "Family Archive"

        reloaded = asyncio.run(config_metadata_get(_user={"id": 1, "role": "admin"}))
        assert reloaded["languages"]["ru-RU"]["source"] == "Коробка 4"