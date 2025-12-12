"""Configuration package for the SSH emulator.

This package contains configuration management code for the SSH emulator,
including loading and parsing configuration files, and providing default values.
"""

from .config import EmulatorConfig, PortConfig

__all__ = [
    'EmulatorConfig',
    'PortConfig',
]
