"""Cisco device emulation."""

import re
from typing import Dict, Any, List, Optional

from .base import BaseDevice
from .factory import register_device

@register_device("cisco")
class CiscoDevice(BaseDevice):
    """Cisco device emulation."""
    
    def __init__(self, name: str, model: str, hostname: str, prompt: str, **kwargs):
        """Initialize the Cisco device.
        
        Args:
            name: Device name/identifier
            model: Device model
            hostname: Device hostname
            prompt: Command prompt
            **kwargs: Additional device-specific configuration
        """
        super().__init__(name, model, hostname, prompt, **kwargs)
        self.enable_password = kwargs.get("enable_password", "cisco")
        self.running_config = self._generate_running_config()
        self.privileged = False
    
    def connect(self) -> bool:
        """Connect to the device.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        self.connected = True
        return True
    
    def disconnect(self) -> None:
        """Disconnect from the device."""
        self.connected = False
    
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
        
        # Handle enable/disable
        if command == "enable":
            return "Password: "
        
        if command == self.enable_password:
            self.privileged = True
            return f"{self.hostname}# "
            
        if command == "disable":
            self.privileged = False
            return f"{self.hostname}> "
        
        # Handle show commands
        if command.startswith("show"):
            if command == "show version":
                return self._show_version()
            elif command == "show running-config":
                return self._show_running_config()
            elif command == "show interfaces":
                return self._show_interfaces()
        
        # Handle configuration mode
        if command == "configure terminal":
            if not self.privileged:
                return "% Invalid input detected at '^' marker"
            return f"Enter configuration commands, one per line. End with CNTL/Z.\r\n{self.hostname}(config)# "
        
        # Handle exit from config mode
        if command in ("exit", "end"):
            if self.privileged:
                return f"{self.hostname}# "
            return f"{self.hostname}> "
        
        return f"% Invalid input detected at '^' marker\r\n"
    
    def _show_version(self) -> str:
        """Generate show version output.
        
        Returns:
            str: Version information
        """
        return f"""
Cisco IOS Software, {self.model} Software ({self.model.upper()}-ADVENTERPRISEK9-M), Version 15.2(4)M6, RELEASE SOFTWARE (fc1)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2013 by Cisco Systems, Inc.
Compiled Wed 26-Jun-13 02:20 by prod_rel_team

ROM: System Bootstrap, Version 15.1(4)M6, RELEASE SOFTWARE (fc1)

{self.hostname} uptime is 5 weeks, 3 days, 12 hours, 37 minutes
System returned to ROM by power-on
System image file is "flash:/{self.model.upper()}-ADVENTERPRISEK9-M", booted via tftp


This product contains cryptographic features and is subject to United
States and local country laws governing import, export, transfer and
use. Delivery of Cisco cryptographic products does not imply
third-party authority to import, export, distribute or use encryption.
Importers, exporters, distributors and users are responsible for
compliance with U.S. and local country laws. By using this product you
agree to comply with applicable laws and regulations. If you are unable
to comply with U.S. and local laws, return this product immediately.

A summary of U.S. laws governing Cisco cryptographic products may be found at:
http://www.cisco.com/wwl/export/crypto/tool/stqrg.html

If you require further assistance please contact us by sending email to
export@cisco.com.

Cisco {self.model} (R7000) processor (revision 1.0) with 1048576K/20480K bytes of memory.
Processor board ID FTX00000000
2 Gigabit Ethernet interfaces
32768K bytes of non-volatile configuration memory.
4194304K bytes of physical memory.
2064384K bytes of at flash0 at bootflash

Configuration register is 0x2102

{self.hostname}# """
    
    def _show_running_config(self) -> str:
        """Generate show running-config output.
        
        Returns:
            str: Running configuration
        """
        return f"""
Building configuration...

Current configuration : 1234 bytes
!
! Last configuration change at 01:23:45 UTC Mon Mar 1 2023 by admin
! NVRAM config last updated at 01:23:45 UTC Mon Mar 1 2023 by admin
!
version 15.2
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
hostname {self.hostname}
!
boot-start-marker
boot-end-marker
!
enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
!
no aaa new-model
!
ip cef
no ipv6 cef
!
multilink bundle-name authenticated
!
ip tcp synwait-time 5
!
interface GigabitEthernet0/0
 no ip address
 shutdown
 duplex auto
 speed auto
!
interface GigabitEthernet0/1
 no ip address
 shutdown
 duplex auto
 speed auto
!
ip forward-protocol nd
!
no ip http server
no ip http secure-server
!
control-plane
!
line con 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line aux 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line vty 0 4
 login
!
end

{self.hostname}# """
    
    def _show_interfaces(self) -> str:
        """Generate show interfaces output.
        
        Returns:
            str: Interface status
        """
        return f"""
GigabitEthernet0/0 is administratively down, line protocol is down 
  Hardware is iGbE, address is 0000.0000.0001 (bia 0000.0000.0001)
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec, 
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

GigabitEthernet0/1 is administratively down, line protocol is down 
  Hardware is iGbE, address is 0000.0000.0002 (bia 0000.0000.0002)
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec, 
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

{self.hostname}# """
    
    def _generate_running_config(self) -> str:
        """Generate a basic running configuration.
        
        Returns:
            str: Running configuration
        """
        return f"""!
version 15.2
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
hostname {self.hostname}
!
boot-start-marker
boot-end-marker
!
enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
!
no aaa new-model
!
ip cef
no ipv6 cef
!
multilink bundle-name authenticated
!
ip tcp synwait-time 5
!
interface GigabitEthernet0/0
 no ip address
 shutdown
 duplex auto
 speed auto
!
interface GigabitEthernet0/1
 no ip address
 shutdown
 duplex auto
 speed auto
!
ip forward-protocol nd
!
no ip http server
no ip http secure-server
!
control-plane
!
line con 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line aux 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line vty 0 4
 login
!
end"""
