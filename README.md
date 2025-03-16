# JumpSecure

## JumpSecure Banner
<!-- Replace with an actual banner image if desired -->

A command-line interface (CLI) tool to establish secure connections between a central server and a jump box using Reverse SSH, OpenVPN, or WireGuard. JumpSecure automates the configuration process, generates preconfigured scripts for jump box deployment, and manages firewall settings for seamless connectivity. Built with Python, it offers a user-friendly interface with colored output and an ASCII banner.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Script Details](#script-details)
- [Firewall Management](#firewall-management)
- [Contributing](#contributing)
- [License](#license)

## Overview

JumpSecure simplifies the process of creating secure connections in scenarios where a jump box (e.g., a remote device with cellular connectivity) needs to connect to a central server. It supports three secure connection methods:

- **Reverse SSH:** Creates a persistent SSH tunnel from the jump box to the central server.
- **OpenVPN:** Establishes a full VPN connection using certificate-based authentication.
- **WireGuard:** Sets up a lightweight, modern VPN with key-based authentication.

The tool automates the central server setup and generates a standalone Python script with hardcoded configuration details. This script can be transferred to the jump box and executed to complete the setup without additional user input.

## Features

- **CLI Menu-Driven Interface:** Easy navigation with options for Reverse SSH, OpenVPN, or WireGuard.
- **Colored Output:** Improved readability with Colorama.
- **ASCII Banner:** Stylish startup banner using PyFiglet.
- **Firewall Management:** Automatically opens user-specified ports for OpenVPN and WireGuard using `ufw`.
- **Preconfigured Jump Box Scripts:** Generates executable Python scripts with embedded configuration details.
- **Cross-Method Support:** Integrates three secure connection methods into a single tool.
- **Error Handling:** Ensures root privileges are present and gracefully manages command failures.

## Prerequisites

- **Operating System:** Debian-based Linux distribution (e.g., Ubuntu). Other distributions may require tweaks to package installation commands.
- **Root Privileges:** Must run the script with `sudo` for system-level operations (e.g., installing packages, managing services).
- **Python 3:** Required to execute the script.

### Dependencies:

- `colorama`: For colored terminal output.
- `pyfiglet`: For the ASCII banner.

## Installation

### Clone the Repository:
```bash
git clone https://github.com/scs-labrat/jumpsecure.git
cd jumpsecure
```

### Install Python Dependencies:
```bash
pip3 install colorama pyfiglet
```

### Ensure Firewall Tool Availability (optional but recommended):
For OpenVPN and WireGuard, the script uses `ufw` to manage ports. Install it if not present:
```bash
sudo apt-get install ufw
```

## Usage

### Run the Script:
```bash
sudo python3 secure_setup.py
```
Root privileges are required for package installation, service configuration, and firewall management.

### Main Menu:
After launching, you'll see an ASCII banner followed by a menu:

```
Choose connection method:
1. Reverse SSH
2. OpenVPN
3. WireGuard
Enter choice (1, 2, or 3):
```
Enter the number corresponding to your desired method.

### Setup Type Menu:
Next, choose the setup type:

```
Choose setup type:
1. Set up Central Server
2. Set up Jump Box (requires pre-generated script)
Enter choice (1 or 2):
```

### Central Server Setup:
- Select option `1` to configure the central server.
- Provide requested details (e.g., IP address, port number).

The script will:
- Configure the server (e.g., generate keys, set up services).
- Open the specified port on the firewall (for OpenVPN and WireGuard).
- Generate a jump box script (e.g., `setup_jumpbox_openvpn.py`).

#### Example output:
```
Generated 'setup_jumpbox_openvpn.py'.
Transfer this file to the jump box and run it with 'sudo python3 setup_jumpbox_openvpn.py'.
```

### Jump Box Setup:
Transfer the generated script to the jump box (e.g., via `scp`):
```bash
scp setup_jumpbox_openvpn.py user@jumpbox:/path/
```

On the jump box, execute the script:
```bash
sudo python3 setup_jumpbox_openvpn.py
```
The script will install required software and configure the connection automatically.

---

## Script Details

### Main Script (`secure_setup.py`)
**Purpose:** Manages the CLI interface and central server configuration.

**Key Functions:**
- Displays the ASCII banner.
- Presents menus for selecting connection methods and setup types.
- Executes shell commands with error handling.
- Opens firewall ports using `ufw`.
- Configures Reverse SSH, OpenVPN, or WireGuard and generates jump box scripts.

### Generated Jump Box Scripts
#### Reverse SSH (`setup_jumpbox_reverse_ssh.py`):
- Installs an SSH key and sets up a persistent reverse tunnel via a `systemd` service.

#### OpenVPN (`setup_jumpbox_openvpn.py`):
- Installs OpenVPN, writes a client configuration with embedded certificates, and starts the service.

#### WireGuard (`setup_jumpbox_wireguard.py`):
- Installs WireGuard, writes a client configuration with keys, and activates the interface.

---

## Firewall Management

**Tool Used:** `ufw` (Uncomplicated Firewall).

**Process:**
- Prompts for a port number (e.g., `1194` for OpenVPN, `51820` for WireGuard).
- Opens the specified UDP port using:
  ```bash
  ufw allow <port>/udp
  ufw reload
  ```
- If `ufw` is unavailable, it warns the user but proceeds, allowing manual configuration.

### Example:
#### Input:
```
Port 1194 for OpenVPN.
```
#### Command:
```bash
ufw allow 1194/udp
ufw reload
```
#### Output:
```
Successfully opened port 1194/udp on the firewall.
```

---

## Contributing

We welcome contributions! To get started:

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/YourFeature
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add YourFeature"
   ```
4. Push to the branch:
   ```bash
   git push origin feature/YourFeature
   ```
5. Open a pull request.

Please maintain the existing code style and include comments where necessary.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
