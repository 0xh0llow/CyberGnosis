"""
Performance Monitor + Anomaly Detection
========================================

Agent completo con:
- Monitoraggio metriche
- Training anomaly detector
- Rilevamento anomalie
- Invio alert
"""

import logging
import time
import sys
import os
from datetime import datetime

# Import moduli
from monitor import PerformanceMonitor
from anomaly_detector import PerformanceAnomalyDetector

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from common.api_sender import SecureAPISender

logger = logging.getLogger(__name__)


class PerformanceAgentWithAnomaly(PerformanceMonitor):
    """
    Estende PerformanceMonitor con anomaly detection.
    """
    
    def __init__(
        self,
        collection_interval: int = 30,
        training_samples: int = 50,
        contamination: float = 0.1
    ):
        """
        Inizializza agent.
        
        Args:
            collection_interval: Intervallo raccolta (secondi)
            training_samples: Samples per training
            contamination: Frazione anomalie previste
        """
        super().__init__(collection_interval)
        
        self.anomaly_detector = PerformanceAnomalyDetector(
            contamination=contamination,
            model_path="data/performance_anomaly_model.pkl"
        )
        
        self.training_samples_required = training_samples
        self.training_phase = True
        
        # Tenta caricamento modello esistente
        if self.anomaly_detector.load_model():
            self.training_phase = False
            logger.info("✓ Loaded pre-trained anomaly detection model")
        else:
            logger.info(f"Training phase: collecting {training_samples} samples...")
    
    def run_with_anomaly_detection(self, sender: SecureAPISender, host_id: str):
        """
        Loop principale con anomaly detection.
        
        Args:
            sender: API sender
            host_id: Host identifier
        """
        logger.info(f"Starting enhanced performance monitoring for host: {host_id}")
        
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
                
                # --- TRAINING PHASE ---
                if self.training_phase:
                    self.anomaly_detector.add_training_sample(metrics)
                    
                    samples_count = len(self.anomaly_detector.training_data)
                    logger.info(f"Training: {samples_count}/{self.training_samples_required} samples")
                    
                    # Training quando campioni sufficienti
                    if samples_count >= self.training_samples_required:
                        if self.anomaly_detector.train(min_samples=self.training_samples_required):
                            self.training_phase = False
                            logger.info("✓ Training completed - switching to detection mode")
                
                # --- DETECTION PHASE ---
                else:
                    # Rileva anomalie
                    is_anomaly, score, explanation = self.anomaly_detector.predict(metrics)
                    
                    if is_anomaly:
                        logger.warning(f"⚠️  ANOMALY DETECTED: {explanation}")
                        
                        # Invia alert al server
                        alert_sent = sender.send_alert(
                            alert_type='performance',
                            severity='high',
                            title='Performance Anomaly Detected',
                            description=explanation,
                            metadata={
                                'anomaly_score': float(score),
                                'metrics': {
                                    'cpu_percent': metrics.get('cpu_percent'),
                                    'ram_percent': metrics.get('ram_percent'),
                                    'disk_percent': metrics.get('disk_percent'),
                                    'process_count': metrics.get('process_count')
                                }
                            },
                            host_id=host_id
                        )
                        
                        if alert_sent:
                            logger.info("✓ Anomaly alert sent")
                    else:
                        logger.info(f"✓ Normal behavior (score: {score:.3f})")
                
                # Aggiorna baseline
                self.update_baseline(metrics)
                
                # Analizza top processi
                top_processes = self.analyze_top_processes(limit=5)
                metrics['top_processes'] = top_processes
                
                # Genera suggerimenti
                suggestions = self.generate_optimization_suggestions(metrics)
                if suggestions:
                    metrics['suggestions'] = suggestions
                
                # Aggiungi info anomaly
                if not self.training_phase:
                    metrics['anomaly_detection'] = {
                        'is_anomaly': is_anomaly,
                        'score': float(score)
                    }
                
                # Invia metriche al server
                success = sender.send_metrics(metrics, host_id=host_id)
                
                if success:
                    logger.info("✓ Metrics sent successfully")
                else:
                    logger.warning("✗ Failed to send metrics")
                
                # Attendi prossimo ciclo
                time.sleep(self.collection_interval)
        
        except KeyboardInterrupt:
            logger.info("Performance agent stopped by user")
        
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)


# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    import argparse
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] %(name)s - %(message)s'
    )
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Performance Monitor Agent with Anomaly Detection'
    )
    parser.add_argument('--server-url', required=True, help='Central server URL')
    parser.add_argument('--api-token', required=True, help='API authentication token')
    parser.add_argument('--host-id', required=True, help='Host identifier')
    parser.add_argument('--interval', type=int, default=30, help='Collection interval (seconds)')
    parser.add_argument('--training-samples', type=int, default=50, help='Training samples')
    parser.add_argument('--contamination', type=float, default=0.1, help='Anomaly contamination rate')
    parser.add_argument('--no-ssl-verify', action='store_true', help='Disable SSL verification')
    
    args = parser.parse_args()
    
    # Crea directory data se non esiste
    os.makedirs('data', exist_ok=True)
    
    # Inizializza sender
    sender = SecureAPISender(
        server_url=args.server_url,
        api_token=args.api_token,
        verify_ssl=not args.no_ssl_verify
    )
    
    # Verifica connettività
    logger.info("Checking server connectivity...")
    if not sender.health_check():
        logger.error("❌ Cannot connect to central server. Exiting.")
        sys.exit(1)
    
    logger.info("✓ Connected to central server")
    
    # Inizializza e avvia agent
    agent = PerformanceAgentWithAnomaly(
        collection_interval=args.interval,
        training_samples=args.training_samples,
        contamination=args.contamination
    )
    
    agent.run_with_anomaly_detection(sender=sender, host_id=args.host_id)
