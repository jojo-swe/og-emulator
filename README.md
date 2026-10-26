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

Requires Python 3.11 or newer (the versions tested in CI). The project runs from a source checkout or from Docker; it is not packaged for `pip install .`.

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Docker Quick Start

```bash
docker compose up --build -d
ssh admin@localhost -p 2222
```

The default password is `admin`. See [docs/DEMO.md](docs/DEMO.md) for a five-minute walkthrough.

## Usage

### Basic Usage

Run with default settings (port 2222, username: admin, password: admin):

```bash
python -m emulator
```

`python scripts/run-ssh-emulator.py` starts the same CLI. The CLI automatically loads the defaults defined in `config/default_config.json`. Update that file (or pass `--config`) to customize devices, credentials, logging, or host key paths.

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

```bash
ssh admin@localhost -p 2222
```

A full session against the default configuration: log in, open `pmshell`, connect to port 2, run `show version`, then `exit` twice. Real output; the long `show version` licence text is trimmed. The emulator currently echoes each typed line twice on an interactive terminal, which is why commands appear doubled.

```
OpenGear Console Server SSH Emulator
Type 'pmshell' to connect to a device
Type 'help' for available commands

admin@opengear:~# pmshell
pmshell

Port Manager

1: opengear-1       2: cisco-switch-1   3: garderos-1       4: cisco-switch-2
5: opengear-2
Connect to port > 2
2

Connected to cisco-switch-1 on port 2
C9300 - cisco-switch-1

cisco-switch-1# show version
show version

Cisco IOS Software, C9300 Software (C9300-ADVENTERPRISEK9-M), Version 15.2(4)M6, RELEASE SOFTWARE (fc1)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2013 by Cisco Systems, Inc.
Compiled Wed 26-Jun-13 02:20 by prod_rel_team

ROM: System Bootstrap, Version 15.1(4)M6, RELEASE SOFTWARE (fc1)

cisco-switch-1 uptime is 5 weeks, 3 days, 12 hours, 37 minutes
[... licence text trimmed ...]
Configuration register is 0x2102

cisco-switch-1# cisco-switch-1# exit
exit

Disconnected from device.
admin@opengear:~# exit
exit

Disconnecting...
```

You can also connect directly to a port with `pmshell -l port02`, or log in as `admin:serial` (`ssh admin:serial@localhost -p 2222`) to skip the shell and land straight in the pmshell port listing.

### Non-interactive Use

Test clients usually run single commands without a terminal (SSH exec mode):

```bash
ssh admin@localhost -p 2222 help
ssh admin@localhost -p 2222 'show system'
ssh admin@localhost -p 2222 pmshell
```

`pmshell` in exec mode reads port numbers and device commands from stdin, so it can be scripted (`printf '3\nshow version\nexit\n' | ssh admin@localhost -p 2222 pmshell`). Exit codes:

| Code | Meaning |
|------|---------|
| `0` | Command succeeded |
| `2` | Unknown `show` subcommand |
| `127` | Command not found |

## Available Commands

### OpenGear Mode (Main Menu)

- `pmshell` - Show port list and enter pmshell mode
- `pmshell -l portXX` - Connect directly to port XX (e.g., `pmshell -l port02`)
- `show version` - Show emulator version
- `show system` - Show console server system information
- `help` - Show available commands
- `exit` or `quit` - Disconnect from SSH session

### pmshell Mode

- `<port>` - Connect to a specific port by number (valid ports are 1–12)
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

All three device types implement:

- `show version` - Show device version information
- `show running-config` - Show running configuration
- `show interfaces` - Show interface status
- `enable` / `disable` - Enter or leave privileged mode. On Cisco devices `enable` prompts for a password: it defaults to `cisco` and can be overridden with `enable_password` in the device's JSON entry
- `configure terminal` - Enter configuration mode (requires `enable`)
- `end` - Leave configuration mode
- `exit` or `quit` - Disconnect from the device and return to OpenGear mode

## Configuration

Settings are applied in this order, each layer overriding the previous one:

1. `config/default_config.json` (shipped defaults)
2. `--config FILE`, merged on top
3. Command-line flags (`--host`, `--port`, `--username`, `--password`)

Create a JSON file with the following structure:

```json
{
  "host": "0.0.0.0",
  "port": 2222,
  "username": "admin",
  "password": "admin123",
  "host_key": "ssh_host_key",
  "logging": {
    "level": "INFO",
    "file": "logs/emulator.log"
  },
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
      "hostname": "cisco-core-sw1",
      "enable_password": "enable123"
    }
  ]
}
```

- `host_key`: path to the SSH host key. It is generated on first start if missing; keep it out of git.
- `logging.level`: standard level name (`DEBUG`, `INFO`, ...). `--debug` overrides it.
- `logging.file`: optional log file path; its directory is created if needed.
- `devices[].port`: pmshell port, 1–12.

The nested form used by `config/config.json`, with server settings under a `"server": {...}` key, is also accepted. Its `banner` and `max_sessions` keys are ignored by the CLI.

## Architecture

- **Device Factory Pattern**: Extensible device registration via `@register_device` decorator
- **Proper SSH Server**: Built on `asyncssh` with full authentication support
- **State Machine**: Clear state transitions between OpenGear shell, pmshell, and device modes
- **Configurable Devices**: JSON configuration for easy device setup

## Running the Tests

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

## Examples

See [examples/README.md](examples/README.md) for a scripted client built on `asyncssh`.

## Troubleshooting

### Port Already in Use

If you see "Port 2222 is already in use", either:

- Stop the other process using that port
- Use a different port: `python -m emulator --port 2223`

### Authentication Failed

- Default credentials are username: `admin`, password: `admin`
- Check your command line arguments or config file
- Enable debug logging to see what credentials are being used

### Can't Connect to Device

- Make sure you're using the `pmshell` command first
- Enter a valid port number from the list
- Type `exit` to leave port selection

## Development Notes

The main components are:

- `BaseDevice` (`devices/base.py`): Base class for emulated devices; concrete devices are created through `DeviceFactory` (`devices/factory.py`)
- `DeviceManager`: Manages all devices and active connections
- `SSHSession`: Handles the SSH session and state management
- `SSHServer`: Handles authentication and session creation

State flow:

1. `opengear` - Main OpenGear shell (Linux-like prompt)
2. `pmshell` - Port manager shell for device selection  
3. `device` - Connected to a specific serial device
