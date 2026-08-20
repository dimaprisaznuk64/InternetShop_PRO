#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — SSH Hardening ==="

SSHD_CONFIG="/etc/ssh/sshd_config"
BACKUP="${SSHD_CONFIG}.bak.$(date +%Y%m%d)"

echo "[1/4] Backup current SSH config..."
cp "$SSHD_CONFIG" "$BACKUP"

echo "[2/4] Hardening SSH config..."
cat > /etc/ssh/sshd_config.d/hardening.conf << 'EOF'
# Disable root login
PermitRootLogin no

# Disable password auth (use keys only)
PasswordAuthentication no
ChallengeResponseAuthentication no

# Limit SSH to specific users
AllowUsers internetshop

# Use SSH protocol 2
Protocol 2

# Disable X11 forwarding
X11Forwarding no

# Set login grace time
LoginGraceTime 30

# Max auth tries
MaxAuthTries 3

# Client alive interval (timeout idle sessions)
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

echo "[3/4] Validate SSH config..."
sshd -t

echo "[4/4] Restart SSH..."
systemctl restart sshd

echo "=== SSH hardened! ==="
echo "Changes: no root login, key-only auth, limited users"
