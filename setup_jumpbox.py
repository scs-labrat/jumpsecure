import os
import subprocess
import getpass

def run_command(command):
    """Run a shell command and handle errors."""
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        exit(1)

def main():
    print("=== Jump Box Reverse SSH Setup ===")
    
    # Prompt for user inputs
    jump_user = input("Enter the username on the jump box (e.g., pi): ")
    central_ip = input("Enter the central server IP address: ")
    tunnel_port = input("Enter the tunnel port on the central server (e.g., 2222): ")
    ssh_key_path = input("Enter path to store the central server’s private key (e.g., /home/{}/central_key): ".format(jump_user))
    
    # Default SSH key path if empty
    if not ssh_key_path:
        ssh_key_path = f"/home/{jump_user}/central_key"
    
    # Ensure SSH client is installed
    print("Installing OpenSSH client if not present...")
    run_command("sudo apt update && sudo apt install -y openssh-client")
    
    # Create .ssh directory and set permissions
    ssh_dir = f"/home/{jump_user}/.ssh"
    os.makedirs(ssh_dir, exist_ok=True)
    run_command(f"chmod 700 {ssh_dir}")
    run_command(f"chown {jump_user}:{jump_user} {ssh_dir}")
    
    # Prompt for private key (manual paste since file transfer isn’t scripted)
    print("\nPaste the private key from the central server (end with Ctrl+D or Ctrl+Z):")
    private_key = ""
    while True:
        try:
            line = input()
            private_key += line + "\n"
        except EOFError:
            break
    
    # Write the private key to file
    with open(ssh_key_path, "w") as f:
        f.write(private_key)
    run_command(f"chmod 600 {ssh_key_path}")
    run_command(f"chown {jump_user}:{jump_user} {ssh_key_path}")
    
    # Test the connection
    print("Testing SSH connection...")
    test_cmd = f"ssh -i {ssh_key_path} -p {tunnel_port} {jump_user}@localhost"
    print(f"After connecting to {central_ip}, run: {test_cmd}")
    
    # Create systemd service for reverse SSH
    service_file = "/etc/systemd/system/reverse-ssh.service"
    service_content = f"""[Unit]
Description=Reverse SSH Tunnel to Central Server
After=network-online.target

[Service]
ExecStart=/usr/bin/ssh -i {ssh_key_path} -R {tunnel_port}:localhost:22 {central_user}@{central_ip} -N -o ServerAliveInterval=60
Restart=always
User={jump_user}

[Install]
WantedBy=multi-user.target
"""
    with open(service_file, "w") as f:
        f.write(service_content)
    
    # Enable and start the service
    run_command("sudo systemctl daemon-reload")
    run_command("sudo systemctl enable reverse-ssh.service")
    run_command("sudo systemctl start reverse-ssh.service")
    
    # Output instructions
    print("\nSetup complete! To access the jump box:")
    print(f"1. SSH to the central server: ssh {central_user}@{central_ip}")
    print(f"2. Then connect to jump box: ssh -p {tunnel_port} {jump_user}@localhost")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must run as root (use sudo).")
        exit(1)
    main()