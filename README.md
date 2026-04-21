# 🛡️ Linux Security AI - Sistema Centralizzato di Monitoraggio e Sicurezza

## 📚 Progetto Didattico Completo per Cybersecurity

Sistema completo di Security Operations Center (SOC) con monitoraggio distribuito, rilevamento malware, intrusion detection e analisi semantica basata su AI/ML e database vettoriali.

**✅ Progetto Completato al 100%** - Pronto per uso didattico (6-8 settimane di corso)

---

## 🎯 Obiettivi Didattici

Questo progetto è pensato per **studenti di informatica / cybersecurity** (livello intermedio–avanzato) e copre un arco di **6–8 settimane** di corso pratico.

Al termine, lo studente sarà in grado di:
- ✅ Progettare un sistema di monitoring distribuito con architettura microservizi
- ✅ Implementare algoritmi di anomaly detection con Machine Learning (Isolation Forest)
- ✅ Utilizzare database vettoriali (Chroma) per ricerca semantica
- ✅ Creare sistemi IDS (log-based e network-based) con detection rules
- ✅ Condurre investigation di sicurezza end-to-end con correlation
- ✅ Applicare best practice di privacy by design e data minimization

### 📚 Per Iniziare

- **👨‍🎓 Studenti**: Leggi [`docs/guides/student_guide.md`](docs/guides/student_guide.md)
- **👨‍🏫 Docenti**: Leggi [`docs/guides/instructor_guide.md`](docs/guides/instructor_guide.md)
- **📖 Esercizi**: Inizia da [`docs/exercises/README.md`](docs/exercises/README.md)

---

## 🏗️ Architettura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                  HOST LINUX MONITORATI (Agents)             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Performance│  │ Malware  │  │   Code   │  │   IDS    │   │
│  │  Monitor  │  │ Detector │  │ Scanner  │  │(Log+Net) │   │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘   │
└────────┼─────────────┼─────────────┼─────────────┼─────────┘
         │             │             │             │
         │       HTTPS/TLS + JWT Auth + Sanitization         
         └─────────────┼─────────────┼─────────────┘
                       ▼             ▼
         ┌─────────────────────────────────────────────────┐
         │         SERVER CENTRALE (Docker Compose)        │
         │  ┌──────────────┐  ┌─────────────────────────┐ │
         │  │   FastAPI    │  │  PostgreSQL 15 + Alembic│ │
         │  │   REST API   │  │  (Metrics, Alerts, Logs)│ │
         │  │  (10+ routes)│  │   + SQLAlchemy ORM      │ │
         │  └──────┬───────┘  └──────┬──────────────────┘ │
         │         │                  │                     │
         │         │  ┌───────────────┴───────────────┐    │
         │         └──│  Chroma Vector Database       │    │
         │            │  (Sentence-Transformers)      │    │
         │            │  384-dim embeddings           │    │
         │            └───────────────────────────────┘    │
         │                                                  │
         │  Security Layer: RBAC + Audit + Encryption      │
         └─────────────────┬────────────────────────────────┘
                           │
                           ▼
         ┌──────────────────────────────────────────────────┐
         │    DASHBOARD WEB (Flask + Bootstrap 5)           │
         │  • Overview: Stats cards + real-time charts      │
         │  • Alerts: List, filters, detail, status update  │
         │  • Hosts: Monitoring, metrics timeline           │
         │  • Search: Semantic vector search                │
         │  • Reports: Weekly/monthly summaries             │
         └──────────────────────────────────────────────────┘
```

---

## 🔧 Moduli Implementati

### 1️⃣ Performance Monitor Agent
- **Monitoraggio**: CPU, RAM, Disco, I/O rete, processi
- **Anomaly Detection**: Isolation Forest (scikit-learn)
- **Features**: 10+ metriche con trend analysis
- **Privacy**: Aggregazione dati, sanitizzazione processi
- **File**: `agents/performance/`

### 2️⃣ Malware Detection Agent
- **Analisi Statica**: Hash (SHA256), entropia, magic bytes
- **YARA Rules**: Custom rule engine per pattern matching
- **ML Classifier**: Random Forest (200+ features)
- **Behavioral Analysis**: Network, file ops, privilege escalation
- **Privacy**: Path hashing, no file content storage
- **File**: `agents/malware/`

### 3️⃣ Code Scanner Agent
- **SAST Tools**: Bandit (Python), Semgrep (multi-language)
- **Detections**: Command injection, SQL injection, XSS, hardcoded secrets
- **Vector Storage**: Code snippets for similarity search
- **Privacy**: Code sanitization, tokenization
- **File**: `agents/code_scanner/`

### 4️⃣ Intrusion Detection System (IDS)
- **Log-Based**: SSH brute force, login anomalies, command injection
- **Network-Based**: Port scan, SYN flood, packet analysis (Scapy)
- **ML Detection**: Anomalous network behavior
- **Privacy**: IP/username hashing
- **File**: `agents/ids/`

### 5️⃣ Central Server (API Backend)
- **Framework**: FastAPI (async) con 10+ REST endpoints
- **Database**: PostgreSQL 15 + SQLAlchemy ORM
- **Vector Search**: Chroma DB con sentence-transformers
- **Security**: JWT auth, RBAC (3 roles), audit logging
- **API Docs**: Swagger UI + ReDoc auto-generated
- **File**: `central_server/`

### 6️⃣ Dashboard Web UI
- **Framework**: Flask + Jinja2 templates
- **Design**: Bootstrap 5 responsive
- **Charts**: Chart.js for real-time visualization
- **Features**: 
  - Overview dashboard con 4 stat cards
  - Alert management (list, filters, detail, update)
  - Host monitoring con metrics timeline
  - Semantic search con vector similarity
  - Reports generation (weekly/monthly)
- **File**: `dashboard/`

### 7️⃣ Security & Privacy Layer
- **Sanitization**: IP, MAC, username, path hashing (SHA-256)
- **Encryption**: AES-256 (Fernet) + HMAC integrity
- **RBAC**: Admin, Security Analyst, Viewer roles
- **Audit**: Structured logging per compliance
- **TLS/SSL**: Certificate generation scripts
- **File**: `central_server/security/`, `agents/common/`

---

## 🚀 Quick Start

### 🧪 Demo distribuita (server remoto + client)

Per una demo realistica su più macchine:

1. **Macchina server remota** (PostgreSQL + Chroma + API + Dashboard):  
   usa `docker-compose.server.yml`.
2. **Macchine client** (agent):  
   usa `docker-compose.client.yml`.

Esempio rapido:

```bash
# SERVER (macchina remota)
cp .env.server.example .env.server
docker compose -f docker-compose.server.yml --env-file .env.server up -d --build

# CLIENT (ogni host monitorato)
cp .env.client.example .env.client
docker compose -f docker-compose.client.yml --env-file .env.client up -d

# Scan codice on-demand dal client
docker compose -f docker-compose.client.yml --env-file .env.client --profile scan run --rm code_scanner
```

#### Variabili da impostare (server)

Minime obbligatorie in `.env.server`:
- `API_TOKEN`: token condiviso usato da agent e dashboard.
- `ENCRYPTION_KEY`: chiave Fernet valida.

Raccomandate:
- `POSTGRES_PASSWORD`, `API_SECRET_KEY`, `JWT_SECRET`, `FLASK_SECRET_KEY`.
- Porte pubbliche (`API_PUBLIC_PORT`, `DASHBOARD_HTTP_PORT`, `DASHBOARD_HTTPS_PORT`).

#### Variabili da impostare (client)

Minime obbligatorie in `.env.client`:
- `CENTRAL_SERVER_URL` (es. `http://<SERVER_IP>:8000`)
- `API_TOKEN` (stesso valore del server)
- `HOST_ID` (identificativo univoco del client)

Opzionali per profili:
- Code scanner: `SCAN_TARGET`, `SCAN_TARGET_HOST`
- Malware: `MALWARE_SCAN_PATH`, `MALWARE_SCAN_INTERVAL`
- IDS: `IDS_INTERVAL`, `IDS_LOG_FILE`, `IDS_LOG_FILE_HOST`

#### Comandi passo-passo

```bash
# 1) SERVER REMOTO
cp .env.server.example .env.server
# modifica .env.server con token/segreti reali
docker compose -f docker-compose.server.yml --env-file .env.server up -d --build

# 2) CLIENT - Avvio stack agent completo (performance + malware + ids)
cp .env.client.example .env.client
# modifica .env.client con CENTRAL_SERVER_URL/API_TOKEN/HOST_ID
docker compose -f docker-compose.client.yml --env-file .env.client up -d

# 3) CLIENT - Code scan on-demand
docker compose -f docker-compose.client.yml --env-file .env.client --profile scan run --rm code_scanner
```

### Prerequisiti

```bash
# Sistema
Ubuntu 20.04+ / macOS / Windows WSL2

# Software
Python 3.9+
Docker 24.0+
Docker Compose 2.0+
Git
```

### 1. Clone & Setup

```bash
# Clone repository
git clone <repo-url> cybersecurity-soc
cd cybersecurity-soc

# Copia configurazione
cp .env.template .env

# Modifica .env con le tue impostazioni
nano .env
```

### 2. Avvio Automatico

```bash
# Script setup completo (genera certificati, DB, container)
chmod +x scripts/setup.sh
./scripts/setup.sh

# Verifica stato
docker-compose ps

# Expected output:
# NAME            STATUS
# postgres        Up
# chroma          Up  
# central_server  Up
# dashboard       Up
```

### 3. Accesso Servizi

```bash
# Dashboard Web
http://localhost:3000

# API Swagger UI
http://localhost:8000/docs

# Chroma DB
http://localhost:8001

# Health check
curl http://localhost:8000/api/health
```

### 4. Primo Agent

```bash
# Attiva virtual environment
python3 -m venv venv
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Avvia performance agent
cd agents/performance
python3 run_agent.py --host-id my-laptop --interval 60
```

---

## 🎓 Percorso Didattico (5 Esercizi)

Il progetto include **5 esercizi progressivi** per un corso completo:

| # | Titolo | Settimane | Difficoltà | File |
|---|--------|-----------|------------|------|
| 1 | **Setup & Anomaly Detection** | 1-2 | ⭐ Beginner | [`01_setup_and_first_analysis.md`](docs/exercises/01_setup_and_first_analysis.md) |
| 2 | **Machine Learning per Malware** | 2-3 | ⭐⭐ Intermediate | [`02_malware_detection_ml.md`](docs/exercises/02_malware_detection_ml.md) |
| 3 | **Vector Search & Investigation** | 3-4 | ⭐⭐ Intermediate | [`03_vector_search_investigation.md`](docs/exercises/03_vector_search_investigation.md) |
| 4 | **IDS & Network Monitoring** | 4-5 | ⭐⭐⭐ Advanced | [`04_ids_network_monitoring.md`](docs/exercises/04_ids_network_monitoring.md) |
| 5 | **Final Project - SOC Completo** | 6-8 | ⭐⭐⭐ Advanced | [`05_final_project_soc.md`](docs/exercises/05_final_project_soc.md) |

**Inizia qui**: [`docs/exercises/README.md`](docs/exercises/README.md)

### Deliverables Finali

Ogni studente completerà:
- ✅ Sistema SOC multi-host funzionante (Docker)
- ✅ 3+ modelli ML trained (anomaly, malware, IDS)
- ✅ Dashboard web con visualizzazioni
- ✅ Investigation report di incident simulato (10-15 pagine)
- ✅ Executive presentation (15 min)
- ✅ Demo video (5 min)

---

## 📖 Documentazione

### 📚 Guide Principali
- **👨‍🎓 Guida Studenti**: [`docs/guides/student_guide.md`](docs/guides/student_guide.md) - Setup, workflow, troubleshooting
- **👨‍🏫 Guida Docenti**: [`docs/guides/instructor_guide.md`](docs/guides/instructor_guide.md) - Lezioni, valutazione, soluzioni
- **📋 Indice Esercizi**: [`docs/exercises/README.md`](docs/exercises/README.md) - Percorso 6-8 settimane

### 🔧 Documentazione Tecnica
- **🏗️ Architettura**: [`docs/architecture/system_design.md`](docs/architecture/system_design.md) - Design pattern, decisioni
- **⚙️ Installazione**: [`docs/guides/installation.md`](docs/guides/installation.md) - Setup dettagliato passo-passo
- **🔌 API Reference**: [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) - Tutti gli endpoint REST
- **📊 Swagger UI**: http://localhost:8000/docs (auto-generata quando running)

---

## 🧪 Testing

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run solo unit tests
pytest tests/unit/ -v

# Run solo integration tests (richiede Docker running)
pytest tests/integration/ -v

# Run with coverage
pytest --cov=agents --cov=central_server --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Suite Completa

- **Unit Tests** (`tests/unit/`):
  - `test_sanitizer.py` - 50+ test per privacy & data sanitization
  - `test_anomaly_detector.py` - 30+ test per ML anomaly detection
  
- **Integration Tests** (`tests/integration/`):
  - `test_system_integration.py` - End-to-end workflows completi

**Coverage Target**: >80% per agenti e central server

---

## 🐳 Docker Compose Services

```yaml
services:
  postgres:       # Database principale (metriche, alert, logs)
    Port: 5432
    
  chroma:         # Vector database (semantic search)
    Port: 8001
    
  central_server: # FastAPI backend
    Port: 8000
    Depends: postgres, chroma
    
  dashboard:      # Flask web UI
    Port: 3000
    Depends: central_server
```

### Comandi Utili

```bash
# Avvia tutto
docker-compose up -d

# Stop tutto
docker-compose down

# Restart singolo servizio
docker-compose restart central_server

# Visualizza logs
docker-compose logs -f

# Rebuild dopo modifiche
docker-compose up -d --build

# Reset completo (elimina dati!)
docker-compose down -v
```

---

## 📊 Stack Tecnologico

### Backend
- **Python 3.9+**: Linguaggio principale
- **FastAPI**: Async REST API framework
- **Flask**: Web dashboard framework
- **SQLAlchemy**: ORM per PostgreSQL
- **Alembic**: Database migrations

### Database
- **PostgreSQL 15**: Relational database
- **Chroma DB**: Vector database per semantic search

### Machine Learning
- **scikit-learn**: Isolation Forest, Random Forest
- **sentence-transformers**: Text embeddings (all-MiniLM-L6-v2)
- **numpy/pandas**: Data processing

### Security
- **cryptography**: AES encryption (Fernet)
- **python-magic**: File type detection
- **YARA**: Pattern matching malware
- **scapy**: Network packet analysis

### Frontend
- **Bootstrap 5**: Responsive CSS framework
- **Chart.js**: Interactive charts
- **Jinja2**: Template engine

### DevOps
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **pytest**: Testing framework
- **GitHub Actions**: CI/CD (configurabile)

---

## 🔒 Sicurezza e Privacy

### Privacy by Design

1. **Data Minimization**: Solo dati necessari raccolti
2. **Sanitization**: IP, MAC, username hashati (SHA-256)
3. **Encryption**: AES-256 per dati sensibili
4. **Audit Logging**: Tracciamento accessi per compliance
5. **RBAC**: 3 livelli (Admin, Security, Viewer)

### Threat Model

- ✅ Protezione contro data leakage
- ✅ Autenticazione JWT token-based
- ✅ TLS/SSL per comunicazioni
- ✅ Input validation & sanitization
- ✅ SQL injection prevention (parametrized queries)

---

## ✅ Status Implementazione

- [x] **Infrastruttura Docker** (PostgreSQL, Chroma DB)
- [x] **Agent Performance Monitor** + Anomaly Detection (Isolation Forest)
- [x] **Agent Malware Detection** (ML + YARA)
- [x] **Agent Code Scanner** (Bandit, Semgrep)
- [x] **Agent IDS** (Log-based + Network-based)
- [x] **Central Server** (FastAPI + Database + Security Layer)
- [x] **Vector Search** (Chroma + Sentence Transformers)
- [x] **Dashboard Web** (Flask + Bootstrap 5 + Chart.js) ✨
- [x] **Test Suite** (pytest - Unit & Integration) ✨
- [x] **Documentazione Completa** (Studenti + Docenti + API) ✨
- [x] **5 Esercizi Pratici** (6-8 settimane di corso) ✨

**🎉 Progetto Completato al 100%!** Pronto per deployment in ambiente didattico.

---

## 🤝 Contributi

Contributi benvenuti! Per contribuire:

1. Fork del repository
2. Crea feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push al branch (`git push origin feature/amazing-feature`)
5. Apri Pull Request

### Aree dove servono contributi:
- 🆕 Nuovi agent types (vulnerability scanner, container security)
- 🤖 Additional ML models (XGBoost, Neural Networks)
- 🎨 Dashboard UI/UX enhancements
- 🧪 Test coverage expansion (target >90%)
- 🌍 Traduzioni documentazione (EN, ES, FR)
- 📚 Tutorial video / blog posts

---

## 📞 Support

### Per Studenti
- 📖 **Documentazione**: Controlla [`docs/guides/student_guide.md`](docs/guides/student_guide.md)
- 🐛 **Bug**: Apri issue su GitHub con label `bug`
- 💡 **Domande**: Usa GitHub Discussions
- 📧 **Email**: [student-support@example.com]

### Per Docenti
- 👨‍🏫 **Guida**: Leggi [`docs/guides/instructor_guide.md`](docs/guides/instructor_guide.md)
- 🔑 **Soluzioni**: Richiedi accesso a repository privato soluzioni
- 💬 **Community**: Slack channel #instructors
- 📧 **Email**: [instructor-support@example.com]

---

## 📜 License

MIT License - Vedi [LICENSE](LICENSE) per dettagli.

**Uso Educativo**: Free per università, scuole, bootcamp.
**Uso Commerciale**: Contatta per licensing commerciale.

---

## 🌟 Credits

Sviluppato per scopi didattici in ambito cybersecurity education.

**Autori**: [Il tuo nome]
**Università**: [La tua università]
**Corso**: Advanced Cybersecurity & AI Applications

### Acknowledgments
- Scikit-learn team per ML algorithms
- Chroma team per vector database
- FastAPI & Flask communities
- Open source security tools (Bandit, Semgrep, YARA)

---

## 📈 Roadmap Future

### v2.0 (Q3 2026)
- [ ] Kubernetes deployment templates
- [ ] Grafana/Prometheus integration
- [ ] Advanced ML models (Deep Learning)
- [ ] Multi-tenant support
- [ ] Real-time collaboration features

### v2.1 (Q4 2026)
- [ ] Mobile dashboard app (React Native)
- [ ] AI-powered remediation suggestions
- [ ] Threat intelligence feed integration
- [ ] Automated penetration testing module

---

**⭐ Se trovi utile questo progetto, lascia una stella su GitHub!**

**🚀 Happy Learning & Stay Secure!**
