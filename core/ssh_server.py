#!/usr/bin/env python3
"""SSH Server implementation for device emulation using the device factory."""

import asyncio
import logging
import os
import sys
import threading
from typing import Dict, Optional, Any, List

import asyncssh

from devices import DeviceFactory, BaseDevice

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages all emulated devices."""
    
    def __init__(self):
        self.devices: Dict[int, BaseDevice] = {}
        self._port_lock = threading.Lock()
        self._port_owners: Dict[int, int] = {}
        
    def add_device(self, port: int, device_type: str, model: str, hostname: str, **kwargs):
        """Add a device to the manager using the device factory."""
        try:
            device = DeviceFactory.create(
                device_type=device_type,
                name=f"{device_type}-{port}",
                model=model,
                hostname=hostname,
                prompt=f"{hostname}# ",
                port=port,
                **kwargs
            )
            self.devices[port] = device
            logger.info("Added %s device on port %d: %s", device_type, port, hostname)
        except ValueError as e:
            logger.error("Failed to create device: %s", e)
        
    def get_device_by_port(self, port: int) -> Optional[BaseDevice]:
        """Get device by port number."""
        return self.devices.get(port)
    
    def try_acquire_port(self, port: int, owner_id: int) -> bool:
        """Attempt to acquire exclusive ownership of a port for a session."""
        with self._port_lock:
            current_owner = self._port_owners.get(port)
            if current_owner is None or current_owner == owner_id:
                self._port_owners[port] = owner_id
                return True
            return False

    def release_port(self, port: int, owner_id: int) -> None:
        """Release port ownership if held by the given session."""
        with self._port_lock:
            if self._port_owners.get(port) == owner_id:
                del self._port_owners[port]
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """List all devices."""
        return [
            {
                'port': port,
                'type': device.device_type,
                'model': device.model,
                'hostname': device.hostname,
                'connected': device.connected
            }
            for port, device in sorted(self.devices.items())
        ]


class SSHSession(asyncssh.SSHServerSession):
    """SSH session handler."""
    
    def __init__(self, device_manager: DeviceManager, username: str = "root"):
        self.device_manager = device_manager
        self.channel = None
        self.buffer = ""
        self.state = "opengear"  # States: opengear, pmshell, device
        self.username = username  # Username for OpenGear prompt
        self.prompt = ""  # Current prompt
        self.direct_pmshell = False  # Flag for direct pmshell access
        self._owner_id = id(self)
        self._exec_mode = False
        self._exec_finished = False
        self._last_was_cr = False
        self.active_port: Optional[int] = None
        self.active_device: Optional[BaseDevice] = None
        self.logger = logging.getLogger(f"{__name__}.session")

    def connection_lost(self, exc):
        """Clean up port ownership and device connection when the session ends."""
        try:
            if self.active_device:
                self.active_device.disconnect()
        finally:
            if self.active_port is not None:
                self.device_manager.release_port(self.active_port, self._owner_id)
                self.active_port = None
                self.active_device = None
        
    def connection_made(self, chan):
        """Handle new connection."""
        self.channel = chan
        peer_info = chan.get_extra_info('peername')
        self.logger.info(f"New SSH session established from {peer_info[0] if peer_info else 'unknown'}")  
        
        # Set the username from connection if available
        conn = chan.get_connection()
        if conn and hasattr(conn, 'get_extra_info'):
            auth_info = conn.get_extra_info('auth_info')
            if auth_info and auth_info.username:
                self.username = auth_info.username
        
        # Initialize the prompt
        self._update_prompt()
        
    def shell_requested(self):
        """Handle shell request."""
        return True
        
    def session_started(self):
        """Start the session."""
        self.logger.info("Session started")
        
        # Check if we should go directly to pmshell
        if hasattr(self, 'direct_pmshell') and self.direct_pmshell:
            self.state = "pmshell"
            self._update_prompt()
            self._show_available_ports()
            self._show_prompt()
            return
            
        # Only show banner and prompt if this is an interactive shell
        if self.channel.get_terminal_type():
            self.channel.write("\r\nOpenGear Console Server SSH Emulator\r\n")
            self.channel.write("Type 'pmshell' to connect to a device\r\n")
            self.channel.write("Type 'help' for available commands\r\n\r\n")
            self._show_prompt()
        else:
            # For non-interactive sessions, just send a welcome message
            self.channel.write("OpenGear Console Server SSH Emulator - Non-interactive session\r\n")
        
    def exec_requested(self, command):
        """Handle command execution request (non-interactive)."""
        self._exec_mode = True
        self.logger.info(f"Command execution requested: {command}")

        command_str = command.decode("utf-8", errors="ignore") if isinstance(command, bytes) else str(command)
        command_str = command_str.strip()

        # Special case: treat 'pmshell' exec as an interactive program which accepts stdin
        if command_str.lower().startswith("pmshell"):
            self._start_exec_pmshell(command_str)
            return True

        async def run_command():
            try:
                exit_status = self._run_one_shot_exec(command_str)
                self.channel.exit(exit_status)
            except Exception as e:
                self.logger.error(f"Error executing command: {e}", exc_info=True)
                self._write_stderr(f"Error: {e}\r\n")
                self.channel.exit(1)

        asyncio.create_task(run_command())
        return True

    def _write_stderr(self, data: str) -> None:
        """Best-effort stderr write (asyncssh supports write_stderr)."""
        try:
            if hasattr(self.channel, "write_stderr"):
                self.channel.write_stderr(data)
            else:
                self.channel.write(data)
        except Exception:
            # Best effort only
            pass

    def _run_one_shot_exec(self, command: str) -> int:
        """Execute a single command in exec mode and return an exit status."""
        if not command:
            return 0

        cmd_parts = command.split()
        cmd = cmd_parts[0].lower() if cmd_parts else ""
        args = cmd_parts[1:]

        if cmd == "help":
            self.channel.write("Available commands:\r\n")
            self.channel.write("pmshell - Access port manager\r\n")
            self.channel.write("pmshell -l portXX - Connect directly to port XX\r\n")
            self.channel.write("show version - Show system version\r\n")
            self.channel.write("show system - Show system information\r\n")
            self.channel.write("exit, quit - Exit session\r\n")
            return 0

        if cmd == "show" and args:
            subcmd = args[0].lower()
            if subcmd == "version":
                self.channel.write("OpenGear Emulator v1.0\r\n")
                return 0
            if subcmd == "system":
                self.channel.write("System Information:\r\n")
                self.channel.write("  Model: ACM7000-5\r\n")
                self.channel.write("  Firmware: 4.2.0\r\n")
                self.channel.write("  Serial: EM12345678\r\n")
                self.channel.write("  Uptime: 5 days, 3 hours, 12 minutes\r\n")
                return 0
            self._write_stderr(f"% Unknown command: {command}\r\n")
            return 2

        if cmd in ("exit", "quit"):
            return 0

        self._write_stderr(f"{command}: not found\r\n")
        return 127

    def _start_exec_pmshell(self, command: str) -> None:
        """Start an exec-mode pmshell which reads subsequent input from stdin."""
        cmd_parts = command.split()
        args = cmd_parts[1:]

        # Enter pmshell state and show listing/prompt
        self.state = "pmshell"
        self._update_prompt()

        # Support direct connect: pmshell -l portXX
        if len(args) >= 2 and args[0] == "-l":
            port_str = args[1].replace("port", "")
            try:
                port = int(port_str)
                self._connect_to_port(port)
            except ValueError:
                self._write_stderr(f"Invalid port format: {args[1]}\r\n")
        else:
            self._show_available_ports()

        self._show_prompt()
        
    def data_received(self, data, datatype=None):
        """Handle incoming data."""
        if datatype == asyncssh.EXTENDED_DATA_STDERR:
            return
            
        # Convert bytes to string if needed
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='ignore')
        
        self.logger.debug(f"Received data: {data!r}")
        
        should_echo = bool(self.channel and self.channel.get_terminal_type())

        # Handle character by character (with CRLF handling)
        for char in data:
            if char == '\r':
                self._last_was_cr = True
                if should_echo:
                    self.channel.write("\r\n")
                if self.buffer.strip():
                    self.logger.debug(f"Processing command: {self.buffer!r}")
                    self._process_command(self.buffer.strip())
                else:
                    self._show_prompt()
                self.buffer = ""
                continue

            if char == '\n':
                if self._last_was_cr:
                    self._last_was_cr = False
                    continue
                if should_echo:
                    self.channel.write("\r\n")
                if self.buffer.strip():
                    self.logger.debug(f"Processing command: {self.buffer!r}")
                    self._process_command(self.buffer.strip())
                else:
                    self._show_prompt()
                self.buffer = ""
                continue

            self._last_was_cr = False

            if char in ('\x7f', '\b'):  # Backspace
                if self.buffer:
                    self.buffer = self.buffer[:-1]
                    if should_echo:
                        self.channel.write('\b \b')
                continue

            if char >= ' ':  # Printable character
                self.buffer += char
                if should_echo:
                    self.channel.write(char)
        
    def _process_command(self, command: str):
        """Process a command based on current state."""
        command = command.strip()
        if not command:
            self._show_prompt()
            return
            
        self.logger.debug(f"Processing command in {self.state} mode: {command}")
        
        try:
            if self.state == "opengear":
                self._handle_opengear_command(command)
            elif self.state == "pmshell":
                self._handle_pmshell_command(command)
            elif self.state == "device":
                self._handle_device_command(command)
            else:
                self.channel.write(f"\r\nUnknown state: {self.state}\r\n")
        except Exception as e:
            self.logger.error(f"Error processing command: {e}", exc_info=True)
            self.channel.write(f"\r\nError processing command: {e}\r\n")

        if self._exec_finished:
            return

        # Show prompt after command processing
        self._show_prompt()
        
    def _handle_opengear_command(self, command: str):
        """Handle commands in OpenGear mode."""
        cmd_parts = command.strip().split()
        
        if not cmd_parts:
            return
            
        cmd = cmd_parts[0].lower()
        args = cmd_parts[1:]
        
        if cmd == "help":
            self.channel.write("\r\nAvailable commands:\r\n")
            self.channel.write("pmshell - Access port manager\r\n")
            self.channel.write("pmshell -l portXX - Connect directly to port XX\r\n")
            self.channel.write("show version - Show system version\r\n")
            self.channel.write("show system - Show system information\r\n")
            self.channel.write("exit, quit - Exit session\r\n")
            self.channel.write("\r\nFor non-interactive usage, use: ssh user@host 'command'\r\n")
        elif cmd == "show" and len(args) > 0:
            subcmd = args[0].lower()
            if subcmd == "version":
                self.channel.write("\r\nOpenGear Emulator v1.0\r\n")
                self.channel.write("Copyright (c) 2023 OpenGear Emulator\r\n")
            elif subcmd == "system":
                self.channel.write("\r\nSystem Information:\r\n")
                self.channel.write("  Model: ACM7000-5\r\n")
                self.channel.write("  Firmware: 4.2.0\r\n")
                self.channel.write("  Serial: EM12345678\r\n")
                self.channel.write("  Uptime: 5 days, 3 hours, 12 minutes\r\n")
            else:
                self.channel.write(f"\r\n% Unknown command: {command}\r\n")
        elif cmd == "pmshell":
            if len(args) >= 2 and args[0] == "-l":
                # Handle direct port login: pmshell -l portXX
                port_str = args[1].replace("port", "")
                try:
                    port = int(port_str)
                    self._connect_to_port(port)
                except ValueError:
                    self.channel.write(f"\r\nInvalid port format: {args[1]}\r\n")
            else:
                # Regular pmshell command
                self.state = "pmshell"
                self._update_prompt()
                self._show_available_ports()
        elif cmd in ("exit", "quit"):
            self.channel.write("\r\nDisconnecting...\r\n")
            self.channel.close()
        else:
            self.channel.write(f"\r\nUnknown command: {command}\r\n")
        
    def _show_available_ports(self):
        """Show Connect to port-like listing in pmshell mode (columns)."""
        # Fetch devices sorted by port number
        devices = sorted(self.device_manager.list_devices(), key=lambda d: d['port'])

        # Blank line before listing for readability
        self.channel.write("\r\nPort Manager\r\n\r\n")

        cols = 4            # number of columns per row
        col_width = 20      # width of each column
        col_count = 0

        for dev in devices:
            # Use hostname if available, otherwise device name
            name = dev.get('hostname') or dev.get('name') or 'N/A'
            entry = f"{dev['port']}: {name}"
            self.channel.write(f"{entry:<{col_width}}")
            col_count += 1
            if col_count == cols:
                self.channel.write("\r\n")
                col_count = 0

        # If the last row wasn't complete, add a newline
        if col_count != 0:
            self.channel.write("\r\n")

        if not devices:
            self.channel.write("(no ports configured)\r\n")

    def _handle_pmshell_command(self, command: str):
        """Handle commands in pmshell mode."""
        # Handle special commands starting with ~
        if command.startswith('~'):
            self._handle_special_command(command[1:])
            return
            
        # Handle port selection
        if command.isdigit():
            port = int(command)
            self._connect_to_port(port)
        elif command.lower() in ('exit', 'quit', '.'):
            self.state = "opengear"
            self._update_prompt()
            self.channel.write("\r\nExited pmshell\r\n")
            if self._exec_mode:
                self._exec_finished = True
                self.channel.exit(0)
        else:
            self.channel.write("\r\nInvalid command. Enter port number or 'exit'.\r\n")
        
    def _handle_special_command(self, command: str):
        """Handle pmshell special commands starting with ~."""
        if not command:
            return
            
        cmd = command[0].lower() if command else ''
        
        if cmd == 'c':  # ~c - Configuration menu
            self.channel.write("\r\nPort Configuration Menu:\r\n")
            self.channel.write("1. Change baud rate\r\n")
            self.channel.write("2. Change flow control\r\n")
            self.channel.write("3. Back to pmshell\r\n")
        elif cmd == 'b' or command.startswith('break'):  # ~b - Send break
            if self.active_device:
                self.channel.write("\r\nSending BREAK signal...\r\n")
            else:
                self.channel.write("\r\nNot connected to any port\r\n")
        elif cmd == 'h' or command.startswith('portlog'):  # ~h - Port log
            self.channel.write("\r\nPort Log:\r\n")
            if self.active_device:
                self.channel.write("No log entries available\r\n")
            else:
                self.channel.write("Not connected to any port\r\n")
        elif cmd == '.':  # ~. - Quit
            self.channel.write("\r\nDisconnecting...\r\n")
            self.channel.close()
            return
        elif cmd == 'p' or command.startswith('power'):  # ~p - Power menu
            self.channel.write("\r\nPower Menu:\r\n")
            if self.active_device:
                self.channel.write("1. Power cycle\r\n")
                self.channel.write("2. Power off\r\n")
                self.channel.write("3. Power on\r\n")
            else:
                self.channel.write("No active device for power control\r\n")
        elif cmd == 'u':  # ~u - User sessions
            self.channel.write("\r\nActive User Sessions:\r\n")
            self.channel.write("No active sessions\r\n")
        elif cmd == 'm' or command.startswith('chooser'):  # ~m - Port chooser
            self._show_available_ports()
        elif cmd == '?' or command.startswith('pmhelp'):  # ~? - Help
            self._show_pmshell_help()
        else:
            self.channel.write(f"\r\nUnknown command: ~{command}\r\n")
            self._show_pmshell_help()
        
    def _show_pmshell_help(self):
        """Display pmshell help message."""
        help_text = """\r\npmshell Commands:\r\n
  <port>           Connect to specified port\r\n
  exit/quit        Exit pmshell\r\n\r\n
Special Commands (start with ~):\r\n
  ~c               Show configuration menu\r\n
  ~b/reak          Send BREAK signal\r\n
  ~h/portlog       Show port log\r\n
  ~.               Quit pmshell\r\n
  ~p/ower          Power management menu\r\n
  ~u               Show user sessions\r\n
  ~m/chooser       Show port selection menu\r\n
  ~?/pmhelp        Show this help\r\n
"""
        self.channel.write(help_text)
        
    def _connect_to_port(self, port: int):
        """Connect to a specific port."""
        valid_ports = list(range(1, 13))  # Ports 1-12
        
        if port in valid_ports:
            device = self.device_manager.get_device_by_port(port)
            if not device:
                self.channel.write(f"\r\nError: No device on port {port}\r\n")
                return

            if not self.device_manager.try_acquire_port(port, self._owner_id):
                self.channel.write(f"\r\nError: Port {port} is currently in use\r\n")
                return

            # Disconnect any previous device attached to this session
            if self.active_device and self.active_port is not None and self.active_port != port:
                try:
                    self.active_device.disconnect()
                finally:
                    self.device_manager.release_port(self.active_port, self._owner_id)

            device.connect()
            self.active_device = device
            self.active_port = port
            self.channel.write(f"\r\nConnected to {device.hostname} on port {port}\r\n")
            self.channel.write(device.get_banner())
            self.state = "device"
            self._update_prompt()
        else:
            self.channel.write(f"\r\nInvalid port number. Valid ports are: {', '.join(map(str, valid_ports))}\r\n")
        
    def _handle_device_command(self, command: str):
        """Handle commands when connected to a device."""
        if command.lower() in ('exit', 'quit'):
            if self.active_device:
                try:
                    self.active_device.disconnect()
                finally:
                    if self.active_port is not None:
                        self.device_manager.release_port(self.active_port, self._owner_id)
                    self.active_port = None
                    self.active_device = None
            self.state = "opengear"  # Set state back to opengear shell
            self._update_prompt()  # Update prompt to reflect state change
            self.channel.write("\r\nDisconnected from device.\r\n")
            if self._exec_mode:
                self._exec_finished = True
                self.channel.exit(0)
            return
            
        device = self.active_device
        if device:
            output = device.execute_command(command)
            self.channel.write(output)
        
    def _update_prompt(self):
        """Update the prompt based on current state and username."""
        if self.state == "opengear":
            self.prompt = f"{self.username}@opengear:~# "
        elif self.state == "pmshell":
            self.prompt = "Connect to port > "
        elif self.state == "device" and self.active_device:
            self.prompt = self.active_device.get_prompt()
        else:
            self.prompt = "$ "
    
    def _show_prompt(self):
        """Show the current prompt."""
        try:
            # Check if channel is valid and not closed
            if not self.channel:
                return
            
            # Check if channel is closing (use the available method)
            if hasattr(self.channel, 'is_closing') and self.channel.is_closing():
                return
                
            # Write the prompt
            self.channel.write(self.prompt)
        except Exception as e:
            self.logger.error(f"Error showing prompt: {e}")


class SSHServer(asyncssh.SSHServer):
    """SSH server implementation."""
    
    def __init__(self, device_manager: DeviceManager, username: str = "admin", password: str = "admin"):
        self.device_manager = device_manager
        self.username = username
        self.password = password
        self.auth_username = None  # Will store the authenticated username
        self.direct_pmshell = False  # Flag for direct pmshell access
        self.conn = None  # Will store the connection
        self.logger = logging.getLogger(f"{__name__}.server")
        
    def connection_made(self, conn):
        """Handle new connection."""
        self.conn = conn
        peer = conn.get_extra_info('peername')
        self.logger.info(f"SSH connection from {peer[0]}:{peer[1]}" if peer else "SSH connection received")
        
    def begin_auth(self, username):
        """Begin authentication."""
        self.auth_username = username
        return True  # Always require password
        
    def password_auth_supported(self):
        """Enable password authentication."""
        return True
        
    def validate_password(self, username, password):
        """Validate password."""
        # Check for :serial suffix in username
        base_username = username
        direct_pmshell = False
        
        if username and username.endswith(':serial'):
            base_username = username[:-7]  # Remove :serial suffix
            direct_pmshell = True
            self.logger.info(f"Detected :serial suffix in username, will connect directly to pmshell")
        
        valid = (base_username == self.username and password == self.password)
        if valid:
            self.logger.info(f"Successful authentication for user '{base_username}'")
            self.auth_username = base_username
            self.direct_pmshell = direct_pmshell
        else:
            self.logger.warning(f"Failed authentication for user '{base_username}'")
        return valid
        
    def session_requested(self):
        """Create a new session."""
        session = SSHSession(self.device_manager, self.auth_username)
        # Set direct_pmshell flag in the session if needed
        if hasattr(self, 'direct_pmshell') and self.direct_pmshell:
            session.direct_pmshell = True
        return session


async def create_ssh_server(config: Dict[str, Any]) -> asyncssh.listener:
    """Create and start the SSH server."""
    # Set up device manager
    device_manager = DeviceManager()
    
    # Add default devices if none configured
    if 'devices' in config:
        for device_config in config['devices']:
            device_manager.add_device(**device_config)
    else:
        # Add some default devices
        device_manager.add_device(1, 'opengear', 'ACM7000', 'opengear-1')
        device_manager.add_device(2, 'cisco', 'C9300', 'switch-1')
        device_manager.add_device(3, 'garderos', 'GCX-3100', 'garderos-1')
    
    # Generate host key if needed
    host_key = config.get('host_key', 'ssh_host_key')
    if not os.path.exists(host_key):
        logger.info("Generating SSH host key...")
        key = asyncssh.generate_private_key('ssh-rsa')
        key.write_private_key(host_key)
        os.chmod(host_key, 0o600)
    
    # Create server
    username = config.get('username', 'admin')
    password = config.get('password', 'admin')
    host = config.get('host', '0.0.0.0')
    port = config.get('port', 2222)
    
    logger.info(f"Starting SSH server on {host}:{port}")
    logger.info(f"Username: {username}, Password: {'*' * len(password)}")
    
    def server_factory():
        return SSHServer(device_manager, username, password)
    
    return await asyncssh.create_server(
        server_factory,
        host=host,
        port=port,
        server_host_keys=[host_key],
        process_factory=None,
        encoding='utf-8'
    )


async def main():
    """Main entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configuration
    config = {
        'host': '0.0.0.0',
        'port': 2222,
        'username': 'admin',
        'password': 'admin',
        'devices': [
            {'port': 1, 'device_type': 'opengear', 'model': 'ACM7000', 'hostname': 'og-device-1'},
            {'port': 2, 'device_type': 'cisco', 'model': 'C9300', 'hostname': 'cisco-switch-1'},
            {'port': 3, 'device_type': 'garderos', 'model': 'GCX-3100', 'hostname': 'gard-device-1'},
        ]
    }
    
    # Start server
    try:
        server = await create_ssh_server(config)
        
        addrs = ', '.join(str(s.getsockname()) for s in server.sockets)
        logger.info(f'SSH server listening on {addrs}')
        
        await server.wait_closed()
    except OSError as e:
        if e.errno == 98:  # Address already in use
            logger.error(f"Port {config['port']} is already in use")
        else:
            logger.error(f"Failed to start server: {e}")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
