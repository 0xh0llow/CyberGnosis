# Esercizio 1: Setup Ambiente e Prime Analisi

**Durata stimata**: 2-3 ore  
**Livello**: Introduttivo  
**Obiettivi**: Familiarizzare con architettura sistema, installare componenti, eseguire primo monitoraggio

---

## Parte A: Setup Infrastructure (60 min)

### Task 1.1: Installazione Server Centrale

**Obiettivo**: Avviare server centrale con Docker Compose

**Steps**:

1. Clone del repository:
```bash
git clone <repo-url>
cd linux-security-ai
```

2. Esegui setup script:
```bash
bash scripts/setup.sh
```

**Domande**:
- Q1.1: Quanti container Docker vengono avviati? Elenca nomi e ruoli.
- Q1.2: Quale porta espone l'API REST? E il database Chroma?
- Q1.3: Perché i certificati SSL sono self-signed? Quali sono le implicazioni?

3. Avvia sistema:
```bash
docker-compose up --build
```

4. Verifica health check:
```bash
curl http://localhost:8000/health
```

**Deliverable**: Screenshot output `docker-compose ps` e risposta health check

---

### Task 1.2: Esplorazione Database Schema

**Obiettivo**: Comprendere struttura database relazionale

**Steps**:

1. Accedi al container PostgreSQL:
```bash
docker exec -it security-postgres psql -U securityuser -d security_monitoring
```

2. Elenca tabelle:
```sql
\dt
```

3. Descrivi schema tabella `alerts`:
```sql
\d alerts
```

**Domande**:
- Q2.1: Quali indici sono presenti sulla tabella `alerts`? Perché?
- Q2.2: Che tipo di dato è `metadata`? Quali vantaggi offre?
- Q2.3: Quale campo gestisce lo stato di un alert? Quali valori può assumere?

**Deliverable**: Schema completo tabelle (output `\d+`) e risposte domande

---

## Parte B: Agent Installation & Monitoring (60 min)

### Task 2.1: Installazione Agent Performance

**Obiettivo**: Installare agent su host locale

**Steps**:

1. Setup virtual environment:
```bash
cd agents
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configura agent (ottieni token da `.env` del server):
```bash
export CENTRAL_SERVER_URL="http://localhost:8000"
export API_TOKEN="<AGENT_API_TOKEN from .env>"
export HOST_ID="lab-machine-$(whoami)"
```

3. Avvia agent in modalità test:
```bash
python performance/run_agent.py \
    --server-url $CENTRAL_SERVER_URL \
    --api-token $API_TOKEN \
    --host-id $HOST_ID \
    --interval 10  # Raccolta ogni 10 secondi per test
```

**Domande**:
- Q3.1: Quanti campioni deve raccogliere prima di completare il training?
- Q3.2: Durante la fase di training, i dati vengono inviati al server? Perché sì/no?
- Q3.3: Quale algoritmo ML usa per anomaly detection?

**Deliverable**: Screenshot log agent che mostra transizione da training a detection mode

---

### Task 2.2: Generazione Anomalia Artificiale

**Obiettivo**: Triggerare anomaly detection con carico artificiale

**Steps**:

1. Lascia agent in esecuzione (attendi fine training)

2. In un altro terminale, genera carico CPU:
```bash
# Installa stress-ng
sudo apt-get install stress-ng

# Stress CPU per 2 minuti
stress-ng --cpu 4 --cpu-load 95 --timeout 120s
```

3. Osserva log agent:
```bash
# Dovresti vedere:
# ⚠️  ANOMALY DETECTED: CPU usage unusually high
# ✓ Anomaly alert sent
```

**Domande**:
- Q4.1: Dopo quanto tempo (secondi) l'agent rileva l'anomalia?
- Q4.2: Quale `anomaly_score` viene riportato? Più negativo = più anomalo?
- Q4.3: L'alert viene inviato con quale `severity`? (low/medium/high/critical)

**Deliverable**: 
- Screenshot alert rilevato
- Query PostgreSQL per visualizzare alert salvato:
```sql
SELECT * FROM alerts WHERE alert_type='performance' ORDER BY timestamp DESC LIMIT 1;
```

---

## Parte C: Vector Search & Similarity (40 min)

### Task 3.1: Indicizzazione Alert nel Vector DB

**Obiettivo**: Verificare che alert sia stato indicizzato in Chroma

**Steps**:

1. Controlla log server centrale:
```bash
docker logs security-central-server | grep "Indexed alert"
```

2. Query diretta a Chroma:
```bash
curl http://localhost:8001/api/v1/collections/security_alerts
```

**Domande**:
- Q5.1: Quanti alert sono attualmente indicizzati?
- Q5.2: Quale modello embedding viene usato? Quante dimensioni ha il vettore?

---

### Task 3.2: Ricerca Semantica Alert Simili

**Obiettivo**: Usare API per trovare alert simili

**Steps**:

1. Crea file `search_test.py`:
```python
import requests
import json

API_URL = "http://localhost:8000"
API_TOKEN = "<YOUR_AGENT_TOKEN>"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Query semantica
search_data = {
    "query": "high CPU usage server performance issue",
    "top_k": 3,
    "collection": "alerts"
}

response = requests.post(
    f"{API_URL}/api/search/similar-alerts",
    headers=headers,
    json=search_data
)

results = response.json()
print(json.dumps(results, indent=2))
```

2. Esegui:
```bash
python search_test.py
```

**Domande**:
- Q6.1: Quali alert vengono restituiti? Hanno descrizioni simili alla query?
- Q6.2: Che significato ha il campo `distance`? Range valori?
- Q6.3: Prova query diverse ("memory leak", "disk full"). Cambia il ranking?

**Deliverable**: Output ricerca semantica per almeno 3 query diverse

---

## Parte D: Privacy & Security Analysis (30 min)

### Task 4.1: Analisi Dati Sanitizzati

**Obiettivo**: Verificare che informazioni sensibili non vengano inviate

**Steps**:

1. Crea processo con cmdline che contiene password:
```bash
python3 -c "import time; import sys; sys.argv.append('--password=secret123'); time.sleep(300)" &
PID=$!
```

2. Forza invio info processi dall'agent (modifica temporanea):
- In `agents/performance/monitor.py`, aggiungi print di `top_processes`

3. Verifica output: la password deve essere mascherata!

**Domande**:
- Q7.1: Quali campi del processo vengono sanitizzati? Elenca.
- Q7.2: Come viene gestito il path dell'eseguibile?
- Q7.3: Perché le variabili d'ambiente non vengono inviate?

4. Verifica database:
```sql
SELECT metrics->'top_processes' FROM metrics ORDER BY timestamp DESC LIMIT 1;
```

**Deliverable**: Screenshot JSON metriche che mostra cmdline sanitizzata

---

### Task 4.2: HMAC Signature Verification

**Obiettivo**: Comprendere meccanismo integrità con HMAC

**Steps**:

1. Studia codice in `agents/common/api_sender.py`, funzione `_send_with_retry`

2. Crea script per generare HMAC valido:
```python
from agents.common.crypto_utils import CryptoManager

payload = {"test": "data"}
secret = "your_api_secret_key"

signature = CryptoManager.hmac_sign(str(payload), secret)
print(f"HMAC: {signature}")
```

3. Prova invio con HMAC errato (modifica signature manualmente):
```bash
curl -X POST http://localhost:8000/api/metrics \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-HMAC-Signature: wrong_signature" \
  -d '{"host_id":"test", "timestamp":"2026-01-24T10:00:00Z", "metrics":{}}'
```

**Domande**:
- Q8.1: Cosa succede con HMAC errato? Status code HTTP?
- Q8.2: HMAC protegge da quali attacchi? (Man-in-the-middle, replay, altro?)
- Q8.3: HMAC cifra i dati? Se no, a cosa serve?

**Deliverable**: Risposte domande + esempio di richiesta con HMAC valido vs invalido

---

## Parte E: Incident Investigation (Bonus - 30 min)

### Task 5.1: Simulazione Incident Response

**Scenario**: Un alert anomalia performance è stato generato. Devi investigare.

**Steps**:

1. Recupera ultimo alert:
```sql
SELECT id, title, description, metadata FROM alerts WHERE alert_type='performance' ORDER BY timestamp DESC LIMIT 1;
```

2. Estrai `alert_id` e usa API search per trovare alert simili storici:
```python
# Cerca alert storici simili per pattern recognition
search_query = "<description dell'alert trovato>"
# ... usa API search
```

3. Analizza:
- Ci sono altri host con stesso pattern?
- Quale metrica ha triggered anomaly?
- Suggerimenti generati dall'agent?

**Domande Investigation**:
- Q9.1: L'anomalia è isolata o pattern ricorrente?
- Q9.2: Quale azione remediation suggerisci? (riavvio processo, upgrade hardware, altro)
- Q9.3: Come documenteresti questo incident per knowledge base futura?

**Deliverable**: Report investigazione (1 pagina) con:
- Timeline evento
- Metriche anomale rilevate
- Alert simili trovati con vector search
- Root cause hypothesis
- Remediation plan

---

## Submission

**Consegnare**:
1. File `risposte_esercizio1.md` con risposte a tutte le domande
2. Screenshot richiesti
3. File `search_test.py` con query semantiche
4. (Bonus) Report investigation incident

**Valutazione**:
- Completezza risposte: 40%
- Correttezza tecnica: 30%
- Screenshot/evidenze: 20%
- Report investigation (bonus): +10%

---

## Tips & Hints

💡 **Stuck on Docker?**
```bash
docker-compose logs <service-name>  # Vedi log dettagliati
docker-compose restart <service>     # Restart singolo servizio
```

💡 **Agent non invia dati?**
- Verifica token corretto
- Check firewall/network
- Aumenta log level: `export LOG_LEVEL=DEBUG`

💡 **Chroma DB issues?**
- Restart: `docker-compose restart chroma`
- Verifica connessione: `curl http://localhost:8001/api/v1/heartbeat`

💡 **Query SQL complesse?**
- Usa `\x` in psql per output verticale
- JSON queries: `SELECT metadata->>'key' FROM table`

---

## Riferimenti

- [Architecture Document](../architecture/system_design.md)
- [Installation Guide](../guides/installation.md)
- [Isolation Forest Paper](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf)
- [HMAC RFC 2104](https://tools.ietf.org/html/rfc2104)

---

**Buon lavoro! 🚀🔐**
