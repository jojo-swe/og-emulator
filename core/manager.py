"""Emulator manager for handling SSH emulator lifecycle."""

import logging
import multiprocessing
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, List, Union

from .config import EmulatorConfig

T = TypeVar("T", bound="EmulatorManager")

class EmulatorManager:
    """Manages the SSH emulator lifecycle with process isolation.
    
    This class handles starting and stopping the SSH emulator in a separate process
    to ensure proper isolation and prevent blocking the main application.
    """
    
    def __init__(self, config: EmulatorConfig) -> None:
        """Initialize the emulator manager.
        
        Args:
            config: Emulator configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._process: Optional[multiprocessing.Process] = None
        self._started: bool = False
        self._start_lock = threading.Lock()
        self._startup_timeout: float = config.startup_timeout
        self._stop_timeout: float = config.stop_timeout

    @classmethod
    def from_dict(cls: Type[T], config_dict: Dict[str, Any]) -> T:
        """Create instance from configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            EmulatorManager instance
        """
        return cls(EmulatorConfig(**config_dict))

    def start(self) -> bool:
        """Start the emulator in a separate process.
        
        Returns:
            bool: True if started successfully
        """
        with self._start_lock:
            if self._started and self._process and self._process.is_alive():
                self.logger.info("Emulator already running")
                return True
                
            self.logger.info("Starting emulator in a separate process...")
            
            # Clear any existing process
            if self._process:
                self.stop()
                
            # Create and start the process
            self._process = multiprocessing.Process(
                target=self._run_emulator_process,
                args=(self.config.to_dict(),),
                daemon=True
            )
            self._process.daemon = True  # Ensure process is marked as daemon
            self._process.start()
            
            # Wait for emulator to start (with timeout)
            start_time = time.time()
            while time.time() - start_time < self._startup_timeout:
                if self._process.is_alive():
                    self._started = True
                    self.logger.info(f"Emulator started (pid={self._process.pid})")
                    return True
                time.sleep(0.1)
                
            # If we got here, the process didn't start properly
            self.logger.error("Failed to start emulator process")
            self.stop()  # Try to clean up
            return False

    def stop(self) -> bool:
        """Stop the emulator process.
        
        Returns:
            bool: True if stopped successfully
        """
        if not self._process:
            self.logger.info("No emulator process to stop")
            self._started = False
            return True
            
        self.logger.info("Stopping emulator process...")
        
        # Try to terminate gracefully
        try:
            self._process.terminate()
            
            # Wait for process to terminate (with timeout)
            start_time = time.time()
            while time.time() - start_time < self._stop_timeout:
                if not self._process.is_alive():
                    break
                time.sleep(0.1)
                
            # If still alive, force kill
            if self._process.is_alive():
                self.logger.warning("Emulator process not responding, force killing...")
                self._process.kill()
                
            # Clean up
            self._process = None
            self._started = False
            self.logger.info("Emulator stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping emulator: {e}")
            return False

    def is_running(self) -> bool:
        """Check if the emulator is running.
        
        Returns:
            bool: True if emulator is running
        """
        return self._started and self._process is not None and self._process.is_alive()

    @staticmethod
    def _run_emulator_process(config_dict: Dict[str, Any]) -> None:
        """Run the emulator in a separate process.
        
        Args:
            config_dict: Configuration dictionary
        """
        # Set up signal handlers first thing
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Get logger after basic config is set up
        logger = logging.getLogger("emulator")
        
        try:
            logger.info("Emulator process started")
            
            # Import here to avoid circular imports and reduce what gets pickled
            from ..utils.config import run_server
            
            # Run the emulator
            run_server(config_dict)
            
        except Exception as e:
            logger.error(f"Error in emulator process: {e}")
            sys.exit(1)


def create_emulator_manager(config_service_or_path: Union[Any, str, Path]) -> EmulatorManager:
    """Create an emulator manager with configuration.
    
    Args:
        config_service_or_path: Configuration service instance or path to config file
        
    Returns:
        EmulatorManager instance
    """
    if isinstance(config_service_or_path, (str, Path)):
        config = EmulatorConfig.from_config_file(config_service_or_path)
    else:
        config = EmulatorConfig.from_config_service(config_service_or_path)
        
    return EmulatorManager(config)
