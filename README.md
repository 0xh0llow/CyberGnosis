# 🛡️ Distributed SOC System – Documentazione

## 1. Visione d’insieme

Il progetto è strutturato come un **SOC distribuito**:

- Gli **host client** eseguono agent:
  - Performance monitoring
  - Malware detection
  - IDS
  - Code scanner
- Gli agent inviano eventi e metriche al **server centrale** tramite API HTTP (Bearer token + HMAC)
- Il **server centrale (FastAPI)**:
  - Salva i dati in PostgreSQL
  - Indicizza alert/snippet in Chroma (vector DB)
- Il **dashboard (Flask)** consuma le API per visualizzazione e investigazione

---

## 2. Stack Server (`docker-compose.server.yml`)

Avvio consigliato:

```bash
./scripts/compose.sh -f docker-compose.server.yml --env-file .env.server up -d --build
```

`./scripts/compose.sh` forza `COMPOSE_BAKE=false` di default per evitare errori Buildx/Compose v2 come `failed to execute bake: read |0: file already closed`.

### Servizi principali

- **postgres**
  - DB relazionale (`security_monitoring`)
  - Init script: `central_server/db/init.sql`

- **chroma**
  - Vector DB per semantic search

- **central_server (FastAPI)**
  - Variabili env:
    - `DATABASE_URL`
    - `CHROMA_HOST/PORT`
    - `API_TOKEN`
    - `EMBEDDING_MODEL`
  - Default embedding model:
    ```
    sentence-transformers/all-MiniLM-L6-v2
    ```

- **dashboard (Flask)**
  - Collegato a:
    ```
    http://central_server:8000
    ```

---

## 3. Stack Client (`docker-compose.client.yml`)

Avvio consigliato:

```bash
./scripts/compose.sh -f docker-compose.client.yml --env-file .env.client up -d
```

Ogni host può eseguire:

- `performance_agent`
- `malware_agent`
- `ids_agent`
- `code_scanner`

### Config comune

- `CENTRAL_SERVER_URL`
- `API_TOKEN`
- `HOST_ID`

---

## 4. Flusso dati end-to-end

Agent → API → Database → Dashboard

### Pipeline

1. Agent raccoglie dati
2. `SecureAPISender`:
   - Payload con timestamp + host
   - Bearer token
   - Firma HMAC
   - Retry esponenziale
3. FastAPI:
   - Verifica token
   - Salva via SQLAlchemy
4. Indicizzazione:
   - Alert/snippet → embedding → Chroma
5. Dashboard:
   - Query API
   - Visualizzazione

---

## 5. Database

### A) PostgreSQL

**Ruolo:** DB principale relazionale

#### Tabelle principali

- `metrics`
- `alerts`
- `code_snippets`
- `hosts`
- `audit_logs`

---

### B) Chroma (Vector DB)

- Collezioni:
  - `security_alerts`
  - `code_snippets`
  - `knowledge_base`

---

## 6. Modelli AI/ML

- IsolationForest → anomaly detection
- RandomForestClassifier → malware detection
- SentenceTransformer → embeddings

---

## 7. Client Agents

- Performance Agent
- Malware Agent
- IDS Agent
- Code Scanner

---

## 8. Sicurezza

- Bearer Token
- HMAC (non sempre enforced)
- Sanitizzazione dati

---

## 9. API Endpoint

- POST /api/metrics
- POST /api/alerts
- GET /api/alerts
- GET /health

---

## 10. Note

- Docker compose multipli
- API token statico
- JWT/RBAC parzialmente implementati
