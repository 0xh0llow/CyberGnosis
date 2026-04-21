"""
Authentication & Authorization
===============================

Gestione autenticazione API token e HMAC.
"""

import os
import hmac
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# API Token da environment (in produzione: gestire con secrets manager)
VALID_API_TOKENS = os.getenv("API_TOKEN", "").split(",")
HMAC_SECRET = os.getenv("API_SECRET_KEY", "changeme")


def verify_api_token(authorization_header: str) -> bool:
    """
    Verifica API token da header Authorization.
    
    Args:
        authorization_header: Header "Authorization: Bearer <token>"
        
    Returns:
        True se token valido
    """
    if not authorization_header:
        logger.warning("Missing Authorization header")
        return False
    
    # Estrai token
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        logger.warning("Invalid Authorization header format")
        return False
    
    token = parts[1]
    
    # Verifica token
    if token in VALID_API_TOKENS:
        return True
    
    logger.warning(f"Invalid API token: {token[:10]}...")
    return False


def verify_hmac_signature(payload: dict, signature: str) -> bool:
    """
    Verifica HMAC signature per integrità payload.
    
    Args:
        payload: Payload richiesta (dict)
        signature: HMAC signature da header
        
    Returns:
        True se firma valida
    """
    try:
        import json
        
        # Serializza payload
        payload_str = json.dumps(payload, sort_keys=True)
        
        # Calcola HMAC atteso
        expected_sig = hmac.new(
            HMAC_SECRET.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Verifica con compare_digest (timing-attack safe)
        return hmac.compare_digest(expected_sig, signature)
    
    except Exception as e:
        logger.error(f"HMAC verification failed: {e}")
        return False


def generate_hmac_signature(payload: dict) -> str:
    """
    Genera HMAC signature per payload.
    
    Args:
        payload: Dati da firmare
        
    Returns:
        HMAC hex string
    """
    import json
    
    payload_str = json.dumps(payload, sort_keys=True)
    
    return hmac.new(
        HMAC_SECRET.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
