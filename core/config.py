"""Emulator configuration management."""

import configparser
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

@dataclass
class PortConfig:
    """Configuration for a single port.
    
    Attributes:
        port_number: Port number
        device_type: Type of device (e.g., cisco, garderos, opengear)
        model: Device model
        hostname: Device hostname
        prompt: Command prompt for the device
        extra: Optional dictionary of additional device-specific configuration
    """
    port_number: int
    device_type: str
    model: str
    hostname: str
    prompt: str
    extra: dict = None
    
    def __post_init__(self):
        """Initialize extra as an empty dict if None."""
        if self.extra is None:
            self.extra = {}
    
    @classmethod
    def from_string(cls, port_number: int, config_str: str) -> "PortConfig":
        """Create PortConfig from configuration string.
        
        Args:
            port_number: Port number
            config_str: Configuration string in format "device_type:model:hostname:prompt"
            
        Returns:
            PortConfig instance
        """
        parts = config_str.split(":", 3)
        if len(parts) != 4:
            raise ValueError(f"Invalid port configuration format: {config_str}")
            
        return cls(
            port_number=port_number,
            device_type=parts[0],
            model=parts[1],
            hostname=parts[2],
            prompt=parts[3]
        )

@dataclass
class EmulatorConfig:
    """Emulator configuration settings.
    
    This class holds configuration settings for the SSH emulator and provides
    methods for loading and converting configurations.
    """
    host: str = "127.0.0.1"
    port: int = 2222
    username: str = "emulator"  # Default username
    password: str = "emulator"  # Default password
    enabled: bool = True
    banner: str = "OpenGear 4.0.0 (Build 1234)"
    prompt: str = "root@opengear:~# "
    pmshell_prompt: str = "Connect to port > "
    valid_ports: list = field(default_factory=lambda: list(range(1, 13)))  # Ports 1-12
    startup_timeout: float = 2.0
    stop_timeout: float = 5.0
    log_level: str = "INFO"
    log_file: str = "emulator.log"
    device_start_port: int = 1
    device_count: int = 10
    port_configs: Dict[int, PortConfig] = None
    
    def __post_init__(self):
        """Initialize port_configs as a dictionary if None."""
        if self.port_configs is None:
            self.port_configs = {}
    
    @classmethod
    def from_config_file(cls, config_path: Union[str, Path]) -> "EmulatorConfig":
        """Create configuration from a config file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            EmulatorConfig instance with values from config file
        """
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return cls()
            
        config = configparser.ConfigParser()
        config.read(config_path)
        
        if "Emulator" not in config:
            logger.warning(f"Emulator section not found in {config_path}, using defaults")
            return cls()
            
        emulator_config = config["Emulator"]
        
        # Create base config
        config = cls(
            host=emulator_config.get("host", cls.host),
            port=int(emulator_config.get("port", str(cls.port))),
            username=emulator_config.get("username", cls.username),
            password=emulator_config.get("password", cls.password),
            enabled=emulator_config.get("enabled", "true").lower() in ("true", "yes", "1", "on"),
            banner=emulator_config.get("banner", cls.banner),
            prompt=emulator_config.get("prompt", cls.prompt),
            startup_timeout=float(emulator_config.get("startup_timeout", str(cls.startup_timeout))),
            stop_timeout=float(emulator_config.get("stop_timeout", str(cls.stop_timeout))),
            log_level=emulator_config.get("log_level", cls.log_level),
            log_file=emulator_config.get("log_file", cls.log_file),
            device_start_port=int(emulator_config.get("device_start_port", str(cls.device_start_port))),
            device_count=int(emulator_config.get("device_count", str(cls.device_count)))
        )
        
        # Parse port configurations
        for key, value in emulator_config.items():
            if key.startswith("port_") and "_" in key:
                try:
                    port_num = int(key.split("_")[1])
                    port_config = PortConfig.from_string(port_num, value)
                    config.port_configs[port_num] = port_config
                except (ValueError, IndexError) as e:
                    logger.warning(f"Invalid port configuration '{key}': {e}")
        
        return config
    
    @classmethod
    def from_config_service(cls, config_service) -> "EmulatorConfig":
        """Create config from config service.
        
        Args:
            config_service: Configuration service instance
            
        Returns:
            EmulatorConfig instance
        """
        # Create base config
        config = cls(
            host=config_service.get_setting("Emulator", "host", default="127.0.0.1"),
            port=config_service.get_int("Emulator", "port", default=2222),
            username=config_service.get_setting("Emulator", "username", default="emulator"),
            password=config_service.get_setting("Emulator", "password", default="emulator"),
            enabled=config_service.get_bool("Emulator", "enabled", default=True),
            banner=config_service.get_setting("Emulator", "banner", default="OpenGear 4.0.0 (Build 1234)"),
            prompt=config_service.get_setting("Emulator", "prompt", default="og> "),
            startup_timeout=config_service.get_float("Emulator", "startup_timeout", default=2.0),
            stop_timeout=config_service.get_float("Emulator", "stop_timeout", default=5.0),
            log_level=config_service.get_setting("Emulator", "log_level", default="INFO"),
            log_file=config_service.get_setting("Emulator", "log_file", default="emulator.log"),
            device_start_port=config_service.get_int("Emulator", "device_start_port", default=1),
            device_count=config_service.get_int("Emulator", "device_count", default=10)
        )
        
        # Parse port configurations
        for section in config_service.sections():
            for key, value in config_service.items(section):
                if key.startswith("port_") and "_" in key:
                    try:
                        port_num = int(key.split("_")[1])
                        port_config = PortConfig.from_string(port_num, value)
                        config.port_configs[port_num] = port_config
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Invalid port configuration '{key}': {e}")
        
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.
        
        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "enabled": self.enabled,
            "banner": self.banner,
            "prompt": self.prompt,
            "startup_timeout": self.startup_timeout,
            "stop_timeout": self.stop_timeout,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "device_start_port": self.device_start_port,
            "device_count": self.device_count
        }
        
    def get_log_level(self) -> int:
        """Get the numeric logging level.
        
        Returns:
            int: Logging level
        """
        log_levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        return log_levels.get(self.log_level.upper(), logging.INFO)
