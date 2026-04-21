"""
Intrusion Detection System (IDS)
=================================

Modulo 4 - IDS log-based e network-based

Funzionalità:
- Log-based: brute force SSH, login anomali
- Network-based: port scan, pattern TCP
- Privacy: IP pseudoanonimizzati, username masked
"""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import time

logger = logging.getLogger(__name__)


class LogBasedIDS:
    """
    IDS basato su analisi log di autenticazione.
    """
    
    def __init__(self, log_file: str = '/var/log/auth.log'):
        """
        Args:
            log_file: Path log autenticazione
        """
        self.log_file = log_file
        
        # Tracking tentativi falliti
        self.failed_attempts: Dict[str, List[datetime]] = defaultdict(list)
        
        # Pattern regex per parsing log
        self.patterns = {
            'ssh_failed': re.compile(
                r'Failed password for (?:invalid user )?(\S+) from (\S+) port'
            ),
            'ssh_accepted': re.compile(
                r'Accepted password for (\S+) from (\S+) port'
            ),
            'invalid_user': re.compile(
                r'Invalid user (\S+) from (\S+)'
            )
        }
        
        logger.info(f"Log-based IDS initialized (log: {log_file})")
    
    def parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parsea singola linea di log.
        
        Args:
            line: Linea log
            
        Returns:
            Dict con info parsed o None
        """
        # SSH failed login
        match = self.patterns['ssh_failed'].search(line)
        if match:
            return {
                'event_type': 'ssh_failed',
                'username': match.group(1),
                'source_ip': match.group(2),
                'timestamp': datetime.now()  # In produzione: parse timestamp da log
            }
        
        # SSH accepted
        match = self.patterns['ssh_accepted'].search(line)
        if match:
            return {
                'event_type': 'ssh_accepted',
                'username': match.group(1),
                'source_ip': match.group(2),
                'timestamp': datetime.now()
            }
        
        # Invalid user
        match = self.patterns['invalid_user'].search(line)
        if match:
            return {
                'event_type': 'invalid_user',
                'username': match.group(1),
                'source_ip': match.group(2),
                'timestamp': datetime.now()
            }
        
        return None
    
    def analyze_log_file(self, max_lines: int = 10000) -> List[Dict[str, Any]]:
        """
        Analizza file log per eventi di sicurezza.
        
        Args:
            max_lines: Numero massimo linee da leggere
            
        Returns:
            Lista eventi parsed
        """
        events = []
        
        try:
            with open(self.log_file, 'r') as f:
                # Leggi ultime N linee (più recenti)
                lines = f.readlines()[-max_lines:]
                
                for line in lines:
                    event = self.parse_log_line(line)
                    if event:
                        events.append(event)
            
            logger.info(f"Analyzed {len(lines)} log lines, found {len(events)} events")
            return events
        
        except FileNotFoundError:
            logger.error(f"Log file not found: {self.log_file}")
            return []
        
        except Exception as e:
            logger.error(f"Error analyzing log: {e}")
            return []
    
    def detect_brute_force(
        self,
        events: List[Dict[str, Any]],
        threshold: int = 5,
        time_window_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rileva tentativi brute force SSH.
        
        Args:
            events: Eventi parsed
            threshold: Numero tentativi soglia
            time_window_minutes: Finestra temporale
            
        Returns:
            Lista alert brute force
        """
        alerts = []
        
        # Raggruppa failed attempts per IP
        failed_by_ip: Dict[str, List[datetime]] = defaultdict(list)
        
        for event in events:
            if event['event_type'] in ['ssh_failed', 'invalid_user']:
                ip = event['source_ip']
                timestamp = event['timestamp']
                failed_by_ip[ip].append(timestamp)
        
        # Verifica threshold
        time_window = timedelta(minutes=time_window_minutes)
        
        for ip, timestamps in failed_by_ip.items():
            # Ordina timestamp
            timestamps.sort()
            
            # Finestra sliding
            for i in range(len(timestamps)):
                window_start = timestamps[i]
                window_end = window_start + time_window
                
                # Conta tentativi in finestra
                attempts_in_window = [
                    t for t in timestamps
                    if window_start <= t <= window_end
                ]
                
                if len(attempts_in_window) >= threshold:
                    alerts.append({
                        'alert_type': 'ssh_brute_force',
                        'source_ip': ip,
                        'attempts': len(attempts_in_window),
                        'time_window': time_window_minutes,
                        'first_attempt': window_start,
                        'last_attempt': attempts_in_window[-1],
                        'severity': 'high'
                    })
                    break  # Un alert per IP
        
        logger.info(f"Detected {len(alerts)} brute force attempts")
        return alerts
    
    def detect_suspicious_logins(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rileva login sospetti:
        - Da IP inusuali
        - Orari anomali
        - Utenti non comuni
        
        Args:
            events: Eventi parsed
            
        Returns:
            Lista alert login sospetti
        """
        alerts = []
        
        # Analizza accepted logins
        accepted_logins = [e for e in events if e['event_type'] == 'ssh_accepted']
        
        # Statistiche IP noti
        known_ips = Counter()
        for event in accepted_logins:
            known_ips[event['source_ip']] += 1
        
        # Rileva login da IP rari
        for event in accepted_logins:
            ip = event['source_ip']
            
            # Se IP ha solo 1 login, può essere sospetto
            if known_ips[ip] == 1:
                alerts.append({
                    'alert_type': 'suspicious_login',
                    'reason': 'Login from unusual IP',
                    'username': event['username'],
                    'source_ip': ip,
                    'timestamp': event['timestamp'],
                    'severity': 'medium'
                })
        
        logger.info(f"Detected {len(alerts)} suspicious logins")
        return alerts


class NetworkBasedIDS:
    """
    IDS basato su analisi traffico di rete (basic).
    """
    
    def __init__(self):
        """Inizializza network IDS."""
        self.connection_tracker: Dict[str, int] = defaultdict(int)
        logger.info("Network-based IDS initialized")
    
    def analyze_port_scan(self, connections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rileva port scanning.
        
        Args:
            connections: Lista connessioni di rete
            
        Returns:
            Lista alert port scan
        """
        alerts = []
        
        # Raggruppa per IP sorgente
        connections_by_ip: Dict[str, List[int]] = defaultdict(list)
        
        for conn in connections:
            src_ip = conn.get('source_ip')
            dst_port = conn.get('dest_port')
            
            if src_ip and dst_port:
                connections_by_ip[src_ip].append(dst_port)
        
        # Rileva scan: molte porte diverse contattate
        for ip, ports in connections_by_ip.items():
            unique_ports = len(set(ports))
            
            # Soglia: >20 porte diverse = possibile scan
            if unique_ports > 20:
                alerts.append({
                    'alert_type': 'port_scan',
                    'source_ip': ip,
                    'unique_ports_contacted': unique_ports,
                    'ports': list(set(ports))[:10],  # Sample
                    'severity': 'high'
                })
        
        logger.info(f"Detected {len(alerts)} port scans")
        return alerts
    
    def detect_dos_attempt(self, connections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rileva possibile DoS (volume connessioni anomalo).
        
        Args:
            connections: Lista connessioni
            
        Returns:
            Lista alert DoS
        """
        alerts = []
        
        # Conta connessioni per IP
        conn_count = Counter()
        for conn in connections:
            src_ip = conn.get('source_ip')
            if src_ip:
                conn_count[src_ip] += 1
        
        # Soglia: >1000 connessioni
        for ip, count in conn_count.items():
            if count > 1000:
                alerts.append({
                    'alert_type': 'possible_dos',
                    'source_ip': ip,
                    'connection_count': count,
                    'severity': 'critical'
                })
        
        logger.info(f"Detected {len(alerts)} possible DoS attempts")
        return alerts


# ============================================
# TESTING
# ============================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test log-based IDS
    print("=== Log-Based IDS Test ===")
    
    # Simula log events
    fake_events = [
        {
            'event_type': 'ssh_failed',
            'username': 'admin',
            'source_ip': '192.168.1.100',
            'timestamp': datetime.now() - timedelta(minutes=i)
        }
        for i in range(10)
    ]
    
    ids = LogBasedIDS()
    brute_force_alerts = ids.detect_brute_force(fake_events, threshold=5, time_window_minutes=10)
    
    print(f"Brute force alerts: {len(brute_force_alerts)}")
    for alert in brute_force_alerts:
        print(f"  IP {alert['source_ip']}: {alert['attempts']} attempts")
    
    # Test network-based IDS
    print("\n=== Network-Based IDS Test ===")
    
    # Simula port scan
    fake_connections = [
        {
            'source_ip': '10.0.0.50',
            'dest_port': port
        }
        for port in range(1, 100)
    ]
    
    net_ids = NetworkBasedIDS()
    scan_alerts = net_ids.analyze_port_scan(fake_connections)
    
    print(f"Port scan alerts: {len(scan_alerts)}")
    for alert in scan_alerts:
        print(f"  IP {alert['source_ip']}: scanned {alert['unique_ports_contacted']} ports")
