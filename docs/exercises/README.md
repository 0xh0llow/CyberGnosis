# Esercizi Didattici - Linux Security AI Monitoring System

**Progetto**: Sistema di Monitoraggio Security Centralizzato basato su AI  
**Durata corso**: 6-8 settimane  
**Livello**: Intermedio-Avanzato  
**Target**: Studenti informatica/cybersecurity

---

## Struttura Corso

Questo percorso didattico è progettato per guidare gli studenti attraverso la costruzione completa di un Security Operations Center (SOC) utilizzando tecnologie moderne come Machine Learning, Vector Databases e Intrusion Detection Systems.

### Progressione Competenze

```
Settimana 1-2: Setup & Fondamentali → Esercizio 1
Settimana 3: Malware Detection & ML → Esercizio 2
Settimana 4: Vector Search & Investigation → Esercizio 3
Settimana 5: Network Security & IDS → Esercizio 4
Settimana 6-8: Progetto Finale Integrato → Esercizio 5
```

---

## 📚 Indice Esercizi

### [Esercizio 1: Setup Ambiente e Prime Analisi](./01_setup_and_first_analysis.md)
**Durata**: 2-3 ore | **Livello**: Introduttivo

**Obiettivi di Apprendimento**:
- ✅ Installare e configurare infrastructure (Docker Compose)
- ✅ Comprendere architettura sistema (agents, server centrale, databases)
- ✅ Primo deployment agent performance monitoring
- ✅ Generare e rilevare anomalie artificiali (CPU stress)
- ✅ Utilizzare vector search per trovare alert simili
- ✅ Analizzare privacy by design (data sanitization)

**Contenuti Chiave**:
- Setup Docker containers (PostgreSQL, Chroma, Central Server)
- Installazione agent con virtual environment
- Training Isolation Forest per anomaly detection
- Query semantiche con embeddings
- HMAC signature verification
- Simulazione incident response

**Deliverables**:
- Screenshot sistema funzionante
- Report investigazione anomalia CPU
- Analisi dati sanitizzati

---

### [Esercizio 2: Malware Detection & ML Classifier](./02_malware_detection_ml.md)
**Durata**: 3-4 ore | **Livello**: Intermedio

**Obiettivi di Apprendimento**:
- ✅ Analisi statica file (entropy, hash, YARA rules)
- ✅ Creazione dataset bilanciato (benign vs malicious)
- ✅ Training Random Forest classifier
- ✅ Evaluation metrics (precision, recall, F1-score)
- ✅ False positive mitigation strategies
- ✅ Process behavior monitoring

**Contenuti Chiave**:
- Shannon entropy calculation
- YARA rules development (5+ regole custom)
- Feature extraction per ML (12 features)
- Hyperparameter tuning con GridSearchCV
- Whitelisting mechanisms
- VirusTotal API integration (bonus)
- Adversarial ML evasion techniques

**Deliverables**:
- Dataset JSON (200+ samples)
- ML model con classification report
- Custom YARA rules file
- False positive analysis

---

### [Esercizio 3: Vector Search & Incident Investigation](./03_vector_search_investigation.md)
**Durata**: 3-4 ore | **Livello**: Intermedio-Avanzato

**Obiettivi di Apprendimento**:
- ✅ Comprendere sentence embeddings (all-MiniLM-L6-v2)
- ✅ Popolare Chroma vector database
- ✅ Semantic search queries
- ✅ Incident investigation workflow completo
- ✅ Knowledge base integration
- ✅ Re-ranking strategies

**Contenuti Chiave**:
- Visualizzazione embeddings con t-SNE/UMAP
- Cosine similarity vs Euclidean distance
- Filtered search con metadata
- Automated investigation pipeline
- Root cause analysis con KB
- Multi-vector search (alerts + code snippets)
- Performance benchmarking (P50, P95, P99 latency)

**Deliverables**:
- Embedding visualization PNG
- Investigation report per 2 incident types
- KB articles (3+ custom)
- Benchmark results

---

### [Esercizio 4: IDS & Network Security Monitoring](./04_ids_network_monitoring.md)
**Durata**: 3-4 ore | **Livello**: Avanzato

**Obiettivi di Apprendimento**:
- ✅ Log-based intrusion detection (brute force, privilege escalation)
- ✅ Network-based IDS (port scan, DDoS)
- ✅ Attack chain detection multi-stage
- ✅ Packet analysis con Scapy
- ✅ ML-based network anomaly detection
- ✅ False positive tuning

**Contenuti Chiave**:
- Regex parsing system logs (/var/log/auth.log)
- Brute force detection con sliding window
- Port scan detection (SYN packets)
- DDoS rate-based detection
- Flow feature extraction (10+ features)
- Snort-like signature engine
- Honeypot deployment (bonus)

**Deliverables**:
- Brute force detector implementation
- PCAP samples con port scan traffic
- IDS agent integration
- Tuning config con before/after metrics

---

### [Esercizio 5: Final Project - Complete SOC](./05_final_project_soc.md)
**Durata**: 8-10 ore (distribuito su 2 settimane) | **Livello**: Avanzato

**Obiettivi di Apprendimento**:
- ✅ Deploy multi-host environment (5+ hosts)
- ✅ Implementare dashboard web (Flask + Bootstrap)
- ✅ Simulare APT attack multi-stage
- ✅ Condurre incident investigation completa
- ✅ Automated containment & remediation
- ✅ Post-incident analysis & lessons learned

**Contenuti Chiave**:
- Docker Compose multi-container deployment
- Flask dashboard con Chart.js visualization
- 5-stage attack simulation:
  1. Reconnaissance (port scan)
  2. Initial Access (SSH brute force)
  3. Execution (malware deployment)
  4. Lateral Movement (internal propagation)
  5. Exfiltration (data theft)
- Alert correlation & timeline reconstruction
- Automated containment (host isolation, process kill)
- Post-mortem report con MITRE ATT&CK mapping
- Executive presentation per management

**Deliverables**:
- Dashboard funzionante
- Attack simulation completa
- Investigation report
- Post-mortem document
- Executive presentation (10 slides)
- Demo video (5 min)
- Technical documentation (4 guides)

---

## 🎯 Obiettivi di Apprendimento Complessivi

Al termine del corso, gli studenti saranno in grado di:

### Competenze Tecniche
- ✅ Implementare sistema monitoring distribuito con agent architecture
- ✅ Applicare ML per anomaly detection (Isolation Forest, Random Forest)
- ✅ Utilizzare vector databases per semantic search
- ✅ Sviluppare IDS log-based e network-based
- ✅ Condurre incident response end-to-end
- ✅ Automatizzare containment e remediation

### Competenze Trasversali
- ✅ Pensiero sistemico (architettura multi-component)
- ✅ Problem-solving sotto pressure (incident response)
- ✅ Documentazione tecnica e comunicazione executive
- ✅ Security mindset (think like attacker)

### Tecnologie Padroneggiate
- **Backend**: Python, FastAPI, Flask, SQLAlchemy
- **ML/AI**: scikit-learn, sentence-transformers
- **Databases**: PostgreSQL, Chroma (vector DB)
- **Security**: YARA, Scapy, HMAC, encryption
- **DevOps**: Docker, Docker Compose
- **Frontend**: Bootstrap 5, Chart.js

---

## 📊 Metodi di Valutazione

### Valutazione Formativa (Durante Corso)
- **Quiz settimanali**: Test comprensione concetti teorici
- **Lab completions**: Verifica esercizi pratici
- **Peer review**: Studenti reviewano codice reciprocamente

### Valutazione Sommativa (Fine Corso)
- **Esercizio Finale (Esercizio 5)**: 60% del voto
- **Esercizi 1-4 combinati**: 30% del voto
- **Partecipazione e documentazione**: 10% del voto

### Criteri Valutazione Progetto Finale
| Categoria | Peso |
|-----------|------|
| Infrastructure Setup | 15% |
| Incident Simulation & Detection | 25% |
| Investigation & Analysis | 20% |
| Response & Remediation | 20% |
| Documentation & Presentation | 20% |

**Bonus Points** (+10%): Automated response, ML improvements, creative enhancements

---

## 🛠️ Prerequisiti

### Conoscenze Richieste
- ✅ Python programming (intermedio)
- ✅ Linux command line (bash, filesystem, permissions)
- ✅ Networking fundamentals (TCP/IP, ports, protocols)
- ✅ Basic SQL queries
- ✅ Git version control
- ✅ (Opzionale) Docker basics

### Software Necessario
- **Sistema Operativo**: Ubuntu 20.04/22.04 LTS (o VM)
- **Python**: 3.9+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.x
- **Editor**: VS Code (raccomandato) o PyCharm
- **RAM**: Minimo 8GB (raccomandato 16GB per multi-container)
- **Disk Space**: 20GB liberi

### Risorse Online
- [Documentazione progetto](../README.md)
- [Architecture Design](../architecture/system_design.md)
- [Installation Guide](../guides/installation.md)
- [MITRE ATT&CK](https://attack.mitre.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

## 📅 Piano Settimanale Suggerito

### Settimana 1: Fondamentali & Setup
- **Giorno 1-2**: Lettura documentazione architettura
- **Giorno 3-4**: [Esercizio 1](./01_setup_and_first_analysis.md) - Parte A, B, C
- **Giorno 5**: Esercizio 1 - Parte D, E + submission

### Settimana 2: Machine Learning
- **Giorno 1**: [Esercizio 2](./02_malware_detection_ml.md) - Parte A (static analysis)
- **Giorno 2-3**: Esercizio 2 - Parte B (ML training)
- **Giorno 4**: Esercizio 2 - Parte C, D
- **Giorno 5**: Esercizio 2 - submission + review

### Settimana 3: Vector Search
- **Giorno 1**: [Esercizio 3](./03_vector_search_investigation.md) - Parte A (embeddings)
- **Giorno 2**: Esercizio 3 - Parte B (Chroma DB)
- **Giorno 3-4**: Esercizio 3 - Parte C (investigation)
- **Giorno 5**: Esercizio 3 - Parte D, E + submission

### Settimana 4: Network Security
- **Giorno 1-2**: [Esercizio 4](./04_ids_network_monitoring.md) - Parte A (log IDS)
- **Giorno 3**: Esercizio 4 - Parte B (network IDS)
- **Giorno 4**: Esercizio 4 - Parte C (integration)
- **Giorno 5**: Esercizio 4 - submission

### Settimana 5-6: Progetto Finale Parte 1
- **Settimana 5 Giorno 1-2**: [Esercizio 5](./05_final_project_soc.md) - Parte A (setup)
- **Settimana 5 Giorno 3-5**: Esercizio 5 - Parte B (simulation)
- **Settimana 6 Giorno 1-2**: Esercizio 5 - Parte C (response)

### Settimana 7: Progetto Finale Parte 2
- **Giorno 1-2**: Esercizio 5 - Parte D (post-incident)
- **Giorno 3-4**: Esercizio 5 - Parte E (presentation)
- **Giorno 5**: Final review & polish

### Settimana 8: Presentazioni
- Presentazioni finali studenti
- Peer review
- Feedback docente

---

## 💡 Consigli per gli Studenti

### Durante gli Esercizi
1. **Leggi TUTTO prima di iniziare**: Comprendi obiettivo complessivo
2. **Testa incrementalmente**: Non aspettare la fine per run
3. **Documenta mentre lavori**: Screenshot, comandi eseguiti, output
4. **Usa versioning**: Commit frequenti con messaggi descrittivi
5. **Chiedi aiuto presto**: Non rimanere bloccato >30 minuti

### Per il Progetto Finale
1. **Pianifica tempo**: 8-10 ore distribuite, non tutto in un giorno
2. **Priorità**: Focus su funzionalità core prima di bonus
3. **Testing**: Testa attack simulation in ambiente isolato
4. **Backup**: Backup VM/container prima di modifiche rischiose
5. **Presentation**: Practice demo per assicurarti funzioni live

### Debugging Tips
```bash
# Check Docker containers
docker-compose ps
docker logs <container-name>

# Check Python errors
export LOG_LEVEL=DEBUG
python -m pdb script.py  # Debug mode

# Network troubleshooting
curl http://localhost:8000/health
docker network inspect soc_network

# Database queries
docker exec -it security-postgres psql -U securityuser -d security_monitoring
```

---

## 🏆 Certificazione & Portfolio

### Al Completamento Corso
Gli studenti ricevono:
- ✅ **Certificate of Completion**: Attestato del corso
- ✅ **GitHub Portfolio**: Repository pubblico con progetto completo
- ✅ **LinkedIn Skills**: Machine Learning, Cybersecurity, Python, Docker
- ✅ **Reference Letter**: (per studenti top performers)

### Portfolio Checklist
Per rendere il progetto attractive per recruiter:
- [ ] README.md completo con screenshots
- [ ] Architecture diagram professionale
- [ ] Demo video su YouTube
- [ ] Documentazione Markdown ben formattata
- [ ] Code comments in inglese
- [ ] Tests implementati (almeno basic unit tests)
- [ ] CI/CD pipeline (GitHub Actions) - bonus

---

## 📞 Supporto & Risorse

### Orari Ufficio (Office Hours)
- **Lunedì & Mercoledì**: 14:00-16:00 (in presenza/online)
- **Venerdì**: 10:00-12:00 (solo online)

### Canali Comunicazione
- **Slack**: #linux-security-ai (Q&A, discussioni)
- **GitHub Issues**: Per bug tecnici repository
- **Email**: [instructor@university.edu] (urgenze)

### Risorse Aggiuntive
- **Video Tutorials**: [YouTube Playlist](#)
- **Past Student Projects**: [GitHub Organization](#)
- **Industry Guest Talks**: Schedule in Slack

---

## 🔄 Versioning & Updates

**Versione Corrente**: v1.0 (Gennaio 2024)

### Changelog
- **v1.0** (2024-01): Release iniziale con 5 esercizi completi
- Prossimi updates saranno annunciati in Slack

### Feedback Studenti
Il corso è in continua evoluzione. Per suggerimenti:
- Compila [Feedback Form](#) a metà e fine corso
- Proponi improvements via Pull Request

---

## 📜 Licenza & Uso

Questo materiale didattico è rilasciato sotto:
- **Codice**: MIT License
- **Documentazione**: CC BY-NC-SA 4.0

**È permesso**:
- ✅ Usare per apprendimento personale
- ✅ Modificare e adattare
- ✅ Includere in portfolio personale

**Non è permesso**:
- ❌ Uso commerciale senza autorizzazione
- ❌ Rivendere materiale
- ❌ Plagiare senza attribution

---

## 🎓 Conclusione

Questo percorso vi trasformerà da studenti con conoscenze base a professionisti capaci di:
- Progettare architetture security scalabili
- Implementare detection systems con ML/AI
- Condurre incident response professionale
- Comunicare technical concepts a audience diverse

**Ready to become a SOC Analyst? Let's start! 🚀🔐**

---

**Ultima modifica**: 2024-01-24  
**Maintainer**: Security Lab Team  
**Contact**: security-lab@university.edu
