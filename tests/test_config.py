#!/usr/bin/env python3
"""Test script for configuration system."""

import os
import sys
import pytest
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the config loader
from utils.config import ConfigLoader

# Fixtures
@pytest.fixture
def config_loader():
    """Create a ConfigLoader instance for testing."""
    return ConfigLoader()

# Tests
def test_default_config(config_loader):
    """Test loading default configuration."""
    # Check server defaults
    assert config_loader.get('server', 'host') == '0.0.0.0', \
        "Server host should be 0.0.0.0"
    assert config_loader.get('server', 'port') == 2222, \
        "Server port should be 2222"
    assert config_loader.get('server', 'username') == 'admin', \
        "Default username should be 'admin'"

def test_config_loading(tmp_path):
    """Test loading configuration from a file."""
    # Create a temporary config file with JSON content
    config_content = """
    {
        "server": {
            "host": "127.0.0.1",
            "port": 2222,
            "username": "testuser",
            "password": "testpass"
        }
    }
    """
    config_file = tmp_path / "test_config.json"
    config_file.write_text(config_content)
    
    # Initialize ConfigLoader with the config file path
    loader = ConfigLoader(str(config_file))
    
    # Verify the loaded values
    assert loader.get('server', 'host') == '127.0.0.1'
    assert loader.get('server', 'port') == 2222
    assert loader.get('server', 'username') == 'testuser'
    assert loader.get('server', 'password') == 'testpass'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
