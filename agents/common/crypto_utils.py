"""
Cryptography Utilities for Agents
===================================

Encryption, hashing, HMAC per sicurezza dati.
"""

import os
import hashlib
import hmac
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
import base64


class CryptoManager:
    """
    Gestisce operazioni crittografiche:
    - Encryption/Decryption (Fernet)
    - Hashing
    - HMAC per integrità
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Inizializza crypto manager.
        
        Args:
            encryption_key: Chiave Fernet (base64). Se None, viene generata.
        """
        if encryption_key:
            self.encryption_key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        else:
            self.encryption_key = Fernet.generate_key()
        
        self.fernet = Fernet(self.encryption_key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Cripta testo con Fernet (AES-128-CBC).
        
        Args:
            plaintext: Testo in chiaro
            
        Returns:
            Testo cifrato (base64)
        """
        if not plaintext:
            return ""
        
        encrypted_bytes = self.fernet.encrypt(plaintext.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decripta testo cifrato.
        
        Args:
            ciphertext: Testo cifrato
            
        Returns:
            Testo in chiaro
        """
        if not ciphertext:
            return ""
        
        try:
            decrypted_bytes = self.fernet.decrypt(ciphertext.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    @staticmethod
    def hash_sha256(data: str) -> str:
        """
        Calcola hash SHA256.
        
        Args:
            data: Dati da hashare
            
        Returns:
            Hash esadecimale
        """
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def hash_file(filepath: str, algorithm: str = 'sha256') -> str:
        """
        Calcola hash di un file.
        
        Args:
            filepath: Path del file
            algorithm: Algoritmo hash (sha256, sha1, md5)
            
        Returns:
            Hash esadecimale
        """
        hash_obj = hashlib.new(algorithm)
        
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            raise IOError(f"Failed to hash file {filepath}: {e}")
    
    @staticmethod
    def hmac_sign(message: str, secret_key: str) -> str:
        """
        Genera HMAC-SHA256 per integrità messaggio.
        
        Args:
            message: Messaggio da firmare
            secret_key: Chiave segreta
            
        Returns:
            HMAC esadecimale
        """
        return hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def hmac_verify(message: str, signature: str, secret_key: str) -> bool:
        """
        Verifica HMAC.
        
        Args:
            message: Messaggio originale
            signature: HMAC da verificare
            secret_key: Chiave segreta
            
        Returns:
            True se valido
        """
        expected_sig = CryptoManager.hmac_sign(message, secret_key)
        return hmac.compare_digest(expected_sig, signature)
    
    @staticmethod
    def generate_key() -> str:
        """
        Genera nuova chiave Fernet.
        
        Returns:
            Chiave base64 encoded
        """
        return Fernet.generate_key().decode('utf-8')
    
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
        """
        Deriva chiave da password usando PBKDF2.
        
        Args:
            password: Password
            salt: Salt (generato se None)
            
        Returns:
            (key_base64, salt_used)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = kdf.derive(password.encode('utf-8'))
        key_base64 = base64.urlsafe_b64encode(key).decode('utf-8')
        
        return key_base64, salt


# ============================================
# TESTING
# ============================================
if __name__ == "__main__":
    # Test encryption
    crypto = CryptoManager()
    
    plaintext = "Sensitive data here"
    encrypted = crypto.encrypt(plaintext)
    decrypted = crypto.decrypt(encrypted)
    
    print(f"Plaintext: {plaintext}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    print(f"Match: {plaintext == decrypted}\n")
    
    # Test hashing
    data = "test data"
    hash_result = CryptoManager.hash_sha256(data)
    print(f"SHA256 hash: {hash_result}\n")
    
    # Test HMAC
    message = "important message"
    secret = "shared_secret_key"
    signature = CryptoManager.hmac_sign(message, secret)
    is_valid = CryptoManager.hmac_verify(message, signature, secret)
    
    print(f"HMAC signature: {signature}")
    print(f"HMAC valid: {is_valid}\n")
    
    # Test key generation
    new_key = CryptoManager.generate_key()
    print(f"Generated key: {new_key}")
