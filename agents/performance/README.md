# Performance Monitor Agent

## Descrizione

Agent per monitoraggio performance sistema con anomaly detection ML-based.

## Funzionalità

✅ **Raccolta Metriche**:
- CPU (percentuale, frequenza, core)
- RAM (uso, disponibile, swap)
- Disco (spazio, I/O read/write)
- Network (bytes sent/received)
- Processi (conteggio, top CPU)

✅ **Anomaly Detection**:
- Algoritmo: **Isolation Forest** (scikit-learn)
- Training automatico su baseline
- Rilevamento comportamenti anomali
- Alert automatici

✅ **Privacy & Security**:
- Sanitizzazione cmdline processi
- Anonimizzazione username/path
- Solo statistiche aggregate inviate
- Validazione pre-invio dati

## Installazione

```bash
cd agents/performance

# Installa dipendenze
pip install -r ../requirements.txt
```

## Configurazione

Opzione 1 - Variabili ambiente:

```bash
export CENTRAL_SERVER_URL="https://your-server:8000"
export API_TOKEN="your_api_token_here"
export HOST_ID="server-001"
```

Opzione 2 - File `.env`:

```env
CENTRAL_SERVER_URL=https://your-server:8000
API_TOKEN=your_api_token
HOST_ID=server-001
```

## Utilizzo

### Avvio Base

```bash
python run_agent.py \
  --server-url https://central-server:8000 \
  --api-token YOUR_TOKEN \
  --host-id server-001
```

### Avvio con Parametri Custom

```bash
python run_agent.py \
  --server-url https://central-server:8000 \
  --api-token YOUR_TOKEN \
  --host-id server-001 \
  --interval 60 \
  --training-samples 100 \
  --contamination 0.05 \
  --no-ssl-verify  # Solo per test con self-signed cert
```

### Parametri

- `--server-url`: URL server centrale (required)
- `--api-token`: Token autenticazione API (required)
- `--host-id`: Identificativo univoco host (required)
- `--interval`: Intervallo raccolta metriche in secondi (default: 30)
- `--training-samples`: Numero campioni per training ML (default: 50)
- `--contamination`: Frazione anomalie previste 0.0-0.5 (default: 0.1)
- `--no-ssl-verify`: Disabilita verifica SSL (solo ambiente didattico)

## Fasi di Funzionamento

### Fase 1: Training (primi N campioni)

L'agent raccoglie metriche "normali" per costruire baseline:

```
Training: 10/50 samples
Training: 20/50 samples
...
Training: 50/50 samples
✓ Training completed - switching to detection mode
```

Il modello viene salvato in `data/performance_anomaly_model.pkl`.

### Fase 2: Detection

Dopo training, ogni metrica viene analizzata:

```
✓ Normal behavior (score: 0.123)
```

Se anomalia rilevata:

```
⚠️  ANOMALY DETECTED: CPU usage unusually high, Memory usage critical
✓ Anomaly alert sent
```

## Output

### Metriche Inviate (JSON)

```json
{
  "cpu_percent": 45.2,
  "ram_percent": 67.8,
  "disk_percent": 55.0,
  "process_count": 156,
  "top_processes": [
    {
      "name": "python3",
      "cpu_percent": 23.5,
      "memory_percent": 5.2
    }
  ],
  "suggestions": [
    "Memory usage critical. Review memory-intensive applications."
  ],
  "anomaly_detection": {
    "is_anomaly": false,
    "score": 0.123
  }
}
```

## Test Locale

Test senza server centrale:

```bash
# Test raccolta metriche
python monitor.py

# Test anomaly detector
python anomaly_detector.py
```

## Troubleshooting

### Errore: "Cannot connect to central server"

- Verifica che server centrale sia in esecuzione
- Controlla firewall/network
- Verifica URL e porta corretti

### Errore: "Authentication failed"

- Controlla API token
- Verifica che token sia valido sul server

### Modello non si allena

- Attendi raccolta baseline (almeno 50 campioni)
- Verifica che metriche siano raccolte correttamente

## File Generati

- `data/performance_anomaly_model.pkl`: Modello ML addestrato
- Log in stdout (reindirizza con `> agent.log`)

## Note Didattiche

### Concetti Chiave

1. **Isolation Forest**: algoritmo unsupervised per anomaly detection
   - Isola osservazioni anomale tramite random forests
   - Non richiede etichette (unsupervised)
   - Efficiente su dataset con poche anomalie

2. **Feature Engineering**: scelta metriche rilevanti
   - CPU, RAM, disk come indicatori chiave
   - Normalizzazione con StandardScaler

3. **Privacy by Design**: sanitizzazione dati
   - No cmdline completi
   - No username/path in chiaro
   - Solo statistiche aggregate

### Esercizi Studenti

1. Modifica threshold contamination e osserva impatto
2. Aggiungi nuove feature (network I/O rate, context switches)
3. Implementa alert per anomalie specifiche (solo CPU, solo RAM)
4. Crea visualizzazione metriche con matplotlib
5. Test con stress artificiale (stress-ng tool)

## Riferimenti

- [Isolation Forest Paper](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf)
- [scikit-learn IsolationForest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
- [psutil Documentation](https://psutil.readthedocs.io/)
