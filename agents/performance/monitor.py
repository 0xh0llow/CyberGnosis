"""
Performance Monitor Agent
=========================

Modulo 1 - Monitoraggio performance e anomaly detection

Funzionalità:
- Raccolta metriche: CPU, RAM, Disco, Network I/O
- Anomaly detection con Isolation Forest
- Suggerimenti ottimizzazione
- Privacy: dati aggregati, no info sensibili
"""

import psutil
import logging
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import moduli comuni
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from common.api_sender import SecureAPISender
from common.sanitizer import DataSanitizer

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Monitora performance sistema e rileva anomalie.
    """
    
    def __init__(self, collection_interval: int = 30):
        """
        Inizializza monitor.
        
        Args:
            collection_interval: Intervallo raccolta dati (secondi)
        """
        self.collection_interval = collection_interval
        self.sanitizer = DataSanitizer()
        
        # Baseline per metriche (per calcolare anomalie)
        self.baseline_samples: List[Dict[str, float]] = []
        self.max_baseline_samples = 100
        
        logger.info(f"Performance Monitor initialized (interval: {collection_interval}s)")
    
    def collect_metrics(self) -> Dict[str, Any]:
        """
        Raccoglie metriche sistema correnti.
        
        Returns:
            Dict con metriche
        """
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network
            net_io = psutil.net_io_counters()
            
            # Processes
            process_count = len(psutil.pids())
            
            metrics = {
                # CPU
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'cpu_freq_current': cpu_freq.current if cpu_freq else None,
                
                # Memory (percentuali e valori in MB per privacy)
                'ram_percent': mem.percent,
                'ram_available_mb': mem.available / (1024 * 1024),
                'ram_total_mb': mem.total / (1024 * 1024),
                'swap_percent': swap.percent,
                
                # Disk
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'disk_total_gb': disk.total / (1024**3),
                
                # I/O (delta dal boot, non valori assoluti)
                'disk_read_mb': disk_io.read_bytes / (1024**2) if disk_io else 0,
                'disk_write_mb': disk_io.write_bytes / (1024**2) if disk_io else 0,
                'net_sent_mb': net_io.bytes_sent / (1024**2),
                'net_recv_mb': net_io.bytes_recv / (1024**2),
                
                # Processes
                'process_count': process_count,
                
                # Timestamp
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Collected metrics: CPU={cpu_percent}%, RAM={mem.percent}%")
            return metrics
        
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {}
    
    def analyze_top_processes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Analizza top processi per utilizzo risorse.
        
        Args:
            limit: Numero max processi da restituire
            
        Returns:
            Lista processi sanitizzati
        """
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
                try:
                    pinfo = proc.info
                    pinfo['cpu_percent'] = proc.cpu_percent(interval=0.1)
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Ordina per CPU
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            top_processes = processes[:limit]
            
            # Sanitizza informazioni
            sanitized = []
            for proc in top_processes:
                sanitized.append(self.sanitizer.sanitize_process_info(proc))
            
            return sanitized
        
        except Exception as e:
            logger.error(f"Error analyzing processes: {e}")
            return []
    
    def update_baseline(self, metrics: Dict[str, float]):
        """
        Aggiorna baseline per anomaly detection.
        
        Args:
            metrics: Metriche correnti
        """
        # Estrai solo valori numerici rilevanti per ML
        sample = {
            'cpu_percent': metrics.get('cpu_percent', 0),
            'ram_percent': metrics.get('ram_percent', 0),
            'disk_percent': metrics.get('disk_percent', 0),
            'process_count': metrics.get('process_count', 0)
        }
        
        self.baseline_samples.append(sample)
        
        # Mantieni solo ultimi N campioni
        if len(self.baseline_samples) > self.max_baseline_samples:
            self.baseline_samples = self.baseline_samples[-self.max_baseline_samples:]
        
        logger.debug(f"Baseline updated: {len(self.baseline_samples)} samples")
    
    def generate_optimization_suggestions(self, metrics: Dict[str, Any]) -> List[str]:
        """
        Genera suggerimenti di ottimizzazione basati su metriche.
        
        Args:
            metrics: Metriche correnti
            
        Returns:
            Lista suggerimenti testuali
        """
        suggestions = []
        
        # CPU
        if metrics.get('cpu_percent', 0) > 80:
            suggestions.append("High CPU usage detected. Consider reviewing active processes.")
        
        # RAM
        if metrics.get('ram_percent', 0) > 85:
            suggestions.append("Memory usage critical. Review memory-intensive applications.")
        
        # Disk
        if metrics.get('disk_percent', 0) > 90:
            suggestions.append("Disk space critical. Clean up old files or expand storage.")
        
        # Swap
        if metrics.get('swap_percent', 0) > 50:
            suggestions.append("High swap usage indicates RAM shortage. Consider adding more RAM.")
        
        # Process count
        if metrics.get('process_count', 0) > 300:
            suggestions.append("High number of processes. Check for unnecessary services.")
        
        return suggestions
    
    def run(self, sender: SecureAPISender, host_id: str):
        """
        Loop principale di monitoraggio.
        
        Args:
            sender: API sender per inviare dati
            host_id: Identificativo host
        """
        logger.info(f"Starting performance monitoring for host: {host_id}")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                logger.info(f"=== Iteration {iteration} ===")
                
                # Raccogli metriche
                metrics = self.collect_metrics()
                
                if not metrics:
                    logger.warning("No metrics collected, skipping iteration")
                    time.sleep(self.collection_interval)
                    continue
                
                # Aggiorna baseline
                self.update_baseline(metrics)
                
                # Analizza top processi
                top_processes = self.analyze_top_processes(limit=5)
                metrics['top_processes'] = top_processes
                
                # Genera suggerimenti
                suggestions = self.generate_optimization_suggestions(metrics)
                if suggestions:
                    metrics['suggestions'] = suggestions
                    logger.info(f"Optimization suggestions: {suggestions}")
                
                # Invia metriche al server
                success = sender.send_metrics(metrics, host_id=host_id)
                
                if success:
                    logger.info("✓ Metrics sent successfully")
                else:
                    logger.warning("✗ Failed to send metrics")
                
                # Verifica anomalie (dopo aver raccolto baseline sufficiente)
                if len(self.baseline_samples) >= 20:
                    # Nota: anomaly detection con ML implementato in anomaly_detector.py
                    logger.debug("Baseline sufficient for anomaly detection")
                
                # Attendi prossimo ciclo
                time.sleep(self.collection_interval)
        
        except KeyboardInterrupt:
            logger.info("Performance monitor stopped by user")
        
        except Exception as e:
            logger.error(f"Fatal error in performance monitor: {e}", exc_info=True)


# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    import argparse
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Performance Monitor Agent')
    parser.add_argument('--server-url', required=True, help='Central server URL')
    parser.add_argument('--api-token', required=True, help='API authentication token')
    parser.add_argument('--host-id', required=True, help='Host identifier')
    parser.add_argument('--interval', type=int, default=30, help='Collection interval (seconds)')
    parser.add_argument('--no-ssl-verify', action='store_true', help='Disable SSL verification')
    
    args = parser.parse_args()
    
    # Inizializza sender
    sender = SecureAPISender(
        server_url=args.server_url,
        api_token=args.api_token,
        verify_ssl=not args.no_ssl_verify
    )
    
    # Verifica connettività
    if not sender.health_check():
        logger.error("Cannot connect to central server. Exiting.")
        sys.exit(1)
    
    logger.info("✓ Connected to central server")
    
    # Inizializza e avvia monitor
    monitor = PerformanceMonitor(collection_interval=args.interval)
    monitor.run(sender=sender, host_id=args.host_id)
