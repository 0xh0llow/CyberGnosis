"""
Anomaly Detector - Isolation Forest
====================================

Rileva anomalie nelle metriche di performance usando Isolation Forest.
"""

import numpy as np
import joblib
import logging
import os
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceAnomalyDetector:
    """
    Rileva anomalie nelle metriche usando Isolation Forest.
    """
    
    def __init__(
        self,
        contamination: float = 0.1,
        random_state: int = 42,
        model_path: Optional[str] = None
    ):
        """
        Inizializza detector.
        
        Args:
            contamination: Frazione prevista di anomalie (0.0 - 0.5)
            random_state: Seed per riproducibilità
            model_path: Path per salvare/caricare modello
        """
        self.contamination = contamination
        self.random_state = random_state
        self.model_path = model_path or "performance_anomaly_model.pkl"
        
        # Modello e scaler
        self.model: Optional[IsolationForest] = None
        self.scaler = StandardScaler()
        
        # Feature names
        self.feature_names = [
            'cpu_percent',
            'ram_percent',
            'disk_percent',
            'process_count'
        ]
        
        # Training data buffer
        self.training_data: List[Dict[str, float]] = []
        self.is_trained = False
        
        logger.info(f"Anomaly Detector initialized (contamination={contamination})")
    
    def add_training_sample(self, metrics: Dict[str, float]):
        """
        Aggiungi sample per training.
        
        Args:
            metrics: Metriche da aggiungere
        """
        sample = {key: metrics.get(key, 0) for key in self.feature_names}
        self.training_data.append(sample)
        logger.debug(f"Training samples: {len(self.training_data)}")
    
    def train(self, min_samples: int = 50) -> bool:
        """
        Addestra modello su baseline raccolta.
        
        Args:
            min_samples: Numero minimo campioni richiesti
            
        Returns:
            True se training completato
        """
        if len(self.training_data) < min_samples:
            logger.warning(
                f"Insufficient training data: {len(self.training_data)}/{min_samples}"
            )
            return False
        
        try:
            # Prepara dati
            X = self._prepare_features(self.training_data)
            
            # Normalizza
            X_scaled = self.scaler.fit_transform(X)
            
            # Addestra Isolation Forest
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=self.random_state,
                n_estimators=100,
                max_samples='auto',
                n_jobs=-1
            )
            
            self.model.fit(X_scaled)
            self.is_trained = True
            
            logger.info(f"✓ Model trained on {len(self.training_data)} samples")
            
            # Salva modello
            self.save_model()
            
            return True
        
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False
    
    def predict(self, metrics: Dict[str, float]) -> Tuple[bool, float, str]:
        """
        Predice se metriche sono anomale.
        
        Args:
            metrics: Metriche da analizzare
            
        Returns:
            (is_anomaly, anomaly_score, explanation)
        """
        if not self.is_trained:
            return False, 0.0, "Model not trained yet"
        
        try:
            # Prepara features
            X = self._prepare_features([metrics])
            X_scaled = self.scaler.transform(X)
            
            # Predizione (-1 = anomalia, 1 = normale)
            prediction = self.model.predict(X_scaled)[0]
            is_anomaly = (prediction == -1)
            
            # Anomaly score (più negativo = più anomalo)
            score = self.model.score_samples(X_scaled)[0]
            
            # Genera spiegazione
            explanation = self._generate_explanation(metrics, is_anomaly, score)
            
            return is_anomaly, score, explanation
        
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return False, 0.0, f"Prediction error: {e}"
    
    def _prepare_features(self, data: List[Dict[str, float]]) -> np.ndarray:
        """
        Prepara matrice features da lista dict.
        
        Args:
            data: Lista di dict con metriche
            
        Returns:
            Array numpy (n_samples, n_features)
        """
        X = []
        for sample in data:
            row = [sample.get(key, 0) for key in self.feature_names]
            X.append(row)
        return np.array(X)
    
    def _generate_explanation(
        self,
        metrics: Dict[str, float],
        is_anomaly: bool,
        score: float
    ) -> str:
        """
        Genera spiegazione testuale dell'anomalia.
        
        Args:
            metrics: Metriche analizzate
            is_anomaly: Se è anomalia
            score: Anomaly score
            
        Returns:
            Spiegazione testuale
        """
        if not is_anomaly:
            return "Normal behavior - metrics within expected range"
        
        # Identifica feature più anomale
        anomalous_features = []
        
        if metrics.get('cpu_percent', 0) > 85:
            anomalous_features.append("CPU usage unusually high")
        
        if metrics.get('ram_percent', 0) > 90:
            anomalous_features.append("Memory usage critical")
        
        if metrics.get('disk_percent', 0) > 95:
            anomalous_features.append("Disk space extremely low")
        
        if metrics.get('process_count', 0) > 400:
            anomalous_features.append("Process count abnormally high")
        
        if anomalous_features:
            features_str = ", ".join(anomalous_features)
            explanation = f"Anomaly detected (score: {score:.3f}): {features_str}"
        else:
            explanation = f"Anomaly detected (score: {score:.3f}): unusual metric combination"
        
        return explanation
    
    def save_model(self):
        """Salva modello e scaler su disco."""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'contamination': self.contamination,
                'trained_at': datetime.utcnow().isoformat()
            }
            
            joblib.dump(model_data, self.model_path)
            logger.info(f"✓ Model saved to {self.model_path}")
        
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def load_model(self) -> bool:
        """
        Carica modello da disco.
        
        Returns:
            True se caricamento riuscito
        """
        if not os.path.exists(self.model_path):
            logger.warning(f"Model file not found: {self.model_path}")
            return False
        
        try:
            model_data = joblib.load(self.model_path)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.contamination = model_data['contamination']
            self.is_trained = True
            
            logger.info(f"✓ Model loaded from {self.model_path}")
            logger.info(f"  Trained at: {model_data.get('trained_at', 'unknown')}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False


# ============================================
# TESTING
# ============================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crea detector
    detector = PerformanceAnomalyDetector(contamination=0.1)
    
    # Simula training con dati normali
    print("Training con dati baseline...")
    
    import random
    for i in range(100):
        normal_metrics = {
            'cpu_percent': random.uniform(20, 60),
            'ram_percent': random.uniform(40, 70),
            'disk_percent': random.uniform(30, 60),
            'process_count': random.uniform(100, 200)
        }
        detector.add_training_sample(normal_metrics)
    
    # Train
    detector.train(min_samples=50)
    
    # Test con dati normali
    print("\n--- Test dati normali ---")
    normal_test = {
        'cpu_percent': 45,
        'ram_percent': 55,
        'disk_percent': 50,
        'process_count': 150
    }
    is_anom, score, exp = detector.predict(normal_test)
    print(f"Is anomaly: {is_anom}")
    print(f"Score: {score:.3f}")
    print(f"Explanation: {exp}")
    
    # Test con anomalia
    print("\n--- Test anomalia ---")
    anomaly_test = {
        'cpu_percent': 98,
        'ram_percent': 95,
        'disk_percent': 98,
        'process_count': 500
    }
    is_anom, score, exp = detector.predict(anomaly_test)
    print(f"Is anomaly: {is_anom}")
    print(f"Score: {score:.3f}")
    print(f"Explanation: {exp}")
