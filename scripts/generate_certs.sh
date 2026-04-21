#!/bin/bash
# Script per generare certificati SSL self-signed (ambiente didattico)

set -e

echo "================================================"
echo "Generazione Certificati SSL Self-Signed"
echo "================================================"
echo ""

# Create directory
mkdir -p certs

# Parametri
CERT_DAYS=365
COUNTRY="IT"
STATE="Italy"
CITY="Rome"
ORG="LinuxSecurityAI"
CN="localhost"

echo "Generazione chiave privata..."
openssl genrsa -out certs/server-key.pem 4096

echo "Generazione certificato..."
openssl req -new -x509 \
    -key certs/server-key.pem \
    -out certs/server-cert.pem \
    -days $CERT_DAYS \
    -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=$CN"

# Set permissions
chmod 600 certs/server-key.pem
chmod 644 certs/server-cert.pem

echo ""
echo "✓ Certificati generati in certs/"
echo "  - server-key.pem  (chiave privata)"
echo "  - server-cert.pem (certificato)"
echo ""
echo "⚠️  ATTENZIONE: Certificati self-signed per SOLO ambiente didattico!"
echo "    In produzione usare certificati da CA affidabile (Let's Encrypt, etc.)"
echo ""
echo "Per vedere dettagli certificato:"
echo "  openssl x509 -in certs/server-cert.pem -text -noout"
