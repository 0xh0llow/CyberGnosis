# Esercizio 3: Vector Search & Incident Investigation

**Durata stimata**: 3-4 ore  
**Livello**: Intermedio-Avanzato  
**Obiettivi**: Comprendere embedding semantici, implementare similarity search, condurre incident investigation

---

## Parte A: Embedding Fundamentals (45 min)

### Task 1.1: Understanding Sentence Transformers

**Obiettivo**: Esplorare come funzionano gli embeddings

**Steps**:

1. Installa dipendenze:
```bash
pip install sentence-transformers matplotlib scikit-learn
```

2. Crea script embedding test:
```python
# explore_embeddings.py
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

# Test sentences
sentences = [
    "High CPU usage detected on server",
    "Server experiencing high processor load",
    "Disk space is running low",
    "Malware found in system32 directory",
    "Virus detected in Windows folder",
    "Network latency increased significantly",
]

# Generate embeddings
embeddings = model.encode(sentences)

print(f"Embedding dimensionality: {embeddings.shape}")
print(f"Embedding for sentence 0:\n{embeddings[0][:10]}...")  # First 10 dims

# Compute similarity matrix
sim_matrix = cosine_similarity(embeddings)

print("\n=== Similarity Matrix ===")
for i, sent in enumerate(sentences):
    print(f"\n{i}: {sent}")
    
for i in range(len(sentences)):
    for j in range(i+1, len(sentences)):
        similarity = sim_matrix[i][j]
        print(f"  [{i}] <-> [{j}]: {similarity:.4f}")
```

3. Esegui:
```bash
python explore_embeddings.py
```

**Domande**:
- Q1.1: Quante dimensioni ha l'embedding vector?
- Q1.2: Quali coppie hanno similarity > 0.7? Hanno significato semantico simile?
- Q1.3: Sentence 0 e 1 (CPU) vs 3 e 4 (malware): quale coppia ha similarity maggiore?
- Q1.4: Perché cosine similarity invece di Euclidean distance?

**Deliverable**: 
- Output similarity matrix completo
- Grafico heatmap delle similarità (usa matplotlib/seaborn)

---

### Task 1.2: Embedding Visualization

**Obiettivo**: Visualizzare embeddings in 2D con t-SNE/UMAP

**Steps**:

1. Espandi dataset:
```python
# visualize_embeddings.py
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

# Expanded dataset
alerts = [
    # Performance issues
    "CPU usage at 95% for 10 minutes",
    "Memory consumption exceeds threshold",
    "High disk I/O detected",
    "Server load average above 15",
    
    # Malware alerts
    "Ransomware signature detected in file",
    "Trojan behavior identified in process",
    "Suspicious file with high entropy",
    "Packed executable found",
    
    # Network intrusion
    "Port scan detected from external IP",
    "Brute force SSH attack in progress",
    "DDoS traffic pattern identified",
    "Unauthorized network connection",
    
    # Application errors
    "Database connection timeout",
    "API response time degraded",
    "Service crashed with segfault",
    "Out of memory error"
]

labels = ['perf']*4 + ['malware']*4 + ['network']*4 + ['app']*4

# Generate embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(alerts)

# Reduce to 2D
tsne = TSNE(n_components=2, random_state=42, perplexity=5)
embeddings_2d = tsne.fit_transform(embeddings)

# Plot
fig, ax = plt.subplots(figsize=(12, 8))
colors = {'perf': 'blue', 'malware': 'red', 'network': 'green', 'app': 'orange'}

for label in set(labels):
    indices = [i for i, l in enumerate(labels) if l == label]
    ax.scatter(
        embeddings_2d[indices, 0],
        embeddings_2d[indices, 1],
        c=colors[label],
        label=label,
        s=100,
        alpha=0.7
    )

# Annotate points
for i, alert in enumerate(alerts):
    ax.annotate(
        str(i),
        (embeddings_2d[i, 0], embeddings_2d[i, 1]),
        fontsize=9
    )

ax.legend()
ax.set_title('Alert Embeddings Visualization (t-SNE)')
plt.savefig('embeddings_visualization.png', dpi=150)
plt.show()
```

**Domande**:
- Q2.1: I cluster sono ben separati? Alert simili sono vicini nello spazio 2D?
- Q2.2: Outliers? Quali alert non si raggruppano con categoria attesa?
- Q2.3: Prova UMAP invece di t-SNE: risultati diversi?

**Deliverable**: PNG visualizzazione + commento su cluster quality

---

## Parte B: Vector Database Operations (60 min)

### Task 2.1: Chroma Database Setup

**Obiettivo**: Popolare Chroma con dati di test

**Steps**:

1. Verifica Chroma server:
```bash
curl http://localhost:8001/api/v1/heartbeat
```

2. Crea script per population:
```python
# populate_chroma.py
import chromadb
from sentence_transformers import SentenceTransformer
import uuid

# Connect to Chroma
client = chromadb.HttpClient(host='localhost', port=8001)

# Get or create collection
collection = client.get_or_create_collection(
    name="security_alerts",
    metadata={"description": "Security alert embeddings"}
)

print(f"Collection: {collection.name}")
print(f"Current count: {collection.count()}")

# Sample alerts
alerts = [
    {
        "id": str(uuid.uuid4()),
        "title": "Critical CPU overload on web-server-01",
        "description": "CPU utilization reached 98% sustained for 15 minutes. Top process: php-fpm consuming 45% CPU.",
        "severity": "critical",
        "host": "web-server-01",
        "alert_type": "performance"
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Memory leak detected in application",
        "description": "Java application memory usage growing linearly. RSS increased from 2GB to 8GB in 2 hours.",
        "severity": "high",
        "host": "app-server-03",
        "alert_type": "performance"
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Suspected ransomware activity",
        "description": "Multiple files encrypted in /home/user/documents. Extension changed to .locked. Process: unknown.exe",
        "severity": "critical",
        "host": "workstation-15",
        "alert_type": "malware"
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Brute force SSH attack detected",
        "description": "287 failed SSH login attempts from IP 203.0.113.5 in 5 minutes. Targeting root account.",
        "severity": "high",
        "host": "edge-server-02",
        "alert_type": "intrusion"
    },
    # Add 20+ more diverse alerts
]

# Generate embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
texts = [f"{a['title']} {a['description']}" for a in alerts]
embeddings = model.encode(texts).tolist()

# Insert into Chroma
collection.add(
    ids=[a['id'] for a in alerts],
    embeddings=embeddings,
    documents=texts,
    metadatas=[{
        "title": a['title'],
        "severity": a['severity'],
        "host": a['host'],
        "alert_type": a['alert_type']
    } for a in alerts]
)

print(f"Inserted {len(alerts)} alerts")
print(f"New count: {collection.count()}")
```

3. Esegui:
```bash
python populate_chroma.py
```

**Domande**:
- Q3.1: Quanti documenti contiene ora la collection?
- Q3.2: Chroma salva gli embeddings o li ricalcola ogni query?
- Q3.3: Quanto spazio disco occupa la collection? (controlla volume Docker)

---

### Task 2.2: Semantic Search Queries

**Obiettivo**: Interrogare DB vettoriale con query semantiche

**Steps**:

1. Crea search test:
```python
# search_test.py
import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.HttpClient(host='localhost', port=8001)
collection = client.get_collection("security_alerts")
model = SentenceTransformer('all-MiniLM-L6-v2')

def search_alerts(query_text, top_k=5, filters=None):
    """Search for similar alerts"""
    query_embedding = model.encode([query_text]).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=filters  # Optional metadata filtering
    )
    
    return results

# Test queries
queries = [
    "server is overloaded and not responding",
    "files are being encrypted by malicious software",
    "someone is trying to break into SSH",
    "application memory keeps growing",
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print('='*60)
    
    results = search_alerts(query, top_k=3)
    
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        print(f"\n[{i+1}] Distance: {distance:.4f}")
        print(f"Title: {metadata['title']}")
        print(f"Severity: {metadata['severity']} | Type: {metadata['alert_type']}")
        print(f"Excerpt: {doc[:100]}...")
```

2. Esegui ricerche:
```bash
python search_test.py
```

**Domande**:
- Q4.1: La query "server is overloaded" trova alert CPU? Rank corretto?
- Q4.2: Distance threshold ottimale? Sotto quale valore i risultati sono rilevanti?
- Q4.3: Query ambigua "system is slow": quali alert restituisce?

**Deliverable**: Output ricerche per 5 query custom + analisi relevance

---

### Task 2.3: Filtered Search

**Obiettivo**: Combinare similarity search con metadata filtering

**Steps**:

1. Test filtered search:
```python
# filtered_search.py

# Case 1: Solo alert critici su server specifico
results = search_alerts(
    query_text="high resource usage",
    top_k=5,
    filters={
        "$and": [
            {"severity": "critical"},
            {"host": "web-server-01"}
        ]
    }
)

# Case 2: Solo alert malware degli ultimi 7 giorni
results = search_alerts(
    query_text="suspicious file activity",
    filters={"alert_type": "malware"}
)

# Case 3: Esclusione low severity
results = search_alerts(
    query_text="performance issue",
    filters={"severity": {"$ne": "low"}}
)
```

**Domande**:
- Q5.1: Filtering pre o post similarity search? Quale più efficiente?
- Q5.2: Combina 3 filtri (severity, type, timestamp): come costruire query?
- Q5.3: Trade-off: semantic search vs traditional SQL WHERE clause?

**Deliverable**: 3 esempi filtered search con spiegazione use case

---

## Parte C: Incident Investigation Workflow (90 min)

### Task 3.1: Investigating Performance Incident

**Scenario**: Alert ricevuto - "Database query timeout on prod-db-01"

**Steps**:

1. Retrieve alert dettagli:
```bash
curl http://localhost:8000/api/alerts?host_id=prod-db-01 \
  -H "Authorization: Bearer <TOKEN>"
```

2. Search similar historical incidents:
```python
# investigate_incident.py
import requests
import json
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"
TOKEN = "<YOUR_TOKEN>"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Step 1: Get alert details
alert_id = "<ALERT_ID>"
response = requests.get(f"{API_URL}/api/alerts/{alert_id}", headers=headers)
alert = response.json()

print("=== INCIDENT DETAILS ===")
print(f"Title: {alert['title']}")
print(f"Description: {alert['description']}")
print(f"Severity: {alert['severity']}")
print(f"Timestamp: {alert['timestamp']}")

# Step 2: Find similar incidents
search_payload = {
    "query": alert['description'],
    "top_k": 5,
    "filters": {
        "alert_type": alert['alert_type']
    }
}

response = requests.post(
    f"{API_URL}/api/search/similar-alerts",
    headers=headers,
    json=search_payload
)
similar = response.json()

print("\n=== SIMILAR HISTORICAL INCIDENTS ===")
for item in similar['results']:
    print(f"\n[Distance: {item['distance']:.4f}]")
    print(f"Date: {item['metadata']['timestamp']}")
    print(f"Host: {item['metadata']['host']}")
    print(f"Title: {item['metadata']['title']}")
    
    # Check if resolved
    if item['metadata'].get('status') == 'resolved':
        print(f"✓ Previously resolved")
        print(f"Resolution: {item['metadata'].get('resolution_notes', 'N/A')}")

# Step 3: Correlate with metrics
response = requests.get(
    f"{API_URL}/api/metrics",
    headers=headers,
    params={
        "host_id": alert['host_id'],
        "start_time": (datetime.fromisoformat(alert['timestamp']) - timedelta(hours=1)).isoformat(),
        "end_time": alert['timestamp']
    }
)
metrics = response.json()

print("\n=== METRICS BEFORE INCIDENT ===")
for metric in metrics[-5:]:  # Last 5 data points
    print(f"{metric['timestamp']}: CPU {metric['metrics']['cpu_percent']}% | "
          f"RAM {metric['metrics']['memory_percent']}%")
```

**Domande**:
- Q6.1: Gli incident simili hanno stessa root cause?
- Q6.2: Pattern temporale? Incident ricorrono a stessi orari?
- Q6.3: Metriche prima incident mostrano anomalie precursori?

**Deliverable**: Report investigazione (template fornito sotto)

---

### Task 3.2: Root Cause Analysis with Knowledge Base

**Obiettivo**: Consultare knowledge base per remediation

**Steps**:

1. Popola knowledge base:
```python
# populate_kb.py
# Add to Chroma collection "knowledge_base"

knowledge_docs = [
    {
        "id": "kb-001",
        "title": "Database Query Timeout - Root Causes",
        "content": """
        Common causes:
        1. Missing indexes on large tables
        2. Blocking queries holding locks
        3. Insufficient connection pool size
        4. Disk I/O saturation
        
        Diagnostic queries:
        - SHOW FULL PROCESSLIST; (MySQL)
        - SELECT * FROM pg_stat_activity; (PostgreSQL)
        
        Resolution:
        - Identify slow queries with EXPLAIN
        - Add indexes on WHERE/JOIN columns
        - Increase innodb_buffer_pool_size
        - Check disk queue depth (iostat)
        """,
        "category": "performance",
        "tags": ["database", "timeout", "query"]
    },
    {
        "id": "kb-002",
        "title": "SSH Brute Force Mitigation",
        "content": """
        Defense strategies:
        1. Implement fail2ban (ban after 5 failed attempts)
        2. Use SSH key authentication only
        3. Change default port from 22
        4. Configure firewall whitelist
        5. Enable two-factor authentication
        
        Detection:
        - Monitor /var/log/auth.log for failed password
        - Check for rapid connection attempts
        
        Response:
        - Block attacker IP immediately
        - Review compromised accounts
        - Rotate credentials
        """,
        "category": "security",
        "tags": ["ssh", "brute-force", "authentication"]
    },
    # Add 10+ more KB articles
]
```

2. Search KB for solutions:
```python
# search_kb.py
def search_knowledge_base(problem_description):
    """Search KB for solutions"""
    response = requests.post(
        f"{API_URL}/api/search/knowledge",
        headers=headers,
        json={"query": problem_description, "top_k": 3}
    )
    return response.json()

# Example
problem = "database queries are timing out frequently"
solutions = search_knowledge_base(problem)

print("=== RECOMMENDED SOLUTIONS ===")
for sol in solutions['results']:
    print(f"\nTitle: {sol['metadata']['title']}")
    print(f"Relevance: {1 - sol['distance']:.2%}")
    print(f"Content:\n{sol['content'][:300]}...")
```

**Domande**:
- Q7.1: KB search trova documentazione rilevante?
- Q7.2: Come aggiornare KB con nuove soluzioni learned?
- Q7.3: Alternative: RAG (Retrieval Augmented Generation) con LLM?

**Deliverable**: Implementazione search KB + 3 KB articles custom

---

### Task 3.3: Automated Investigation Workflow

**Obiettivo**: Creare pipeline investigation automatizzata

**Steps**:

1. Script completo investigation:
```python
# auto_investigate.py
class IncidentInvestigator:
    def __init__(self, api_url, token):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def investigate(self, alert_id):
        """Full investigation workflow"""
        
        # 1. Get alert
        alert = self._get_alert(alert_id)
        report = {
            "alert_id": alert_id,
            "timestamp": datetime.now().isoformat(),
            "sections": {}
        }
        
        # 2. Find similar incidents
        similar = self._find_similar(alert)
        report['sections']['similar_incidents'] = {
            "count": len(similar),
            "resolved_count": sum(1 for s in similar if s.get('status') == 'resolved'),
            "top_3": similar[:3]
        }
        
        # 3. Retrieve metrics timeline
        metrics = self._get_metrics_timeline(alert)
        report['sections']['metrics_analysis'] = self._analyze_metrics(metrics)
        
        # 4. Search KB
        kb_results = self._search_kb(alert['description'])
        report['sections']['recommended_solutions'] = kb_results[:2]
        
        # 5. Generate recommendations
        report['recommendations'] = self._generate_recommendations(
            alert, similar, metrics, kb_results
        )
        
        return report
    
    def _generate_recommendations(self, alert, similar, metrics, kb):
        """AI-powered recommendations"""
        recommendations = []
        
        # Pattern-based logic
        if alert['alert_type'] == 'performance':
            if metrics['cpu_trend'] == 'increasing':
                recommendations.append({
                    "action": "Investigate top CPU processes",
                    "priority": "high",
                    "command": "top -bn1 | head -20"
                })
        
        # Similar incidents logic
        resolved_similar = [s for s in similar if s.get('status') == 'resolved']
        if resolved_similar:
            recommendations.append({
                "action": f"Apply solution from similar incident {resolved_similar[0]['id']}",
                "priority": "medium",
                "details": resolved_similar[0].get('resolution_notes')
            })
        
        # KB-based
        if kb:
            recommendations.append({
                "action": f"Follow KB article: {kb[0]['title']}",
                "priority": "medium",
                "link": f"/kb/{kb[0]['id']}"
            })
        
        return recommendations

# Usage
investigator = IncidentInvestigator(API_URL, TOKEN)
report = investigator.investigate("<ALERT_ID>")

print(json.dumps(report, indent=2))
```

**Domande**:
- Q8.1: Investigation automation riduce MTTR (Mean Time To Resolve)?
- Q8.2: Quali step richiedono ancora human decision?
- Q8.3: Come integrare con incident management (PagerDuty, ServiceNow)?

**Deliverable**: 
- Script `auto_investigate.py` completo
- Report JSON per 3 diversi alert types

---

## Parte D: Advanced Vector Search Techniques (45 min)

### Task 4.1: Multi-Vector Search

**Obiettivo**: Combinare alert + code snippet search

**Steps**:

1. Cross-collection search:
```python
# multi_search.py
def investigate_code_related_alert(alert_id):
    """
    When performance alert detected, search for problematic code
    that might cause issue
    """
    
    # Get alert
    alert = get_alert(alert_id)
    
    # Extract potential code-related keywords
    keywords = extract_keywords(alert['description'])
    # e.g., "memory leak" -> ["memory", "allocation", "free"]
    
    # Search code snippets
    code_results = search_code_snippets(
        query=f"code causing {' '.join(keywords)}",
        top_k=5
    )
    
    # Cross-reference: code snippets on same host
    relevant_code = [
        c for c in code_results 
        if c['metadata']['host'] == alert['host_id']
    ]
    
    return relevant_code

# Example
alert_id = "<PERFORMANCE_ALERT_ID>"
suspicious_code = investigate_code_related_alert(alert_id)

for code in suspicious_code:
    print(f"\nFile: {code['metadata']['file_path']}")
    print(f"Issues: {', '.join(code['metadata']['issues'])}")
    print(f"Snippet:\n{code['content'][:200]}...")
```

**Domande**:
- Q9.1: Quali alert types beneficiano di code snippet search?
- Q9.2: Come rankare risultati da collection diverse?
- Q9.3: Performance multi-query vs single aggregated query?

---

### Task 4.2: Re-ranking Results

**Obiettivo**: Migliorare relevance con re-ranking strategies

**Steps**:

1. Implement re-ranker:
```python
# rerank.py
def rerank_results(query, initial_results, rerank_model=None):
    """
    Re-rank using:
    1. Recency boost (newer alerts more relevant)
    2. Severity weight (critical alerts prioritized)
    3. Host affinity (same host incidents related)
    """
    
    scored_results = []
    
    for result in initial_results:
        score = 1 - result['distance']  # Base semantic similarity
        
        # Recency boost
        age_days = (datetime.now() - datetime.fromisoformat(result['timestamp'])).days
        recency_boost = 1 / (1 + age_days * 0.1)  # Decay over time
        
        # Severity weight
        severity_weights = {'critical': 1.5, 'high': 1.2, 'medium': 1.0, 'low': 0.8}
        severity_weight = severity_weights.get(result['severity'], 1.0)
        
        # Final score
        final_score = score * recency_boost * severity_weight
        
        scored_results.append({
            **result,
            'reranked_score': final_score,
            'breakdown': {
                'semantic': score,
                'recency': recency_boost,
                'severity': severity_weight
            }
        })
    
    return sorted(scored_results, key=lambda x: x['reranked_score'], reverse=True)
```

**Domande**:
- Q10.1: Re-ranking migliora user satisfaction? Come misurare?
- Q10.2: Pesi ottimali per recency/severity? A/B test?
- Q10.3: Machine learning per learn optimal weights?

**Deliverable**: Comparazione ranking prima/dopo re-rank per 3 queries

---

## Parte E: Production Considerations (Bonus - 30 min)

### Task 5.1: Performance Benchmarking

**Obiettivo**: Misurare latency vector search

**Steps**:

1. Benchmark script:
```python
# benchmark_search.py
import time
import statistics

def benchmark_search(num_queries=100):
    queries = [
        "high CPU usage",
        "malware detected",
        "network intrusion",
        # ... 100 diverse queries
    ]
    
    latencies = []
    
    for query in queries:
        start = time.time()
        results = search_alerts(query, top_k=10)
        latency = (time.time() - start) * 1000  # ms
        latencies.append(latency)
    
    print(f"Mean latency: {statistics.mean(latencies):.2f} ms")
    print(f"P50: {statistics.median(latencies):.2f} ms")
    print(f"P95: {statistics.quantiles(latencies, n=20)[18]:.2f} ms")
    print(f"P99: {statistics.quantiles(latencies, n=100)[98]:.2f} ms")
```

**Domande**:
- Q11.1: Latenza accettabile per dashboard real-time? (<200ms?)
- Q11.2: Come scala con collection size? Test con 10K, 100K, 1M docs
- Q11.3: Indexing strategy: HNSW parameters tuning?

---

### Task 5.2: Embedding Drift Monitoring

**Obiettivo**: Detectare quando model embeddings degradano

**Scenario**: Model upgrade da all-MiniLM-L6-v2 a all-MiniLM-L12-v2

**Steps**:

1. Compute embedding drift:
```python
# drift_detection.py
model_v1 = SentenceTransformer('all-MiniLM-L6-v2')
model_v2 = SentenceTransformer('all-MiniLM-L12-v2')

test_sentences = [...]  # Representative samples

embeddings_v1 = model_v1.encode(test_sentences)
embeddings_v2 = model_v2.encode(test_sentences)

# Can't directly compare (different dimensions), use proxy metric:
# Rank correlation
from scipy.stats import spearmanr

for query in test_queries:
    query_emb_v1 = model_v1.encode([query])
    query_emb_v2 = model_v2.encode([query])
    
    sims_v1 = cosine_similarity(query_emb_v1, embeddings_v1)[0]
    sims_v2 = cosine_similarity(query_emb_v2, embeddings_v2)[0]
    
    rank_corr, p_value = spearmanr(sims_v1, sims_v2)
    print(f"Query: {query}")
    print(f"Rank correlation: {rank_corr:.4f} (p={p_value:.4f})")
```

**Domande**:
- Q12.1: Quando è necessario re-index tutta la collection?
- Q12.2: Strategy per versioning embeddings?
- Q12.3: Blue-green deployment per model updates?

**Deliverable**: Procedura migration plan per model upgrade

---

## Investigation Report Template

```markdown
# Incident Investigation Report

**Incident ID**: <alert_id>  
**Investigator**: <your_name>  
**Date**: <timestamp>  
**Status**: In Progress / Resolved

## 1. Incident Summary
- **Title**: 
- **Severity**: 
- **Affected Host**: 
- **Detection Time**: 
- **Description**: 

## 2. Timeline
| Time | Event |
|------|-------|
| T-60min | Normal baseline metrics |
| T-30min | First anomaly indicator |
| T0 | Alert triggered |
| T+15min | Investigation started |

## 3. Similar Historical Incidents
- Found X similar incidents in past 90 days
- Y were successfully resolved
- Common pattern: 

**Most Similar Incident**:
- ID: 
- Date: 
- Resolution: 

## 4. Metrics Analysis
- CPU: 
- Memory: 
- Disk I/O: 
- Network: 

**Anomaly Detected**: [metric] exceeded threshold by X%

## 5. Root Cause Analysis
**Primary Cause**: 

**Contributing Factors**:
1. 
2. 

**Evidence**:
-

## 6. Resolution Steps
1. 
2. 
3. 

**Commands Executed**:
```bash
# 
```

## 7. Validation
- [ ] Issue resolved
- [ ] Metrics returned to normal
- [ ] No recurrence in 24h
- [ ] Documented in KB

## 8. Lessons Learned
**What went well**:
-

**What could improve**:
-

**Action items**:
- [ ] Update monitoring threshold
- [ ] Add preventive check
- [ ] Update runbook

## 9. Knowledge Base Update
Added/Updated KB article: [ID]
```

---

## Submission

**Consegnare**:
1. Risposte domande in `risposte_esercizio3.md`
2. Embedding visualization PNG
3. Script `investigate_incident.py` completo
4. Investigation report per almeno 2 incident types
5. Benchmark results
6. (Bonus) Drift detection analysis

**Valutazione**:
- Understanding embeddings: 20%
- Vector search queries: 25%
- Investigation workflow: 30%
- KB integration: 15%
- Report quality: 10%
- Bonus tasks: +10%

---

## References

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Chroma DB Guide](https://docs.trychroma.com/)
- [Vector Search Algorithms](https://arxiv.org/abs/1603.09320)
- [HNSW Index](https://arxiv.org/abs/1603.09320)
- [Semantic Search Best Practices](https://www.pinecone.io/learn/semantic-search/)

**Happy investigating! 🔍🚨**
