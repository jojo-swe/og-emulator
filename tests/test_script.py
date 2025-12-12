#!/usr/bin/env python3
"""Test script for configuration system."""

import os
import sys
import json
import pytest
from pathlib import Path

# Fix Windows console encoding (only when running this file as a script)
if __name__ == '__main__' and sys.platform == 'win32':
    sys.stdout = open(sys.stdout.fileno(), mode='w', 
                     encoding='utf-8', errors='replace', buffering=1)
    sys.stderr = open(sys.stderr.fileno(), mode='w',
                     encoding='utf-8', errors='replace', buffering=1)

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

def test_config_loading(tmp_path, config_loader):
    """Test loading configuration from a file."""
    # Create a temporary config file
    config_content = """
    [server]
    host = 127.0.0.1
    port = 2222
    username = testuser
    password = testpass
    """
    config_file = tmp_path / "test_config.ini"
    config_file.write_text(config_content)
    
    # Load the config
    config_loader.load(str(config_file))
    
    # Verify the loaded values
    assert config_loader.get('server', 'host') == '127.0.0.1'
    assert config_loader.get('server', 'port') == 2222
    assert config_loader.get('server', 'username') == 'testuser'
    assert config_loader.get('server', 'password') == 'testpass'

def test_custom_config():
    """Test custom configuration loading."""
    # Create a ConfigLoader instance
    config_loader = ConfigLoader()
    
    # Set custom values
    config_loader.set('server', 'host', '192.168.1.1')
    config_loader.set('server', 'port', 8022)
    
    # Verify the values
    assert config_loader.get('server', 'host') == '192.168.1.1'
    assert config_loader.get('server', 'port') == 8022
    
    return True

def test_server_config_format():
    """Test server configuration formatting."""
    print("\nTesting server configuration format...")
    
    config = ConfigLoader()
    server_config = config.get_server_config()
    
    # Check all required keys are present
    required_keys = ['host', 'port', 'username', 'password', 'host_key']
    for key in required_keys:
        assert key in server_config, f"Missing key: {key}"
    
    print("✓ Server configuration format is correct")
    print(f"  - Keys: {list(server_config.keys())}")


def test_device_list():
    """Test device list functionality."""
    print("\nTesting device list...")
    
    config = ConfigLoader()
    devices = config.get_devices()
    
    if devices:
        print(f"✓ Found {len(devices)} devices:")
        for device in devices[:3]:  # Show first 3
            print(f"  - Port {device['port']}: {device['hostname']} ({device['device_type']})")
        if len(devices) > 3:
            print(f"  - ... and {len(devices) - 3} more")
    else:
        print("✗ No devices found")


def test_nested_access():
    """Test nested configuration access."""
    print("\nTesting nested configuration access...")
    
    config = ConfigLoader()
    
    # Test valid nested access
    log_level = config.get('logging', 'level', default='DEFAULT')
    print(f"  - Logging level: {log_level}")
    
    # Test invalid nested access returns default
    invalid = config.get('nonexistent', 'key', default='NOTFOUND')
    assert invalid == 'NOTFOUND'
    
    print("✓ Nested access works correctly")


def main():
    """Run all tests."""
    print("=" * 50)
    print("Configuration System Tests")
    print("=" * 50)
    
    tests = [
        ("Default Configuration", test_default_config),
        ("Custom Configuration", test_custom_config),
        ("Server Config Format", test_server_config_format),
        ("Device List", test_device_list),
        ("Nested Access", test_nested_access),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test in tests:
        print(f"\n{name}:")
        print("-" * (len(name) + 1))
        try:
            if test() is not False:  # Only count as passed if not explicitly returning False
                passed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__} failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    try:
        pass
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()