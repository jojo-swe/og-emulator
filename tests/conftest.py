"""Pytest configuration and fixtures for emulator tests."""

import os
import sys

import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def unused_port() -> int:
    """Return an unused port number."""
    import socket
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture
def test_config() -> dict:
    """Return a test configuration dictionary."""
    return {
        'host': '127.0.0.1',
        'port': 0,  # Let the OS choose a free port
        'username': 'testuser',
        'password': 'testpass',
        'log_level': 'DEBUG',
        'device_type': 'opengear',
        'model': 'ACM7000',
        'hostname': 'test-device',
        'ports': {
            1: {
                'device_type': 'opengear',
                'model': 'ACM7000',
                'hostname': 'og1',
                'description': 'OpenGear ACM7000',
            },
            2: {
                'device_type': 'cisco',
                'model': 'C9300',
                'hostname': 'switch1',
                'description': 'Cisco C9300 Switch',
            },
        }
    }
