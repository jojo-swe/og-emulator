"""Tests for the SSH emulator."""

import logging
import sys
from pathlib import Path

import asyncssh
import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.ssh_server import DeviceManager, SSHSession, create_ssh_server

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_HOST = "127.0.0.1"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass"


@pytest.fixture
async def ssh_server(tmp_path):
    """Start the real SSH server on an ephemeral port and yield the bound port."""
    config = {
        "host": TEST_HOST,
        "port": 0,
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "host_key": str(tmp_path / "key"),
        "devices": [],
    }
    server = await create_ssh_server(config)
    try:
        yield server.sockets[0].getsockname()[1]
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_ssh_connection(ssh_server):
    """Test basic SSH connection to the emulator."""
    # Connect to the SSH server
    async with asyncssh.connect(
        host=TEST_HOST,
        port=ssh_server,
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
        port=ssh_server,
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
        port=ssh_server,
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


class _RecordingChannel:
    """Minimal channel stub that records everything written to it."""

    def __init__(self):
        self.written = []

    def write(self, data):
        self.written.append(data)


def test_port_listing_marks_busy_ports():
    """Ports held by another session are flagged in the pmshell listing."""
    manager = DeviceManager()
    manager.add_device(1, "opengear", "ACM7000", "og-1")
    manager.add_device(2, "cisco", "C9300", "sw-1")
    session = SSHSession(manager)
    session.channel = _RecordingChannel()
    assert manager.try_acquire_port(2, owner_id=-1)

    session._show_available_ports()

    listing = "".join(session.channel.written)
    assert "2: sw-1 (in use)" in listing
    assert "1: og-1 (in use)" not in listing
