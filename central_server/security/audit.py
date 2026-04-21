"""
Audit Logging
=============

Log di tutte le operazioni sensibili per compliance.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Logger per audit trail (chi, cosa, quando).
    """
    
    def __init__(self, log_file: str = "logs/audit.log"):
        """
        Args:
            log_file: Path file log audit
        """
        self.log_file = log_file
        
        # Setup file handler dedicato
        self.audit_logger = logging.getLogger("audit")
        self.audit_logger.setLevel(logging.INFO)
        
        # File handler (JSON structured logs)
        try:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            
            # Format: JSON per parsing facile
            formatter = logging.Formatter('%(message)s')
            fh.setFormatter(formatter)
            
            self.audit_logger.addHandler(fh)
            logger.info(f"Audit logger initialized: {log_file}")
        
        except Exception as e:
            logger.error(f"Failed to initialize audit logger: {e}")
    
    def log_action(
        self,
        action: str,
        user: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Log azione per audit trail.
        
        Args:
            action: Tipo azione (es: "metrics_received", "search_alerts")
            user: Utente o agent che ha eseguito azione
            resource: Risorsa acceduta (es: "host:server-01")
            details: Dettagli aggiuntivi
            ip_address: IP sorgente
            user_agent: User agent
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user": user,
            "resource": resource,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        # Log come JSON
        self.audit_logger.info(json.dumps(audit_entry))
    
    def log_data_access(
        self,
        user: str,
        data_type: str,
        record_ids: list,
        purpose: str
    ):
        """
        Log specifico per accesso dati sensibili.
        
        Args:
            user: Utente
            data_type: Tipo dati (es: "alerts", "metrics")
            record_ids: ID record acceduti
            purpose: Scopo accesso
        """
        self.log_action(
            action="data_access",
            user=user,
            resource=f"{data_type}:{','.join(map(str, record_ids))}",
            details={
                "data_type": data_type,
                "record_count": len(record_ids),
                "purpose": purpose
            }
        )


# ============================================
# RBAC - Role-Based Access Control
# ============================================

class RBACManager:
    """
    Gestione ruoli e permessi (semplificata per didattica).
    """
    
    # Definizione ruoli e permessi
    ROLES = {
        "admin": {
            "permissions": ["*"]  # Tutti i permessi
        },
        "security": {
            "permissions": [
                "view_alerts",
                "view_metrics",
                "search_vector_db",
                "update_alert_status",
                "view_code_snippets"
            ]
        },
        "viewer": {
            "permissions": [
                "view_alerts",
                "view_metrics",
                "view_dashboards"
            ]
        }
    }
    
    @staticmethod
    def has_permission(user_role: str, required_permission: str) -> bool:
        """
        Verifica se ruolo ha permesso richiesto.
        
        Args:
            user_role: Ruolo utente
            required_permission: Permesso richiesto
            
        Returns:
            True se autorizzato
        """
        if user_role not in RBACManager.ROLES:
            return False
        
        permissions = RBACManager.ROLES[user_role]["permissions"]
        
        # Admin ha tutti i permessi
        if "*" in permissions:
            return True
        
        return required_permission in permissions
    
    @staticmethod
    def get_user_role(username: str) -> Optional[str]:
        """
        Ottiene ruolo utente (in produzione: da DB/LDAP).
        
        Args:
            username: Username
            
        Returns:
            Ruolo o None
        """
        # Mapping semplificato (in produzione: query DB)
        user_roles = {
            "admin": "admin",
            "security_analyst": "security",
            "operator": "viewer",
            "agent": "security"  # Agent hanno ruolo security
        }
        
        return user_roles.get(username)


if __name__ == "__main__":
    # Test audit logger
    audit = AuditLogger(log_file="test_audit.log")
    
    audit.log_action(
        action="alert_created",
        user="agent_server01",
        resource="alert:12345",
        details={"severity": "high", "type": "malware"}
    )
    
    audit.log_data_access(
        user="security_analyst",
        data_type="alerts",
        record_ids=[1, 2, 3],
        purpose="incident_investigation"
    )
    
    print("✓ Audit logs written")
    
    # Test RBAC
    rbac = RBACManager()
    
    print(f"\nAdmin can view alerts: {rbac.has_permission('admin', 'view_alerts')}")
    print(f"Viewer can update alerts: {rbac.has_permission('viewer', 'update_alert_status')}")
    print(f"Security can search vector DB: {rbac.has_permission('security', 'search_vector_db')}")
