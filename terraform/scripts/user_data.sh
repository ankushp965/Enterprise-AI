#!/bin/bash
set -e

# Update and upgrade system packages
apt-get update -y
apt-get upgrade -y

# Install essential dependencies
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    unzip \
    wget

# 1. Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm -f get-docker.sh

# 2. Add ubuntu user to docker group (no sudo needed for docker)
usermod -aG docker ubuntu

# 3. Install Docker Compose plugin
apt-get update -y
apt-get install -y docker-compose-plugin

# Enable and start Docker service
systemctl enable docker
systemctl start docker

# 4. Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip

# 5. Install AWS CloudWatch Agent (Prepping for Point 5 Service Health Monitoring)
wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb
rm -f amazon-cloudwatch-agent.deb

# Create application workspace
mkdir -p /home/ubuntu/enterprise-ai
chown -R ubuntu:ubuntu /home/ubuntu/enterprise-ai

echo "Enterprise AI EC2 Bootstrap Completed Successfully at $(date)" >> /var/log/user-data-bootstrap.log