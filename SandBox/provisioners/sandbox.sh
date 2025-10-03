#!/bin/bash

# Set hostname
sudo hostnamectl set-hostname sandbox

# Update package lists (without upgrade)
sudo apt-get update -y

# Install basic dependencies
sudo apt-get install -y python3 python3-pip python3-venv curl gnupg lsb-release

# Setup Docker
sudo mkdir -p /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker vagrant

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Setup Python environment
mkdir -p /home/vagrant/devsepops
cd /home/vagrant/devsepops
python3 -m venv venv

# Install basic Python packages for our project
source /home/vagrant/devsepops/venv/bin/activate
pip install --upgrade pip

# Install project requirements or basic packages
if [ -f "/home/vagrant/devsepops/requirements.txt" ]; then
    pip install -r /home/vagrant/devsepops/requirements.txt
else
    echo "Installing default Python packages..."
    pip install fastapi uvicorn sqlalchemy alembic python-jose[cryptography] passlib[bcrypt] python-multipart requests psycopg2-binary
fi

# Fix permissions
sudo chown -R vagrant:vagrant /home/vagrant/devsepops

echo "✅ Provisioning completed successfully!"
echo "🐍 Python virtual environment: /home/vagrant/devsepops/venv"
echo "🐳 Docker installed and configured"
