"""
Common Security Utilities for Agents
=====================================

Sanitizzazione dati per garantire privacy:
- Rimozione password, token, API keys
- Masking di informazioni sensibili
- Anonimizzazione path e username
"""

import re
import hashlib
from typing import Dict, Any, List, Optional


class DataSanitizer:
    """
    Sanitizza dati prima dell'invio al server centrale.
    Implementa data minimization e privacy by design.
    """
    
    # Pattern per identificare dati sensibili
    SENSITIVE_PATTERNS = {
        'password': re.compile(r'(password|passwd|pwd)[\s=:]+[^\s]+', re.IGNORECASE),
        'api_key': re.compile(r'(api[_-]?key|apikey|token)[\s=:]+[A-Za-z0-9_\-]+', re.IGNORECASE),
        'secret': re.compile(r'(secret|private[_-]?key)[\s=:]+[^\s]+', re.IGNORECASE),
        'credit_card': re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'ipv4_private': re.compile(r'\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b'),
        'ssh_key': re.compile(r'-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----.*?-----END (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----', re.DOTALL),
    }
    
    @staticmethod
    def sanitize_text(text: str, mask: str = "<MASKED>") -> str:
        """
        Sanitizza testo rimuovendo/mascherando dati sensibili.
        
        Args:
            text: Testo da sanitizzare
            mask: Stringa di sostituzione
            
        Returns:
            Testo sanitizzato
        """
        if not text:
            return text
            
        sanitized = text
        for pattern_type, pattern in DataSanitizer.SENSITIVE_PATTERNS.items():
            sanitized = pattern.sub(mask, sanitized)
        
        return sanitized
    
    @staticmethod
    def sanitize_process_info(process_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizza informazioni processo:
        - Rimuove cmdline completa (può contenere password)
        - Anonimizza path
        - Rimuove variabili ambiente
        
        Args:
            process_info: Dict con info processo
            
        Returns:
            Dict sanitizzato
        """
        sanitized = process_info.copy()
        
        # Rimuovi cmdline completa (sostituisci con solo nome eseguibile)
        if 'cmdline' in sanitized:
            cmdline = sanitized['cmdline']
            if isinstance(cmdline, list) and cmdline:
                sanitized['cmdline'] = [cmdline[0]]  # Solo primo elemento (comando)
            elif isinstance(cmdline, str):
                sanitized['cmdline'] = cmdline.split()[0] if cmdline else ""
        
        # Anonimizza path
        if 'exe' in sanitized:
            sanitized['exe_hash'] = hashlib.sha256(sanitized['exe'].encode()).hexdigest()[:16]
            sanitized.pop('exe', None)  # Rimuovi path originale
        
        # Rimuovi env vars (contengono dati sensibili)
        sanitized.pop('environ', None)
        
        # Rimuovi username se presente (opzionale)
        if 'username' in sanitized:
            sanitized['username_hash'] = hashlib.sha256(sanitized['username'].encode()).hexdigest()[:16]
            sanitized.pop('username', None)
        
        return sanitized
    
    @staticmethod
    def sanitize_file_path(path: str) -> str:
        """
        Anonimizza path file mantenendo solo info rilevanti.
        
        Args:
            path: Path completo file
            
        Returns:
            Path anonimizzato o hash
        """
        if not path:
            return ""
        
        # Genera hash univoco
        path_hash = hashlib.sha256(path.encode()).hexdigest()[:16]
        
        # Mantieni solo estensione e directory base generica
        import os
        ext = os.path.splitext(path)[1]
        return f"file_{path_hash}{ext}"
    
    @staticmethod
    def sanitize_network_info(net_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizza informazioni di rete:
        - Pseudoanonimizza IP privati
        - Mantiene IP pubblici solo se necessario
        
        Args:
            net_info: Dict con info network
            
        Returns:
            Dict sanitizzato
        """
        sanitized = net_info.copy()
        
        # Anonimizza IP locali/privati
        for key in ['local_addr', 'remote_addr', 'source_ip', 'dest_ip']:
            if key in sanitized:
                ip = sanitized[key]
                if DataSanitizer._is_private_ip(ip):
                    sanitized[key] = DataSanitizer._anonymize_ip(ip)
        
        return sanitized
    
    @staticmethod
    def _is_private_ip(ip: str) -> bool:
        """Verifica se IP è privato (RFC 1918)"""
        if not ip:
            return False
        
        private_ranges = [
            r'^10\.',
            r'^172\.(1[6-9]|2\d|3[01])\.',
            r'^192\.168\.',
            r'^127\.',
            r'^169\.254\.'
        ]
        
        return any(re.match(pattern, ip) for pattern in private_ranges)
    
    @staticmethod
    def _anonymize_ip(ip: str) -> str:
        """Pseudoanonimizza IP mantenendo range"""
        parts = ip.split('.')
        if len(parts) == 4:
            # Mantieni primi 2 ottetti, hash ultimi 2
            prefix = '.'.join(parts[:2])
            suffix_hash = hashlib.sha256(ip.encode()).hexdigest()[:4]
            return f"{prefix}.{suffix_hash[:2]}.{suffix_hash[2:]}"
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    @staticmethod
    def sanitize_code_snippet(code: str, max_length: int = 500) -> str:
        """
        Sanitizza snippet di codice:
        - Rimuove commenti con info sensibili
        - Limita lunghezza
        - Rimuove pattern sensibili
        
        Args:
            code: Codice sorgente
            max_length: Lunghezza massima snippet
            
        Returns:
            Snippet sanitizzato
        """
        if not code:
            return ""
        
        # Sanitizza pattern sensibili
        sanitized = DataSanitizer.sanitize_text(code)
        
        # Limita lunghezza
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "\n... [truncated]"
        
        return sanitized
    
    @staticmethod
    def validate_before_send(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validazione pre-invio: controlla che non ci siano dati sensibili.
        
        Args:
            data: Dati da inviare
            
        Returns:
            (is_valid, error_message)
        """
        # Converti in stringa per check veloce
        data_str = str(data)
        
        # Check pattern critici
        critical_patterns = [
            (r'-----BEGIN.*PRIVATE KEY-----', "Private key detected"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Password detected"),
            (r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', "Bearer token detected"),
        ]
        
        for pattern, error_msg in critical_patterns:
            if re.search(pattern, data_str, re.IGNORECASE):
                return False, f"Security validation failed: {error_msg}"
        
        return True, None


# ============================================
# Funzioni standalone per compatibilità importazione
# ============================================

def sanitize_ip(ip: str) -> str:
    """Sanitizza indirizzo IP"""
    return DataSanitizer._anonymize_ip(ip) if DataSanitizer._is_private_ip(ip) else ip

def sanitize_mac(mac: str) -> str:
    """Sanitizza indirizzo MAC"""
    if not mac:
        return ""
    return hashlib.sha256(mac.encode()).hexdigest()[:12]

def sanitize_username(username: str) -> str:
    """Sanitizza username"""
    if not username:
        return ""
    return hashlib.sha256(username.encode()).hexdigest()[:16]

def sanitize_path(path: str) -> str:
    """Sanitizza file path"""
    return DataSanitizer.sanitize_file_path(path)

def sanitize_process_name(process_name: str) -> str:
    """Sanitizza nome processo"""
    if not process_name:
        return ""
    return hashlib.sha256(process_name.encode()).hexdigest()[:16]

def sanitize_command(command: str) -> str:
    """Sanitizza comando"""
    return DataSanitizer.sanitize_text(command)

def sanitize_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizza metriche di sistema"""
    sanitized = metrics.copy()
    # Sanitizza qualsiasi indirizzo IP nelle metriche
    for key, value in sanitized.items():
        if isinstance(value, str) and DataSanitizer._is_private_ip(value):
            sanitized[key] = sanitize_ip(value)
    return sanitized

# ============================================
# TESTING
# ============================================
if __name__ == "__main__":
    # Test sanitizzazione
    sanitizer = DataSanitizer()
    
    # Test testo
    text = "password=secret123 api_key=abcd1234 normal_text"
    print(f"Original: {text}")
    print(f"Sanitized: {sanitizer.sanitize_text(text)}\n")
    
    # Test processo
    process = {
        'name': 'python3',
        'cmdline': ['python3', 'script.py', '--password=secret'],
        'exe': '/usr/bin/python3',
        'username': 'admin',
        'environ': {'SECRET_KEY': 'xxx'}
    }
    print(f"Process sanitized: {sanitizer.sanitize_process_info(process)}\n")
    
    # Test validation
    bad_data = {'key': 'password=secret123'}
    is_valid, error = sanitizer.validate_before_send(bad_data)
    print(f"Validation: {is_valid}, Error: {error}")
