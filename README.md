# JumpSecure

![JumpSecure Banner](#) <!-- Replace with an actual banner image if desired -->

JumpSecure is a powerful command-line multitool designed to establish and manage secure connections between systems using Tor SSH, Reverse SSH, OpenVPN, and WireGuard. Built in Python, it automates the setup process, generates configuration files, and provides a simple interface for starting, stopping, and testing connections. Whether you're a red teamer seeking anonymity or a sysadmin securing remote access, JumpSecure streamlines the process with flexibility and ease of use.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

JumpSecure integrates multiple secure connection methods into a single tool, allowing users to:

- **Tor SSH**: Route traffic through the Tor network for anonymity via an SSH tunnel.
- **Reverse SSH**: Create a persistent tunnel from a remote server back to your machine.
- **OpenVPN**: Set up a full VPN server and client configuration.
- **WireGuard**: Establish a lightweight, modern VPN with minimal setup.

The tool automates dependency checks, firewall management, and configuration generation, making it ideal for red team operations, secure remote access, or privacy-focused networking.

## Features

- **Multiple Connection Methods**: Supports Tor SSH, Reverse SSH, OpenVPN, and WireGuard.
- **Interactive CLI**: Menu-driven interface when run without arguments, or command-based with options.
- **Dependency Management**: Checks for required tools and provides installation instructions if missing.
- **Firewall Automation**: Opens necessary ports using `ufw` for OpenVPN and WireGuard.
- **Configuration Persistence**: Stores settings in a YAML file for reuse.
- **Testing Capabilities**: Verifies connection functionality with built-in tests.
- **Colorized Output**: Enhances readability with `colorama`.

## Prerequisites

Before installing and running `jump-secure.py`, ensure the following are met:

- **Operating System**: Debian-based Linux distribution (e.g., Ubuntu or Kali Linux). Other distributions may require adjusting package installation commands.
- **Root Privileges**: The script must be run with `sudo` to manage system services, install dependencies, and configure firewall rules.
- **Python 3**: Version 3.6 or higher is required.
- **Internet Access**: Needed to install dependencies and test connections.

### Required Tools

Depending on the connection method, you’ll need:

- **Tor SSH**: `tor`, `autossh`, `ssh`, `curl`
- **Reverse SSH**: `ssh`, `autossh`
- **OpenVPN**: `openvpn`, `easy-rsa`
- **WireGuard**: `wireguard`

### Python Dependencies

- `click`: For the CLI interface.
- `pyyaml`: For configuration file handling.
- `colorama`: For colored terminal output.

## Installation

### Clone the Repository

```bash
git clone https://github.com/scs-labrat/jumpsecure.git
cd jumpsecure
```

### Install Python Dependencies

```bash
pip3 install click pyyaml colorama
```

If you encounter permission issues, use:

```bash
pip3 install --user click pyyaml colorama
```

### Ensure System Tools

Install the core tools required for all methods:

```bash
sudo apt update && sudo apt install -y tor autossh openssh-client curl openvpn easy-rsa wireguard
```

If you only plan to use specific methods, install just those dependencies (e.g., `tor` and `autossh` for Tor SSH).

### Verify Installation

Check Python version:

```bash
python3 --version
```

Confirm tools are installed:

```bash
tor --version && autossh --version && ssh -V && curl --version && openvpn --version && wg --version
```

### Set Up Permissions

Make the script executable:

```bash
chmod +x jump-secure.py
```

## Usage

`jump-secure.py` can be run in two modes: interactive (no arguments) or command-line (with arguments). It requires root privileges due to system-level operations.

### Interactive Mode

Run the script without arguments to use the interactive menu:

```bash
sudo ./jump-secure.py
```

You'll see:

```
Welcome to the Secure Connection Multitool!
Choose connection method (tor-ssh, reverse-ssh, openvpn, wireguard):
```

Enter a method (e.g., `tor-ssh`), then choose an action (`setup`, `start`, `stop`, `test`).

### Command-Line Mode

#### Setup a Connection

```bash
sudo ./jump-secure.py setup --method <method>
```

Examples:

```bash
sudo ./jump-secure.py setup --method tor-ssh
sudo ./jump-secure.py setup --method reverse-ssh
sudo ./jump-secure.py setup --method openvpn
sudo ./jump-secure.py setup --method wireguard
```

#### Start a Connection

```bash
sudo ./jump-secure.py start --method <method>
```

#### Stop a Connection

```bash
sudo ./jump-secure.py stop --method <method>
```

#### Test a Connection

```bash
sudo ./jump-secure.py test --method <method>
```

## Configuration

The script stores settings in a `config.yaml` file in the same directory. Example structure:

```yaml
tor-ssh:
  port: 9050
reverse-ssh:
  remote_host: "example.com"
  remote_user: "user"
  remote_port: 22
  local_port: 2222
openvpn:
  port: 1194
wireguard:
  port: 51820
```

## Troubleshooting

- **Permission Denied**: Ensure you run the script with `sudo`.
- **Dependency Missing**: If a tool isn’t installed, the script will warn you with an installation command (e.g., `sudo apt install tor`).
- **Firewall Issues**: If `ufw` isn’t installed, manually open ports (e.g., `iptables -A INPUT -p udp --dport 1194 -j ACCEPT` for OpenVPN).
- **Connection Fails**: Verify network connectivity, SSH credentials, and that services (e.g., Tor, OpenVPN) are running on the target machine.
- **Test Fails**: Check if the tunnel or VPN is active (`ps aux | grep autossh` for Reverse SSH, `systemctl status openvpn@server` for OpenVPN).

### For detailed logs:

- **Tor SSH**: Check `/var/log/tor/log`.
- **OpenVPN**: See `/etc/openvpn/server/openvpn-status.log`.
- **WireGuard**: Run `wg show`.
