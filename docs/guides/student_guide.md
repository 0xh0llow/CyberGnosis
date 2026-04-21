# 🎓 Guida per Studenti

## Benvenuto!

Questa guida ti accompagnerà attraverso l'utilizzo del sistema di monitoraggio cybersecurity per il tuo percorso didattico.

## 📋 Indice

1. [Prerequisiti](#prerequisiti)
2. [Setup Ambiente](#setup-ambiente)
3. [Come Seguire il Corso](#come-seguire-il-corso)
4. [Struttura Progetto](#struttura-progetto)
5. [Comandi Utili](#comandi-utili)
6. [Troubleshooting](#troubleshooting)
7. [Risorse Aggiuntive](#risorse-aggiuntive)

## Prerequisiti

### Conoscenze Richieste

- **Python**: Livello intermedio (classi, funzioni, moduli)
- **Linux**: Comandi base, gestione processi
- **Networking**: Protocolli TCP/IP, HTTP/HTTPS
- **Docker**: Concetti base (container, images, volumes)
- **Machine Learning**: Concetti introduttivi (opzionale ma consigliato)

### Software Necessario

```bash
# Sistema Operativo
- Linux (Ubuntu 20.04+ consigliato) o macOS
- Windows con WSL2 (alternativa)

# Software
- Python 3.9+
- Docker 24.0+
- Docker Compose 2.0+
- Git
- Editor di testo (VSCode consigliato)
```

### Installazione Rapida

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv docker.io docker-compose git

# macOS (con Homebrew)
brew install python@3.9 docker docker-compose git

# Verifica installazione
python3 --version
docker --version
docker-compose --version
```

## Setup Ambiente

### 1. Clone Repository

```bash
cd ~/projects
git clone <repository-url> cybersecurity-soc
cd cybersecurity-soc
```

### 2. Setup Python Environment

```bash
# Crea virtual environment
python3 -m venv venv

# Attiva environment
source venv/bin/activate  # Linux/macOS
# oppure
venv\Scripts\activate     # Windows

# Installa dipendenze
pip install -r requirements.txt
```

### 3. Configurazione

```bash
# Copia template configurazione
cp .env.template .env

# Modifica .env con i tuoi parametri
nano .env
```

**Variabili importanti da configurare:**

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=security_db
DB_USER=security_user
DB_PASSWORD=<genera-password-sicura>

# API
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=<genera-secret-key>

# Chroma DB
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

### 4. Avvia Sistema

```bash
# Opzione 1: Usa script automatico
./scripts/setup.sh

# Opzione 2: Manuale con Docker Compose
docker-compose up -d

# Verifica che tutti i container siano running
docker-compose ps

# Expected output:
# NAME                STATUS
# postgres            Up
# chroma              Up
# central_server      Up
# dashboard           Up
```

### 5. Verifica Installazione

```bash
# Test API
curl http://localhost:8000/api/health

# Expected: {"status":"healthy","database":"connected"}

# Test Dashboard
open http://localhost:3000  # oppure visita nel browser

# Test Chroma
curl http://localhost:8001/api/v1/heartbeat
```

## Come Seguire il Corso

### Struttura del Corso (6-8 Settimane)

Il corso è organizzato in **5 esercizi progressivi**:

#### 📖 Settimana 1-2: Setup & Anomaly Detection
- **Esercizio**: `docs/exercises/01_setup_and_first_analysis.md`
- **Obiettivi**: Installare sistema, capire architettura, primo alert
- **Deliverables**: Report di setup, screenshot dashboard, primo anomaly detection

#### 🦠 Settimana 2-3: Machine Learning per Malware
- **Esercizio**: `docs/exercises/02_malware_detection_ml.md`
- **Obiettivi**: Training modello ML, feature engineering, YARA rules
- **Deliverables**: Dataset 200+ samples, modello trained, report classificazione

#### 🔍 Settimana 3-4: Vector Search & Investigation
- **Esercizio**: `docs/exercises/03_vector_search_investigation.md`
- **Obiettivi**: Semantic search, incident investigation, knowledge base
- **Deliverables**: Query semantiche, incident report, KB articles

#### 🛡️ Settimana 4-5: IDS & Network Monitoring
- **Esercizio**: `docs/exercises/04_ids_network_monitoring.md`
- **Obiettivi**: Log analysis, network packet capture, attack detection
- **Deliverables**: IDS rules, PCAP samples, detection report

#### 🎯 Settimana 6-8: Final Project - SOC Completo
- **Esercizio**: `docs/exercises/05_final_project_soc.md`
- **Obiettivi**: Deploy multi-host, APT simulation, incident response
- **Deliverables**: Sistema completo, presentation, demo video

### Workflow Consigliato

**Per ogni esercizio:**

1. **📚 Lettura** (1-2 ore)
   - Leggi completamente l'esercizio
   - Studia i concetti teorici collegati
   - Guarda le risorse video consigliate

2. **💻 Implementazione** (4-6 ore)
   - Segui le istruzioni passo-passo
   - Testa ogni componente individualmente
   - Annota dubbi e problemi

3. **🧪 Testing** (1-2 ore)
   - Esegui tutti i test suggeriti
   - Verifica output attesi
   - Cattura screenshot per documentazione

4. **📝 Documentazione** (2-3 ore)
   - Completa il report richiesto
   - Rispondi alle domande teoriche
   - Prepara presentazione (se richiesta)

5. **🔄 Review** (1 ora)
   - Rivedi il codice scritto
   - Confronta con soluzioni alternative
   - Chiedi feedback al docente/mentor

### Metodo di Studio Suggerito

```
Lunedì:     Teoria + Setup (2h)
Martedì:    Coding parte 1 (3h)
Mercoledì:  Riposo / Consolidamento
Giovedì:    Coding parte 2 (3h)
Venerdì:    Testing + Debug (2h)
Weekend:    Documentazione + Review (3h)
```

## Struttura Progetto

### Directory Principali

```
cybersecurity-soc/
├── agents/                  # Agenti di monitoraggio
│   ├── common/             # Utilities condivise
│   ├── performance/        # Performance monitoring
│   ├── malware/            # Malware detection
│   ├── code_scanner/       # Code security scanning
│   └── ids/                # Intrusion detection
│
├── central_server/         # Backend API
│   ├── api/                # REST endpoints
│   ├── database/           # ORM models
│   ├── vector_search/      # Semantic search
│   └── security/           # Auth, RBAC, encryption
│
├── dashboard/              # Web UI
│   ├── templates/          # HTML Jinja2
│   ├── static/             # CSS, JS, images
│   └── app.py              # Flask application
│
├── docs/                   # Documentazione
│   ├── architecture/       # Design tecnico
│   ├── guides/             # Guide installazione
│   └── exercises/          # Esercizi studenti ⭐
│
├── tests/                  # Test suite
│   ├── unit/               # Test unitari
│   └── integration/        # Test integrazione
│
└── docker/                 # Docker configs
    └── ...
```

### File Importanti

| File | Descrizione |
|------|-------------|
| `README.md` | Overview progetto |
| `docker-compose.yml` | Orchestrazione container |
| `.env` | Configurazione ambiente |
| `requirements.txt` | Dipendenze Python |
| `setup.sh` | Script setup automatico |

## Comandi Utili

### Docker Management

```bash
# Avvia tutto
docker-compose up -d

# Ferma tutto
docker-compose down

# Restart singolo servizio
docker-compose restart central_server

# Visualizza logs
docker-compose logs -f central_server

# Accedi a container
docker-compose exec central_server bash

# Rebuild dopo modifiche
docker-compose up -d --build
```

### Agent Management

```bash
# Avvia performance agent
cd agents/performance
python3 run_agent.py --host-id my-laptop

# Avvia malware detector
cd agents/malware
python3 run_agent.py --scan-path /home/user/Downloads

# Avvia IDS
cd agents/ids
sudo python3 run_agent.py --interface eth0  # Richiede sudo per network
```

### Database Operations

```bash
# Accedi al database
docker-compose exec postgres psql -U security_user -d security_db

# Backup database
docker-compose exec postgres pg_dump -U security_user security_db > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U security_user security_db

# Reset database (ATTENZIONE: cancella tutti i dati!)
docker-compose down -v
docker-compose up -d
```

### Testing

```bash
# Attiva virtual environment
source venv/bin/activate

# Installa dipendenze test
pip install -r requirements-test.txt

# Run all tests
pytest

# Run solo unit tests
pytest tests/unit/ -v

# Run con coverage
pytest --cov=agents --cov=central_server --cov-report=html

# Run test specifico
pytest tests/unit/test_sanitizer.py::TestIPSanitization::test_ipv4_sanitization
```

### Monitoring & Debugging

```bash
# Monitora risorse Docker
docker stats

# Check API health
curl http://localhost:8000/api/health | jq

# Lista alert recenti
curl http://localhost:8000/api/alerts?limit=10 | jq

# Test vector search
curl -X POST http://localhost:8000/api/search/similar-alerts \
  -H "Content-Type: application/json" \
  -d '{"query": "high CPU usage", "top_k": 5}' | jq

# Monitora logs in tempo reale
tail -f central_server/logs/app.log
```

## Troubleshooting

### Problemi Comuni

#### ❌ Container non si avviano

**Sintomo**: `docker-compose up` fallisce

**Soluzione**:
```bash
# Verifica porte occupate
sudo lsof -i :8000
sudo lsof -i :5432

# Pulisci volumi
docker-compose down -v
docker system prune -a

# Riavvia Docker
sudo systemctl restart docker
```

#### ❌ Agent non riesce a connettersi all'API

**Sintomo**: `Connection refused` quando agent invia dati

**Soluzione**:
```bash
# Verifica API sia up
curl http://localhost:8000/api/health

# Check firewall
sudo ufw status
sudo ufw allow 8000

# Verifica .env
cat .env | grep API_HOST
# Deve essere 0.0.0.0, non localhost
```

#### ❌ Import errors Python

**Sintomo**: `ModuleNotFoundError`

**Soluzione**:
```bash
# Verifica virtual environment attivo
which python3
# Dovrebbe mostrare: /path/to/venv/bin/python3

# Reinstalla dipendenze
pip install -r requirements.txt --force-reinstall

# Aggiungi project root al PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### ❌ Database connection errors

**Sintomo**: `database "security_db" does not exist`

**Soluzione**:
```bash
# Accedi al container postgres
docker-compose exec postgres bash

# Crea database manualmente
psql -U security_user -c "CREATE DATABASE security_db;"

# Verifica connessione
psql -U security_user -d security_db -c "\dt"
```

#### ❌ Chroma DB non risponde

**Sintomo**: Vector search fallisce

**Soluzione**:
```bash
# Restart Chroma
docker-compose restart chroma

# Verifica logs
docker-compose logs chroma

# Test heartbeat
curl http://localhost:8001/api/v1/heartbeat
```

### Dove Chiedere Aiuto

1. **Forum del Corso**: Prima risorsa per domande
2. **GitHub Issues**: Bug tecnici del progetto
3. **Office Hours**: Slot settimanali con docente
4. **Slack/Discord**: Chat con altri studenti

## Risorse Aggiuntive

### Documentazione Tecnica

- **Architettura**: `docs/architecture/system_design.md`
- **API Reference**: http://localhost:8000/docs (quando sistema è running)
- **Database Schema**: `central_server/database/models.py`

### Tutorial & Learning

- [Python Asyncio Guide](https://docs.python.org/3/library/asyncio.html)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Scikit-learn ML](https://scikit-learn.org/stable/tutorial/)
- [YARA Rules Writing](https://yara.readthedocs.io/)

### Tools Consigliati

- **VSCode Extensions**:
  - Python
  - Docker
  - REST Client
  - YAML
  
- **Browser Extensions**:
  - JSON Formatter
  - React Developer Tools (per dashboard)

### Dataset & Resources

- **Malware Samples**: https://github.com/ytisf/theZoo (⚠️ Usa con cautela!)
- **Network PCAPs**: https://www.netresec.com/index.ashx?page=PcapFiles
- **Security Logs**: https://github.com/logpai/loghub

### Libri Consigliati

1. **"Black Hat Python"** - Justin Seitz (Security automation)
2. **"Practical Malware Analysis"** - Michael Sikorski
3. **"Applied Security Visualization"** - Raffael Marty
4. **"Building Machine Learning Systems with Python"** - Luis Pedro Coelho

---

## 🎯 Tips per il Successo

### ✅ DO
- Leggi **tutta** la documentazione prima di iniziare
- Fai **backup regolari** del tuo lavoro
- **Testa** ogni componente isolatamente
- **Documenta** mentre lavori, non alla fine
- Chiedi **aiuto** quando bloccato (dopo aver provato a risolvere)
- **Sperimenta** oltre i requisiti minimi

### ❌ DON'T
- Non copiare codice senza capirlo
- Non saltare i test
- Non aspettare l'ultimo giorno per gli esercizi
- Non usare malware reali senza sandbox appropriato
- Non condividere le soluzioni complete (ok discutere approcci)

---

## 📧 Contatti

- **Docente**: [email]
- **Teaching Assistant**: [email]
- **Forum**: [link]
- **Office Hours**: Giovedì 14:00-16:00

---

**Buon lavoro e buon apprendimento! 🚀**
