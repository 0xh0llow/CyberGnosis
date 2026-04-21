# Architettura Sistema - Linux Security AI

## Panoramica

Sistema di monitoraggio sicurezza centralizzato basato su:
- **Agenti distribuiti** su server Linux monitorati
- **Server centrale** con API REST, database relazionale e vettoriale
- **Dashboard web** per visualizzazione e analisi

---

## Componenti Principali

### 1. Agenti (Client-Side)

Installati su ogni server Linux da monitorare. Raccolgono dati, li sanitizzano e inviano al server centrale.

#### Agent Performance Monitor
- **Tecnologia**: Python, psutil, scikit-learn
- **Funzioni**:
  - Raccolta metriche CPU, RAM, disco, network
  - Anomaly detection con Isolation Forest
  - Suggerimenti ottimizzazione
- **Privacy**: Solo statistiche aggregate, no cmdline/env vars
- **Output**: JSON sanitizzato via HTTPS

#### Agent Malware Detector
- **Tecnologia**: Python, python-magic, YARA
- **Funzioni**:
  - Analisi statica file (hash, entropia, tipo)
  - Analisi comportamentale processi
  - Classificatore ML (Random Forest)
- **Privacy**: Path anonimizzati (hash), no contenuti file
- **Output**: Alert con severity e confidence score

#### Agent Code Scanner
- **Tecnologia**: bandit, semgrep
- **Funzioni**:
  - Scan vulnerabilità Python/multi-language
  - Detection injection, secrets, unsafe code
  - Snippet sanitizzati per vector DB
- **Privacy**: Codice troncato (max 500 char), path hashati
- **Output**: Issue strutturate con metadati

#### Agent IDS
- **Tecnologia**: Python, log parsing, scapy
- **Funzioni**:
  - Log-based: brute force SSH, login anomali
  - Network-based: port scan, DoS detection
  - Pattern matching + ML anomaly detection
- **Privacy**: IP pseudoanonimizzati, username masked
- **Output**: Alert IDS con evidenze

---

### 2. Server Centrale

#### API REST (FastAPI)
- **Endpoints principali**:
  - `POST /api/metrics` - Riceve metriche performance
  - `POST /api/alerts` - Riceve alert
  - `POST /api/code-snippets` - Riceve snippet codice
  - `GET  /api/alerts` - Lista alert (con filtri)
  - `POST /api/search/similar-alerts` - Ricerca semantica
  - `POST /api/search/similar-snippets` - Ricerca codice simile
  - `GET  /api/stats` - Statistiche globali

- **Autenticazione**: 
  - Bearer token per agent
  - HMAC signature per integrità
  - HTTPS/TLS obbligatorio

#### Database Relazionale (PostgreSQL)
- **Tabelle**:
  - `metrics`: metriche performance con timestamp
  - `alerts`: alert sicurezza con status
  - `code_snippets`: snippet codice con vulnerabilità
  - `hosts`: registry host monitorati
  - `audit_logs`: log accessi per compliance

- **Indexes**: Ottimizzati per query temporali e filtri

#### Database Vettoriale (Chroma)
- **Collezioni**:
  - `security_alerts`: embedding alert per ricerca semantica
  - `code_snippets`: embedding codice per similarity
  - `knowledge_base`: documentazione e playbook

- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
  - 384 dimensioni
  - Multi-language support
  - ~120MB RAM

- **Ricerca**: Cosine similarity, top-k results

#### Modulo Sicurezza
- **Auth**: Token-based + HMAC
- **Encryption**: Fernet (AES) per campi sensibili
- **RBAC**: 3 ruoli (admin, security, viewer)
- **Audit**: Log strutturati JSON di ogni operazione

---

### 3. Dashboard Web

#### Frontend
- **Stack**: HTML5, Bootstrap 5, Chart.js, JavaScript vanilla
- **Pagine**:
  - Overview: grafici metriche aggregate
  - Alerts: tabella filtrabili con search
  - Alert Detail: info completa + "find similar"
  - Code Issues: lista snippet con ricerca
  - Investigation: workspace per analisi incidenti

#### Backend (Flask)
- Proxy per API centrale
- Session management
- Rendering templates HTML

---

## Flussi Dati

### Flusso 1: Monitoraggio Performance

```
Agent Performance Monitor
    ↓ (ogni 30s)
    Raccolta metriche (psutil)
    ↓
    Sanitizzazione (rimuovi dati sensibili)
    ↓
    Anomaly Detection (Isolation Forest)
    ↓ (se anomalia)
    Genera alert + descrizione
    ↓
    HTTPS POST → Server API
    ↓
    Salva in PostgreSQL (metrics, alerts)
    ↓
    Indicizza in Chroma (alert embedding)
    ↓
    Dashboard: query PostgreSQL per grafici
    Dashboard: query Chroma per "similar alerts"
```

### Flusso 2: Rilevamento Malware

```
Agent Malware Detector
    ↓
    Scan file + processi
    ↓
    Estrai feature (hash, entropy, behavior)
    ↓
    ML Classifier (Random Forest)
    ↓ (se malicious)
    Alert + confidence score
    ↓
    Sanitizzazione (path → hash)
    ↓
    POST → Server API
    ↓
    PostgreSQL (alert + metadata)
    ↓
    Chroma (embedding per similarity)
```

### Flusso 3: Ricerca Semantica

```
Utente dashboard: "find similar alerts"
    ↓
    Query testuale (es: "high CPU usage")
    ↓
    POST /api/search/similar-alerts
    ↓
    Server: genera embedding query
    ↓
    Chroma: vector similarity search
    ↓
    Top-5 alert simili con distance score
    ↓
    Dashboard: mostra risultati con evidenziazione
```

---

## Privacy & Security Design

### Data Minimization
- Agent invia solo dati necessari (no contenuti completi file)
- Metriche aggregate, no singoli valori raw

### Sanitizzazione Pre-Invio
- Regex pattern per rimuovere password/token/secrets
- Cmdline processi: solo nome eseguibile
- Env vars: rimosse completamente

### Anonimizzazione
- Path file → SHA256 hash (primi 16 char) + estensione
- Username → hash se non necessario
- IP privati → pseudoanonimizzati (primi 2 ottetti + hash)

### Encryption at Rest
- Campi sensibili DB → cifrati con Fernet
- Chiave encryption → env var (secrets manager)

### Encryption in Transit
- HTTPS/TLS obbligatorio (certificati self-signed ok per didattica)
- HMAC signature per integrità payload

### RBAC
- `admin`: tutti i permessi
- `security`: view/update alert, search vector DB
- `viewer`: solo visualizzazione

### Audit Logging
- Ogni operazione → JSON log con timestamp, user, action, resource
- Query su dati sensibili → tracciata con purpose

### Retention Policy
- Script cron: auto-delete metriche > 90 giorni
- Alert: archivio dopo 180 giorni

---

## Scalabilità

### Vertical Scaling
- PostgreSQL: indici ottimizzati, partitioning per timestamp
- Chroma: supporta milioni di vettori

### Horizontal Scaling
- Agent: uno per host, indipendenti
- API: stateless → load balancer + N istanze
- Chroma: clustering per dataset grandi

### Performance
- Agent: overhead <2% CPU/RAM su host monitorato
- API: ~100 req/s per istanza (FastAPI async)
- Vector search: <100ms per query (384-dim embeddings)

---

## Deployment

### Development (Docker Compose)
```bash
docker-compose up --build
```

Containers:
- `postgres`: PostgreSQL DB
- `chroma`: Chroma vector DB
- `central_server`: FastAPI backend
- `dashboard`: Flask frontend
- (optional) `agent_performance`: test agent locale

### Production
- Kubernetes manifests (vedi `k8s/`)
- Separazione network: agents → API (firewall)
- Secrets: Vault o K8s secrets
- Monitoring: Prometheus + Grafana

---

## Tecnologie Scelte - Motivazioni Didattiche

### Python
✅ Linguaggio didattico
✅ Ricco ecosistema ML/security
✅ Leggibile per studenti

### FastAPI
✅ Moderno, async, veloce
✅ Auto-documentation (Swagger)
✅ Type hints → codice più chiaro

### PostgreSQL
✅ Standard industria
✅ Feature avanzate (JSON, time-series)
✅ Free & open source

### Chroma
✅ Vector DB semplice da usare
✅ Python-native
✅ Ottimo per progetti didattici
✅ Alternative: Qdrant, Weaviate, Milvus

### scikit-learn
✅ Isolation Forest ready-to-use
✅ Ampia documentazione
✅ Performance adeguate per didattica

### sentence-transformers
✅ Embedding pre-trained eccellenti
✅ Facile integrazione
✅ Supporto multi-language

---

## Limiti & Miglioramenti Futuri

### Limiti Attuali (Design Didattico)
- Anomaly detection: baseline statica (no adaptive learning)
- Malware classifier: training su dataset sintetico (serve dataset reale)
- IDS: pattern semplici (no deep learning)
- Vector search: modello generico (non ottimizzato per security domain)

### Possibili Estensioni (Esercizi Studenti)
1. **Adaptive learning**: retrain modelli ML periodicamente
2. **Deep learning**: LSTM per anomaly detection su time-series
3. **Threat intelligence**: integrazione feed esterni (MISP, STIX)
4. **Automated response**: playbook automatici per remediation
5. **Multi-tenancy**: supporto organizzazioni multiple
6. **Compliance reports**: generazione automatica report GDPR/SOC2

---

## Riferimenti Architetturali

- **SIEM Pattern**: Elastic Stack (Elasticsearch, Logstash, Kibana)
- **SOAR**: Splunk Phantom, IBM Resilient
- **Vector DB**: Pinecone, Weaviate architecture
- **ML for Security**: Google Chronicle, Darktrace

---

## Contatti & Supporto

Per domande sull'architettura:
- Documentazione completa: `docs/`
- GitHub Issues
- Email docente
