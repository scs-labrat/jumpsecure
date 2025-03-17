import click
import os
import subprocess
import yaml
from colorama import Fore, Style, init

# Initialize colorama for colored output
init()

# Configuration file
CONFIG_FILE = "config.yaml"

# Dependency requirements for each method
DEPENDENCIES = {
    "tor-ssh": ["tor", "autossh", "ssh", "curl"],
    "reverse-ssh": ["ssh", "autossh"],
    "openvpn": ["openvpn", "easy-rsa"],
    "wireguard": ["wireguard"]
}

# Helper Functions
def run_command(command):
    """Execute a shell command and handle errors."""
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        click.echo(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        raise

def check_dependencies(method):
    """Check if required dependencies are installed."""
    for dep in DEPENDENCIES.get(method, []):
        if not subprocess.run(f"which {dep}", shell=True, stdout=subprocess.PIPE).stdout:
            click.echo(f"{Fore.YELLOW}Warning: '{dep}' is not installed. Install it with: sudo apt install {dep}{Style.RESET_ALL}")
            return False
    return True

def open_firewall_port(port, protocol="udp"):
    """Open a firewall port using ufw."""
    if not subprocess.run("which ufw", shell=True, stdout=subprocess.PIPE).stdout:
        click.echo(f"{Fore.YELLOW}Warning: 'ufw' is not installed. Install it or manually open port {port}/{protocol}.{Style.RESET_ALL}")
        return
    run_command(f"ufw allow {port}/{protocol}")
    click.echo(f"{Fore.GREEN}Opened port {port}/{protocol} on firewall.{Style.RESET_ALL}")

def load_config():
    """Load the configuration file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_config(config):
    """Save the configuration file."""
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config, f)

# CLI Group with Menu System
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Multitool for managing secure connections."""
    if ctx.invoked_subcommand is None:
        click.echo(f"{Fore.CYAN}Welcome to the Secure Connection Multitool!{Style.RESET_ALL}")
        method = click.prompt("Choose connection method", type=click.Choice(["tor-ssh", "reverse-ssh", "openvpn", "wireguard"]))
        action = click.prompt("Choose action", type=click.Choice(["setup", "start", "stop", "test"]))
        ctx.invoke(globals()[action], method=method)

# Setup Command
@cli.command()
@click.option("--method", type=click.Choice(["tor-ssh", "reverse-ssh", "openvpn", "wireguard"]), prompt="Choose connection method")
def setup(method):
    """Set up a connection method."""
    if not check_dependencies(method):
        click.echo(f"{Fore.RED}Setup aborted due to missing dependencies.{Style.RESET_ALL}")
        return

    config = load_config()
    if method not in config:
        config[method] = {}

    if method == "tor-ssh":
        config[method]["server_ip"] = click.prompt("Enter server IP")
        config[method]["port"] = click.prompt("Enter SSH port", type=int, default=22)
        save_config(config)
        click.echo(f"{Fore.GREEN}Tor SSH setup complete. Configure applications to use SOCKS proxy at localhost:9050.{Style.RESET_ALL}")

    elif method == "reverse-ssh":
        config[method]["server_ip"] = click.prompt("Enter server IP")
        config[method]["port"] = click.prompt("Enter reverse SSH port", type=int)
        script = f"autossh -M 0 -R {config[method]['port']}:localhost:22 user@{config[method]['server_ip']}"
        with open("reverse_ssh.sh", "w") as f:
            f.write(script)
        save_config(config)
        click.echo(f"{Fore.GREEN}Reverse SSH setup complete. Transfer 'reverse_ssh.sh' to the jump box with: scp reverse_ssh.sh user@<jump-box-ip>:~/ && ssh user@<jump-box-ip> 'bash reverse_ssh.sh'{Style.RESET_ALL}")

    elif method == "openvpn":
        config[method]["port"] = click.prompt("Enter OpenVPN port", type=int, default=1194)
        open_firewall_port(config[method]["port"])
        save_config(config)
        click.echo(f"{Fore.GREEN}OpenVPN setup complete. Configure OpenVPN server and transfer client config to the jump box.{Style.RESET_ALL}")

    elif method == "wireguard":
        config[method]["port"] = click.prompt("Enter WireGuard port", type=int, default=51820)
        open_firewall_port(config[method]["port"])
        save_config(config)
        click.echo(f"{Fore.GREEN}WireGuard setup complete. Configure WireGuard keys and transfer peer config to the jump box.{Style.RESET_ALL}")

# Start Command
@cli.command()
@click.option("--method", type=click.Choice(["tor-ssh", "reverse-ssh", "openvpn", "wireguard"]), prompt="Choose connection method")
def start(method):
    """Start a connection."""
    if not check_dependencies(method):
        return
    config = load_config()
    if method not in config:
        click.echo(f"{Fore.RED}Please run 'setup {method}' first.{Style.RESET_ALL}")
        return

    if method == "tor-ssh":
        run_command(f"ssh -D 9050 -p {config[method]['port']} user@{config[method]['server_ip']} -N &")
        click.echo(f"{Fore.GREEN}Tor SSH tunnel started. Use SOCKS proxy at localhost:9050.{Style.RESET_ALL}")

    # Add start logic for other methods as needed

# Stop and Test Commands (placeholders)
@cli.command()
@click.option("--method", type=click.Choice(["tor-ssh", "reverse-ssh", "openvpn", "wireguard"]), prompt="Choose connection method")
def stop(method):
    """Stop a connection."""
    click.echo(f"Stopping {method} (not fully implemented yet).")

@cli.command()
@click.option("--method", type=click.Choice(["tor-ssh", "reverse-ssh", "openvpn", "wireguard"]), prompt="Choose connection method")
def test(method):
    """Test a connection."""
    click.echo(f"Testing {method} (not fully implemented yet).")

if __name__ == "__main__":
    cli()