"""Test configuration and fixtures."""

import os
import tempfile
from pathlib import Path
from typing import Dict, Optional

import pytest


@pytest.fixture
def temp_config_file():
    """Temporary config file fixture."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_path = f.name
    yield config_path
    os.unlink(config_path)


@pytest.fixture
def temp_dir():
    """Temporary directory fixture."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def clean_env():
    """Clean environment variables fixture.
    
    Temporarily removes OPENAI_API_KEY and ANTHROPIC_API_KEY environment variables,
    then restores them after the test.
    """
    # Store original values
    original_values: Dict[str, Optional[str]] = {
        "OPENAI_API_KEY": os.environ.pop("OPENAI_API_KEY", None),
        "ANTHROPIC_API_KEY": os.environ.pop("ANTHROPIC_API_KEY", None),
    }
    
    yield
    
    # Restore original values
    for key, value in original_values.items():
        if value is not None:
            os.environ[key] = value


@pytest.fixture
def env_with_keys():
    """Environment with test API keys fixture.
    
    Sets test API keys for the duration of the test,
    then restores original environment.
    """
    # Store original values
    original_values: Dict[str, Optional[str]] = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
    }
    
    # Set test values
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["ANTHROPIC_API_KEY"] = "test-claude-key"
    
    yield
    
    # Restore original values
    for key, value in original_values.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)