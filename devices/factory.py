"""Device factory for creating emulated devices."""

import importlib
import logging
from typing import Dict, Type, Optional, Any, Callable

from .base import BaseDevice

logger = logging.getLogger(__name__)

def register_device(device_type: str) -> Callable[[Type[BaseDevice]], Type[BaseDevice]]:
    """Decorator to register a device class with the factory.
    
    Args:
        device_type: Device type identifier (e.g., 'cisco', 'garderos')
        
    Returns:
        Decorator function that registers the device class
    """
    def decorator(device_class: Type[BaseDevice]) -> Type[BaseDevice]:
        DeviceFactory.register(device_type, device_class)
        return device_class
    return decorator

class DeviceFactory:
    """Factory for creating emulated devices."""
    
    _device_registry: Dict[str, Type[BaseDevice]] = {}
    
    @classmethod
    def register(cls, device_type: str, device_class: Type[BaseDevice]) -> None:
        """Register a device class for a specific device type.
        
        Args:
            device_type: Device type identifier (e.g., 'cisco', 'garderos')
            device_class: Device class to register
        """
        cls._device_registry[device_type] = device_class
        logger.debug(f"Registered device type '{device_type}': {device_class.__name__}")
    
    @classmethod
    def create(
        cls, 
        device_type: str, 
        name: str, 
        model: str, 
        hostname: str, 
        prompt: str,
        **kwargs
    ) -> BaseDevice:
        """Create a device instance.
        
        Args:
            device_type: Type of device to create
            name: Device name/identifier
            model: Device model
            hostname: Device hostname
            prompt: Command prompt
            **kwargs: Additional device-specific configuration
            
        Returns:
            BaseDevice: Device instance
            
        Raises:
            ValueError: If device type is not registered
        """
        if device_type not in cls._device_registry:
            raise ValueError(f"Unknown device type: {device_type}")
            
        return cls._device_registry[device_type](
            name=name,
            model=model,
            hostname=hostname,
            prompt=prompt,
            **kwargs
        )

# Import device implementations to register them
# This avoids circular imports by using the register_device decorator
try:
    from . import cisco, garderos, opengear  # noqa
except ImportError as e:
    logger.warning(f"Failed to import device implementations: {e}")
