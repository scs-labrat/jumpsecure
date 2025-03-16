import os
import subprocess
import getpass
import shutil

def run_command(command):
    """Run a shell command and handle errors."""
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        exit(1)

def setup_easyrsa():
    """Set up Easy-RSA for certificate generation."""
    if not os.path.exists("/usr/share/easy-rsa"):
        run_command("sudo apt update && sudo apt install -y easy-rsa")
    if not os.path.exists("/etc/easy-rsa"):
        run_command("sudo mkdir -p /etc/easy-rsa")
        run_command("sudo ln -s /usr/share/easy-rsa/* /etc/easy-rsa/")
    os.chdir("/etc/easy-rsa")
    if not os.path.exists("pki"):
        run_command("./easyrsa init-pki")
        run_command("./easyrsa build-ca nopass")
        run_command("./easyrsa gen-dh")
        run_command("./easyrsa build-server-full server nopass")
        run_command("./easyrsa build-client-full jumpbox nopass")

def generate_jump_box_script(central_ip, vpn_port, ca_cert, client_cert, client_key):
    """Generate the preconfigured jump box setup script."""
    jump_box_script = f"""#!/usr/bin/env python3
import os
import subprocess

def run_command(command):
    \"\"\"Run a shell command and handle errors.\"\"\"
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {{e}}")
        exit(1)

def main():
    print("=== Jump Box OpenVPN Setup ===")
    
    # Preconfigured details
    central_ip = "{central_ip}"
    vpn_port = "{vpn_port}"
    ca_cert = \"\"\"{ca_cert}\"\"\"
    client_cert = \"\"\"{client_cert}\"\"\"
    client_key = \"\"\"{client_key}\"\"\"
    
    # Install OpenVPN
    print("Installing OpenVPN if not present...")
    run_command("sudo apt update && sudo apt install -y openvpn")
    
    # Write certificates and keys
    os.makedirs("/etc/openvpn/client", exist_ok=True)
    with open("/etc/openvpn/client/ca.crt", "w") as f:
        f.write(ca_cert)
    with open("/etc/openvpn/client/jumpbox.crt", "w") as f:
        f.write(client_cert)
    with open("/etc/openvpn/client/jumpbox.key", "w") as f:
        f.write(client_key)
    run_command("sudo chmod 600 /etc/openvpn/client/*")
    
    # Write OpenVPN client config
    client_config = f\"\"\"client
dev tun
proto udp
remote {{central_ip}} {{vpn_port}}
resolv-retry infinite
nobind
persist-key
persist-tun
ca /etc/openvpn/client/ca.crt
cert /etc/openvpn/client/jumpbox.crt
key /etc/openvpn/client/jumpbox.key
remote-cert-tls server
cipher AES-256-CBC
verb 3
\"\"\"
    with open("/etc/openvpn/client/jumpbox.conf", "w") as f:
        f.write(client_config)
    
    # Start OpenVPN
    run_command("sudo systemctl enable openvpn-client@jumpbox")
    run_command("sudo systemctl start openvpn-client@jumpbox")
    
    # Output instructions
    print("\\nSetup complete! To access the jump box:")
    print("1. Connect to the VPN from your client using the same server details.")
    print("2. SSH to the jump box at 10.8.0.2 (e.g., ssh user@10.8.0.2)")
    print("Note: Ensure your client is also an OpenVPN client of the central server.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must run as root (use sudo).")
        exit(1)
    main()
"""
    with open("setup_jump_box_openvpn.py", "w") as f:
        f.write(jump_box_script.format(
            central_ip=central_ip,
            vpn_port=vpn_port,
            ca_cert=ca_cert,
            client_cert=client_cert,
            client_key=client_key
        ))
    run_command("chmod +x setup_jump_box_openvpn.py")

def main():
    print("=== Central Server OpenVPN Setup ===")
    
    # Prompt for user inputs
    central_ip = input("Enter the central server public IP address: ")
    vpn_port = input("Enter the OpenVPN port (e.g., 1194): ")
    
    # Install OpenVPN and Easy-RSA
    print("Installing OpenVPN and Easy-RSA if not present...")
    run_command("sudo apt update && sudo apt install -y openvpn easy-rsa")
    
    # Set up Easy-RSA and generate certificates
    setup_easyrsa()
    
    # Read generated certificates and keys
    with open("/etc/easy-rsa/pki/ca.crt", "r") as f:
        ca_cert = f.read()
    with open("/etc/easy-rsa/pki/issued/jumpbox.crt", "r") as f:
        client_cert = f.read()
    with open("/etc/easy-rsa/pki/private/jumpbox.key", "r") as f:
        client_key = f.read()
    
    # Write OpenVPN server config
    server_config = f"""port {vpn_port}
proto udp
dev tun
ca /etc/easy-rsa/pki/ca.crt
cert /etc/easy-rsa/pki/issued/server.crt
key /etc/easy-rsa/pki/private/server.key
dh /etc/easy-rsa/pki/dh.pem
server 10.8.0.0 255.255.255.0
ifconfig-pool-persist ipp.txt
keepalive 10 120
cipher AES-256-CBC
persist-key
persist-tun
verb 3
"""
    config_path = "/etc/openvpn/server/server.conf"
    os.makedirs("/etc/openvpn/server", exist_ok=True)
    with open(config_path, "w") as f:
        f.write(server_config)
    run_command(f"chmod 600 {config_path}")
    
    # Copy certificates to OpenVPN directory
    run_command("sudo cp /etc/easy-rsa/pki/ca.crt /etc/openvpn/server/")
    run_command("sudo cp /etc/easy-rsa/pki/issued/server.crt /etc/openvpn/server/")
    run_command("sudo cp /etc/easy-rsa/pki/private/server.key /etc/openvpn/server/")
    run_command("sudo cp /etc/easy-rsa/pki/dh.pem /etc/openvpn/server/")
    run_command("sudo chmod 600 /etc/openvpn/server/*")
    
    # Enable IP forwarding
    run_command("sudo sysctl -w net.ipv4.ip_forward=1")
    run_command("echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf")
    
    # Start OpenVPN
    run_command("sudo systemctl enable openvpn-server@server")
    run_command("sudo systemctl start openvpn-server@server")
    
    # Open firewall (if ufw is used)
    run_command(f"sudo ufw allow {vpn_port}/udp")
    
    # Generate the jump box script
    generate_jump_box_script(central_ip, vpn_port, ca_cert, client_cert, client_key)
    
    # Output instructions
    print("\nCentral Server setup complete!")
    print("Server VPN IP: 10.8.0.1")
    print("Jump Box VPN IP: 10.8.0.2")
    print("\nNext steps:")
    print("1. Transfer 'setup_jump_box_openvpn.py' to the jump box (e.g., via SCP or USB).")
    print("2. Run it on the jump box with: sudo python3 setup_jump_box_openvpn.py")
    print("3. To access, add your own OpenVPN client to the central server.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must run as root (use sudo).")
        exit(1)
    main()