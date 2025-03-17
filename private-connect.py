#!/usr/bin/env python3

import click
import os
import subprocess
import yaml
import sys

# Configuration directory and files
CONFIG_DIR = os.path.expanduser('~/.jumpsecure')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.yaml')
PID_FILE = os.path.join(CONFIG_DIR, 'pid')

# Ensure configuration directory exists
def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)

# Save configuration to file
def save_config(kali_ip, kali_user):
    ensure_config_dir()
    config = {'kali_ip': kali_ip, 'kali_user': kali_user}
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f)

# Load configuration from file
def load_config():
    if not os.path.exists(CONFIG_FILE):
        click.echo("Error: Configuration not found. Run 'jumpsecure setup' first.")
        sys.exit(1)
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

# Check if a system tool is installed
def is_tool_installed(tool):
    return subprocess.call(f"which {tool}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

# Check if a Python module is installed
def is_module_installed(module):
    try:
        __import__(module)
        return True
    except ImportError:
        return False

# Setup SSH keys if not already configured
def setup_ssh_keys(kali_user, kali_ip):
    ssh_dir = os.path.expanduser('~/.ssh')
    key_file = os.path.join(ssh_dir, 'id_rsa')
    if not os.path.exists(key_file):
        click.echo("SSH key not found. Generating a new key pair...")
        subprocess.run("ssh-keygen -t rsa -b 4096", shell=True, check=True)
    click.echo("Copying SSH public key to the Kali box...")
    subprocess.run(f"ssh-copy-id {kali_user}@{kali_ip}", shell=True, check=True)

# Define CLI group
@click.group()
def cli():
    """JumpSecure: Automate SSH tunnel setup with Tor routing."""
    pass

# Setup command
@cli.command()
@click.option('--kali-ip', prompt='Kali box IP address', help='IP address of the Kali box')
@click.option('--kali-user', prompt='Kali box username', help='Username for SSH access to Kali box')
def setup(kali_ip, kali_user):
    """Set up the Kali box and save configuration."""
    # Check for required tools and modules
    if not is_tool_installed('ssh'):
        click.echo("Error: 'ssh' is not installed. Please install it with 'sudo apt install openssh-client -y'.")
        sys.exit(1)
    if not is_module_installed('click'):
        click.echo("Error: Python package 'click' is not installed. Please install it with 'pip3 install click'.")
        sys.exit(1)
    if not is_module_installed('yaml'):
        click.echo("Error: Python package 'pyyaml' is not installed. Please install it with 'pip3 install pyyaml'.")
        sys.exit(1)

    # Setup SSH keys
    setup_ssh_keys(kali_user, kali_ip)

    click.echo(f"Configuring Kali box at {kali_ip}...")
    # Commands to run on Kali box
    commands = [
        "dpkg -l tor || sudo apt update && sudo apt install tor -y",  # Install Tor if not present
        "sudo systemctl enable tor",  # Enable Tor on boot
        "sudo systemctl start tor"    # Start Tor service
    ]
    # Execute commands via SSH
    for cmd in commands:
        try:
            subprocess.run(
                f"ssh {kali_user}@{kali_ip} '{cmd}'",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            click.echo(f"Error executing '{cmd}': {e.stderr.decode()}")
            sys.exit(1)
    # Save configuration
    save_config(kali_ip, kali_user)
    click.echo("Setup completed successfully.")

# Start command
@cli.command()
def start():
    """Start the SSH tunnel to the Kali box."""
    # Check for autossh
    if not is_tool_installed('autossh'):
        click.echo("Error: 'autossh' is not installed. Please install it with 'sudo apt install autossh -y'.")
        sys.exit(1)
    config = load_config()
    kali_user = config['kali_user']
    kali_ip = config['kali_ip']
    # Check if tunnel is already running
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            pid = f.read().strip()
        if subprocess.call(f"kill -0 {pid}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
            click.echo("Tunnel is already running.")
            return
        else:
            os.remove(PID_FILE)  # Remove stale PID file
    # Start autossh tunnel
    tunnel_cmd = f"autossh -M 0 -L 1080:localhost:9050 {kali_user}@{kali_ip} -f -N"
    try:
        subprocess.run(tunnel_cmd, shell=True, check=True)
        # Find autossh PID
        pid = subprocess.check_output(
            f"pgrep -f 'autossh -M 0 -L 1080:localhost:9050 {kali_user}@{kali_ip}'",
            shell=True
        ).decode().strip().split('\n')[0]  # Take first PID if multiple
        with open(PID_FILE, 'w') as f:
            f.write(pid)
        click.echo("Tunnel started. Configure applications to use SOCKS proxy at localhost:1080.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Failed to start tunnel: {e}")
        sys.exit(1)

# Stop command
@cli.command()
def stop():
    """Stop the SSH tunnel."""
    if not os.path.exists(PID_FILE):
        click.echo("No tunnel is running.")
        return
    with open(PID_FILE, 'r') as f:
        pid = f.read().strip()
    try:
        subprocess.run(f"kill {pid}", shell=True, check=True)
        os.remove(PID_FILE)
        click.echo("Tunnel stopped.")
    except subprocess.CalledProcessError:
        click.echo("Failed to stop tunnel. It may have already terminated.")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

# Test command
@cli.command()
def test():
    """Test the tunnel by retrieving the exit IP."""
    # Check for curl
    if not is_tool_installed('curl'):
        click.echo("Error: 'curl' is not installed. Please install it with 'sudo apt install curl -y'.")
        sys.exit(1)
    try:
        ip = subprocess.check_output(
            "curl --socks5 localhost:1080 http://icanhazip.com",
            shell=True
        ).decode().strip()
        click.echo(f"Exit IP via Tor: {ip}")
    except subprocess.CalledProcessError:
        click.echo("Failed to retrieve IP. Ensure the tunnel is running and Tor is active.")

if __name__ == '__main__':
    cli()