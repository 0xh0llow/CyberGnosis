"""
Code Scanner - Security Vulnerability Detection
================================================

Modulo 3 - Scanner codice pericoloso con bandit/semgrep

Funzionalità:
- Integrazione bandit per Python
- Detection: command injection, SQL injection, hardcoded secrets
- Snippet sanitizzati per vector DB
"""

import subprocess
import json
import logging
import os
import sys
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from common.sanitizer import DataSanitizer
from common.api_sender import SecureAPISender

logger = logging.getLogger(__name__)


class CodeScanner:
    """
    Scanner per vulnerabilità di sicurezza nel codice.
    """
    
    def __init__(self):
        """Inizializza scanner."""
        self.sanitizer = DataSanitizer()
        
        # Verifica tool disponibili
        self.has_bandit = self._check_tool_available('bandit')
        self.has_semgrep = self._check_tool_available('semgrep')
        
        logger.info(f"Code Scanner initialized (bandit: {self.has_bandit}, semgrep: {self.has_semgrep})")
    
    @staticmethod
    def _check_tool_available(tool_name: str) -> bool:
        """Verifica se tool è installato."""
        try:
            subprocess.run(
                [tool_name, '--version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def scan_python_with_bandit(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Scansiona codice Python con bandit.
        
        Args:
            target_path: File o directory Python
            
        Returns:
            Lista issue trovate
        """
        if not self.has_bandit:
            logger.warning("Bandit not installed")
            return []
        
        try:
            # Esegui bandit con output JSON
            result = subprocess.run(
                ['bandit', '-r', target_path, '-f', 'json'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )
            
            # Parse output JSON
            output = json.loads(result.stdout.decode('utf-8'))
            
            # Estrai risultati
            issues = []
            for result_item in output.get('results', []):
                issue = {
                    'tool': 'bandit',
                    'test_id': result_item.get('test_id'),
                    'test_name': result_item.get('test_name'),
                    'severity': result_item.get('issue_severity', 'UNKNOWN').lower(),
                    'confidence': result_item.get('issue_confidence', 'UNKNOWN').lower(),
                    'file': result_item.get('filename'),
                    'line_number': result_item.get('line_number'),
                    'issue_text': result_item.get('issue_text'),
                    'code_snippet': result_item.get('code', '')
                }
                issues.append(issue)
            
            logger.info(f"Bandit scan completed: {len(issues)} issues found")
            return issues
        
        except subprocess.TimeoutExpired:
            logger.error("Bandit scan timeout")
            return []
        
        except Exception as e:
            logger.error(f"Bandit scan failed: {e}")
            return []
    
    def scan_with_semgrep(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Scansiona codice con semgrep (multi-language).
        
        Args:
            target_path: File o directory
            
        Returns:
            Lista issue trovate
        """
        if not self.has_semgrep:
            logger.warning("Semgrep not installed")
            return []
        
        try:
            # Esegui semgrep con regole security
            result = subprocess.run(
                ['semgrep', '--config=auto', '--json', target_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120
            )
            
            # Parse output
            output = json.loads(result.stdout.decode('utf-8'))
            
            # Estrai risultati
            issues = []
            for result_item in output.get('results', []):
                issue = {
                    'tool': 'semgrep',
                    'rule_id': result_item.get('check_id'),
                    'severity': self._map_semgrep_severity(result_item.get('extra', {}).get('severity')),
                    'message': result_item.get('extra', {}).get('message'),
                    'file': result_item.get('path'),
                    'line_number': result_item.get('start', {}).get('line'),
                    'code_snippet': result_item.get('extra', {}).get('lines', '')
                }
                issues.append(issue)
            
            logger.info(f"Semgrep scan completed: {len(issues)} issues found")
            return issues
        
        except subprocess.TimeoutExpired:
            logger.error("Semgrep scan timeout")
            return []
        
        except Exception as e:
            logger.error(f"Semgrep scan failed: {e}")
            return []
    
    @staticmethod
    def _map_semgrep_severity(severity: Optional[str]) -> str:
        """Mappa severity semgrep a formato standard."""
        mapping = {
            'ERROR': 'high',
            'WARNING': 'medium',
            'INFO': 'low'
        }
        return mapping.get(severity, 'unknown')
    
    def scan_codebase(self, target_path: str) -> Dict[str, Any]:
        """
        Scansiona intera codebase con tutti i tool disponibili.
        
        Args:
            target_path: Directory radice codebase
            
        Returns:
            Risultati aggregati
        """
        logger.info(f"Starting codebase scan: {target_path}")
        
        all_issues = []
        
        # Scan Python files con bandit
        if self.has_bandit:
            bandit_issues = self.scan_python_with_bandit(target_path)
            all_issues.extend(bandit_issues)
        
        # Scan con semgrep (multi-language)
        if self.has_semgrep:
            semgrep_issues = self.scan_with_semgrep(target_path)
            all_issues.extend(semgrep_issues)
        
        # Statistiche
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for issue in all_issues:
            severity = issue.get('severity', 'unknown')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        results = {
            'total_issues': len(all_issues),
            'severity_counts': severity_counts,
            'issues': all_issues
        }
        
        logger.info(f"Scan completed: {len(all_issues)} total issues")
        return results
    
    def send_issues_to_server(
        self,
        issues: List[Dict[str, Any]],
        sender: SecureAPISender,
        host_id: str
    ) -> int:
        """
        Invia issue al server centrale.
        
        Args:
            issues: Lista issue da inviare
            sender: API sender
            host_id: Host identifier
            
        Returns:
            Numero issue inviate con successo
        """
        sent_count = 0
        
        for issue in issues:
            # Sanitizza snippet
            code_snippet = issue.get('code_snippet', '')
            sanitized_code = self.sanitizer.sanitize_code_snippet(code_snippet, max_length=500)
            
            # Anonimizza path
            file_path = issue.get('file', '')
            sanitized_path = self.sanitizer.sanitize_file_path(file_path)
            
            # Invia al server
            success = sender.send_code_snippet(
                code=sanitized_code,
                vulnerability_type=issue.get('test_name') or issue.get('rule_id', 'unknown'),
                severity=issue.get('severity', 'medium'),
                file_path=sanitized_path,
                line_number=issue.get('line_number'),
                host_id=host_id
            )
            
            if success:
                sent_count += 1
        
        logger.info(f"Sent {sent_count}/{len(issues)} issues to server")
        return sent_count


# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] %(name)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Code Security Scanner')
    parser.add_argument('--target', required=True, help='Path to scan (file or directory)')
    parser.add_argument('--server-url', help='Central server URL (optional)')
    parser.add_argument('--api-token', help='API token (required if server-url provided)')
    parser.add_argument('--host-id', help='Host identifier')
    parser.add_argument('--interval', type=int, default=0, help='Run continuously every N seconds (0 = single run)')
    
    args = parser.parse_args()
    
    # Inizializza scanner
    scanner = CodeScanner()

    def run_once():
        results = scanner.scan_codebase(args.target)

        print(f"\n{'='*60}")
        print("Code Scan Results")
        print(f"{'='*60}")
        print(f"Total Issues: {results['total_issues']}")
        print("Severity Distribution:")
        for severity, count in results['severity_counts'].items():
            if count > 0:
                print(f"  {severity.capitalize()}: {count}")

        if args.server_url and args.api_token:
            sender = SecureAPISender(
                server_url=args.server_url,
                api_token=args.api_token,
                verify_ssl=False
            )

            scanner.send_issues_to_server(
                results['issues'],
                sender,
                host_id=args.host_id or 'unknown'
            )

    if args.interval and args.interval > 0:
        logger.info(f"Starting continuous scan mode (interval={args.interval}s)")
        while True:
            run_once()
            time.sleep(args.interval)
    else:
        run_once()
