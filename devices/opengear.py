"""Opengear device emulation."""

import time
from typing import Dict, Any, List, Optional

from .base import BaseDevice
from .factory import register_device

@register_device("opengear")
class OpengearDevice(BaseDevice):
    """Emulated Opengear device.
    
    This class emulates an Opengear console server with typical commands
    and behavior for testing and development purposes.
    """
    
    def __init__(
        self,
        name: str,
        model: str,
        hostname: str,
        prompt: str,
        **kwargs
    ) -> None:
        """Initialize the Opengear device.
        
        Args:
            name: Device name/identifier
            model: Device model
            hostname: Device hostname
            prompt: Command prompt
            **kwargs: Additional device-specific configuration
        """
        super().__init__(name, model, hostname, prompt, **kwargs)
        self.firmware_version = kwargs.get("firmware_version", "4.0.0")
        self.build_number = kwargs.get("build_number", "1234")
        self.uptime_start = time.time()
        self._current_mode = "user"  # user, enable, config, shell
        self._configured_hostname = hostname
        self._users = {
            "admin": {
                "password": "default",
                "privilege": 15,
                "ssh_keys": []
            }
        }
        
    def _enter_config_mode(self, prev_mode):
        """Enter configuration mode."""
        return "Entering configuration mode\r\n"
        
    def _exit_config_mode(self, mode):
        """Exit configuration mode."""
        return "Exiting configuration mode\r\n"
        
    def _enter_shell_mode(self, prev_mode):
        """Enter shell mode."""
        return "Entering shell mode\r\n"
        
    def _exit_shell_mode(self, mode):
        """Exit shell mode."""
        return "Exiting shell mode\r\n"
    
    def connect(self) -> bool:
        """Connect to the device.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        self.connected = True
        self._current_mode = "user"
        return True
    
    def disconnect(self) -> None:
        """Disconnect from the device."""
        self.connected = False
        self._current_mode = None
    
    def execute_command(self, command: str) -> str:
        """Execute a command on the device.
        
        Args:
            command: Command to execute
            
        Returns:
            Command output
        """
        if not self.connected:
            return "% Not connected to device\r\n"
        
        command = command.strip().lower()
        
        # Handle mode changes
        if command == "enable":
            self._current_mode = "enable"
            return f"{self._configured_hostname}# "
            
        if command == "disable":
            self._current_mode = "user"
            return f"{self._configured_hostname}> "
            
        if command == "config" or command == "configure terminal":
            if self._current_mode != "enable":
                return "% Invalid input detected at '^' marker"
            self._current_mode = "config"
            return f"Enter configuration commands, one per line. End with CNTL/Z.\r\n{self._configured_hostname}(config)# "
            
        if command == "shell":
            self._current_mode = "shell"
            return f"OpenGear {self.model} - {self.firmware_version} (Build {self.build_number})\r\n# "
            
        if command == "exit" or command == "end":
            if self._current_mode == "config":
                self._current_mode = "enable"
                return f"{self._configured_hostname}# "
            elif self._current_mode == "enable":
                self._current_mode = "user"
                return f"{self._configured_hostname}> "
            elif self._current_mode == "shell":
                self._current_mode = "user"
                return f"{self._configured_hostname}> "
        
        # Handle show commands
        if command.startswith("show"):
            if command == "show version":
                return self._show_version()
            elif command == "show running-config":
                return self._show_running_config()
            elif command == "show interfaces":
                return self._show_interfaces()
        
        # Handle hostname change
        if command.startswith("hostname ") and self._current_mode == "config":
            new_hostname = command[9:].strip()
            if new_hostname:
                self._configured_hostname = new_hostname
                return f"{self._configured_hostname}(config)# "
        
        # Handle unknown commands
        if self._current_mode == "user":
            return f"% Unknown command or computer name, or unable to find computer address\r\n{self._configured_hostname}> "
        elif self._current_mode == "enable":
            return f"% Unknown command or computer name, or unable to find computer address\r\n{self._configured_hostname}# "
        elif self._current_mode == "config":
            return f"% Unknown command or computer name, or unable to find computer address\r\n{self._configured_hostname}(config)# "
        elif self._current_mode == "shell":
            return f"sh: {command}: not found\r\n# "
        
        return "% Invalid input detected at '^' marker\r\n"
    
    def get_banner(self) -> str:
        """Get the device banner.
        
        Returns:
            str: Device banner
        """
        return f"OpenGear {self.firmware_version} (Build {self.build_number})\r\n\r\n"
    
    def _show_version(self) -> str:
        """Generate show version output.
        
        Returns:
            str: Version information
        """
        uptime_seconds = int(time.time() - self.uptime_start)
        days = uptime_seconds // 86400
        uptime_seconds %= 86400
        hours = uptime_seconds // 3600
        uptime_seconds %= 3600
        minutes = uptime_seconds // 60
        
        uptime = []
        if days > 0:
            uptime.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0 or days > 0:
            uptime.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0 or hours > 0 or days > 0:
            uptime.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            
        return ", ".join(uptime)
    
    def _cmd_show_version(self, command_line: str) -> str:
        """Handle the 'show version' command.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Version information
        """
        return f"""
System Information:
  Model:            {self.model}
  Firmware Version: {self.firmware_version}
  Build Number:     {self.build_number}
  Hostname:         {self.hostname}
  Uptime:           {self.get_uptime()}
\r\n"""
    
    def _cmd_show_system(self, command_line: str) -> str:
        """Handle the 'show system' command.
        
        Args:
            command_line: Command line
            
        Returns:
            str: System information
        """
        return f"""
System Information:
  Hostname:       {self.hostname}
  Model:          {self.model}
  Firmware:       {self.firmware_version} (Build {self.build_number})
  Serial:         {self.name.upper()}1234567890
  Uptime:         {self.get_uptime()}
  CPU Usage:      5% user, 2% system, 93% idle
  Memory:         25% used (125MB / 500MB)
  Storage:        15% used (750MB / 5GB)
  Temperature:    42°C
\r\n"""
    
    def _cmd_show_network(self, command_line: str) -> str:
        """Handle the 'show network' command.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Network information
        """
        return """
Network Configuration:
  Interface eth0:
    State:        UP
    IP Address:   192.168.1.1
    Netmask:      255.255.255.0
    Gateway:      192.168.1.254
    MAC Address:  00:11:22:33:44:55
    
  DNS Configuration:
    Primary:      8.8.8.8
    Secondary:    8.8.4.4
    
  Hostname:       opengear
  Domain:         local
\r\n"""
    
    def _cmd_show_users(self, command_line: str) -> str:
        """Handle the 'show users' command.
        
        Args:
            command_line: Command line
            
        Returns:
            str: User information
        """
        return """
Configured Users:
  Username    Access Level    Last Login
  ----------  -------------   -------------------
  root        Administrator   2023-01-01 12:00:00
  admin       Administrator   2023-01-02 14:30:00
  user        User            Never
\r\n"""
    
    def _cmd_config(self, command_line: str) -> str:
        """Handle the 'config' command.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Result of entering config mode
        """
        self.enter_mode("config")
        return "Entering configuration mode\r\n"
    
    def _cmd_shell(self, command_line: str) -> str:
        """Handle the 'shell' command.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Result of entering shell mode
        """
        self.enter_mode("shell")
        return "Entering shell mode\r\n"
    
    def _cmd_config_hostname(self, command_line: str) -> str:
        """Handle the 'hostname' command in config mode.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Result of setting hostname
        """
        parts = command_line.split()
        if len(parts) < 2:
            return "Error: Missing hostname parameter\r\n"
            
        self.hostname = parts[1]
        return f"Hostname set to {self.hostname}\r\n"
    
    def _cmd_config_user(self, command_line: str) -> str:
        """Handle the 'user' command in config mode.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Result of user configuration
        """
        return "User configuration not implemented in emulator\r\n"
    
    def _cmd_config_network(self, command_line: str) -> str:
        """Handle the 'network' command in config mode.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Result of network configuration
        """
        return "Network configuration not implemented in emulator\r\n"
    
    def _cmd_config_show(self, command_line: str) -> str:
        """Handle the 'show' command in config mode.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Configuration information
        """
        parts = command_line.split()
        if len(parts) < 2:
            return "Error: Missing parameter for 'show'\r\n"
            
        subcommand = parts[1]
        if subcommand == "running-config":
            return """
Current Configuration:
  hostname {self.hostname}
  user root password <encrypted>
  user admin password <encrypted>
  network interface eth0 dhcp
  network dns primary 8.8.8.8
  network dns secondary 8.8.4.4
\r\n"""
        else:
            return f"Unknown show command: {subcommand}\r\n"
    
    def _cmd_shell_ls(self, command_line: str) -> str:
        """Handle the 'ls' command in shell mode.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Directory listing
        """
        return """
bin/  etc/  home/  lib/  sbin/  tmp/  usr/  var/
\r\n"""
    
    def _cmd_shell_cat(self, command_line: str) -> str:
        """Handle the 'cat' command in shell mode.
        
        Args:
            command_line: Command line
            
        Returns:
            str: File contents
        """
        parts = command_line.split()
        if len(parts) < 2:
            return "Error: Missing file parameter\r\n"
            
        filename = parts[1]
        if filename == "/etc/version":
            return f"{self.firmware_version}-{self.build_number}\r\n"
        elif filename == "/etc/hostname":
            return f"{self.hostname}\r\n"
        else:
            return f"cat: {filename}: No such file or directory\r\n"
    
    def _cmd_shell_ps(self, command_line: str) -> str:
        """Handle the 'ps' command in shell mode.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Process listing
        """
        return """
  PID TTY      STAT   TIME COMMAND
    1 ?        Ss     0:01 /sbin/init
    2 ?        S      0:00 [kthreadd]
  101 ?        S      0:00 /usr/sbin/sshd
  102 ?        S      0:00 /usr/sbin/httpd
  103 ?        S      0:00 /usr/sbin/pmshell
  104 ?        S      0:00 /bin/bash
\r\n"""
