# 🎓 Linee Guida per Docenti

Questa guida fornisce istruzioni per docenti e teaching assistant che utilizzano questo progetto per insegnamento cybersecurity.

## 📋 Indice

1. [Panoramica del Corso](#panoramica-del-corso)
2. [Setup Ambiente Didattico](#setup-ambiente-didattico)
3. [Struttura Lezioni](#struttura-lezioni)
4. [Valutazione Studenti](#valutazione-studenti)
5. [Soluzioni Esercizi](#soluzioni-esercizi)
6. [Tips Didattici](#tips-didattici)
7. [Troubleshooting Comuni](#troubleshooting-comuni)

---

## Panoramica del Corso

### Obiettivi Didattici

Gli studenti al termine del corso dovranno essere capaci di:

1. **Progettare** un sistema di monitoring distribuito
2. **Implementare** algoritmi ML per anomaly/malware detection
3. **Utilizzare** vector databases per semantic search
4. **Configurare** sistemi IDS log-based e network-based
5. **Condurre** incident investigation end-to-end
6. **Applicare** principi di privacy by design

### Prerequisiti Studenti

**Obbligatori:**
- Python intermedio (classi, async, decorators)
- Linux command line
- Networking basics (TCP/IP, HTTP)
- Docker/container basics

**Consigliati:**
- Machine Learning introduttivo
- Database (SQL basics)
- Security concepts (CIA triad, common attacks)

### Durata Consigliata

- **Versione Standard**: 6-8 settimane (3h/settimana lezione + 5h/settimana lab)
- **Versione Intensiva**: 4 settimane (6h/settimana lezione + 10h/settimana lab)
- **Workshop**: 2 giorni full-time

---

## Setup Ambiente Didattico

### Opzione 1: Lab Universitario

**Setup consigliato per 25 studenti:**

```yaml
Infrastructure:
  - 1 Server centrale (16 CPU, 64GB RAM)
    - Docker Swarm per multi-tenancy
    - Postgres shared
    - Chroma DB shared
  
  - 25 VM studenti (2 CPU, 4GB RAM each)
    - Ubuntu 22.04 LTS
    - Python 3.9+, Docker preinstallato
    - Network isolation tra studenti
```

**Script setup automatico** (run come admin):

```bash
#!/bin/bash
# setup_lab.sh

NUM_STUDENTS=25

for i in $(seq 1 $NUM_STUDENTS); do
  # Crea VM per studente
  docker run -d \
    --name student-${i} \
    --hostname student-${i} \
    -v /lab/student-${i}:/workspace \
    -p $((8000+i)):8000 \
    ubuntu:22.04
  
  # Setup ambiente
  docker exec student-${i} bash -c "
    apt update && apt install -y python3 python3-pip git
    cd /workspace
    git clone <repo-url> cybersecurity-soc
    cd cybersecurity-soc
    pip3 install -r requirements.txt
  "
done
```

### Opzione 2: Cloud Deployment

**AWS/Azure/GCP:**

```bash
# Template Terraform per deploy automatico
terraform apply -var="student_count=25"

# Ogni studente riceve:
# - EC2 instance t3.medium
# - Public IP
# - Credentials SSH
# - Workspace preconfigurato
```

### Opzione 3: Locale (BYOD)

Studenti usano laptop personali. Testare su:
- Windows 10+ con WSL2
- macOS 12+
- Linux (qualsiasi distro recente)

**Requisiti minimi hardware:**
- 8GB RAM
- 20GB disk space
- Dual-core CPU

---

## Struttura Lezioni

### Settimana 1: Introduction & Setup

**Lezione 1.1 - Teoria (1.5h)**
- Cybersecurity landscape
- SOC (Security Operations Center) overview
- System architecture walkthrough
- Privacy by design principles

**Lab 1.1 (2h)**
- Setup ambiente (docker-compose)
- Prima esecuzione agent
- Test API con curl/Postman
- Esplorare dashboard

**Homework:**
- Completare Esercizio 1 Parte A-B
- Lettura: docs/architecture/system_design.md

---

### Settimana 2: Anomaly Detection & ML

**Lezione 2.1 - Teoria (1.5h)**
- Anomaly detection overview
- Isolation Forest algorithm
- Feature engineering for security
- False positives management

**Lab 2.1 (2h)**
- Training Isolation Forest
- Generare anomalie artificiali
- Tuning contamination parameter
- Visualizzare decision boundaries

**Homework:**
- Completare Esercizio 1 Parte C-E
- Report: analisi 10 anomalie rilevate

---

### Settimana 3: Malware Detection

**Lezione 3.1 - Teoria (1.5h)**
- Malware types & behavior
- Static vs dynamic analysis
- ML per classification
- YARA rules

**Lab 3.1 (3h)**
- Creare dataset malware/benign (200+ samples)
- Training Random Forest classifier
- Scrivere YARA custom rules
- Evaluation: precision, recall, F1

**Homework:**
- Completare Esercizio 2
- Report: performance modello ML

---

### Settimana 4: Vector Search & Investigation

**Lezione 4.1 - Teoria (1.5h)**
- Embeddings & semantic search
- Vector databases (Chroma)
- Similarity metrics
- Incident investigation workflow

**Lab 4.1 (3h)**
- Populate Chroma con alert storici
- Query semantiche
- Clustering alert simili (t-SNE)
- Build knowledge base articles

**Homework:**
- Completare Esercizio 3
- Investigation report: incident simulato

---

### Settimana 5: Intrusion Detection

**Lezione 5.1 - Teoria (1.5h)**
- IDS types: HIDS vs NIDS
- Log analysis & parsing
- Network packet capture (Scapy)
- Common attack patterns

**Lab 5.1 (3h)**
- Implement log-based IDS (brute force, command injection)
- Network-based IDS (port scan, DDoS)
- Packet analysis con Wireshark
- Tuning detection rules

**Homework:**
- Completare Esercizio 4
- Report: 3 detection rules custom

---

### Settimana 6-8: Final Project

**Lezione 6.1 - Kickoff (1h)**
- Final project requirements
- APT (Advanced Persistent Threat) simulation
- Team formation (2-3 studenti)
- Timeline & milestones

**Lab 6.1-8.3 (15h totali)**
- Deploy sistema multi-host
- Simulare attacco APT 5-stage
- Incident detection & response
- Post-mortem analysis
- Presentation prep

**Deliverables:**
- Sistema completo funzionante
- Investigation report (10-15 pagine)
- Presentation (15 min)
- Demo video (5 min)

---

## Valutazione Studenti

### Grading Rubric

| Componente | Peso | Dettagli |
|------------|------|----------|
| **Infrastructure** | 15% | Setup corretto, Docker, configurazione |
| **Detection Systems** | 25% | Performance monitoring, malware, IDS |
| **Investigation** | 20% | Vector search, incident analysis |
| **Response** | 20% | Mitigation, remediation, playbooks |
| **Documentation** | 20% | Reports, code comments, presentation |

### Esercizio 1: Setup & Anomaly (10%)

**Criteri:**
- [ ] Sistema deployed correttamente (3%)
- [ ] Agent performance funzionante (2%)
- [ ] Almeno 5 anomalie rilevate (3%)
- [ ] Report completo con screenshot (2%)

### Esercizio 2: Malware Detection (15%)

**Criteri:**
- [ ] Dataset ≥200 samples (50/50 split) (3%)
- [ ] Modello ML trained (accuracy >85%) (4%)
- [ ] YARA rules custom (≥3 rules) (3%)
- [ ] Evaluation report con confusion matrix (3%)
- [ ] Bonus: Comparazione algoritmi ML (+2%)

### Esercizio 3: Vector Search (15%)

**Criteri:**
- [ ] Chroma populated (≥100 alert) (3%)
- [ ] Query semantiche (≥10 esempi) (3%)
- [ ] t-SNE visualization (2%)
- [ ] Investigation report dettagliato (5%)
- [ ] Bonus: KB integration (+2%)

### Esercizio 4: IDS (15%)

**Criteri:**
- [ ] Log-based IDS implementato (4%)
- [ ] Network-based IDS implementato (4%)
- [ ] PCAP samples catturati (2%)
- [ ] Tuning & false positive analysis (3%)
- [ ] Bonus: ML-based anomaly (+2%)

### Esercizio 5: Final Project (45%)

**Criteri:**

**Technical Implementation (20%)**
- [ ] Multi-host deployment (5 hosts) (5%)
- [ ] APT simulation 5-stage completa (8%)
- [ ] Detection coverage (≥80% stage rilevate) (5%)
- [ ] System stability & performance (2%)

**Investigation & Response (15%)**
- [ ] Alert correlation (4%)
- [ ] Timeline ricostruita (4%)
- [ ] Containment scripts (3%)
- [ ] Remediation plan (4%)

**Documentation (10%)**
- [ ] Investigation report (10-15 pagine) (4%)
- [ ] Technical guides (3 documenti) (3%)
- [ ] Executive summary (1-2 pagine) (3%)

**Presentation & Demo (5%)**
- [ ] Oral presentation (15 min) (2%)
- [ ] Demo video (5 min) (2%)
- [ ] Q&A handling (1%)

### Extra Credit Opportunities

- **Code Quality** (+5%): Clean code, test coverage >80%
- **Innovation** (+5%): Features aggiuntive (dashboard custom, ML model nuovo)
- **Collaboration** (+3%): Contributi GitHub, peer review
- **Documentation** (+2%): Tutorial o blog post pubblico

---

## Soluzioni Esercizi

### ⚠️ Access Restricted

Le soluzioni complete sono disponibili solo per docenti verificati.

**Per richiedere accesso:**
1. Email a: [instructor-support@example.com]
2. Include:
   - Nome istituzione
   - Corso title & codice
   - Email istituzionale
   - Proof of teaching (syllabus o simile)

**Contenuto repository soluzioni:**
```
solutions/
├── exercise_01/
│   ├── solution.md          # Walkthrough completo
│   ├── code_samples/        # Codice soluzione
│   └── grading_checklist.md # Checklist valutazione
├── exercise_02/
├── exercise_03/
├── exercise_04/
└── exercise_05/
```

### Sample Solution Snippet (Esercizio 1)

```python
# Esempio soluzione attesa per anomaly detection
from agents.performance.anomaly_detector import AnomalyDetector

def train_detector():
    """Train anomaly detector con dati normali"""
    detector = AnomalyDetector(contamination=0.1)
    
    # Collect 100 metriche normali
    training_data = []
    for _ in range(100):
        metrics = collect_metrics()  # Implementato dallo studente
        training_data.append(metrics)
    
    detector.train(training_data)
    detector.save_model("models/anomaly_detector.pkl")
    
    return detector

def generate_anomaly():
    """Genera anomalia artificiale per test"""
    # Simula high CPU
    import psutil
    # ... codice per stress test ...
```

---

## Tips Didattici

### Best Practices

**1. Live Coding Sessions**
- Fai vedere debugging real-time
- Commit to Git durante lezione (mostra workflow)
- Usa `pdb` per step through codice

**2. Incident Response Simulations**
- Crea scenari realistici (es: cryptominer in produzione)
- Time-boxed challenges (30 min per investigate)
- Debrief: discuti approcci diversi

**3. Peer Review**
- Assegna code review tra studenti
- Usa GitHub Pull Requests
- Insegna a dare feedback costruttivo

**4. Guest Speakers**
- Invita SOC analyst reale
- CTF organizer
- Security researcher

### Common Student Mistakes

| Errore | Perché Succede | Come Prevenire |
|--------|----------------|----------------|
| Import errors | PYTHONPATH non configurato | Setup script automatico |
| Container conflicts | Porte già in uso | Check con `lsof -i` prima |
| Overfitting ML | Training set troppo piccolo | Enforce minimum 200 samples |
| Ignoring sanitization | Non leggono docs privacy | Quiz su privacy prima Ex2 |
| Last-minute rush | Sottostimano complessità | Milestone intermedi obbligatori |

### Office Hours Strategy

**Setup:**
- 2h/settimana in-person
- 1h/settimana online (Zoom/Meet)
- Slack/Discord per async

**Triage Questions:**
1. "Hai letto la documentazione?"
2. "Hai cercato l'errore su Google/StackOverflow?"
3. "Qual è l'ultimo comando/codice che hai provato?"
4. "Puoi mostrarmi l'errore esatto?"

**Red Flags (possible cheating):**
- Soluzioni identiche tra studenti
- Commit Git tutti lo stesso giorno finale
- Codice troppo avanzato rispetto a skill dimostrate

---

## Troubleshooting Comuni

### Studenti Bloccati

**Scenario 1: "Docker non parte"**

```bash
# Troubleshooting checklist
1. Check Docker service running
   systemctl status docker

2. Check port conflicts
   sudo lsof -i :8000
   sudo lsof -i :5432

3. Check disk space
   df -h

4. Prune old containers
   docker system prune -a

5. Restart Docker
   sudo systemctl restart docker
```

**Scenario 2: "Agent non invia dati"**

```bash
# Debug steps
1. Check API reachable
   curl http://localhost:8000/api/health

2. Check agent logs
   python3 run_agent.py --debug

3. Verify .env configuration
   cat .env | grep API_URL

4. Test API manually
   curl -X POST http://localhost:8000/api/metrics \
     -H "Content-Type: application/json" \
     -d '{"host_id":"test","agent_type":"performance",...}'
```

**Scenario 3: "ML model non converge"**

```python
# Common issues
1. Training data insufficiente
   # SOLUZIONE: collect almeno 100 samples

2. Features non normalized
   # SOLUZIONE: usa StandardScaler

3. Contamination troppo alta
   # SOLUZIONE: prova contamination=0.05 invece di 0.1

4. Overfitting
   # SOLUZIONE: aumenta training set, usa validation set
```

### Lab Equipment Issues

**Server centrale down:**
```bash
# Emergency recovery
1. Check server status
   ping lab-server.university.edu

2. Access via IPMI/iDRAC
   # Reboot if necessary

3. Restore from backup
   docker-compose down
   ./restore_backup.sh latest

4. Notify students via email/Slack
```

**Network segmentation broken:**
```bash
# Security issue - studenti vedono containers altrui
1. Immediate isolation
   iptables -I FORWARD -j DROP

2. Fix Docker network
   docker network create --driver overlay --subnet 10.0.0.0/24 student-net

3. Restart containers con network corretta
   docker-compose down
   docker-compose --env-file .env.student1 up -d
```

---

## Risorse Aggiuntive per Docenti

### Slides & Materiali

**Template PowerPoint:**
- Week 1-8 slide decks (nella repo docenti)
- Quiz Kahoot per ogni settimana
- Exam practice questions

### Assessment Tools

**Auto-grading Scripts:**
```bash
# Grade esercizio automaticamente
./scripts/grade_exercise.sh student_submission.zip

# Output:
# ✓ Docker deployment: 3/3
# ✓ Agent running: 2/2
# ✗ Anomalies detected: 0/3 (insufficient data)
# ✓ Report submitted: 2/2
# Total: 7/10 (70%)
```

### Research Opportunities

**Possibili paper topics per studenti PhD:**
- ML model effectiveness su malware dataset reali
- Privacy-preserving techniques per security telemetry
- Scalability analysis SOC systems
- Comparative study: supervised vs unsupervised anomaly detection

---

## Feedback & Improvement

### End-of-Course Survey

**Chiedi agli studenti:**
1. Difficulty level (1-5)
2. Time commitment vs aspettative
3. Lezioni più/meno utili
4. Suggerimenti miglioramento
5. Interesse in advanced course follow-up

### Iterate & Improve

**Traccia metriche:**
- Average grade per esercizio
- Dropout rate
- Time to completion
- Most common errors
- Office hours attendance

**Update materiali:**
- Annual review dei contenuti
- Update tools/libraries versioni
- Add new attack techniques (stay current)

---

## Contatti

**Support per Docenti:**
- Email: instructor-support@example.com
- Slack: #instructors-only channel
- Monthly instructor sync call (first Friday)

**Contribute:**
- GitHub issues per bug/miglioramenti
- Pull requests benvenute!
- Share your lecture notes

---

**Buon insegnamento! 👨‍🏫👩‍🏫**
