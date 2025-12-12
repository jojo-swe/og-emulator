#!/usr/bin/env python3
"""SSH Device Emulator with Configuration Support."""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, List

# Lazy import for SSH server to avoid import errors when only using ConfigLoader
_ssh_server_module = None

def _get_ssh_server():
    """Lazily import the SSH server module."""
    global _ssh_server_module
    if _ssh_server_module is None:
        try:
            from core.ssh_server import create_ssh_server
            _ssh_server_module = create_ssh_server
        except ImportError:
            try:
                from ..core.ssh_server import create_ssh_server
                _ssh_server_module = create_ssh_server
            except ImportError as e:
                raise ImportError(f"Could not import ssh_server: {e}")
    return _ssh_server_module


class ConfigLoader:
    """Load and manage configuration settings."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration loader.
        
        Args:
            config_path: Optional path to a custom config file.
                        If not provided, loads from default locations.
        """
        self.config_path = self._find_config_file(config_path)
        self._config: Dict[str, Any] = self._get_default_config()
        if self.config_path:
            self.load()
    
    def _find_config_file(self, config_path: Optional[str]) -> Optional[Path]:
        """Find the configuration file."""
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            else:
                logging.warning(f"Config file not found: {config_path}, using defaults")
                return None
        
        # Try default locations
        for location in ['config.json', 'config/config.json', 'config/default.json']:
            path = Path(location)
            if path.exists():
                return path
        
        return None
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'server': {
                'host': '0.0.0.0',
                'port': 2222,
                'username': 'admin',
                'password': 'admin',
                'host_key': 'ssh_host_key',
                'banner': 'SSH Device Emulator\r\n',
                'max_sessions': 10
            },
            'logging': {
                'level': 'INFO',
                'file': 'emulator.log'
            },
            'devices': [
                {
                    'port': 1,
                    'device_type': 'opengear',
                    'model': 'ACM7000',
                    'hostname': 'opengear-1',
                    'firmware_version': '4.5.0',
                    'build_number': '45678'
                },
                {
                    'port': 2,
                    'device_type': 'cisco',
                    'model': 'C9300-48P',
                    'hostname': 'cisco-switch-1',
                    'firmware_version': '17.3.4'
                },
                {
                    'port': 3,
                    'device_type': 'garderos',
                    'model': 'GCX-3100',
                    'hostname': 'garderos-1',
                    'firmware_version': '3.7.1',
                    'build_number': '98765'
                }
            ]
        }
    
    def load(self) -> None:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # Deep merge with defaults
                self._deep_merge(self._config, file_config)
            logging.info(f"Loaded configuration from {self.config_path}")
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in configuration file: {e}")
            raise
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            raise
    
    def _deep_merge(self, base: dict, update: dict) -> None:
        """Deep merge update dict into base dict."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """Get a configuration value using nested keys.
        
        Args:
            *keys: Nested keys to access (e.g., 'server', 'port')
            default: Default value if key is not found
            
        Returns:
            The configuration value or default if not found
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration formatted for create_ssh_server."""
        server_config = self.get('server', default={})
        return {
            'host': server_config.get('host', '0.0.0.0'),
            'port': server_config.get('port', 2222),
            'username': server_config.get('username', 'admin'),
            'password': server_config.get('password', 'admin'),
            'host_key': server_config.get('host_key', 'ssh_host_key'),
            'banner': server_config.get('banner', ''),
            'max_sessions': server_config.get('max_sessions', 10)
        }
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of device configurations."""
        return self.get('devices', default=[])
    
    def to_dict(self) -> Dict[str, Any]:
        """Get the full configuration as a dictionary."""
        return self._config.copy()


def setup_logging(config: ConfigLoader, debug: bool = False) -> None:
    """Configure logging for the application.
    
    Args:
        config: Configuration loader instance
        debug: Enable debug logging if True
    """
    log_config = config.get('logging', default={})
    log_level = logging.DEBUG if debug else getattr(logging, log_config.get('level', 'INFO'))
    log_file = log_config.get('file', 'emulator.log')
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        logging.warning(f"Could not create log file {log_file}: {e}")
    
    # Reduce noise from asyncio and asyncssh
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('asyncssh').setLevel(logging.WARNING)


def parse_arguments():
    """Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='SSH Device Emulator',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--host',
        help='Server host address'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        help='Server port'
    )
    parser.add_argument(
        '--username', '-u',
        help='SSH username'
    )
    parser.add_argument(
        '--password', '-pw',
        help='SSH password'
    )
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--save-config',
        type=str,
        help='Save current configuration to file'
    )
    return parser.parse_args()


async def run_server(config: Dict[str, Any]) -> None:
    """Run the SSH server.
    
    Args:
        config: Server configuration dictionary
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Create the SSH server
        create_ssh_server = _get_ssh_server()
        server = await create_ssh_server(config)
        
        # Get the actual bound address
        addrs = []
        for sock in server.sockets:
            addr = sock.getsockname()
            addrs.append(f"{addr[0]}:{addr[1]}")
        
        logger.info(f"SSH server listening on {', '.join(addrs)}")
        logger.info("Press Ctrl+C to stop the server")
        
        # Keep the server running
        await server.wait_closed()
        
    except OSError as e:
        if e.errno == 98:  # Address already in use
            logger.error(f"Port {config['port']} is already in use")
        else:
            logger.error(f"OS error: {e}")
        raise
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


def save_config(config: ConfigLoader, filepath: str) -> None:
    """Save configuration to file.
    
    Args:
        config: Configuration loader instance
        filepath: Path to save the configuration
    """
    try:
        # Ensure directory exists
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2)
        
        logging.info(f"Configuration saved to {filepath}")
    except Exception as e:
        logging.error(f"Failed to save configuration: {e}")
        raise


def main():
    """Main entry point for the SSH emulator."""
    args = parse_arguments()
    
    try:
        # Load configuration
        config_loader = ConfigLoader(args.config)
        
        # Set up logging
        setup_logging(config_loader, args.debug)
        logger = logging.getLogger(__name__)
        
        # Build server configuration with command line overrides
        server_config = config_loader.get_server_config()
        
        # Apply command line overrides
        if args.host:
            server_config['host'] = args.host
        if args.port:
            server_config['port'] = args.port
        if args.username:
            server_config['username'] = args.username
        if args.password:
            server_config['password'] = args.password
        
        # Add devices to configuration
        server_config['devices'] = config_loader.get_devices()
        
        # Save configuration if requested
        if args.save_config:
            # Update config loader with overrides
            if args.host:
                config_loader._config['server']['host'] = args.host
            if args.port:
                config_loader._config['server']['port'] = args.port
            if args.username:
                config_loader._config['server']['username'] = args.username
            if args.password:
                config_loader._config['server']['password'] = args.password
            
            save_config(config_loader, args.save_config)
            logger.info("Configuration saved. Exiting.")
            return
        
        # Log configuration summary
        logger.info("=" * 60)
        logger.info("SSH Device Emulator Starting")
        logger.info("=" * 60)
        logger.info(f"Server: {server_config['host']}:{server_config['port']}")
        logger.info(f"Authentication: {server_config['username']} / {'*' * len(server_config['password'])}")
        logger.info(f"Devices: {len(server_config['devices'])} configured")
        if config_loader.config_path:
            logger.info(f"Config file: {config_loader.config_path}")
        else:
            logger.info("Config file: Using defaults (no config file found)")
        logger.info("=" * 60)
        
        # Log device details if debug
        if args.debug:
            logger.debug("Configured devices:")
            for device in server_config['devices']:
                logger.debug(f"  Port {device['port']}: {device['hostname']} ({device['device_type']} {device['model']})")
        
        # Run the server
        asyncio.run(run_server(server_config))
        
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("SSH emulator stopped")


if __name__ == '__main__':
    main()
