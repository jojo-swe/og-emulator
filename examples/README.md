# Examples

This directory contains example scripts that demonstrate how to use the SSH emulator.

## Available Examples

- `asyncssh_example.py`: Connects to the emulator with `asyncssh`, drives pmshell, runs concurrent sessions, and prints Paramiko, Netmiko and Ansible snippets.

## Running Examples

1. Start the SSH emulator in a separate terminal:
   ```bash
   python -m emulator
   ```

2. Run the example script in another terminal:
   ```bash
   python examples/asyncssh_example.py
   ```
