#!/bin/bash
set -euo pipefail

echo "============================================="
echo "  InternetShop PRO — Security Audit"
echo "============================================="

ISSUES=0

echo ""
echo "=== [1/8] Server packages ==="
if command -v apt >/dev/null 2>&1; then
    UPDATES=$(apt list --upgradable 2>/dev/null | grep -c upgradable || true)
    echo "  Upgradable packages: $UPDATES"
    [ "$UPDATES" -gt 0 ] && echo "  ⚠ WARNING: Updates available" && ISSUES=$((ISSUES+1))
else
    echo "  apt not found, skipping"
fi

echo ""
echo "=== [2/8] SSH security ==="
SSHD_CONFIG="/etc/ssh/sshd_config"
if [ -f "$SSHD_CONFIG" ]; then
    ROOT_LOGIN=$(grep -E "^PermitRootLogin" "$SSHD_CONFIG" | awk '{print $2}' || echo "unknown")
    echo "  PermitRootLogin: $ROOT_LOGIN"
    if [ "$ROOT_LOGIN" = "yes" ]; then
        echo "  ⚠ WARNING: Root login enabled"
        ISSUES=$((ISSUES+1))
    fi

    PASS_AUTH=$(grep -E "^PasswordAuthentication" "$SSHD_CONFIG" | awk '{print $2}' || echo "unknown")
    echo "  PasswordAuthentication: $PASS_AUTH"
    if [ "$PASS_AUTH" = "yes" ]; then
        echo "  ⚠ WARNING: Password auth enabled (prefer key-only)"
        ISSUES=$((ISSUES+1))
    fi
else
    echo "  sshd_config not found"
fi

echo ""
echo "=== [3/8] Firewall (UFW) ==="
if command -v ufw >/dev/null 2>&1; then
    UFW_STATUS=$(ufw status 2>/dev/null | head -1 || echo "unknown")
    echo "  Status: $UFW_STATUS"
    if echo "$UFW_STATUS" | grep -q "inactive"; then
        echo "  ⚠ WARNING: Firewall inactive"
        ISSUES=$((ISSUES+1))
    fi
else
    echo "  ufw not found"
fi

echo ""
echo "=== [4/8] Open ports ==="
OPEN_PORTS=$(ss -tlnp 2>/dev/null | grep LISTEN | awk '{print $4}' | sort -u || echo "unknown")
echo "  Listening:"
echo "$OPEN_PORTS" | sed 's/^/    /'

echo ""
echo "=== [5/8] Docker secrets exposure ==="
for compose in docker-compose.yml docker-compose.prod.yml; do
    if [ -f "$compose" ]; then
        SECRETS=$(grep -c "password\|secret\|token\|key" "$compose" 2>/dev/null || true)
        echo "  $compose: $SECRETS potential secrets"
        if [ "$SECRETS" -gt 0 ]; then
            echo "  ⚠ WARNING: Check for hardcoded secrets in $compose"
            ISSUES=$((ISSUES+1))
        fi
    fi
done

echo ""
echo "=== [6/8] .env files exposure ==="
for env_file in .env .env.docker .env.prod; do
    if [ -f "$env_file" ]; then
        echo "  ⚠ WARNING: $env_file exists — ensure it is in .gitignore"
        ISSUES=$((ISSUES+1))
    fi
done

echo ""
echo "=== [7/8] Docker running containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  Docker not running"

echo ""
echo "=== [8/8] Failed login attempts ==="
if [ -f /var/log/auth.log ]; then
    FAILED=$(grep -c "Failed password" /var/log/auth.log 2>/dev/null || echo "0")
    echo "  Failed attempts: $FAILED"
    if [ "$FAILED" -gt 100 ]; then
        echo "  ⚠ WARNING: High failed login attempts"
        ISSUES=$((ISSUES+1))
    fi
elif [ -f /var/log/secure ]; then
    FAILED=$(grep -c "Failed password" /var/log/secure 2>/dev/null || echo "0")
    echo "  Failed attempts: $FAILED"
else
    echo "  No auth log found"
fi

echo ""
echo "============================================="
if [ $ISSUES -eq 0 ]; then
    echo "  ✅ Security audit passed!"
else
    echo "  ⚠ $ISSUES issue(s) found"
fi
echo "============================================="
