"""
Test suite per il modulo anomaly detector
Testa l'algoritmo Isolation Forest e la gestione dei dati.
"""
import pytest
import numpy as np
from datetime import datetime, timedelta
from agents.performance.anomaly_detector import PerformanceAnomalyDetector


# Alias per compatibilità nei test
AnomalyDetector = PerformanceAnomalyDetector


class TestAnomalyDetectorInit:
    """Test inizializzazione detector"""
    
    def test_default_initialization(self):
        """Test inizializzazione con parametri default"""
        detector = AnomalyDetector()
        assert detector.contamination == 0.1
        assert detector.model is not None
        assert detector.is_trained is False
    
    def test_custom_contamination(self):
        """Test inizializzazione con contamination custom"""
        detector = AnomalyDetector(contamination=0.05)
        assert detector.contamination == 0.05
    
    def test_invalid_contamination(self):
        """Test che contamination invalido sollevi errore"""
        with pytest.raises(ValueError):
            AnomalyDetector(contamination=1.5)  # Deve essere tra 0 e 0.5


class TestFeatureExtraction:
    """Test estrazione features dalle metriche"""
    
    def test_extract_features_basic(self):
        """Test estrazione features base"""
        detector = AnomalyDetector()
        metrics = {
            "cpu_percent": 50.0,
            "memory_percent": 60.0,
            "disk_percent": 70.0
        }
        
        features = detector._extract_features(metrics)
        
        assert len(features) == 3
        assert features[0] == 50.0
        assert features[1] == 60.0
        assert features[2] == 70.0
    
    def test_extract_features_missing_keys(self):
        """Test estrazione con chiavi mancanti"""
        detector = AnomalyDetector()
        metrics = {
            "cpu_percent": 50.0,
            # memory_percent mancante
            "disk_percent": 70.0
        }
        
        features = detector._extract_features(metrics)
        
        assert len(features) == 3
        assert features[0] == 50.0
        assert features[1] == 0.0  # Default per chiave mancante
        assert features[2] == 70.0
    
    def test_extract_features_nested(self):
        """Test estrazione da metriche nested"""
        detector = AnomalyDetector()
        metrics = {
            "metrics": {
                "cpu_percent": 80.0,
                "memory_percent": 70.0,
                "disk_percent": 60.0
            }
        }
        
        features = detector._extract_features(metrics["metrics"])
        assert len(features) == 3
        assert features[0] == 80.0


class TestTraining:
    """Test training del modello"""
    
    def test_train_with_normal_data(self):
        """Test training con dati normali"""
        detector = AnomalyDetector(contamination=0.1)
        
        # Genera dati normali (CPU 20-50%, Memory 30-60%, Disk 40-70%)
        training_data = []
        for _ in range(100):
            training_data.append({
                "cpu_percent": np.random.uniform(20, 50),
                "memory_percent": np.random.uniform(30, 60),
                "disk_percent": np.random.uniform(40, 70)
            })
        
        detector.train(training_data)
        
        assert detector.is_trained is True
        assert detector.model is not None
    
    def test_train_insufficient_data(self):
        """Test che training con dati insufficienti sollevi errore"""
        detector = AnomalyDetector()
        
        # Solo 5 campioni (troppo pochi)
        training_data = [
            {"cpu_percent": 20, "memory_percent": 30, "disk_percent": 40}
            for _ in range(5)
        ]
        
        with pytest.raises(ValueError):
            detector.train(training_data)
    
    def test_train_updates_model(self):
        """Test che train aggiorni il modello"""
        detector = AnomalyDetector()
        
        training_data = [
            {"cpu_percent": 30, "memory_percent": 40, "disk_percent": 50}
            for _ in range(50)
        ]
        
        detector.train(training_data)
        first_model = detector.model
        
        # Re-train con nuovi dati
        detector.train(training_data)
        second_model = detector.model
        
        # Verifica che il modello sia stato aggiornato
        assert first_model is not second_model


class TestPrediction:
    """Test previsione anomalie"""
    
    @pytest.fixture
    def trained_detector(self):
        """Fixture con detector già trained"""
        detector = AnomalyDetector(contamination=0.1)
        
        # Training con dati normali
        training_data = []
        for _ in range(100):
            training_data.append({
                "cpu_percent": np.random.uniform(20, 50),
                "memory_percent": np.random.uniform(30, 60),
                "disk_percent": np.random.uniform(40, 70)
            })
        
        detector.train(training_data)
        return detector
    
    def test_predict_normal_data(self, trained_detector):
        """Test previsione su dati normali"""
        normal_metrics = {
            "cpu_percent": 35.0,
            "memory_percent": 45.0,
            "disk_percent": 55.0
        }
        
        result = trained_detector.predict(normal_metrics)
        
        assert "is_anomaly" in result
        assert "anomaly_score" in result
        assert "confidence" in result
        assert result["is_anomaly"] is False
    
    def test_predict_anomalous_data(self, trained_detector):
        """Test previsione su dati anomali"""
        anomalous_metrics = {
            "cpu_percent": 99.9,  # Molto alto
            "memory_percent": 98.5,  # Molto alto
            "disk_percent": 95.0  # Molto alto
        }
        
        result = trained_detector.predict(anomalous_metrics)
        
        assert result["is_anomaly"] is True
        assert result["anomaly_score"] < -0.5  # Score negativo per anomalie
    
    def test_predict_without_training(self):
        """Test che predict senza training sollevi errore"""
        detector = AnomalyDetector()
        
        metrics = {"cpu_percent": 50, "memory_percent": 60, "disk_percent": 70}
        
        with pytest.raises(RuntimeError):
            detector.predict(metrics)
    
    def test_anomaly_score_range(self, trained_detector):
        """Test che anomaly score sia nel range valido"""
        metrics = {"cpu_percent": 40, "memory_percent": 50, "disk_percent": 60}
        
        result = trained_detector.predict(metrics)
        
        # Score deve essere tra -1 e 1 circa
        assert -2 <= result["anomaly_score"] <= 2
        assert 0 <= result["confidence"] <= 1


class TestBatchPrediction:
    """Test previsione batch"""
    
    @pytest.fixture
    def trained_detector(self):
        """Fixture con detector trained"""
        detector = AnomalyDetector(contamination=0.1)
        training_data = [
            {"cpu_percent": np.random.uniform(20, 50),
             "memory_percent": np.random.uniform(30, 60),
             "disk_percent": np.random.uniform(40, 70)}
            for _ in range(100)
        ]
        detector.train(training_data)
        return detector
    
    def test_batch_predict(self, trained_detector):
        """Test previsione su batch di dati"""
        batch_metrics = [
            {"cpu_percent": 30, "memory_percent": 40, "disk_percent": 50},
            {"cpu_percent": 35, "memory_percent": 45, "disk_percent": 55},
            {"cpu_percent": 99, "memory_percent": 98, "disk_percent": 97}  # Anomalo
        ]
        
        results = trained_detector.predict_batch(batch_metrics)
        
        assert len(results) == 3
        assert all("is_anomaly" in r for r in results)
        
        # L'ultimo dovrebbe essere anomalo
        assert results[2]["is_anomaly"] is True


class TestModelPersistence:
    """Test salvataggio e caricamento modello"""
    
    def test_save_model(self, tmp_path, trained_detector):
        """Test salvataggio modello"""
        model_path = tmp_path / "model.pkl"
        
        trained_detector.save_model(str(model_path))
        
        assert model_path.exists()
    
    def test_load_model(self, tmp_path):
        """Test caricamento modello"""
        # Train e salva
        detector1 = AnomalyDetector()
        training_data = [
            {"cpu_percent": 30, "memory_percent": 40, "disk_percent": 50}
            for _ in range(50)
        ]
        detector1.train(training_data)
        
        model_path = tmp_path / "model.pkl"
        detector1.save_model(str(model_path))
        
        # Carica in un nuovo detector
        detector2 = AnomalyDetector()
        detector2.load_model(str(model_path))
        
        assert detector2.is_trained is True
        
        # Test che funzioni
        metrics = {"cpu_percent": 35, "memory_percent": 45, "disk_percent": 55}
        result = detector2.predict(metrics)
        assert "is_anomaly" in result


class TestStatistics:
    """Test statistiche e metriche del detector"""
    
    def test_get_statistics(self, trained_detector):
        """Test ottenimento statistiche"""
        stats = trained_detector.get_statistics()
        
        assert "contamination" in stats
        assert "is_trained" in stats
        assert "n_features" in stats
        assert stats["is_trained"] is True
    
    def test_get_feature_importance(self, trained_detector):
        """Test ottenimento importanza features"""
        importance = trained_detector.get_feature_importance()
        
        assert "cpu_percent" in importance
        assert "memory_percent" in importance
        assert "disk_percent" in importance
        
        # Tutte le importanze devono sommare a 1
        total = sum(importance.values())
        assert abs(total - 1.0) < 0.01


class TestRealWorldScenarios:
    """Test scenari realistici"""
    
    def test_gradual_degradation(self):
        """Test rilevamento degrado graduale"""
        detector = AnomalyDetector(contamination=0.05)
        
        # Training con metriche normali
        training_data = [
            {"cpu_percent": np.random.uniform(20, 40),
             "memory_percent": np.random.uniform(30, 50),
             "disk_percent": np.random.uniform(40, 60)}
            for _ in range(100)
        ]
        detector.train(training_data)
        
        # Simula degrado graduale
        cpu_values = [30, 40, 50, 60, 70, 80, 90, 95]
        anomalies_detected = 0
        
        for cpu in cpu_values:
            metrics = {
                "cpu_percent": cpu,
                "memory_percent": 45,
                "disk_percent": 55
            }
            result = detector.predict(metrics)
            if result["is_anomaly"]:
                anomalies_detected += 1
        
        # Dovrebbe rilevare anomalie quando CPU diventa troppo alta
        assert anomalies_detected > 0
    
    def test_spike_detection(self):
        """Test rilevamento spike improvviso"""
        detector = AnomalyDetector(contamination=0.1)
        
        # Training con dati stabili
        training_data = [
            {"cpu_percent": 30, "memory_percent": 40, "disk_percent": 50}
            for _ in range(100)
        ]
        detector.train(training_data)
        
        # Spike improvviso
        spike_metrics = {
            "cpu_percent": 95.0,
            "memory_percent": 40.0,
            "disk_percent": 50.0
        }
        
        result = detector.predict(spike_metrics)
        
        assert result["is_anomaly"] is True
        assert result["confidence"] > 0.7  # Alta confidenza


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
