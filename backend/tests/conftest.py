"""
Root conftest for all tests.
Patches MODEL_PATH to a temp directory before any app module is imported,
so tests can run outside Docker without needing /app to exist.

NOTE: The old module-level constants MODEL_VERSION_FILE / MODEL_FILE etc.
have been removed from comfort_model.py — file paths now live as
instance properties on ComfortModel that read settings.MODEL_PATH at
runtime, so we only need to patch the setting itself.
"""
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def patch_model_path(tmp_path):
    """Redirect MODEL_PATH and DATA_PATH so app can write files during tests."""
    with patch("app.core.config.settings.MODEL_PATH", str(tmp_path / "models")), \
         patch("app.core.config.settings.DATA_PATH", str(tmp_path)):
        yield tmp_path
