"""
API Sender for Agents
======================

Gestisce invio sicuro di dati al server centrale:
- HTTPS/TLS
- Autenticazione via API token
- HMAC per integrità
- Retry logic
"""

import requests
import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from .crypto_utils import CryptoManager
from .sanitizer import DataSanitizer


logger = logging.getLogger(__name__)


class SecureAPISender:
    """
    Sender sicuro per comunicazioni agent -> server centrale.
    """
    
    def __init__(
        self,
        server_url: str,
        api_token: str,
        hmac_secret: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: int = 30
    ):
        """
        Inizializza sender.
        
        Args:
            server_url: URL server centrale (es. https://server:8000)
            api_token: Token autenticazione
            hmac_secret: Chiave per HMAC (se None, usa api_token)
            verify_ssl: Verifica certificati SSL (False solo per test con self-signed)
            timeout: Timeout richieste HTTP (secondi)
        """
        self.server_url = server_url.rstrip('/')
        self.api_token = api_token
        self.hmac_secret = hmac_secret or api_token
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.sanitizer = DataSanitizer()
        
        # Session HTTP persistente
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'LinuxSecurityAgent/1.0'
        })
        
        if not verify_ssl:
            # Disabilita warning SSL (solo per ambiente didattico!)
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def send_metrics(self, metrics: Dict[str, Any], host_id: str) -> bool:
        """
        Invia metriche performance al server.
        
        Args:
            metrics: Dict con metriche
            host_id: Identificativo host
            
        Returns:
            True se successo
        """
        endpoint = f"{self.server_url}/api/metrics"
        
        payload = {
            'host_id': host_id,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics
        }
        
        return self._send_with_retry(endpoint, payload, max_retries=3)
    
    def send_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        host_id: str = None
    ) -> bool:
        """
        Invia alert al server.
        
        Args:
            alert_type: Tipo alert (performance, malware, ids, code)
            severity: low, medium, high, critical
            title: Titolo breve
            description: Descrizione testuale (sarà sanitizzata)
            metadata: Metadati aggiuntivi
            host_id: Identificativo host
            
        Returns:
            True se successo
        """
        endpoint = f"{self.server_url}/api/alerts"
        
        # Sanitizza descrizione
        sanitized_description = self.sanitizer.sanitize_text(description)
        
        payload = {
            'host_id': host_id,
            'alert_type': alert_type,
            'severity': severity,
            'title': title,
            'description': sanitized_description,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Validazione pre-invio
        is_valid, error = self.sanitizer.validate_before_send(payload)
        if not is_valid:
            logger.error(f"Alert validation failed: {error}")
            return False
        
        return self._send_with_retry(endpoint, payload, max_retries=3)
    
    def send_code_snippet(
        self,
        code: str,
        vulnerability_type: str,
        severity: str,
        file_path: str,
        line_number: Optional[int] = None,
        host_id: str = None
    ) -> bool:
        """
        Invia snippet di codice sospetto al server.
        
        Args:
            code: Snippet codice (sarà sanitizzato e troncato)
            vulnerability_type: Tipo vulnerabilità
            severity: low, medium, high, critical
            file_path: Path file (sarà anonimizzato)
            line_number: Numero linea
            host_id: Identificativo host
            
        Returns:
            True se successo
        """
        endpoint = f"{self.server_url}/api/code-snippets"
        
        # Sanitizza snippet
        sanitized_code = self.sanitizer.sanitize_code_snippet(code, max_length=500)
        sanitized_path = self.sanitizer.sanitize_file_path(file_path)
        
        payload = {
            'host_id': host_id,
            'code_snippet': sanitized_code,
            'vulnerability_type': vulnerability_type,
            'severity': severity,
            'file_path_hash': sanitized_path,
            'line_number': line_number,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return self._send_with_retry(endpoint, payload, max_retries=2)
    
    def _send_with_retry(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        max_retries: int = 3
    ) -> bool:
        """
        Invia richiesta HTTP POST con retry logic.
        
        Args:
            endpoint: URL endpoint
            payload: Dati da inviare
            max_retries: Numero massimo tentativi
            
        Returns:
            True se successo
        """
        # Aggiungi HMAC per integrità
        payload_json = json.dumps(payload, sort_keys=True)
        hmac_signature = CryptoManager.hmac_sign(payload_json, self.hmac_secret)
        
        headers = {
            'X-HMAC-Signature': hmac_signature
        }
        
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent data to {endpoint}")
                    return True
                elif response.status_code == 401:
                    logger.error(f"Authentication failed: {response.text}")
                    return False  # Non ritentare se auth fallita
                else:
                    logger.warning(
                        f"Request failed (attempt {attempt+1}/{max_retries}): "
                        f"Status {response.status_code}, Response: {response.text}"
                    )
            
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout (attempt {attempt+1}/{max_retries})")
            
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error (attempt {attempt+1}/{max_retries}): {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return False
            
            # Backoff esponenziale
            if attempt < max_retries - 1:
                sleep_time = 2 ** attempt
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
        
        logger.error(f"Failed to send data after {max_retries} attempts")
        return False
    
    def health_check(self) -> bool:
        """
        Verifica connettività con server centrale.
        
        Returns:
            True se server raggiungibile
        """
        try:
            response = self.session.get(
                f"{self.server_url}/health",
                timeout=10,
                verify=self.verify_ssl
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# ============================================
# TESTING
# ============================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Configurazione test (modifica con il tuo server)
    sender = SecureAPISender(
        server_url="https://localhost:8000",
        api_token="test_token_123",
        verify_ssl=False  # Self-signed cert in ambiente didattico
    )
    
    # Test health check
    if sender.health_check():
        print("✓ Server reachable")
    else:
        print("✗ Server not reachable")
    
    # Test invio metriche
    test_metrics = {
        'cpu_percent': 45.2,
        'ram_percent': 67.8,
        'disk_percent': 55.0
    }
    
    # Nota: questo fallirà se server non è in esecuzione
    # sender.send_metrics(test_metrics, host_id="test-host-001")
