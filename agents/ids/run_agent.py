"""
IDS Agent Runner
================

Monitoraggio continuo log + network con invio alert al server centrale.
"""

import argparse
import logging
import os
import time
import psutil

from intrusion_detector import LogBasedIDS, NetworkBasedIDS

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from common.api_sender import SecureAPISender
from common.sanitizer import DataSanitizer

logger = logging.getLogger(__name__)


class IDSAgent:
    def __init__(self, sender: SecureAPISender, host_id: str, log_file: str):
        self.sender = sender
        self.host_id = host_id
        self.log_ids = LogBasedIDS(log_file=log_file)
        self.net_ids = NetworkBasedIDS()
        self.sanitizer = DataSanitizer()

    def _collect_connections(self):
        connections = []
        for conn in psutil.net_connections(kind="inet"):
            if not conn.raddr:
                continue
            try:
                source_ip = conn.raddr.ip
                dest_port = conn.laddr.port if conn.laddr else None
                if source_ip and dest_port:
                    connections.append({"source_ip": source_ip, "dest_port": dest_port})
            except Exception:
                continue
        return connections

    def _send_alert(self, alert):
        safe_alert = self.sanitizer.sanitize_network_info(alert)
        self.sender.send_alert(
            alert_type="ids",
            severity=alert.get("severity", "medium"),
            title=f"IDS: {alert.get('alert_type', 'intrusion')}",
            description=str(alert),
            metadata=safe_alert,
            host_id=self.host_id,
        )

    def run_once(self, brute_force_threshold: int, time_window_minutes: int):
        events = self.log_ids.analyze_log_file(max_lines=2000)
        brute_force = self.log_ids.detect_brute_force(
            events,
            threshold=brute_force_threshold,
            time_window_minutes=time_window_minutes,
        )
        suspicious = self.log_ids.detect_suspicious_logins(events)
        for alert in brute_force + suspicious:
            self._send_alert(alert)

        connections = self._collect_connections()
        for alert in self.net_ids.analyze_port_scan(connections):
            self._send_alert(alert)
        for alert in self.net_ids.detect_dos_attempt(connections):
            self._send_alert(alert)


def main():
    parser = argparse.ArgumentParser(description="IDS Agent")
    parser.add_argument("--server-url", required=True)
    parser.add_argument("--api-token", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--log-file", default="/var/log/auth.log")
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--brute-force-threshold", type=int, default=5)
    parser.add_argument("--time-window-minutes", type=int, default=5)
    parser.add_argument("--no-ssl-verify", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] %(name)s - %(message)s",
    )

    sender = SecureAPISender(
        server_url=args.server_url,
        api_token=args.api_token,
        verify_ssl=not args.no_ssl_verify,
    )
    if not sender.health_check():
        logger.error("Unable to reach central server")
        return

    agent = IDSAgent(sender=sender, host_id=args.host_id, log_file=args.log_file)
    logger.info(f"Starting IDS agent host={args.host_id} log={args.log_file}")

    while True:
        agent.run_once(args.brute_force_threshold, args.time_window_minutes)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
