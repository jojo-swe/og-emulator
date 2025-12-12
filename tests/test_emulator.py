"""Tests for the SSH emulator."""

import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator

import asyncssh
import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.ssh_server import SSHServer, DeviceManager
from core.config import EmulatorConfig

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_HOST = "127.0.0.1"
TEST_PORT = 2222
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass"


@pytest.fixture
def temp_config():
    """Create a temporary configuration file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
        f.write("""
[Emulator]
host = 127.0.0.1
port = 2222
username = testuser
password = testpass
log_level = DEBUG

[Device]
type = opengear
model = ACM7000
hostname = test-device
""")
        return f.name


@pytest.fixture
async def ssh_server(temp_config, event_loop):
    """Fixture to start and stop the SSH server for testing."""
    # Create config
    config = EmulatorConfig.from_config_file(temp_config)
    
    # Create device manager
    device_manager = DeviceManager()
    
    # Create and start the server
    server = await asyncssh.create_server(
        lambda: SSHServer(
            device_manager=device_manager,
            username=config.username,
            password=config.password
        ),
        host=config.host,
        port=config.port,
        server_host_keys=['ssh_host_key']  # For testing, we'll use a placeholder
    )
    
    # Give the server a moment to start
    await asyncio.sleep(0.5)
    
    try:
        yield server
    finally:
        # Cleanup
        server.close()
        await server.wait_closed()
        if os.path.exists(temp_config):
            os.unlink(temp_config)


@pytest.mark.asyncio
async def test_ssh_connection(ssh_server):
    """Test basic SSH connection to the emulator."""
    # Connect to the SSH server
    async with asyncssh.connect(
        host=TEST_HOST,
        port=TEST_PORT,
        username=TEST_USERNAME,
        password=TEST_PASSWORD,
        known_hosts=None,  # Skip host key verification for testing
    ) as conn:
        # Execute a command
        result = await conn.run("help")
        assert result.returncode == 0
        assert "Available commands" in result.stdout


@pytest.mark.asyncio
async def test_pmshell_command(ssh_server):
    """Test the pmshell command."""
    async with asyncssh.connect(
        host=TEST_HOST,
        port=TEST_PORT,
        username=TEST_USERNAME,
        password=TEST_PASSWORD,
        known_hosts=None,
    ) as conn:
        # Enter pmshell
        pmshell = await conn.create_process("pmshell\n")
        
        # Wait for the prompt
        output = await pmshell.stdout.read(1024)
        assert "Port Manager" in output
        
        # Exit pmshell
        pmshell.stdin.write("exit\n")
        await pmshell.wait_closed()


@pytest.mark.asyncio
async def test_device_emulation(ssh_server):
    """Test device emulation functionality."""
    async with asyncssh.connect(
        host=TEST_HOST,
        port=TEST_PORT,
        username=TEST_USERNAME,
        password=TEST_PASSWORD,
        known_hosts=None,
    ) as conn:
        # Test Opengear-specific commands
        result = await conn.run("show version")
        assert result.returncode == 0
        assert "OpenGear" in result.stdout
        
        # Test invalid command
        result = await conn.run("invalid-command")
        assert result.returncode != 0
        assert "not found" in result.stderr
