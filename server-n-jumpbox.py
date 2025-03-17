import os
import subprocess
from colorama import Fore, Style, init
from pyfiglet import Figlet

# Initialize colorama for colored output
init()

# Check for root privileges
if os.geteuid() != 0:
    print(Fore.RED + "This script must be run as root. Please use 'sudo'." + Style.RESET_ALL)
    exit(1)

# Helper function to run shell commands with error handling
def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Command failed: {e}" + Style.RESET_ALL)
        exit(1)

# Function to open a firewall port using ufw
def open_firewall_port(port, protocol='udp'):
    try:
        # Check if ufw is installed
        subprocess.run("ufw --version", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Open the port
        run_command(f"ufw allow {port}/{protocol}")
        run_command("ufw reload")
        print(Fore.GREEN + f"Successfully opened port {port}/{protocol} on the firewall." + Style.RESET_ALL)
    except subprocess.CalledProcessError as e:
        if "not found" in str(e):
            print(Fore.YELLOW + "ufw is not installed. Please install ufw or manually open the port." + Style.RESET_ALL)
        else:
            print(Fore.RED + f"Failed to open port {port}/{protocol}. Error: {e}" + Style.RESET_ALL)

# Function to set up Reverse SSH on the central server
def setup_central_reverse_ssh():
    print(Fore.CYAN + "\nSetting up Central Server for Reverse SSH" + Style.RESET_ALL)
    central_user = input(Fore.YELLOW + "Enter central server username: " + Style.RESET_ALL)
    central_ip = input(Fore.YELLOW + "Enter central server IP: " + Style.RESET_ALL)
    tunnel_port = input(Fore.YELLOW + "Enter tunnel port (e.g., 2222): " + Style.RESET_ALL)
    ssh_key_path = input(Fore.YELLOW + "Enter path for SSH key (e.g., /root/jumpbox_key) [default: /root/jumpbox_key]: " + Style.RESET_ALL) or "/root/jumpbox_key"

    # Generate SSH key if it doesn't exist
    if not os.path.exists(ssh_key_path):
        print(Fore.CYAN + "Generating SSH key pair..." + Style.RESET_ALL)
        run_command(f"ssh-keygen -t rsa -b 4096 -f {ssh_key_path} -N ''")

    # Add public key to authorized_keys
    authorized_keys = f"/home/{central_user}/.ssh/authorized_keys"
    os.makedirs(f"/home/{central_user}/.ssh", exist_ok=True)
    with open(f"{ssh_key_path}.pub", "r") as pub_file:
        pub_key = pub_file.read()
    with open(authorized_keys, "a") as auth_file:
        auth_file.write(pub_key)
    run_command(f"chown {central_user}:{central_user} {authorized_keys}")
    run_command(f"chmod 600 {authorized_keys}")
    print(Fore.GREEN + "Public key added to authorized_keys." + Style.RESET_ALL)

    # Read private key for embedding in the script
    with open(ssh_key_path, "r") as key_file:
        private_key = key_file.read().replace("\n", "\\n")

    # Generate jump box script with hardcoded details
    script_content = f'''#!/usr/bin/env python3
import os
import subprocess

# Hardcoded configuration from central server
central_ip = "{central_ip}"
tunnel_port = "{tunnel_port}"
private_key = r"""{private_key}"""

# Set up SSH key on jump box
key_path = "/root/.ssh/jumpbox_key"
os.makedirs("/root/.ssh", exist_ok=True)
with open(key_path, "w") as f:
    f.write(private_key.replace("\\\\n", "\\n"))
subprocess.run(f"chmod 600 {{key_path}}", shell=True, check=True)

# Create systemd service for persistent reverse SSH tunnel
service_content = f"""[Unit]
Description=Reverse SSH Tunnel
After=network.target

[Service]
ExecStart=/usr/bin/ssh -i {{key_path}} -R {tunnel_port}:localhost:22 {central_user}@{{central_ip}} -N -o ServerAliveInterval=60
Restart=always
User=root

[Install]
WantedBy=multi-user.target
"""
with open("/etc/systemd/system/reverse-ssh.service", "w") as f:
    f.write(service_content)
subprocess.run("systemctl daemon-reload", shell=True, check=True)
subprocess.run("systemctl enable reverse-ssh.service", shell=True, check=True)
subprocess.run("systemctl start reverse-ssh.service", shell=True, check=True)
print("Reverse SSH tunnel set up and started on the jump box.")
'''
    script_filename = "setup_jumpbox_reverse_ssh.py"
    with open(script_filename, "w") as script_file:
        script_file.write(script_content)
    run_command(f"chmod +x {script_filename}")
    print(Fore.GREEN + f"\nGenerated '{script_filename}'." + Style.RESET_ALL)
    print(Fore.YELLOW + f"Transfer this file to the jump box and run it with 'sudo python3 {script_filename}'." + Style.RESET_ALL)

# Function to set up OpenVPN on the central server
def setup_central_openvpn():
    print(Fore.CYAN + "\nSetting up Central Server for OpenVPN" + Style.RESET_ALL)
    central_ip = input(Fore.YELLOW + "Enter central server IP: " + Style.RESET_ALL)
    vpn_port = input(Fore.YELLOW + "Enter OpenVPN port (e.g., 1194): " + Style.RESET_ALL)

    # Open the specified port on the firewall
    open_firewall_port(vpn_port, 'udp')

    # Install OpenVPN and Easy-RSA
    run_command("apt-get update && apt-get install -y openvpn easy-rsa")

    # Set up Easy-RSA for certificate management
    easy_rsa_dir = "/etc/openvpn/easy-rsa"
    os.makedirs(easy_rsa_dir, exist_ok=True)
    run_command(f"cp -r /usr/share/easy-rsa/* {easy_rsa_dir}/")
    os.chdir(easy_rsa_dir)
    run_command("./easyrsa --batch init-pki")
    run_command("./easyrsa --batch build-ca nopass")
    run_command("./easyrsa --batch gen-req server nopass")
    run_command("./easyrsa --batch sign-req server server")
    run_command("./easyrsa --batch gen-req jumpbox nopass")
    run_command("./easyrsa --batch sign-req client jumpbox")
    run_command("./easyrsa --batch gen-dh")

    # Create OpenVPN server configuration
    server_config = f"""
port {vpn_port}
proto udp
dev tun
ca {easy_rsa_dir}/pki/ca.crt
cert {easy_rsa_dir}/pki/issued/server.crt
key {easy_rsa_dir}/pki/private/server.key
dh {easy_rsa_dir}/pki/dh.pem
server 10.8.0.0 255.255.255.0
push "redirect-gateway def1"
keepalive 10 120
cipher AES-256-CBC
persist-key
persist-tun
status openvpn-status.log
verb 3
"""
    with open("/etc/openvpn/server.conf", "w") as f:
        f.write(server_config)

    # Enable IP forwarding
    run_command("sysctl -w net.ipv4.ip_forward=1")
    run_command("sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf")

    # Start OpenVPN server
    run_command("systemctl enable openvpn@server")
    run_command("systemctl start openvpn@server")

    # Read certificates and keys for client config
    with open(f"{easy_rsa_dir}/pki/ca.crt", "r") as f:
        ca_cert = f.read()
    with open(f"{easy_rsa_dir}/pki/issued/jumpbox.crt", "r") as f:
        client_cert = f.read()
    with open(f"{easy_rsa_dir}/pki/private/jumpbox.key", "r") as f:
        client_key = f.read()

    # Generate client configuration with inline certificates
    client_config = f"""
client
dev tun
proto udp
remote {central_ip} {vpn_port}
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-CBC
verb 3
<ca>
{ca_cert}
</ca>
<cert>
{client_cert}
</cert>
<key>
{client_key}
</key>
"""

    # Generate jump box setup script
    script_content = f'''#!/usr/bin/env python3
import os
import subprocess

# Hardcoded client configuration
client_config = r"""{client_config}"""

# Install OpenVPN if not present
subprocess.run("apt-get update && apt-get install -y openvpn", shell=True, check=True)

# Write client config to file
with open("/etc/openvpn/jumpbox.conf", "w") as f:
    f.write(client_config)

# Enable and start OpenVPN client service
subprocess.run("systemctl enable openvpn@jumpbox", shell=True, check=True)
subprocess.run("systemctl start openvpn@jumpbox", shell=True, check=True)
print("OpenVPN client set up and started on the jump box.")
'''
    script_filename = "setup_jumpbox_openvpn.py"
    with open(script_filename, "w") as script_file:
        script_file.write(script_content)
    run_command(f"chmod +x {script_filename}")
    print(Fore.GREEN + f"\nGenerated '{script_filename}'." + Style.RESET_ALL)
    print(Fore.YELLOW + f"Transfer this file to the jump box and run it with 'sudo python3 {script_filename}'." + Style.RESET_ALL)

# Function to set up WireGuard on the central server
def setup_central_wireguard():
    print(Fore.CYAN + "\nSetting up Central Server for WireGuard" + Style.RESET_ALL)
    central_ip = input(Fore.YELLOW + "Enter central server IP: " + Style.RESET_ALL)
    wg_port = input(Fore.YELLOW + "Enter WireGuard port (e.g., 51820): " + Style.RESET_ALL)

    # Open the specified port on the firewall
    open_firewall_port(wg_port, 'udp')

    # Install WireGuard
    run_command("apt-get update && apt-get install -y wireguard")

    # Generate server keys
    server_private_key = subprocess.check_output("wg genkey", shell=True).decode().strip()
    server_public_key = subprocess.check_output(f"echo '{server_private_key}' | wg pubkey", shell=True).decode().strip()

    # Generate client keys
    client_private_key = subprocess.check_output("wg genkey", shell=True).decode().strip()
    client_public_key = subprocess.check_output(f"echo '{client_private_key}' | wg pubkey", shell=True).decode().strip()

    # Create server configuration
    server_config = f"""
[Interface]
PrivateKey = {server_private_key}
Address = 10.0.0.1/24
ListenPort = {wg_port}

[Peer]
PublicKey = {client_public_key}
AllowedIPs = 10.0.0.2/32
"""
    with open("/etc/wireguard/wg0.conf", "w") as f:
        f.write(server_config)

    # Enable and start WireGuard
    run_command("systemctl enable wg-quick@wg0")
    run_command("systemctl start wg-quick@wg0")

    # Generate client configuration
    client_config = f"""
[Interface]
PrivateKey = {client_private_key}
Address = 10.0.0.2/24
DNS = 8.8.8.8

[Peer]
PublicKey = {server_public_key}
Endpoint = {central_ip}:{wg_port}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""

    # Generate jump box setup script
    script_content = f'''#!/usr/bin/env python3
import os
import subprocess

# Hardcoded client configuration
client_config = r"""{client_config}"""

# Install WireGuard if not present
subprocess.run("apt-get update && apt-get install -y wireguard", shell=True, check=True)

# Write client config to file
with open("/etc/wireguard/wg0.conf", "w") as f:
    f.write(client_config)

# Start WireGuard client
subprocess.run("wg-quick up wg0", shell=True, check=True)
subprocess.run("systemctl enable wg-quick@wg0", shell=True, check=True)
print("WireGuard client set up and started on the jump box.")
'''
    script_filename = "setup_jumpbox_wireguard.py"
    with open(script_filename, "w") as script_file:
        script_file.write(script_content)
    run_command(f"chmod +x {script_filename}")
    print(Fore.GREEN + f"\nGenerated '{script_filename}'." + Style.RESET_ALL)
    print(Fore.YELLOW + f"Transfer this file to the jump box and run it with 'sudo python3 {script_filename}'." + Style.RESET_ALL)

# Menu functions
def print_banner():
    fig = Figlet(font='slant')
    print(Fore.GREEN + fig.renderText('Secure Setup') + Style.RESET_ALL)

def main_menu():
    print(Fore.CYAN + "Choose connection method:" + Style.RESET_ALL)
    print(Fore.GREEN + "1. Reverse SSH" + Style.RESET_ALL)
    print(Fore.GREEN + "2. OpenVPN" + Style.RESET_ALL)
    print(Fore.GREEN + "3. WireGuard" + Style.RESET_ALL)
    return input(Fore.YELLOW + "Enter choice (1, 2, or 3): " + Style.RESET_ALL)

def setup_type_menu():
    print(Fore.CYAN + "Choose setup type:" + Style.RESET_ALL)
    print(Fore.GREEN + "1. Set up Central Server" + Style.RESET_ALL)
    print(Fore.GREEN + "2. Set up Jump Box (requires pre-generated script)" + Style.RESET_ALL)
    return input(Fore.YELLOW + "Enter choice (1 or 2): " + Style.RESET_ALL)

# Main function to run the CLI tool
def main():
    print_banner()
    method = main_menu()
    setup_type = setup_type_menu()
    if setup_type == '1':
        if method == '1':
            setup_central_reverse_ssh()
        elif method == '2':
            setup_central_openvpn()
        elif method == '3':
            setup_central_wireguard()
    elif setup_type == '2':
        print(Fore.YELLOW + "To set up the jump box, transfer the generated script and run it there." + Style.RESET_ALL)

if __name__ == "__main__":
    main()