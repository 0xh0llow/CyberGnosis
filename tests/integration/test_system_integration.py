"""
Test di integrazione per l'intero sistema
Testa l'interazione tra componenti: agents, central_server, vector_search.
"""
import pytest
import requests
import time
from datetime import datetime
import json


# Configurazione
API_BASE_URL = "http://localhost:8000/api"
CHROMA_BASE_URL = "http://localhost:8001"
TIMEOUT = 10


class TestSystemHealthChecks:
    """Test health check di tutti i componenti"""
    
    def test_central_server_health(self):
        """Test health check central server"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except requests.exceptions.ConnectionError:
            pytest.skip("Central server not running")
    
    def test_database_connection(self):
        """Test connessione database"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
            data = response.json()
            assert "database" in data
            assert data["database"] == "connected"
        except requests.exceptions.ConnectionError:
            pytest.skip("Central server not running")
    
    def test_chroma_health(self):
        """Test health check Chroma DB"""
        try:
            response = requests.get(f"{CHROMA_BASE_URL}/api/v1/heartbeat", timeout=TIMEOUT)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Chroma DB not running")


class TestMetricsIngestion:
    """Test ingestion metriche da agents"""
    
    @pytest.fixture
    def sample_metrics(self):
        """Fixture con metriche di esempio"""
        return {
            "host_id": "test-host-integration",
            "agent_type": "performance",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metrics": {
                "cpu_percent": 45.5,
                "memory_percent": 60.2,
                "disk_percent": 70.1,
                "network_in": 1024000,
                "network_out": 512000
            }
        }
    
    def test_ingest_metrics(self, sample_metrics):
        """Test ingestion metriche"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/metrics",
                json=sample_metrics,
                timeout=TIMEOUT
            )
            
            assert response.status_code in [200, 201]
            data = response.json()
            assert "id" in data or "message" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Central server not running")
    
    def test_retrieve_metrics(self, sample_metrics):
        """Test recupero metriche"""
        try:
            # Prima ingest
            requests.post(
                f"{API_BASE_URL}/metrics",
                json=sample_metrics,
                timeout=TIMEOUT
            )
            
            # Poi retrieve
            time.sleep(1)  # Aspetta che siano salvate
            response = requests.get(
                f"{API_BASE_URL}/metrics",
                params={"host_id": sample_metrics["host_id"]},
                timeout=TIMEOUT
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            
            if len(data) > 0:
                assert data[0]["host_id"] == sample_metrics["host_id"]
        except requests.exceptions.ConnectionError:
            pytest.skip("Central server not running")


class TestAlertFlow:
    """Test flusso completo degli alert"""
    
    @pytest.fixture
    def sample_alert(self):
        """Fixture con alert di esempio"""
        return {
            "host_id": "test-host-integration",
            "alert_type": "performance",
            "severity": "high",
            "title": "High CPU Usage Detected",
            "description": "CPU usage exceeded 90% for 5 minutes",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": {
                "cpu_percent": 95.5,
                "threshold": 90.0,
                "duration_seconds": 300
            }
        }
    
    def test_create_alert(self, sample_alert):
        """Test creazione alert"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/alerts",
                json=sample_alert,
                timeout=TIMEOUT
            )
            
            assert response.status_code in [200, 201]
            data = response.json()
            assert "id" in data
            return data["id"]
        except requests.exceptions.ConnectionError:
            pytest.skip("Central server not running")
    
    def test_list_alerts(self):
        """Test lista alert"""
        try:
            response = requests.get(f"{API_BASE_URL}/alerts", timeout=TIMEOUT)
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
        except requests.exceptions.ConnectionError:
            pytest.skip("Central server not running")
    
    def test_get_alert_by_id(self, sample_alert):
        """Test recupero singolo alert"""
        try:
            # Crea alert
            create_response = requests.post(
                f"{API_BASE_URL}/alerts",
                json=sample_alert,
                timeout=TIMEOUT
            )
            
            if create_response.status_code in [200, 201]:
                alert_id = create_response.json()["id"]
                
                # Recupera alert
                get_response = requests.get(
                    f"{API_BASE_URL}/alerts/{alert_id}",
                    timeout=TIMEOUT
                )
                
                assert get_response.status_code == 200
                data = get_response.json()
                assert data["id"] == alert_id
                assert data["title"] == sample_alert["title"]
        except requests.exceptions.ConnectionError:
            pytest.skip("Central server not running")
    
    def test_update_alert_status(self, sample_alert):
        """Test aggiornamento status alert"""
        try:
            # Crea alert
            create_response = requests.post(
                f"{API_BASE_URL}/alerts",
                json=sample_alert,
                timeout=TIMEOUT
            )
            
            if create_response.status_code in [200, 201]:
                alert_id = create_response.json()["id"]
                
                # Aggiorna status
                update_data = {
                    "status": "resolved",
                    "resolution_notes": "Issue resolved by restarting service"
                }
                
                update_response = requests.put(
                    f"{API_BASE_URL}/alerts/{alert_id}",
                    json=update_data,
                    timeout=TIMEOUT
                )
                
                assert update_response.status_code == 200
                
                # Verifica aggiornamento
                get_response = requests.get(
                    f"{API_BASE_URL}/alerts/{alert_id}",
                    timeout=TIMEOUT
                )
                data = get_response.json()
                assert data["status"] == "resolved"
        except requests.exceptions.ConnectionError:
            pytest.skip("Central server not running")


class TestVectorSearch:
    """Test ricerca semantica con vector database"""
    
    def test_store_and_search_alerts(self):
        """Test memorizzazione e ricerca alert con vector search"""
        try:
            # Crea alert con descrizione dettagliata
            alert_data = {
                "host_id": "web-server-01",
                "alert_type": "intrusion",
                "severity": "critical",
                "title": "SQL Injection Attempt Detected",
                "description": "Multiple SQL injection attempts detected from IP 192.168.1.100 targeting login endpoint",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            create_response = requests.post(
                f"{API_BASE_URL}/alerts",
                json=alert_data,
                timeout=TIMEOUT
            )
            
            if create_response.status_code not in [200, 201]:
                pytest.skip("Cannot create alert")
            
            time.sleep(2)  # Aspetta indicizzazione
            
            # Cerca alert simili
            search_data = {
                "query": "SQL injection attack on web application",
                "top_k": 5
            }
            
            search_response = requests.post(
                f"{API_BASE_URL}/search/similar-alerts",
                json=search_data,
                timeout=TIMEOUT
            )
            
            assert search_response.status_code == 200
            results = search_response.json()
            
            assert "results" in results
            assert isinstance(results["results"], list)
            
            # Verifica che almeno un risultato sia rilevante
            if len(results["results"]) > 0:
                first_result = results["results"][0]
                assert "content" in first_result or "metadata" in first_result
                assert "distance" in first_result
        except requests.exceptions.ConnectionError:
            pytest.skip("Services not running")
    
    def test_semantic_similarity(self):
        """Test similarità semantica nelle ricerche"""
        try:
            # Crea due alert correlati
            alerts = [
                {
                    "host_id": "db-server-01",
                    "alert_type": "performance",
                    "severity": "high",
                    "title": "Database High Load",
                    "description": "Database experiencing high query load and slow response times",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                {
                    "host_id": "db-server-02",
                    "alert_type": "performance",
                    "severity": "high",
                    "title": "Database Performance Issue",
                    "description": "Database queries are taking too long to execute, causing timeouts",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            ]
            
            for alert in alerts:
                requests.post(f"{API_BASE_URL}/alerts", json=alert, timeout=TIMEOUT)
            
            time.sleep(2)
            
            # Cerca con query semanticamente simile
            search_response = requests.post(
                f"{API_BASE_URL}/search/similar-alerts",
                json={
                    "query": "database slow performance problem",
                    "top_k": 3
                },
                timeout=TIMEOUT
            )
            
            if search_response.status_code == 200:
                results = search_response.json()["results"]
                
                # Dovrebbe trovare alert correlati a database performance
                if len(results) > 0:
                    # Verifica che la distance sia ragionevole (< 0.5 è simile)
                    assert results[0]["distance"] < 0.7
        except requests.exceptions.ConnectionError:
            pytest.skip("Services not running")


class TestEndToEnd:
    """Test end-to-end del flusso completo"""
    
    def test_complete_incident_workflow(self):
        """Test workflow completo: detection -> alert -> investigation -> resolution"""
        try:
            # 1. Agent invia metriche anomale
            metrics = {
                "host_id": "prod-server-01",
                "agent_type": "performance",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "metrics": {
                    "cpu_percent": 98.5,
                    "memory_percent": 95.2,
                    "disk_percent": 85.0
                }
            }
            
            metrics_response = requests.post(
                f"{API_BASE_URL}/metrics",
                json=metrics,
                timeout=TIMEOUT
            )
            assert metrics_response.status_code in [200, 201]
            
            # 2. Sistema genera alert
            alert = {
                "host_id": "prod-server-01",
                "alert_type": "performance",
                "severity": "critical",
                "title": "Critical Resource Exhaustion",
                "description": "CPU and Memory usage critically high, potential resource exhaustion attack",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "metadata": {
                    "cpu_percent": 98.5,
                    "memory_percent": 95.2
                }
            }
            
            alert_response = requests.post(
                f"{API_BASE_URL}/alerts",
                json=alert,
                timeout=TIMEOUT
            )
            assert alert_response.status_code in [200, 201]
            alert_id = alert_response.json()["id"]
            
            time.sleep(1)
            
            # 3. Analyst cerca incidenti simili
            search_response = requests.post(
                f"{API_BASE_URL}/search/similar-alerts",
                json={
                    "query": "high CPU memory usage resource exhaustion",
                    "top_k": 5
                },
                timeout=TIMEOUT
            )
            assert search_response.status_code == 200
            
            # 4. Analyst aggiorna status alert
            update_response = requests.put(
                f"{API_BASE_URL}/alerts/{alert_id}",
                json={
                    "status": "investigating",
                    "resolution_notes": "Investigating high resource usage. Possible cryptominer detected."
                },
                timeout=TIMEOUT
            )
            assert update_response.status_code == 200
            
            # 5. Dopo investigation, risolve alert
            resolve_response = requests.put(
                f"{API_BASE_URL}/alerts/{alert_id}",
                json={
                    "status": "resolved",
                    "resolution_notes": "Cryptominer removed. Security policies updated."
                },
                timeout=TIMEOUT
            )
            assert resolve_response.status_code == 200
            
            # 6. Verifica stato finale
            final_response = requests.get(
                f"{API_BASE_URL}/alerts/{alert_id}",
                timeout=TIMEOUT
            )
            final_data = final_response.json()
            
            assert final_data["status"] == "resolved"
            assert "Cryptominer removed" in final_data["resolution_notes"]
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Services not running")


class TestSecurityFeatures:
    """Test funzionalità di sicurezza"""
    
    def test_data_sanitization(self):
        """Test che i dati sensibili vengano sanitizzati"""
        try:
            # Invia metriche con dati sensibili
            metrics = {
                "host_id": "192.168.1.100",  # IP che dovrebbe essere sanitizzato
                "agent_type": "performance",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "metrics": {
                    "username": "admin",  # Username sensibile
                    "cpu_percent": 50.0
                }
            }
            
            response = requests.post(
                f"{API_BASE_URL}/metrics",
                json=metrics,
                timeout=TIMEOUT
            )
            
            # Il sistema dovrebbe accettare i dati
            assert response.status_code in [200, 201]
            
            # TODO: Verificare che nei log/storage i dati siano sanitizzati
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Central server not running")


@pytest.mark.slow
class TestPerformance:
    """Test performance del sistema"""
    
    def test_bulk_metrics_ingestion(self):
        """Test ingestion massiva di metriche"""
        try:
            start_time = time.time()
            
            # Invia 100 metriche
            for i in range(100):
                metrics = {
                    "host_id": f"load-test-host-{i % 10}",
                    "agent_type": "performance",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "metrics": {
                        "cpu_percent": 30 + (i % 50),
                        "memory_percent": 40 + (i % 40)
                    }
                }
                
                requests.post(
                    f"{API_BASE_URL}/metrics",
                    json=metrics,
                    timeout=TIMEOUT
                )
            
            elapsed = time.time() - start_time
            
            # Dovrebbe completare in meno di 30 secondi
            assert elapsed < 30
            
            # Throughput: almeno 3 richieste/secondo
            throughput = 100 / elapsed
            assert throughput > 3
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Central server not running")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
