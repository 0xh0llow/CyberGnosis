# Guida Installazione Completa

## Prerequisiti

### Hardware Minimo

**Server Centrale**:
- CPU: 4 cores
- RAM: 8 GB
- Disco: 50 GB SSD
- Network: 1 Gbps

**Host Monitorati** (per agent):
- CPU: 1 core disponibile
- RAM: 512 MB disponibili
- Disco: 1 GB
- Network: connettività HTTPS verso server centrale

### Software

- **SO**: Ubuntu 20.04/22.04 LTS (o Debian-based)
- **Docker**: 20.10+ 
- **Docker Compose**: 2.0+
- **Python**: 3.9+ (per agent standalone)
- **Git**: per clonare repository

---

## Parte 1: Setup Server Centrale con Docker

### Step 1.1: Clone Repository

```bash
git clone <repository-url>
cd linux-security-ai
```

### Step 1.2: Configurazione Environment

```bash
# Copia template
cp .env.template .env

# Edita .env con i tuoi valori
nano .env
```

**Variabili chiave da modificare**:

```env
# Database password (cambia!)
DB_PASSWORD=your_strong_password_here

# API tokens per agent
API_SECRET_KEY=<genera con: python -c "import secrets; print(secrets.token_urlsafe(32))">
AGENT_API_TOKEN=<genera con: python -c "import secrets; print(secrets.token_urlsafe(48))">

# Encryption key
ENCRYPTION_KEY=<genera con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# Dashboard secret
DASHBOARD_SECRET_KEY=<genera con: python -c "import secrets; print(secrets.token_urlsafe(32))">
```

### Step 1.3: Genera Certificati SSL (Self-Signed per Test)

```bash
./scripts/generate_certs.sh
```

Oppure manualmente:

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout certs/server-key.pem \
  -out certs/server-cert.pem \
  -days 365 \
  -subj "/CN=localhost"
```

### Step 1.4: Build e Avvio con Docker Compose

```bash
# Build immagini
docker-compose build

# Avvio servizi
docker-compose up -d

# Verifica status
docker-compose ps
```

**Output atteso**:

```
NAME                    STATUS         PORTS
security-postgres       Up (healthy)   5432
security-chroma         Up (healthy)   8001
security-central-server Up (healthy)   8000
security-dashboard      Up             8443, 8080
```

### Step 1.5: Verifica Installazione

```bash
# Test health endpoint
curl http://localhost:8000/health

# Risposta attesa:
# {"status":"healthy","timestamp":"2026-01-24T..."}

# Test dashboard (browser)
# https://localhost:8443
# (accetta certificato self-signed)
```

### Step 1.6: Inizializza Database

```bash
# Accedi al container server
docker exec -it security-central-server bash

# Run migrations (se implementate con Alembic)
# alembic upgrade head

# Oppure verifica creazione tabelle
python -c "from central_server.db.database import engine, Base; Base.metadata.create_all(engine); print('✓ Tables created')"

exit
```

---

## Parte 2: Setup Agent su Host Monitorati

### Opzione A: Installazione con Python (Nativa)

#### Step 2A.1: Installa Dipendenze Sistema

```bash
# Su Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    tcpdump \
    libmagic1

# Su RHEL/CentOS
sudo yum install -y \
    python3-pip \
    tcpdump \
    file-libs
```

#### Step 2A.2: Setup Virtual Environment

```bash
# Crea directory agent
mkdir -p /opt/security-agent
cd /opt/security-agent

# Clone solo agents/
git clone <repo-url> temp
cp -r temp/agents .
rm -rf temp

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Installa dipendenze
pip install -r agents/requirements.txt
```

#### Step 2A.3: Configurazione Agent

```bash
# Crea file config
nano agents/config.env
```

Contenuto:

```env
CENTRAL_SERVER_URL=https://<server-centrale-ip>:8000
API_TOKEN=<AGENT_API_TOKEN dal server>
HOST_ID=<hostname-univoco>  # es: web-server-01
COLLECTION_INTERVAL=30
NO_SSL_VERIFY=false  # true se certificato self-signed
```

#### Step 2A.4: Test Agent Performance

```bash
source venv/bin/activate
cd agents

# Test manuale
python performance/run_agent.py \
    --server-url https://<server-ip>:8000 \
    --api-token <YOUR_TOKEN> \
    --host-id test-host-001 \
    --no-ssl-verify  # se self-signed cert

# Ctrl+C per fermare dopo verifica
```

**Output atteso**:

```
INFO - Checking server connectivity...
INFO - ✓ Connected to central server
INFO - Starting enhanced performance monitoring for host: test-host-001
INFO - Training: 1/50 samples
...
INFO - ✓ Metrics sent successfully
```

#### Step 2A.5: Setup Systemd Service (Esecuzione Continua)

```bash
sudo nano /etc/systemd/system/security-agent-performance.service
```

Contenuto:

```ini
[Unit]
Description=Security Agent - Performance Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/security-agent/agents
Environment="PATH=/opt/security-agent/venv/bin"
ExecStart=/opt/security-agent/venv/bin/python performance/run_agent.py \
    --server-url https://<SERVER_IP>:8000 \
    --api-token <TOKEN> \
    --host-id %H \
    --no-ssl-verify
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Abilita e avvia:

```bash
sudo systemctl daemon-reload
sudo systemctl enable security-agent-performance
sudo systemctl start security-agent-performance

# Verifica status
sudo systemctl status security-agent-performance

# Log
sudo journalctl -u security-agent-performance -f
```

### Opzione B: Installazione con Docker (Host con Docker)

```bash
# Pull immagine agent
docker pull <registry>/security-agent:latest

# Oppure build locale
cd /path/to/repo
docker build -t security-agent -f docker/Dockerfile.agent .

# Run agent performance
docker run -d \
    --name security-agent-performance \
    --network host \
    --privileged \
    -v /proc:/host/proc:ro \
    -v /sys:/host/sys:ro \
    -e CENTRAL_SERVER_URL=https://<SERVER>:8000 \
    -e API_TOKEN=<TOKEN> \
    -e HOST_ID=$(hostname) \
    security-agent \
    python performance/run_agent.py \
        --server-url $CENTRAL_SERVER_URL \
        --api-token $API_TOKEN \
        --host-id $HOST_ID \
        --no-ssl-verify

# Verifica logs
docker logs -f security-agent-performance
```

---

## Parte 3: Configurazione Aggiuntiva

### Setup Malware Agent

```bash
# Installa YARA (opzionale)
sudo apt-get install -y yara

# Avvia agent malware
python agents/malware/run_agent.py \
    --server-url https://<SERVER>:8000 \
    --api-token <TOKEN> \
    --host-id $(hostname) \
    --scan-interval 3600  # Scan ogni ora
```

### Setup Code Scanner

```bash
# Installa bandit e semgrep
pip install bandit semgrep

# Scan codebase
python agents/code_scanner/scanner.py \
    --target /path/to/codebase \
    --server-url https://<SERVER>:8000 \
    --api-token <TOKEN> \
    --host-id $(hostname)
```

### Setup IDS

```bash
# Permessi per leggere auth.log
sudo usermod -a -G adm <agent-user>

# Avvia IDS
sudo python agents/ids/run_agent.py \
    --server-url https://<SERVER>:8000 \
    --api-token <TOKEN> \
    --host-id $(hostname)
```

---

## Parte 4: Verifica Sistema Completo

### Test End-to-End

#### 1. Genera Metriche Test

```bash
# Su host monitorato: stress CPU
stress-ng --cpu 4 --timeout 60s --metrics-brief

# Verifica alert anomalia su dashboard
```

#### 2. Test Ricerca Semantica

- Dashboard → Alerts
- Click su alert → "Find Similar Alerts"
- Verifica risultati da vector DB

#### 3. Test Code Scanning

```bash
# Crea file Python con vulnerabilità
cat > /tmp/test_vuln.py << 'EOF'
import os
password = "hardcoded_secret123"
user_input = input("Enter command: ")
os.system(user_input)  # Command injection!
EOF

# Scan
python agents/code_scanner/scanner.py \
    --target /tmp/test_vuln.py \
    --server-url https://<SERVER>:8000 \
    --api-token <TOKEN> \
    --host-id test
```

Verifica issue su dashboard → Code Issues.

---

## Troubleshooting Comune

### Problema: "Cannot connect to server"

**Cause**:
- Firewall blocca porta 8000/8443
- Server non in esecuzione
- URL errato

**Soluzioni**:
```bash
# Verifica server in ascolto
netstat -tlnp | grep 8000

# Test connettività
telnet <SERVER_IP> 8000

# Verifica firewall
sudo ufw status
sudo ufw allow 8000/tcp
sudo ufw allow 8443/tcp
```

### Problema: "Authentication failed"

**Causa**: Token errato o non configurato

**Soluzione**:
```bash
# Verifica token in .env server
cat .env | grep AGENT_API_TOKEN

# Usa stesso token in agent
```

### Problema: Agent non invia dati

**Debug**:
```bash
# Aumenta log level
export LOG_LEVEL=DEBUG
python performance/run_agent.py ...

# Verifica sanitizzazione non blocchi invio
# Check logs per "Security validation failed"
```

### Problema: Chroma DB non inizializza

**Soluzione**:
```bash
# Restart container Chroma
docker-compose restart chroma

# Verifica port mapping
docker-compose ps chroma

# Test diretto
curl http://localhost:8001/api/v1/heartbeat
```

### Problema: PostgreSQL connection error

**Soluzione**:
```bash
# Verifica password corretta
docker exec -it security-postgres psql -U securityuser -d security_monitoring

# Verifica connessione da container server
docker exec -it security-central-server python -c "from central_server.db.database import engine; engine.connect(); print('✓ Connected')"
```

---

## Manutenzione

### Backup Database

```bash
# PostgreSQL dump
docker exec security-postgres pg_dump -U securityuser security_monitoring > backup_$(date +%Y%m%d).sql

# Chroma data
docker cp security-chroma:/chroma/chroma ./chroma_backup
```

### Update Sistema

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Log Rotation

```bash
# Configure logrotate
sudo nano /etc/logrotate.d/security-agent

# Contenuto:
/opt/security-agent/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
```

---

## Disinstallazione

### Server Centrale

```bash
cd linux-security-ai

# Stop e rimuovi containers
docker-compose down -v  # -v rimuove volumes (dati!)

# Rimuovi immagini
docker images | grep security | awk '{print $3}' | xargs docker rmi

# Rimuovi directory
cd ..
rm -rf linux-security-ai
```

### Agent su Host

```bash
# Stop service
sudo systemctl stop security-agent-performance
sudo systemctl disable security-agent-performance
sudo rm /etc/systemd/system/security-agent-performance.service

# Rimuovi files
sudo rm -rf /opt/security-agent
```

---

## Configurazioni Avanzate

### High Availability (HA)

- Load balancer (HAProxy/Nginx) davanti a N istanze API
- PostgreSQL replication (primary + standby)
- Shared storage per Chroma (NFS/S3)

### Monitoring

```bash
# Prometheus metrics endpoint (già implementato)
curl http://localhost:8000/metrics
```

Integrazione Grafana dashboard (vedi `docs/monitoring/`).

---

## Supporto

- **Documentazione**: `docs/`
- **Issues**: GitHub Issues
- **Email**: [support-email]
- **Forum studenti**: [link]

✅ **Installazione completata!** Ora puoi:
1. Monitorare host con dashboard
2. Analizzare alert con vector search
3. Investigare incidenti
4. Estendere con nuovi moduli
