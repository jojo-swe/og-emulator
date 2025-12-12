#!/usr/bin/env python3
"""Example script showing how to use the SSH emulator programmatically."""

import asyncio
import asyncssh
import json
from pathlib import Path


async def test_basic_connection():
    """Test basic SSH connection to the emulator."""
    print("Testing basic SSH connection...")
    
    try:
        async with asyncssh.connect(
            'localhost',
            port=2222,
            username='admin',
            password='admin',
            known_hosts=None
        ) as conn:
            print("✓ Connected successfully")
            
            # Run a simple command
            result = await conn.run('help', check=True)
            print(f"✓ Help command output:\n{result.stdout}")
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")


async def test_device_connection():
    """Test connecting to a specific device."""
    print("\nTesting device connection...")
    
    try:
        async with asyncssh.connect(
            'localhost',
            port=2222,
            username='admin',
            password='admin',
            known_hosts=None
        ) as conn:
            # Start an interactive session
            async with conn.create_process() as process:
                # Read initial prompt
                output = await process.stdout.read(512)
                print("Initial prompt received")
                
                # Send pmshell command
                process.stdin.write('pmshell\n')
                await asyncio.sleep(0.5)
                output = await process.stdout.read(1024)
                print("Device list received")
                
                # Connect to port 2 (Cisco device)
                process.stdin.write('2\n')
                await asyncio.sleep(0.5)
                output = await process.stdout.read(1024)
                
                if "Connected to" in output:
                    print("✓ Connected to Cisco device")
                    
                    # Run show version
                    process.stdin.write('show version\n')
                    await asyncio.sleep(0.5)
                    output = await process.stdout.read(1024)
                    print(f"✓ Device output:\n{output}")
                else:
                    print("✗ Failed to connect to device")
                
    except Exception as e:
        print(f"✗ Error: {e}")


def create_custom_config(filename='custom_config.json'):
    """Create a custom configuration file."""
    print(f"\nCreating custom configuration: {filename}")
    
    config = {
        "server": {
            "host": "127.0.0.1",
            "port": 2225,
            "username": "customuser",
            "password": "custompass",
            "banner": "Custom SSH Emulator\r\n"
        },
        "logging": {
            "level": "DEBUG",
            "file": "custom.log"
        },
        "devices": [
            {
                "port": 1,
                "device_type": "cisco",
                "model": "C9500",
                "hostname": "custom-switch",
                "firmware_version": "17.9.1"
            },
            {
                "port": 2,
                "device_type": "garderos",
                "model": "GCX-5000",
                "hostname": "custom-garderos",
                "firmware_version": "4.0.0",
                "build_number": "40001"
            }
        ]
    }
    
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Created {filename}")
    print(f"  Run with: python main.py --config {filename}")
    return filename


async def test_multiple_sessions():
    """Test multiple concurrent SSH sessions."""
    print("\nTesting multiple concurrent sessions...")
    
    async def session_task(session_id):
        """Run a session task."""
        try:
            async with asyncssh.connect(
                'localhost',
                port=2222,
                username='admin',
                password='admin',
                known_hosts=None
            ) as conn:
                result = await conn.run('help', check=True)
                return f"Session {session_id}: Success"
        except Exception as e:
            return f"Session {session_id}: Failed - {e}"
    
    # Run 5 concurrent sessions
    tasks = [session_task(i) for i in range(1, 6)]
    results = await asyncio.gather(*tasks)
    
    for result in results:
        print(f"  {result}")


def show_programmatic_usage():
    """Show how to use the emulator programmatically."""
    print("\nProgrammatic Usage Examples:")
    print("-" * 50)
    
    print("\n1. Using with Paramiko:")
    print("""
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('localhost', port=2222, username='admin', password='admin')

stdin, stdout, stderr = client.exec_command('help')
print(stdout.read().decode())
client.close()
""")
    
    print("\n2. Using with Netmiko:")
    print("""
from netmiko import ConnectHandler

device = {
    'device_type': 'generic',
    'host': 'localhost',
    'port': 2222,
    'username': 'admin',
    'password': 'admin'
}

conn = ConnectHandler(**device)
output = conn.send_command('help')
print(output)
conn.disconnect()
""")
    
    print("\n3. Using with Ansible:")
    print("""
# inventory.yml
all:
  hosts:
    emulator:
      ansible_host: localhost
      ansible_port: 2222
      ansible_user: admin
      ansible_password: admin
      ansible_connection: ssh
      ansible_ssh_common_args: '-o StrictHostKeyChecking=no'

# Run: ansible all -i inventory.yml -m raw -a "help"
""")


async def main():
    """Run all examples."""
    print("SSH Emulator Usage Examples")
    print("=" * 50)
    
    # Note: Make sure the emulator is running before executing these tests
    print("\nNOTE: Make sure the SSH emulator is running on port 2222")
    print("      Run 'python main.py' in another terminal\n")
    
    try:
        # Test basic connection
        await test_basic_connection()
        
        # Test device connection
        await test_device_connection()
        
        # Test multiple sessions
        await test_multiple_sessions()
        
        # Create custom config
        create_custom_config()
        
        # Show usage examples
        show_programmatic_usage()
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure the SSH emulator is running:")
        print("  python main.py")


if __name__ == '__main__':
    asyncio.run(main())