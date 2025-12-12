"""Pytest configuration and fixtures for emulator tests."""

import asyncio
import os
import signal
import sys
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up asyncio policy for Windows (deprecated in Python 3.16+)
if sys.platform == 'win32' and sys.version_info < (3, 16):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError:
        pass  # Policy not available in future Python versions


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    if sys.platform == 'win32':
        # On Windows, ProactorEventLoop is required for subprocess support
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    
    yield loop
    
    # Clean up
    if not loop.is_closed():
        loop.close()


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
