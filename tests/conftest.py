"""
Conftest per pytest - fixtures condivise e configurazione test.
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path

# Aggiungi root project al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_dir():
    """Directory root del progetto"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir():
    """Directory per test data"""
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def temp_dir():
    """Directory temporanea per singolo test"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_metrics_payload():
    """Payload metriche di esempio per test"""
    return {
        "host_id": "test-host-001",
        "agent_type": "performance",
        "timestamp": "2026-01-24T10:00:00Z",
        "metrics": {
            "cpu_percent": 45.5,
            "memory_percent": 60.2,
            "disk_percent": 70.1,
            "network_in": 1024000,
            "network_out": 512000
        }
    }


@pytest.fixture
def sample_alert_payload():
    """Payload alert di esempio per test"""
    return {
        "host_id": "test-host-001",
        "alert_type": "performance",
        "severity": "high",
        "title": "High CPU Usage",
        "description": "CPU usage exceeded threshold",
        "timestamp": "2026-01-24T10:00:00Z",
        "metadata": {
            "cpu_percent": 95.5,
            "threshold": 90.0
        }
    }


@pytest.fixture
def sample_malware_file(temp_dir):
    """File di test per malware detection"""
    malware_file = temp_dir / "suspicious.exe"
    
    # Crea file binario con pattern sospetti
    with open(malware_file, "wb") as f:
        # Magic bytes per PE executable
        f.write(b"MZ\x90\x00")
        # Aggiungi contenuto sospetto
        f.write(b"eval" * 100)
        f.write(b"exec" * 100)
        f.write(b"\x00" * 1000)
    
    return malware_file


@pytest.fixture
def sample_log_entries():
    """Log entries di esempio per test IDS"""
    return [
        {
            "timestamp": "2026-01-24T10:00:00Z",
            "level": "INFO",
            "source": "ssh",
            "message": "Accepted password for user from 192.168.1.100"
        },
        {
            "timestamp": "2026-01-24T10:00:05Z",
            "level": "ERROR",
            "source": "ssh",
            "message": "Failed password for invalid user admin from 192.168.1.100"
        },
        {
            "timestamp": "2026-01-24T10:00:10Z",
            "level": "ERROR",
            "source": "ssh",
            "message": "Failed password for invalid user root from 192.168.1.100"
        }
    ]


@pytest.fixture
def mock_vector_db():
    """Mock per vector database (Chroma)"""
    class MockVectorDB:
        def __init__(self):
            self.documents = []
        
        def add_documents(self, documents, embeddings, metadata):
            self.documents.append({
                "documents": documents,
                "embeddings": embeddings,
                "metadata": metadata
            })
        
        def query(self, query_embedding, top_k=5):
            # Restituisce documenti mockati
            return {
                "results": self.documents[:top_k] if self.documents else [],
                "distances": [0.1, 0.2, 0.3][:top_k]
            }
        
        def clear(self):
            self.documents = []
    
    return MockVectorDB()


# Markers personalizzati
def pytest_configure(config):
    """Configura markers personalizzati"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "requires_docker: marks tests that require Docker services"
    )


# Setup/Teardown globale
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup ambiente di test globale"""
    print("\n=== Setting up test environment ===")
    
    # Imposta variabili ambiente per test
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    yield
    
    print("\n=== Tearing down test environment ===")
    
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


# Hooks per log dettagliati
def pytest_runtest_setup(item):
    """Hook eseguito prima di ogni test"""
    print(f"\n>>> Running: {item.nodeid}")


def pytest_runtest_teardown(item, nextitem):
    """Hook eseguito dopo ogni test"""
    print(f"<<< Completed: {item.nodeid}\n")
