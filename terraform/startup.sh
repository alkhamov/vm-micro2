#!/bin/bash
set -e

exec > /var/log/startup-script.log 2>&1

echo "=== Startup script started ==="

USER="${vm_user}"
TZ="${timezone}"

apt-get update -y

# Base packages
apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  git \
  make \
  sudo

# Docker install (official)
curl -fsSL https://get.docker.com | sh

systemctl enable docker
systemctl start docker

# Add user to docker group
usermod -aG docker "$USER"

# Docker Compose plugin
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.25.0/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Timezone
timedatectl set-timezone "$TZ"

echo "=== Startup script finished ==="
