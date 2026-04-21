"""
Test suite per il modulo sanitizer
Testa tutte le funzioni di sanitizzazione per garantire la privacy.
"""
import pytest
from agents.common.sanitizer import (
    sanitize_ip,
    sanitize_mac,
    sanitize_username,
    sanitize_path,
    sanitize_process_name,
    sanitize_command,
    sanitize_metrics
)


class TestIPSanitization:
    """Test sanitizzazione indirizzi IP"""
    
    def test_ipv4_sanitization(self):
        """Test sanitizzazione IPv4"""
        ip = "192.168.1.100"
        sanitized = sanitize_ip(ip)
        assert sanitized.startswith("ip_")
        assert len(sanitized) == 67  # ip_ + 64 caratteri SHA256
    
    def test_ipv6_sanitization(self):
        """Test sanitizzazione IPv6"""
        ip = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        sanitized = sanitize_ip(ip)
        assert sanitized.startswith("ip_")
        assert len(sanitized) == 67
    
    def test_localhost_sanitization(self):
        """Test sanitizzazione localhost"""
        assert sanitize_ip("127.0.0.1") == "ip_localhost"
        assert sanitize_ip("::1") == "ip_localhost"
    
    def test_same_ip_same_hash(self):
        """Test che lo stesso IP produca sempre lo stesso hash"""
        ip = "10.0.0.1"
        hash1 = sanitize_ip(ip)
        hash2 = sanitize_ip(ip)
        assert hash1 == hash2
    
    def test_different_ips_different_hashes(self):
        """Test che IP diversi producano hash diversi"""
        hash1 = sanitize_ip("192.168.1.1")
        hash2 = sanitize_ip("192.168.1.2")
        assert hash1 != hash2


class TestMACSanitization:
    """Test sanitizzazione indirizzi MAC"""
    
    def test_mac_sanitization(self):
        """Test sanitizzazione MAC address"""
        mac = "00:1B:44:11:3A:B7"
        sanitized = sanitize_mac(mac)
        assert sanitized.startswith("mac_")
        assert len(sanitized) == 68  # mac_ + 64 caratteri
    
    def test_mac_consistency(self):
        """Test consistenza hash MAC"""
        mac = "AA:BB:CC:DD:EE:FF"
        assert sanitize_mac(mac) == sanitize_mac(mac)


class TestUsernameSanitization:
    """Test sanitizzazione username"""
    
    def test_username_sanitization(self):
        """Test sanitizzazione username normale"""
        username = "john_doe"
        sanitized = sanitize_username(username)
        assert sanitized.startswith("user_")
        assert len(sanitized) == 69  # user_ + 64 caratteri
    
    def test_root_username(self):
        """Test che root rimanga root"""
        assert sanitize_username("root") == "root"
    
    def test_system_usernames(self):
        """Test che gli utenti di sistema rimangano invariati"""
        system_users = ["daemon", "nobody", "www-data", "mysql"]
        for user in system_users:
            assert sanitize_username(user) == user
    
    def test_username_consistency(self):
        """Test consistenza hash username"""
        username = "alice"
        assert sanitize_username(username) == sanitize_username(username)


class TestPathSanitization:
    """Test sanitizzazione percorsi file"""
    
    def test_home_path_sanitization(self):
        """Test sanitizzazione percorso home"""
        path = "/home/john/documents/file.txt"
        sanitized = sanitize_path(path)
        assert "/home/" not in sanitized
        assert "user_" in sanitized
        assert "file.txt" in sanitized  # Il filename può rimanere
    
    def test_user_path_sanitization(self):
        """Test sanitizzazione percorsi utente"""
        path = "/Users/alice/Desktop/secret.doc"
        sanitized = sanitize_path(path)
        assert "alice" not in sanitized
        assert "user_" in sanitized
    
    def test_system_path_preserved(self):
        """Test che i percorsi di sistema rimangano invariati"""
        system_paths = [
            "/etc/passwd",
            "/var/log/syslog",
            "/usr/bin/python3"
        ]
        for path in system_paths:
            sanitized = sanitize_path(path)
            # Verifica che non sia stato aggiunto user_
            assert "user_" not in sanitized


class TestProcessNameSanitization:
    """Test sanitizzazione nomi processi"""
    
    def test_benign_process(self):
        """Test che i processi benigni rimangano invariati"""
        benign = ["python3", "systemd", "sshd", "nginx"]
        for proc in benign:
            assert sanitize_process_name(proc) == proc
    
    def test_suspicious_process(self):
        """Test sanitizzazione processi sospetti"""
        suspicious = "/tmp/backdoor.sh"
        sanitized = sanitize_process_name(suspicious)
        assert sanitized.startswith("proc_")


class TestCommandSanitization:
    """Test sanitizzazione comandi"""
    
    def test_command_with_path(self):
        """Test sanitizzazione comando con percorsi"""
        cmd = "cat /home/john/secret.txt"
        sanitized = sanitize_command(cmd)
        assert "john" not in sanitized
        assert "user_" in sanitized
    
    def test_command_with_ip(self):
        """Test sanitizzazione comando con IP"""
        cmd = "ssh admin@192.168.1.100"
        sanitized = sanitize_command(cmd)
        assert "192.168.1.100" not in sanitized
        assert "ip_" in sanitized
    
    def test_command_with_username(self):
        """Test sanitizzazione comando con username"""
        cmd = "sudo -u alice python script.py"
        sanitized = sanitize_command(cmd)
        assert "alice" not in sanitized


class TestMetricsSanitization:
    """Test sanitizzazione metriche complete"""
    
    def test_metrics_dict_sanitization(self):
        """Test sanitizzazione dizionario metriche"""
        metrics = {
            "host_id": "server-192.168.1.50",
            "username": "alice",
            "ip_address": "192.168.1.50",
            "cpu_percent": 45.2,
            "process": "/home/alice/script.py"
        }
        
        sanitized = sanitize_metrics(metrics)
        
        # Verifica che i dati sensibili siano stati sanitizzati
        assert "alice" not in str(sanitized)
        assert "192.168.1.50" not in str(sanitized)
        
        # Verifica che i dati non sensibili siano preservati
        assert sanitized["cpu_percent"] == 45.2
    
    def test_nested_metrics_sanitization(self):
        """Test sanitizzazione metriche nested"""
        metrics = {
            "system": {
                "host": "192.168.1.100",
                "user": "root"
            },
            "network": {
                "connections": [
                    {"src": "10.0.0.1", "dst": "8.8.8.8"},
                    {"src": "10.0.0.2", "dst": "1.1.1.1"}
                ]
            }
        }
        
        sanitized = sanitize_metrics(metrics)
        
        # Verifica struttura preservata
        assert "system" in sanitized
        assert "network" in sanitized
        
        # Verifica sanitizzazione
        assert "10.0.0.1" not in str(sanitized)
        assert sanitized["system"]["user"] == "root"  # root non viene sanitizzato


class TestEdgeCases:
    """Test casi edge"""
    
    def test_empty_string(self):
        """Test con stringhe vuote"""
        assert sanitize_ip("") == ""
        assert sanitize_username("") == ""
        assert sanitize_path("") == ""
    
    def test_none_values(self):
        """Test con valori None"""
        assert sanitize_ip(None) is None
        assert sanitize_username(None) is None
    
    def test_special_characters(self):
        """Test con caratteri speciali"""
        username = "user@domain.com"
        sanitized = sanitize_username(username)
        assert sanitized.startswith("user_")
    
    def test_unicode_characters(self):
        """Test con caratteri unicode"""
        username = "utente_€"
        sanitized = sanitize_username(username)
        assert sanitized.startswith("user_")


# Pytest fixtures
@pytest.fixture
def sample_metrics():
    """Fixture con metriche di esempio"""
    return {
        "host_id": "web-server-01",
        "timestamp": "2026-01-24T10:00:00Z",
        "cpu_percent": 75.5,
        "memory_percent": 60.2,
        "user": "www-data",
        "ip": "192.168.1.100",
        "processes": [
            {"name": "nginx", "pid": 1234},
            {"name": "/home/admin/suspicious.sh", "pid": 5678}
        ]
    }


def test_complete_sanitization(sample_metrics):
    """Test sanitizzazione completa di un payload reale"""
    sanitized = sanitize_metrics(sample_metrics)
    
    # Verifica che i dati sensibili siano stati rimossi
    assert "192.168.1.100" not in str(sanitized)
    
    # Verifica che i dati utili siano preservati
    assert sanitized["cpu_percent"] == 75.5
    assert sanitized["memory_percent"] == 60.2
    assert sanitized["user"] == "www-data"  # Utente di sistema non sanitizzato
    
    # Verifica che i processi siano stati gestiti
    assert "suspicious.sh" not in str(sanitized)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
