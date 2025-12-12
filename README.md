# OpenGear SSH Device Emulator

An SSH emulator that simulates OpenGear console servers with connected Cisco and Garderos devices for testing and development.

## Features

- **Modular Architecture**: Device factory pattern with extensible device types
- **Multiple Device Types**: Supports OpenGear, Cisco, and Garderos devices
- **Easy Authentication**: Simple username/password authentication
- **Realistic OpenGear Experience**: Authentic prompts and complete pmshell functionality
- **Direct Port Access**: Use `pmshell -l portXX` to connect directly to a specific port
- **Special Commands**: Support for all standard OpenGear pmshell commands (like ~c, ~b, ~h)
- **Configurable**: Support for JSON configuration files and command-line arguments

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run with default settings (port 2222, username: admin, password: admin):

```bash
python -m emulator
```

The CLI automatically loads the defaults defined in `config/default_config.json`. Update that file (or pass `--config`) to customize devices, credentials, logging, or host key paths.

### With Custom Settings

```bash
python -m emulator --host 0.0.0.0 --port 2222 --username root --password secret123
```

### With Configuration File

```bash
python -m emulator --config config.json
```

If the path is omitted, the emulator falls back to the bundled `config/default_config.json`.

### Enable Debug Logging

```bash
python -m emulator --debug
```

## Connecting to the Emulator

1. SSH to the emulator:

```bash
ssh admin@localhost -p 2222
```

2. Once connected, you'll see the OpenGear prompt:

```
OpenGear Console Server SSH Emulator
Type 'pmshell' to connect to a device

root@opengear:~# 
```

3. Type `pmshell` to see available devices:

```
root@opengear:~# pmshell

Connect to port:
==================================================
Port    Name                Status
==================================================
port01  opengear-1          Available
port02  cisco-switch-1      Available
port03  garderos-1          Available
port04  N/A                 N/A
port05  N/A                 N/A
port06  N/A                 N/A
port07  N/A                 N/A
port08  N/A                 N/A
port09  N/A                 N/A
port10  N/A                 N/A
port11  N/A                 N/A
port12  N/A                 N/A
==================================================

Connect to port > 
```

4. Select a port number to connect to that device:

```
Connect to port > 2

Connected to cisco-switch-1 on port 2

Cisco C9300 - cisco-switch-1

cisco-switch-1# 
```

5. Alternatively, connect directly to a port using the `-l` option:

```
root@opengear:~# pmshell -l port02

Connected to cisco-switch-1 on port 2

Cisco C9300 - cisco-switch-1

cisco-switch-1# 
```

6. Use device-specific commands:

```
cisco-switch-1# show version
cisco-switch-1# help
cisco-switch-1# exit
```

## Available Commands

### OpenGear Mode (Main Menu)

- `pmshell` - Show port list and enter pmshell mode
- `pmshell -l portXX` - Connect directly to port XX (e.g., `pmshell -l port02`)
- `help` - Show available commands
- `exit` or `quit` - Disconnect from SSH session

### pmshell Mode

- `<port>` - Connect to a specific port by number
- `exit`, `quit`, `.` - Exit pmshell

### pmshell Special Commands

The following special commands start with ~ (tilde):

- `~c` - Configuration menu for current port
- `~b` or `~break` - Send BREAK signal
- `~h` or `~portlog` - Show port log
- `~.` - Quit pmshell and disconnect
- `~p` or `~power` - Power management menu
- `~u` - Show user sessions
- `~m` or `~chooser` - Show port selection menu
- `~?` or `~pmhelp` - Show help for pmshell commands

### Device Mode

- `help` - Show available commands for the device
- `show version` - Show device version information
- `show system` - Show system information (Garderos/OpenGear)
- `show running-config` - Show running configuration (Cisco)
- `exit` or `quit` - Return to OpenGear mode

## Configuration File Format

Create a JSON file with the following structure:

```json
{
  "host": "0.0.0.0",
  "port": 2222,
  "username": "admin",
  "password": "admin123",
  "devices": [
    {
      "port": 1,
      "device_type": "opengear",
      "model": "ACM7000",
      "hostname": "opengear-console-1",
      "firmware_version": "4.5.0",
      "build_number": "45678"
    },
    {
      "port": 2,
      "device_type": "cisco",
      "model": "C9300-48P",
      "hostname": "cisco-core-sw1"
    }
  ]
}
```

## Architecture

- **Device Factory Pattern**: Extensible device registration via `@register_device` decorator
- **Proper SSH Server**: Built on `asyncssh` with full authentication support
- **State Machine**: Clear state transitions between OpenGear shell, pmshell, and device modes
- **Configurable Devices**: JSON configuration for easy device setup

## Troubleshooting

### Port Already in Use

If you see "Port 2222 is already in use", either:

- Stop the other process using that port
- Use a different port: `python run_ssh_emulator.py --port 2223`

### Authentication Failed

- Default credentials are username: `admin`, password: `admin`
- Check your command line arguments or config file
- Enable debug logging to see what credentials are being used

### Can't Connect to Device

- Make sure you're using the `pmshell` command first
- Enter a valid port number from the list
- Type 'q' to cancel port selection

## Development Notes

The main components are:

- `Device`: Simple device representation with command handlers
- `DeviceManager`: Manages all devices and active connections
- `SSHSession`: Handles the SSH session and state management
- `SSHServer`: Handles authentication and session creation

State flow:

1. `opengear` - Main OpenGear shell (Linux-like prompt)
2. `pmshell` - Port manager shell for device selection  
3. `device` - Connected to a specific serial device
