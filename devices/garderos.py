"""Garderos device emulation."""

import time
from typing import Dict, Any, List, Optional

from .base import BaseDevice
from .factory import register_device

@register_device("garderos")
class GarderosDevice(BaseDevice):
    """Emulated Garderos device.
    
    This class emulates a Garderos console server with typical commands
    and behavior for testing and development purposes.
    """
    
    device_type = "garderos"
    
    def __init__(
        self,
        name: str,
        model: str,
        hostname: str,
        prompt: str,
        **kwargs
    ) -> None:
        """Initialize the Garderos device.
        
        Args:
            name: Device name/identifier
            model: Device model
            hostname: Device hostname
            prompt: Command prompt
            **kwargs: Additional device-specific configuration
        """
        super().__init__(name, model, hostname, prompt, **kwargs)
        self.firmware_version = kwargs.get("firmware_version", "3.5.2")
        self.build_number = kwargs.get("build_number", "7890")
        self.uptime_start = time.time()
        self._current_mode = "user"  # user, enable, configure, cli
        self._configured_hostname = hostname
        self._users = {
            "admin": {
                "password": "admin",
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
        
    def _enter_cli_mode(self, prev_mode):
        """Enter CLI mode."""
        return "Entering CLI mode\r\n"
        
    def _exit_cli_mode(self, mode):
        """Exit CLI mode."""
        return "Exiting CLI mode\r\n"
    
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
            
        if command == "configure terminal":
            if self._current_mode != "enable":
                return "% Invalid input detected at '^' marker"
            self._current_mode = "configure"
            return f"Enter configuration commands, one per line. End with CNTL/Z.\r\n{self._configured_hostname}(config)# "
            
        if command == "end" or command == "exit":
            if self._current_mode == "configure":
                self._current_mode = "enable"
                return f"{self._configured_hostname}# "
            elif self._current_mode == "enable":
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
        if command.startswith("hostname ") and self._current_mode == "configure":
            new_hostname = command[9:].strip()
            if new_hostname:
                self._configured_hostname = new_hostname
                return f"{self._configured_hostname}(config)# "
        
        # Handle unknown commands
        if self._current_mode == "user":
            return f"% Unknown command or computer name, or unable to find computer address\r\n{self._configured_hostname}> "
        elif self._current_mode == "enable":
            return f"% Unknown command or computer name, or unable to find computer address\r\n{self._configured_hostname}# "
        elif self._current_mode == "configure":
            return f"% Unknown command or computer name, or unable to find computer address\r\n{self._configured_hostname}(config)# "
        
        return "% Invalid input detected at '^' marker\r\n"
    
    def get_banner(self) -> str:
        """Get the device banner.
        
        Returns:
            str: Device banner
        """
        return f"Garderos {self.model} {self.firmware_version} (Build {self.build_number})\r\n\r\n"
    
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
        
        return f"""
Garderos {self.model} Software, Version {self.firmware_version} (Build {self.build_number})
Copyright (c) 2023 Garderos, Inc. All rights reserved.

Uptime: {days} days, {hours} hours, {minutes} minutes
System image file is "flash:/image.bin"

{self._configured_hostname}# """
    
    def _show_running_config(self) -> str:
        """Generate show running-config output.
        
        Returns:
            str: Running configuration
        """
        config = f"""!
! Last configuration change at 01:23:45 UTC Mon Mar 1 2023 by admin
! NVRAM config last updated at 01:23:45 UTC Mon Mar 1 2023 by admin
!
version {self.firmware_version}
!
hostname {self._configured_hostname}
!
enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
!
username admin privilege 15 secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
!
interface Ethernet0/0
 no ip address
 shutdown
!
interface Ethernet0/1
 no ip address
 shutdown
!
ip http server
ip http secure-server
!
line con 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line vty 0 4
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 transport input ssh
!
end"""
        
        if self._current_mode == "enable":
            return f"{config}\r\n{self._configured_hostname}# "
        elif self._current_mode == "configure":
            return f"{config}\r\n{self._configured_hostname}(config)# "
        return config
    
    def _show_interfaces(self) -> str:
        """Generate show interfaces output.
        
        Returns:
            str: Interface status
        """
        interfaces = """
Ethernet0/0 is administratively down, line protocol is down 
  Hardware is Ethernet, address is 0000.0000.0001 (bia 0000.0000.0001)
  MTU 1500 bytes, BW 10000 Kbit/sec, DLY 1000 usec, 
     reliability 255/255, txload 1/255, rxload 1/255
  Encapsulation ARPA, loopback not set
  Keepalive set (10 sec)
  Auto-duplex, Auto-speed, link type is auto, media type is RJ45
  output flow-control is unsupported, input flow-control is unsupported
  ARP type: ARPA, ARP Timeout 04:00:00
  Last input never, output never, output hang never
  Last clearing of "show interface" counters never
  Input queue: 0/75/0/0 (size/max/drops/flushes); Total output drops: 0
  Queueing strategy: fifo
  Output queue: 0/40 (size/max)
  5 minute input rate 0 bits/sec, 0 packets/sec
  5 minute output rate 0 bits/sec, 0 packets/sec
     0 packets input, 0 bytes, 0 no buffer
     Received 0 broadcasts (0 IP multicasts)
     0 runts, 0 giants, 0 throttles 
     0 input errors, 0 CRC, 0 frame, 0 overrun, 0 ignored
     0 watchdog, 0 multicast, 0 pause input
     0 input packets with dribble condition detected
     0 packets output, 0 bytes, 0 underruns
     0 output errors, 0 collisions, 1 interface resets
     0 unknown protocol drops
     0 babbles, 0 late collision, 0 deferred
     0 lost carrier, 0 no carrier, 0 pause output
     0 output buffer failures, 0 output buffers swapped out

Ethernet0/1 is administratively down, line protocol is down 
  Hardware is Ethernet, address is 0000.0000.0002 (bia 0000.0000.0002)
  MTU 1500 bytes, BW 10000 Kbit/sec, DLY 1000 usec, 
     reliability 255/255, txload 1/255, rxload 1/255
  Encapsulation ARPA, loopback not set
  Keepalive set (10 sec)
  Auto-duplex, Auto-speed, link type is auto, media type is RJ45
  output flow-control is unsupported, input flow-control is unsupported
  ARP type: ARPA, ARP Timeout 04:00:00
  Last input never, output never, output hang never
  Last clearing of "show interface" counters never
  Input queue: 0/75/0/0 (size/max/drops/flushes); Total output drops: 0
  Queueing strategy: fifo
  Output queue: 0/40 (size/max)
  5 minute input rate 0 bits/sec, 0 packets/sec
  5 minute output rate 0 bits/sec, 0 packets/sec
     0 packets input, 0 bytes, 0 no buffer
     Received 0 broadcasts (0 IP multicasts)
     0 runts, 0 giants, 0 throttles 
     0 input errors, 0 CRC, 0 frame, 0 overrun, 0 ignored
     0 watchdog, 0 multicast, 0 pause input
     0 input packets with dribble condition detected
     0 packets output, 0 bytes, 0 underruns
     0 output errors, 0 collisions, 1 interface resets
     0 unknown protocol drops
     0 babbles, 0 late collision, 0 deferred
     0 lost carrier, 0 no carrier, 0 pause output
     0 output buffer failures, 0 output buffers swapped out"""
        
        if self._current_mode == "enable":
            return f"{interfaces}\r\n{self._configured_hostname}# "
        elif self._current_mode == "configure":
            return f"{interfaces}\r\n{self._configured_hostname}(config)# "
        return interfaces
        
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
  Serial:         GRD{self.name.upper()}1234567890
  Uptime:         {self.get_uptime()}
  CPU Load:       0.15, 0.10, 0.05 (1, 5, 15 min)
  Memory:         30% used (150MB / 512MB)
  Storage:        20% used (1.0GB / 5GB)
  Temperature:    38°C
\r\n"""
    
    def _cmd_show_interfaces(self, command_line: str) -> str:
        """Handle the 'show interfaces' command.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Network interface information
        """
        return """
Network Interfaces:
  eth0:
    Status:       UP
    IP Address:   192.168.10.1
    Netmask:      255.255.255.0
    Gateway:      192.168.10.254
    MAC Address:  AA:BB:CC:DD:EE:FF
    
  eth1:
    Status:       DOWN
    IP Address:   Not configured
    MAC Address:  AA:BB:CC:DD:EE:00
    
  DNS Configuration:
    Primary:      8.8.8.8
    Secondary:    1.1.1.1
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
  Username    Role           Last Login
  ----------  -------------  -------------------
  root        Administrator  2023-02-01 10:15:00
  admin       Administrator  2023-02-02 09:30:00
  operator    Operator       2023-02-03 14:45:00
  guest       Guest          Never
\r\n"""
    
    def _cmd_configure(self, command_line: str) -> str:
        """Handle the 'configure' command.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Result of entering configure mode
        """
        self.enter_mode("configure")
        return "Entering configuration mode\r\n"
    
    def _cmd_cli(self, command_line: str) -> str:
        """Handle the 'cli' command.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Result of entering CLI mode
        """
        self.enter_mode("cli")
        return "Entering CLI mode\r\n"
    
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
    
    def _cmd_config_interface(self, command_line: str) -> str:
        """Handle the 'interface' command in config mode.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Result of interface configuration
        """
        return "Interface configuration not implemented in emulator\r\n"
    
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
            return f"""
Current Configuration:
  hostname {self.hostname}
  user root password <encrypted>
  user admin password <encrypted>
  user operator password <encrypted>
  interface eth0 address 192.168.10.1/24
  interface eth0 gateway 192.168.10.254
  dns primary 8.8.8.8
  dns secondary 1.1.1.1
\r\n"""
        else:
            return f"Unknown show command: {subcommand}\r\n"
    
    def _cmd_cli_ls(self, command_line: str) -> str:
        """Handle the 'ls' command in CLI mode.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Directory listing
        """
        return """
bin/  boot/  dev/  etc/  home/  lib/  opt/  root/  sbin/  tmp/  usr/  var/
\r\n"""
    
    def _cmd_cli_cat(self, command_line: str) -> str:
        """Handle the 'cat' command in CLI mode.
        
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
    
    def _cmd_cli_ps(self, command_line: str) -> str:
        """Handle the 'ps' command in CLI mode.
        
        Args:
            command_line: Command line
            
        Returns:
            str: Process listing
        """
        return """
  PID USER     TIME  COMMAND
    1 root     0:02  /sbin/init
    2 root     0:00  [kthreadd]
  100 root     0:01  /usr/sbin/sshd
  101 root     0:01  /usr/sbin/httpd
  102 root     0:00  /usr/sbin/console-server
  103 root     0:00  /bin/bash
\r\n"""
