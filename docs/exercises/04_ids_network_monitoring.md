# Esercizio 4: IDS & Network Security Monitoring

**Durata stimata**: 3-4 ore  
**Livello**: Avanzato  
**Obiettivi**: Implementare detection pattern-based, analizzare traffico rete, gestire alert IDS, tuning false positives

---

## Parte A: Log-Based Intrusion Detection (60 min)

### Task 1.1: Understanding System Logs

**Obiettivo**: Familiarizzare con log format e pattern analysis

**Steps**:

1. Genera log samples:
```bash
# simulate_logs.sh
cat > /tmp/auth.log << 'EOF'
Jan 24 10:15:23 server sshd[12345]: Failed password for root from 192.168.1.100 port 45678 ssh2
Jan 24 10:15:25 server sshd[12346]: Failed password for root from 192.168.1.100 port 45679 ssh2
Jan 24 10:15:27 server sshd[12347]: Failed password for root from 192.168.1.100 port 45680 ssh2
Jan 24 10:15:29 server sshd[12348]: Failed password for admin from 192.168.1.100 port 45681 ssh2
Jan 24 10:15:31 server sshd[12349]: Failed password for admin from 192.168.1.100 port 45682 ssh2
Jan 24 10:15:33 server sshd[12350]: Accepted password for user1 from 10.0.0.50 port 55123 ssh2
Jan 24 10:20:15 server sshd[12380]: Failed password for root from 203.0.113.5 port 12345 ssh2
Jan 24 10:20:16 server sshd[12381]: Failed password for root from 203.0.113.5 port 12346 ssh2
Jan 24 10:20:17 server sshd[12382]: Failed password for root from 203.0.113.5 port 12347 ssh2
Jan 24 10:20:18 server sshd[12383]: Failed password for root from 203.0.113.5 port 12348 ssh2
Jan 24 10:20:19 server sshd[12384]: Failed password for root from 203.0.113.5 port 12349 ssh2
Jan 24 10:20:20 server sshd[12385]: Failed password for root from 203.0.113.5 port 12350 ssh2
Jan 24 10:20:21 server sshd[12386]: Failed password for root from 203.0.113.5 port 12351 ssh2
Jan 24 10:25:45 server sudo: user1 : TTY=pts/0 ; PWD=/home/user1 ; USER=root ; COMMAND=/bin/bash
Jan 24 10:25:45 server sudo: pam_unix(sudo:session): session opened for user root
Jan 24 10:26:10 server su: pam_unix(su:auth): authentication failure; logname= uid=1000 euid=0 tty=pts/0 ruser=user1 rhost=  user=root
Jan 24 10:26:12 server su: FAILED SU (to root) user1 on pts/0
EOF
```

2. Parse logs con regex:
```python
# parse_logs.py
import re
from datetime import datetime
from collections import defaultdict

class LogParser:
    def __init__(self):
        self.patterns = {
            'failed_ssh': r'Failed password for (\w+) from ([\d\.]+) port (\d+)',
            'accepted_ssh': r'Accepted password for (\w+) from ([\d\.]+) port (\d+)',
            'sudo_command': r'sudo:.*USER=(\w+).*COMMAND=(.+)',
            'failed_su': r'FAILED SU \(to (\w+)\) (\w+)',
        }
    
    def parse_line(self, line):
        """Parse single log line"""
        # Extract timestamp
        ts_match = re.match(r'(\w+ \d+ \d+:\d+:\d+)', line)
        if not ts_match:
            return None
        
        timestamp = ts_match.group(1)
        
        # Try each pattern
        for event_type, pattern in self.patterns.items():
            match = re.search(pattern, line)
            if match:
                return {
                    'timestamp': timestamp,
                    'event_type': event_type,
                    'details': match.groups(),
                    'raw': line
                }
        
        return None
    
    def analyze_file(self, filepath):
        """Analyze entire log file"""
        events = []
        
        with open(filepath) as f:
            for line in f:
                parsed = self.parse_line(line)
                if parsed:
                    events.append(parsed)
        
        return events

# Parse auth.log
parser = LogParser()
events = parser.analyze_file('/tmp/auth.log')

print(f"Total events: {len(events)}")
print(f"\nEvent breakdown:")
for event_type in set(e['event_type'] for e in events):
    count = sum(1 for e in events if e['event_type'] == event_type)
    print(f"  {event_type}: {count}")
```

**Domande**:
- Q1.1: Quanti failed SSH login attempts nel log?
- Q1.2: Quali IP sorgente hanno generato tentativi falliti?
- Q1.3: Pattern time-based: gli attacchi sono concentrati temporalmente?

**Deliverable**: Output parsing + lista IP sospetti con frequenza tentativi

---

### Task 1.2: Brute Force Detection Implementation

**Obiettivo**: Implementare detector per SSH brute force

**Steps**:

1. Crea detector:
```python
# brute_force_detector.py
from datetime import datetime, timedelta
from collections import defaultdict

class BruteForceDetector:
    def __init__(self, threshold=5, time_window=300):
        """
        Args:
            threshold: Max failed attempts before alert
            time_window: Time window in seconds
        """
        self.threshold = threshold
        self.time_window = timedelta(seconds=time_window)
        
        # Track attempts per IP
        self.attempts = defaultdict(list)  # IP -> [timestamps]
    
    def process_event(self, event):
        """Process authentication event"""
        if event['event_type'] != 'failed_ssh':
            return None
        
        username, ip, port = event['details']
        timestamp = datetime.strptime(
            event['timestamp'], 
            '%b %d %H:%M:%S'
        ).replace(year=datetime.now().year)
        
        # Add attempt
        self.attempts[ip].append(timestamp)
        
        # Clean old attempts outside window
        cutoff = timestamp - self.time_window
        self.attempts[ip] = [
            ts for ts in self.attempts[ip] 
            if ts > cutoff
        ]
        
        # Check threshold
        if len(self.attempts[ip]) >= self.threshold:
            return self._create_alert(ip, username, timestamp)
        
        return None
    
    def _create_alert(self, ip, username, timestamp):
        """Generate brute force alert"""
        return {
            'alert_type': 'brute_force',
            'severity': 'high',
            'source_ip': ip,
            'target_username': username,
            'attempt_count': len(self.attempts[ip]),
            'time_window': self.time_window.seconds,
            'timestamp': timestamp.isoformat(),
            'description': f"Brute force attack detected from {ip}. "
                          f"{len(self.attempts[ip])} failed attempts in {self.time_window.seconds}s"
        }

# Test detector
detector = BruteForceDetector(threshold=5, time_window=300)

alerts = []
for event in events:
    alert = detector.process_event(event)
    if alert:
        alerts.append(alert)
        print(f"\n🚨 ALERT: {alert['description']}")
        print(f"   Source: {alert['source_ip']}")
        print(f"   Attempts: {alert['attempt_count']}")

print(f"\n\nTotal alerts generated: {len(alerts)}")
```

**Domande**:
- Q2.1: Con threshold=5 e window=300s, quanti alert vengono generati?
- Q2.2: Prova threshold=3: aumentano falsi positivi?
- Q2.3: Come gestire distributed brute force (multiple IP)?

**Deliverable**: 
- Output detector con almeno 2 alert triggered
- Analisi tuning: tabella (threshold, window) vs (alerts, estimated_FP)

---

### Task 1.3: Multi-Stage Attack Detection

**Obiettivo**: Detect attack chain (brute force → successful login → privilege escalation)

**Steps**:

1. Correlation engine:
```python
# attack_chain_detector.py
class AttackChainDetector:
    def __init__(self):
        self.attack_chains = []  # Lista catene rilevate
        self.recent_events = []  # Sliding window eventi
        self.window_size = timedelta(minutes=30)
    
    def process_event(self, event):
        """Correlate events to detect multi-stage attacks"""
        timestamp = self._parse_timestamp(event['timestamp'])
        
        # Add to window
        self.recent_events.append((timestamp, event))
        
        # Clean old events
        cutoff = timestamp - self.window_size
        self.recent_events = [
            (ts, evt) for ts, evt in self.recent_events 
            if ts > cutoff
        ]
        
        # Check for attack patterns
        chain = self._detect_chain()
        if chain:
            self.attack_chains.append(chain)
            return chain
        
        return None
    
    def _detect_chain(self):
        """Detect attack sequence patterns"""
        # Pattern: failed attempts → successful login → sudo/su
        
        # 1. Find brute force window
        failed_logins = [
            (ts, evt) for ts, evt in self.recent_events
            if evt['event_type'] == 'failed_ssh'
        ]
        
        if len(failed_logins) < 3:
            return None
        
        # 2. Check for subsequent successful login from same IP
        for ts_success, evt_success in self.recent_events:
            if evt_success['event_type'] != 'accepted_ssh':
                continue
            
            _, source_ip_success, _ = evt_success['details']
            
            # Find prior failed attempts from same IP
            prior_failures = [
                (ts, evt) for ts, evt in failed_logins
                if ts < ts_success and evt['details'][1] == source_ip_success
            ]
            
            if len(prior_failures) < 3:
                continue
            
            # 3. Check for privilege escalation after successful login
            for ts_priv, evt_priv in self.recent_events:
                if ts_priv <= ts_success:
                    continue
                
                if evt_priv['event_type'] in ['sudo_command', 'failed_su']:
                    return {
                        'alert_type': 'attack_chain',
                        'severity': 'critical',
                        'stages': [
                            f"Stage 1: {len(prior_failures)} failed login attempts",
                            f"Stage 2: Successful login from {source_ip_success}",
                            f"Stage 3: Privilege escalation attempt"
                        ],
                        'source_ip': source_ip_success,
                        'timeline': {
                            'start': prior_failures[0][0].isoformat(),
                            'compromise': ts_success.isoformat(),
                            'escalation': ts_priv.isoformat()
                        }
                    }
        
        return None

# Test
chain_detector = AttackChainDetector()
for event in events:
    chain = chain_detector.process_event(event)
    if chain:
        print("\n🔥 CRITICAL: Multi-stage attack detected!")
        for stage in chain['stages']:
            print(f"  - {stage}")
        print(f"\nTimeline:")
        for key, time in chain['timeline'].items():
            print(f"  {key}: {time}")
```

**Domande**:
- Q3.1: Il log contiene attack chain completa?
- Q3.2: Quali altri pattern attack chain sono rilevanti? (es: login → file exfiltration)
- Q3.3: Come evitare alert su legitimate user behavior?

**Deliverable**: Implementazione detector per almeno 2 attack chain patterns

---

## Parte B: Network-Based IDS (90 min)

### Task 2.1: Port Scan Detection

**Obiettivo**: Rilevare port scanning activity con packet analysis

**Steps**:

1. Genera traffico port scan:
```bash
# simulate_portscan.sh
# ATTENZIONE: eseguire solo su rete di test!

# SYN scan simulato (target localhost)
for port in {20..100}; do
    timeout 0.1 bash -c "</dev/tcp/127.0.0.1/$port" 2>/dev/null
done

echo "Port scan simulation completed"
```

2. Capture packets:
```bash
# Richiede root
sudo tcpdump -i lo -w /tmp/portscan.pcap "tcp[tcpflags] & tcp-syn != 0" -c 100
```

3. Analyze con scapy:
```python
# analyze_portscan.py
from scapy.all import rdpcap, TCP, IP
from collections import defaultdict
from datetime import datetime, timedelta

class PortScanDetector:
    def __init__(self, threshold=20, time_window=60):
        """
        Args:
            threshold: Min unique ports to consider scan
            time_window: Time window in seconds
        """
        self.threshold = threshold
        self.time_window = time_window
        
        # Track: src_ip -> {dst_port: timestamp}
        self.connections = defaultdict(dict)
    
    def analyze_packet(self, packet):
        """Analyze single packet"""
        if not packet.haslayer(TCP) or not packet.haslayer(IP):
            return None
        
        tcp = packet[TCP]
        ip = packet[IP]
        
        # Only SYN packets (scan attempts)
        if tcp.flags != 'S':  # SYN flag
            return None
        
        src_ip = ip.src
        dst_port = tcp.dport
        timestamp = datetime.fromtimestamp(float(packet.time))
        
        # Record connection attempt
        self.connections[src_ip][dst_port] = timestamp
        
        # Clean old entries
        cutoff = timestamp - timedelta(seconds=self.time_window)
        self.connections[src_ip] = {
            port: ts for port, ts in self.connections[src_ip].items()
            if ts > cutoff
        }
        
        # Check threshold
        unique_ports = len(self.connections[src_ip])
        if unique_ports >= self.threshold:
            return self._create_alert(src_ip, timestamp)
        
        return None
    
    def _create_alert(self, src_ip, timestamp):
        """Generate port scan alert"""
        ports_scanned = sorted(self.connections[src_ip].keys())
        
        return {
            'alert_type': 'port_scan',
            'severity': 'high',
            'source_ip': src_ip,
            'unique_ports_count': len(ports_scanned),
            'port_range': f"{min(ports_scanned)}-{max(ports_scanned)}",
            'timestamp': timestamp.isoformat(),
            'description': f"Port scan detected from {src_ip}. "
                          f"{len(ports_scanned)} ports scanned in {self.time_window}s"
        }

# Analyze pcap
packets = rdpcap('/tmp/portscan.pcap')
detector = PortScanDetector(threshold=20, time_window=60)

print(f"Analyzing {len(packets)} packets...")

for packet in packets:
    alert = detector.analyze_packet(packet)
    if alert:
        print(f"\n🚨 PORT SCAN ALERT")
        print(f"   Source: {alert['source_ip']}")
        print(f"   Ports scanned: {alert['unique_ports_count']}")
        print(f"   Range: {alert['port_range']}")
```

**Domande**:
- Q4.1: Quanti unique ports devono essere scansionati per trigger alert?
- Q4.2: Come distinguere scan aggressivo (nmap -T5) da slow scan (nmap -T1)?
- Q4.3: Stealth SYN scan vs TCP connect scan: differenze nel detection?

**Deliverable**: 
- PCAP file con port scan traffic
- Output detector + analisi pattern (sequential vs random ports)

---

### Task 2.2: DDoS Detection

**Obiettivo**: Identificare pattern DDoS tramite traffic analysis

**Steps**:

1. Simula DDoS traffic:
```python
# simulate_ddos.py
import socket
import threading
import time

def send_flood(target_ip, target_port, duration=10):
    """Simulate SYN flood (educational only!)"""
    end_time = time.time() + duration
    count = 0
    
    while time.time() < end_time:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            s.connect((target_ip, target_port))
            s.close()
            count += 1
        except:
            pass
    
    print(f"Thread sent {count} packets")

# Simulate multiple sources (threads)
threads = []
for i in range(10):
    t = threading.Thread(target=send_flood, args=('127.0.0.1', 8080, 5))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("DDoS simulation completed")
```

2. Detector basato su rate:
```python
# ddos_detector.py
from collections import defaultdict
from datetime import datetime, timedelta

class DDoSDetector:
    def __init__(self, rate_threshold=1000, time_window=10):
        """
        Args:
            rate_threshold: Packets per second threshold
            time_window: Measurement window in seconds
        """
        self.rate_threshold = rate_threshold
        self.time_window = timedelta(seconds=time_window)
        
        # Track packets: dst_ip -> [timestamps]
        self.packet_counts = defaultdict(list)
    
    def process_packet(self, packet):
        """Analyze packet for DDoS patterns"""
        if not packet.haslayer(IP):
            return None
        
        dst_ip = packet[IP].dst
        timestamp = datetime.fromtimestamp(float(packet.time))
        
        # Record packet
        self.packet_counts[dst_ip].append(timestamp)
        
        # Clean old packets
        cutoff = timestamp - self.time_window
        self.packet_counts[dst_ip] = [
            ts for ts in self.packet_counts[dst_ip]
            if ts > cutoff
        ]
        
        # Calculate rate
        count = len(self.packet_counts[dst_ip])
        rate = count / self.time_window.seconds
        
        if rate > self.rate_threshold:
            return self._create_alert(dst_ip, rate, timestamp)
        
        return None
    
    def _create_alert(self, dst_ip, rate, timestamp):
        """Generate DDoS alert"""
        return {
            'alert_type': 'ddos',
            'severity': 'critical',
            'target_ip': dst_ip,
            'packets_per_second': round(rate, 2),
            'threshold': self.rate_threshold,
            'timestamp': timestamp.isoformat(),
            'description': f"Potential DDoS attack on {dst_ip}. "
                          f"Rate: {rate:.0f} pps (threshold: {self.rate_threshold} pps)"
        }
```

**Domande**:
- Q5.1: Quale rate (pps) indica DDoS vs traffico legittimo?
- Q5.2: Come distinguere DDoS da legitimate traffic spike (flash crowd)?
- Q5.3: Protezione: rate limiting vs CAPTCHA vs blackholing?

**Deliverable**: Implementazione detector + test con traffic rates variabili

---

### Task 2.3: Network Anomaly Detection

**Obiettivo**: ML-based traffic anomaly detection

**Steps**:

1. Feature extraction da traffico:
```python
# network_features.py
from scapy.all import rdpcap
import numpy as np

def extract_flow_features(pcap_file, time_window=60):
    """Extract statistical features from network traffic"""
    packets = rdpcap(pcap_file)
    
    # Group packets into flows (src_ip, dst_ip, dst_port)
    flows = defaultdict(list)
    
    for pkt in packets:
        if not pkt.haslayer(IP):
            continue
        
        flow_key = (pkt[IP].src, pkt[IP].dst, pkt[TCP].dport if pkt.haslayer(TCP) else 0)
        flows[flow_key].append(pkt)
    
    # Extract features for each flow
    features = []
    
    for flow_key, flow_packets in flows.items():
        feature_vector = {
            'flow_duration': (flow_packets[-1].time - flow_packets[0].time),
            'total_packets': len(flow_packets),
            'total_bytes': sum(len(pkt) for pkt in flow_packets),
            'avg_packet_size': np.mean([len(pkt) for pkt in flow_packets]),
            'std_packet_size': np.std([len(pkt) for pkt in flow_packets]),
            'packets_per_second': len(flow_packets) / (flow_packets[-1].time - flow_packets[0].time + 0.001),
            
            # TCP-specific
            'syn_count': sum(1 for pkt in flow_packets if pkt.haslayer(TCP) and pkt[TCP].flags == 'S'),
            'fin_count': sum(1 for pkt in flow_packets if pkt.haslayer(TCP) and pkt[TCP].flags & 0x01),
            'rst_count': sum(1 for pkt in flow_packets if pkt.haslayer(TCP) and pkt[TCP].flags & 0x04),
            
            # Directionality (rough estimate)
            'packet_size_variance': np.var([len(pkt) for pkt in flow_packets]),
        }
        
        features.append(feature_vector)
    
    return features

# Extract from normal traffic
normal_features = extract_flow_features('normal_traffic.pcap')

# Extract from attack traffic
attack_features = extract_flow_features('portscan.pcap')

print(f"Normal flows: {len(normal_features)}")
print(f"Attack flows: {len(attack_features)}")
```

2. Train anomaly detector:
```python
# train_network_anomaly.py
from sklearn.ensemble import IsolationForest
import pandas as pd

# Convert to DataFrame
df_normal = pd.DataFrame(normal_features)
df_attack = pd.DataFrame(attack_features)

# Train on normal traffic
X_train = df_normal.values

model = IsolationForest(
    contamination=0.1,  # Expected anomaly rate
    random_state=42
)
model.fit(X_train)

# Test on attack traffic
X_test = df_attack.values
predictions = model.predict(X_test)
anomaly_scores = model.decision_function(X_test)

print(f"Attack flows detected as anomalies: {sum(predictions == -1)}/{len(predictions)}")

# Analyze most anomalous flows
anomaly_indices = np.argsort(anomaly_scores)[:5]  # Top 5 most anomalous
print("\nMost anomalous flows:")
for idx in anomaly_indices:
    print(f"\nFlow {idx}:")
    print(df_attack.iloc[idx])
```

**Domande**:
- Q6.1: Quali feature hanno maggiore importanza per detection?
- Q6.2: Accuracy su port scan traffic? False positive rate?
- Q6.3: Come gestire concept drift (traffico normale cambia nel tempo)?

**Deliverable**: 
- Feature extraction script completo
- ML model con evaluation metrics (precision, recall, F1)
- Feature importance analysis

---

## Parte C: IDS Integration & Tuning (60 min)

### Task 3.1: Deploy IDS Agent

**Obiettivo**: Integrare IDS con central server

**Steps**:

1. Crea IDS agent runner:
```python
# agents/ids/run_agent.py
import time
import logging
from intrusion_detector import LogBasedIDS, NetworkBasedIDS
from ..common.api_sender import SecureAPISender
from ..common.sanitizer import DataSanitizer

class IDSAgent:
    def __init__(self, server_url, api_token, host_id):
        self.log_ids = LogBasedIDS(log_path='/var/log/auth.log')
        self.network_ids = NetworkBasedIDS(interface='eth0')
        
        self.sender = SecureAPISender(server_url, api_token, host_id)
        self.sanitizer = DataSanitizer()
        
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self):
        """Start IDS monitoring"""
        self.logger.info("Starting IDS agent...")
        
        # Start network monitoring in separate thread
        import threading
        network_thread = threading.Thread(target=self._monitor_network)
        network_thread.daemon = True
        network_thread.start()
        
        # Monitor logs in main thread
        self._monitor_logs()
    
    def _monitor_logs(self):
        """Monitor system logs"""
        while True:
            try:
                # Process new log entries
                alerts = self.log_ids.check_for_intrusions()
                
                for alert in alerts:
                    self._send_alert(alert)
                
                time.sleep(10)  # Check every 10s
                
            except Exception as e:
                self.logger.error(f"Log monitoring error: {e}")
    
    def _monitor_network(self):
        """Monitor network traffic"""
        while True:
            try:
                alerts = self.network_ids.analyze_traffic(duration=30)
                
                for alert in alerts:
                    self._send_alert(alert)
                
            except Exception as e:
                self.logger.error(f"Network monitoring error: {e}")
    
    def _send_alert(self, alert):
        """Send alert to central server"""
        # Sanitize sensitive data
        sanitized = self.sanitizer.validate_before_send(alert)
        
        # Send to server
        success = self.sender.send_alert(sanitized)
        
        if success:
            self.logger.info(f"Alert sent: {alert['alert_type']}")
        else:
            self.logger.error(f"Failed to send alert: {alert['alert_type']}")

if __name__ == '__main__':
    import os
    
    agent = IDSAgent(
        server_url=os.getenv('CENTRAL_SERVER_URL'),
        api_token=os.getenv('API_TOKEN'),
        host_id=os.getenv('HOST_ID')
    )
    
    agent.start_monitoring()
```

2. Deploy agent:
```bash
cd agents
export CENTRAL_SERVER_URL="http://localhost:8000"
export API_TOKEN="<TOKEN>"
export HOST_ID="ids-protected-host"

python -m ids.run_agent
```

**Domande**:
- Q7.1: Agent monitora logs e network concorrentemente?
- Q7.2: Come gestire backpressure se server non risponde?
- Q7.3: Performance impact: CPU/memory overhead?

---

### Task 3.2: False Positive Tuning

**Obiettivo**: Ridurre false positive rate

**Steps**:

1. Collect alert statistics:
```python
# analyze_alerts.py
import requests
from collections import Counter

# Get all IDS alerts
response = requests.get(
    f"{API_URL}/api/alerts?alert_type=intrusion",
    headers=headers
)
alerts = response.json()

# Analyze patterns
alert_types = Counter(a['metadata'].get('attack_type') for a in alerts)
severities = Counter(a['severity'] for a in alerts)
sources = Counter(a['metadata'].get('source_ip') for a in alerts)

print("=== Alert Statistics ===")
print(f"\nTotal IDS alerts: {len(alerts)}")
print(f"\nBy type:")
for type_, count in alert_types.most_common():
    print(f"  {type_}: {count}")

print(f"\nTop source IPs:")
for ip, count in sources.most_common(10):
    print(f"  {ip}: {count} alerts")
```

2. Implement whitelist/blacklist:
```python
# tuning_config.py
IDS_CONFIG = {
    # Whitelisted IPs (trusted sources)
    'whitelisted_ips': {
        '10.0.0.0/8',      # Internal network
        '192.168.0.0/16',  # Internal network
        '172.16.0.0/12',   # Internal network
    },
    
    # Blacklisted IPs (known attackers)
    'blacklisted_ips': {
        '203.0.113.0/24',  # Known scanner range
    },
    
    # Threshold adjustments
    'thresholds': {
        'brute_force': {
            'failed_attempts': 10,  # Increased from 5
            'time_window': 600,     # 10 minutes
        },
        'port_scan': {
            'unique_ports': 30,     # Increased from 20
            'time_window': 120,
        },
    },
    
    # Alert suppression rules
    'suppression_rules': [
        {
            'alert_type': 'brute_force',
            'source_ip': '10.0.0.5',  # Monitoring system
            'reason': 'Automated health checks'
        },
        {
            'alert_type': 'port_scan',
            'source_ip': '10.0.0.10',  # Vulnerability scanner
            'reason': 'Scheduled security scan'
        }
    ]
}

def should_suppress_alert(alert, config):
    """Check if alert should be suppressed"""
    # Check whitelist
    if alert.get('source_ip') in config['whitelisted_ips']:
        return True
    
    # Check suppression rules
    for rule in config['suppression_rules']:
        if (alert['alert_type'] == rule['alert_type'] and
            alert.get('source_ip') == rule['source_ip']):
            logging.info(f"Alert suppressed: {rule['reason']}")
            return True
    
    return False
```

**Domande**:
- Q8.1: Dopo tuning, quanto si riduce false positive rate?
- Q8.2: Trade-off: ridurre FP aumenta false negatives?
- Q8.3: Come gestire whitelist di IP dinamici (DHCP)?

**Deliverable**: 
- Tuning config file
- Before/after metrics: FP rate, alert volume, detection accuracy

---

## Parte D: Advanced IDS Topics (Bonus - 45 min)

### Task 4.1: Signature-Based Detection with Snort Rules

**Obiettivo**: Implementare signature matching

**Steps**:

1. Create Snort-like rules:
```python
# snort_rules.txt
alert tcp any any -> $HOME_NET 22 (msg:"SSH Brute Force Attempt"; flags:S; threshold:type threshold, track by_src, count 10, seconds 60; sid:1000001;)
alert tcp any any -> $HOME_NET any (msg:"Possible Port Scan"; flags:S; threshold:type threshold, track by_src, count 20, seconds 30; sid:1000002;)
alert tcp $EXTERNAL_NET any -> $HOME_NET 80 (msg:"SQL Injection Attempt"; content:"' OR '1'='1"; nocase; sid:1000003;)
alert tcp any any -> $HOME_NET any (msg:"Malware C&C Communication"; content:"|00 00 00 00|"; dsize:4; sid:1000004;)
```

2. Rule engine:
```python
# signature_engine.py
import re

class SignatureEngine:
    def __init__(self, rules_file):
        self.rules = self._parse_rules(rules_file)
    
    def _parse_rules(self, filepath):
        """Parse Snort-style rules"""
        rules = []
        
        with open(filepath) as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                
                rule = self._parse_rule_line(line)
                if rule:
                    rules.append(rule)
        
        return rules
    
    def match_packet(self, packet):
        """Check if packet matches any signature"""
        matches = []
        
        for rule in self.rules:
            if self._check_rule(packet, rule):
                matches.append(rule)
        
        return matches
```

**Domande**:
- Q9.1: Signature vs anomaly detection: quando usare quale?
- Q9.2: Evasion techniques: fragmentation, encoding bypass signatures?
- Q9.3: Performance: regex matching su high-speed network (10Gbps)?

---

### Task 4.2: Honeypot Integration

**Obiettivo**: Deploy honeypot per early warning

**Steps**:

1. Simple SSH honeypot:
```python
# honeypot.py
import socket
import threading

class SSHHoneypot:
    def __init__(self, port=2222):
        self.port = port
        self.connections = []
    
    def start(self):
        """Start honeypot listener"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', self.port))
        sock.listen(5)
        
        print(f"Honeypot listening on port {self.port}")
        
        while True:
            client, addr = sock.accept()
            threading.Thread(target=self._handle_client, args=(client, addr)).start()
    
    def _handle_client(self, client, addr):
        """Handle attacker connection"""
        print(f"🍯 Honeypot connection from {addr}")
        
        # Log connection
        self.connections.append({
            'source_ip': addr[0],
            'timestamp': datetime.now().isoformat(),
        })
        
        # Send fake SSH banner
        client.send(b"SSH-2.0-OpenSSH_7.4\r\n")
        
        # Receive and log attempts
        try:
            data = client.recv(1024)
            # Log credentials, commands, etc.
        except:
            pass
        finally:
            client.close()
```

**Domande**:
- Q10.1: Honeypot traffic è sempre malevolo?
- Q10.2: Legal risks di running honeypots?
- Q10.3: Come correlate honeypot alerts con production IDS?

**Deliverable**: Honeypot deployment + alert correlation strategy

---

## Submission

**Consegnare**:
1. File `risposte_esercizio4.md`
2. Brute force detector implementation
3. Port scan detector con PCAP samples
4. IDS agent integration code
5. Tuning config con before/after metrics
6. (Bonus) Signature engine o honeypot

**Valutazione**:
- Log parsing & brute force detection: 25%
- Network-based detection (port scan, DDoS): 30%
- IDS agent integration: 20%
- False positive tuning: 20%
- Documentation quality: 5%
- Bonus: +10%

---

## References

- [Snort Rule Writing](https://www.snort.org/documents)
- [Scapy Documentation](https://scapy.readthedocs.io/)
- [OSSEC Log Analysis](https://www.ossec.net/)
- [Bro/Zeek IDS](https://docs.zeek.org/)
- [MITRE ATT&CK Framework](https://attack.mitre.org/)

**Stay vigilant! 🛡️👁️**
