"""Base device class for all emulated devices."""

from abc import ABC, abstractmethod

class BaseDevice(ABC):
    """Base class for all emulated devices."""
    
    # Device type should be overridden by subclasses
    device_type = "base"
    
    def __init__(self, name: str, model: str, hostname: str, prompt: str, **kwargs):
        """Initialize the base device.
        
        Args:
            name: Device name/identifier
            model: Device model
            hostname: Device hostname
            prompt: Command prompt
            **kwargs: Additional device-specific configuration
                - port: Port number for this device
                - firmware_version: Device firmware version
                - build_number: Device build number
        """
        self.name = name
        self.model = model
        self.hostname = hostname
        self.prompt = prompt
        self.port = kwargs.pop('port', 0)
        self.device_type = kwargs.pop('device_type', self.__class__.__name__.lower().replace('device', ''))
        self.firmware_version = kwargs.pop('firmware_version', '1.0.0')
        self.build_number = kwargs.pop('build_number', '1234')
        self.config = kwargs
        self.connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the device.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the device."""
        pass
    
    @abstractmethod
    def execute_command(self, command: str) -> str:
        """Execute a command on the device.
        
        Args:
            command: Command to execute
            
        Returns:
            Command output
        """
        pass
    
    def get_banner(self) -> str:
        """Get the device banner.
        
        Returns:
            str: Device banner
        """
        return f"{self.model} - {self.hostname}\r\n\r\n"
    
    def get_prompt(self) -> str:
        """Get the current command prompt.
        
        Returns:
            str: Command prompt
        """
        return self.prompt
