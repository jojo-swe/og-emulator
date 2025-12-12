"""SSH Emulator package for Opengear/Garderos devices.

This package provides a standalone SSH emulator that mimics the behavior of
Opengear and Garderos console servers for testing and development purposes.
"""

__version__ = "0.1.0"

# Lazy imports to avoid issues when running as script vs installed package
def __getattr__(name):
    """Lazy import of package components."""
    _imports = {
        "EmulatorManager": ("core.manager", "EmulatorManager"),
        "create_emulator_manager": ("core.manager", "create_emulator_manager"),
        "EmulatorConfig": ("core.config", "EmulatorConfig"),
        "OpengearDevice": ("devices.opengear", "OpengearDevice"),
        "GarderosDevice": ("devices.garderos", "GarderosDevice"),
        "CiscoDevice": ("devices.cisco", "CiscoDevice"),
        "SSHServer": ("core.ssh_server", "SSHServer"),
    }
    
    if name in _imports:
        module_name, attr_name = _imports[name]
        import importlib
        module = importlib.import_module(f".{module_name}", __package__)
        return getattr(module, attr_name)
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "EmulatorManager",
    "create_emulator_manager", 
    "EmulatorConfig",
    "OpengearDevice",
    "GarderosDevice",
    "CiscoDevice",
    "SSHServer",
]
