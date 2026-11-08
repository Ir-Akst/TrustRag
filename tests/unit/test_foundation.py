import os
import sys
import json
import logging
import random
from io import StringIO

import pytest

# Import package
import trustrag
from trustrag.utils import get_logger, set_random_seed, get_hardware_info
from trustrag.config.settings import Settings
from trustrag.exceptions import (
    TrustRAGError,
    ConfigurationError,
    DatasetError,
    RetrievalError,
    ModelError,
    ProviderError,
    DetectionError,
    GuardrailError,
    EvaluationError,
)

def test_package_import():
    assert trustrag.__version__ == "0.1.0"

def test_config_loading_defaults():
    cfg = Settings()
    assert cfg.app.env == "development"
    assert cfg.app.log_level == "INFO"
    assert cfg.app.random_seed == 42

def test_config_env_override(monkeypatch):
    monkeypatch.setenv("TRUSTRAG_APP_ENV", "production")
    monkeypatch.setenv("TRUSTRAG_APP_LOG_LEVEL", "DEBUG")
    cfg = Settings()
    assert cfg.app.env == "production"
    assert cfg.app.log_level == "DEBUG"

def test_invalid_config_raises(monkeypatch):
    # Set a non-integer seed to trigger validation error
    monkeypatch.setenv("TRUSTRAG_APP_RANDOM_SEED", "not-an-int")
    with pytest.raises(ValueError):
        Settings()

def test_logger_json_output(capfd):
    logger = get_logger("test_logger", level="INFO")
    logger.info("test message", extra={"user": "alice"})
    out, _ = capfd.readouterr()
    data = json.loads(out.strip())
    assert data["message"] == "test message"
    assert data["user"] == "alice"

def test_logger_filters_secret(capfd):
    logger = get_logger("secret_logger", level="INFO")
    logger.info("secret test", extra={"api_key": "12345", "foo": "bar"})
    out, _ = capfd.readouterr()
    data = json.loads(out.strip())
    assert "api_key" not in data
    assert data["foo"] == "bar"

def test_exception_hierarchy():
    for exc in [
        TrustRAGError,
        ConfigurationError,
        DatasetError,
        RetrievalError,
        ModelError,
        ProviderError,
        DetectionError,
        GuardrailError,
        EvaluationError,
    ]:
        assert issubclass(exc, TrustRAGError)

def test_random_seed_reproducibility():
    set_random_seed(123)
    a = list(range(5))
    random.shuffle(a)
    set_random_seed(123)
    b = list(range(5))
    random.shuffle(b)
    assert a == b

def test_hardware_info_structure():
    info = get_hardware_info()
    assert "cpu_count" in info
    # Ensure optional fields are present when possible
    if "torch_version" in info:
        assert isinstance(info["torch_version"], str)
    if "cuda_available" in info:
        assert isinstance(info["cuda_available"], bool)

