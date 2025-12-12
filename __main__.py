#!/usr/bin/env python3
"""Simple runner script for the SSH emulator."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Import the fixed server module
from core.ssh_server import create_ssh_server


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "default_config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "host": "0.0.0.0",
    "port": 2222,
    "username": "admin",
    "password": "admin",
    "host_key": "ssh_host_key",
    "devices": [],
}


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON data from path."""
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_config(raw_config: Dict[str, Any], base: Dict[str, Any]) -> Dict[str, Any]:
    """Merge a raw configuration dictionary onto the base config."""
    config = dict(base)

    server_section = raw_config.get("server") if isinstance(raw_config, dict) else None
    if isinstance(server_section, dict):
        for key in ("host", "port", "username", "password", "host_key"):
            if key in server_section:
                config[key] = server_section[key]

    for key in ("host", "port", "username", "password", "host_key", "devices", "logging"):
        if key in raw_config:
            config[key] = raw_config[key]

    # Ensure expected types
    try:
        config["port"] = int(config.get("port", DEFAULT_CONFIG["port"]))
    except (TypeError, ValueError):
        config["port"] = DEFAULT_CONFIG["port"]

    if not isinstance(config.get("devices"), list):
        config["devices"] = []

    return config


def configure_logging(log_config: Dict[str, Any], debug: bool) -> logging.Logger:
    """Configure application logging based on configuration."""
    level_name = log_config.get("level", "INFO") if isinstance(log_config, dict) else "INFO"
    log_level = logging.DEBUG if debug else getattr(logging, str(level_name).upper(), logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if isinstance(log_config, dict):
        log_file = log_config.get("file")
        if log_file:
            try:
                log_path = Path(log_file)
                if log_path.parent and not log_path.parent.exists():
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_path, encoding="utf-8")
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except Exception as exc:  # pragma: no cover - best effort logging setup
                root_logger.warning("Failed to configure file logging at %s: %s", log_file, exc)

    return root_logger


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='SSH Device Emulator')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=2222, help='Port to listen on')
    parser.add_argument('--username', default='admin', help='SSH username')
    parser.add_argument('--password', default='admin', help='SSH password')
    parser.add_argument('--config', type=str, help='JSON config file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Build configuration from defaults and optional files
    config: Dict[str, Any] = dict(DEFAULT_CONFIG)
    config_messages = []

    if DEFAULT_CONFIG_PATH.exists():
        try:
            default_data = load_json(DEFAULT_CONFIG_PATH)
            config = normalize_config(default_data, config)
            config_messages.append(f"Loaded default configuration from {DEFAULT_CONFIG_PATH}")
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON in default configuration file {DEFAULT_CONFIG_PATH}: {exc}", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:  # pragma: no cover - unlikely failure
            print(f"Failed to read default configuration file {DEFAULT_CONFIG_PATH}: {exc}", file=sys.stderr)
            sys.exit(1)

    if args.config:
        override_path = Path(args.config)
        if not override_path.exists():
            print(f"Configuration file not found: {override_path}", file=sys.stderr)
            sys.exit(1)
        try:
            override_data = load_json(override_path)
            config = normalize_config(override_data, config)
            config_messages.append(f"Loaded configuration from {override_path}")
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON in configuration file {override_path}: {exc}", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:
            print(f"Failed to read configuration file {override_path}: {exc}", file=sys.stderr)
            sys.exit(1)

    # Override with command line args
    if args.host != parser.get_default('host'):
        config['host'] = args.host
    if args.port != parser.get_default('port'):
        config['port'] = args.port
    if args.username != parser.get_default('username'):
        config['username'] = args.username
    if args.password != parser.get_default('password'):
        config['password'] = args.password

    config.setdefault('host_key', DEFAULT_CONFIG['host_key'])
    config.setdefault('devices', DEFAULT_CONFIG['devices'])

    logger = configure_logging(config.get('logging', {}), args.debug)

    for message in config_messages:
        logger.info(message)
    
    logger.info("Starting SSH Emulator")
    logger.info(f"Configuration: Host={config['host']}, Port={config['port']}")
    logger.info(f"Credentials: Username={config['username']}, Password={'*' * len(config['password'])}")
    logger.info(f"Devices: {len(config.get('devices', []))} configured")
    
    # Run the server
    async def run_server():
        try:
            server = await create_ssh_server(config)
            logger.info(f"SSH server is running on {config['host']}:{config['port']}")
            logger.info("Press Ctrl+C to stop")
            
            # Keep running until interrupted
            await server.wait_closed()
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            sys.exit(1)
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
