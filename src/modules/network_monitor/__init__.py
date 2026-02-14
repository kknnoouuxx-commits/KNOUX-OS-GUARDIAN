"""
Privacy-First Network Monitor
مراقبة ذكية لحركة الشبكة لكشف التسريبات والاتصالات المشبوهة
"""

import logging
import threading
import time
import socket
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.communication_bus import get_bus
from src.core.database import get_database
from src.core.config import get_config

logger = logging.getLogger(__name__)


class ConnectionRisk(Enum):
    """مخاطر الاتصال"""
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    PRIVACY_LEAK = "privacy_leak"
    MALICIOUS = "malicious"


@dataclass
class NetworkConnection:
    """اتصال شبكي"""
    timestamp: datetime
    process_name: str
    process_pid: int
    process_path: str
    dest_ip: str
    dest_port: int
    dest_hostname: Optional[str]
    protocol: str
    bytes_sent: int
    bytes_received: int
    risk_score: float
    classification: ConnectionRisk


class NetworkMonitor:
    """
    مراقب الشبكة المحترم للخصوصية
    Privacy-First Network Monitor
    """
    
    def __init__(self):
        self.bus = get_bus()
        self.db = get_database()
        self.config = get_config()
        self.running = False
        self.monitor_thread = None
        
        # Known safe domains
        self.SAFE_DOMAINS = [
            'microsoft.com',
            'windows.com',
            'windowsupdate.com',
            'google.com',
            'googleapis.com',
            'gstatic.com'
        ]
        
        # Known tracker domains
        self.TRACKER_DOMAINS = [
            'doubleclick.net',
            'google-analytics.com',
            'facebook.com',
            'fbcdn.net',
            'twitter.com',
            'twimg.com'
        ]
        
        # Critical system processes
        self.CRITICAL_PROCESSES = [
            'svchost.exe',
            'lsass.exe',
            'System',
            'wininit.exe'
        ]
        
        # Connection history
        self.connection_history = {}
        
        logger.info("Network Monitor initialized")
    
    def start(self):
        """بدء المراقبة"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitor_thread.start()
            
            logger.info("Network Monitor started")
    
    def stop(self):
        """إيقاف المراقبة"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Network Monitor stopped")
    
    def _monitoring_loop(self):
        """حلقة المراقبة الرئيسية"""
        monitor_interval = 60  # Check every minute
        
        while self.running:
            try:
                # Check network connections
                self._check_network_connections()
                
                # Wait for next check
                time.sleep(monitor_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Wait 30 seconds on error
    
    def _check_network_connections(self):
        """فحص الاتصالات الشبكية"""
        logger.debug("Checking network connections...")
        
        try:
            # Get current network connections
            connections = self._get_network_connections()
            
            for connection in connections:
                # Analyze connection
                risk_assessment = self._analyze_connection(connection)
                
                # Log connection
                self._log_connection(connection, risk_assessment)
                
                # Take action if needed
                if risk_assessment['classification'] in [ConnectionRisk.PRIVACY_LEAK, ConnectionRisk.MALICIOUS]:
                    self._handle_suspicious_connection(connection, risk_assessment)
            
        except Exception as e:
            logger.error(f"Error checking network connections: {e}")
    
    def _get_network_connections(self) -> List[NetworkConnection]:
        """الحصول على الاتصالات الشبكية الحالية"""
        import psutil
        
        connections = []
        
        for conn in psutil.net_connections(kind='inet'):
            try:
                # Skip if no local address
                if not conn.laddr:
                    continue
                
                # Get process info
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        process_name = proc.name()
                        process_path = proc.exe()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_name = f"PID_{conn.pid}"
                        process_path = "unknown"
                else:
                    process_name = "System"
                    process_path = "unknown"
                
                # Get destination info
                dest_ip = conn.raddr.ip if conn.raddr else "0.0.0.0"
                dest_port = conn.raddr.port if conn.raddr else 0
                
                # Get hostname (reverse DNS)
                dest_hostname = None
                if dest_ip and dest_ip != "0.0.0.0":
                    try:
                        dest_hostname = socket.gethostbyaddr(dest_ip)[0]
                    except socket.herror:
                        logger.debug(f"Reverse DNS lookup failed for {dest_ip}: Host not found")
                        dest_hostname = dest_ip
                    except Exception as e:
                        logger.debug(f"Reverse DNS lookup failed for {dest_ip}: {e}")
                        dest_hostname = dest_ip
                
                # Determine protocol
                protocol = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
                
                # Create connection object
                connection = NetworkConnection(
                    timestamp=datetime.now(),
                    process_name=process_name,
                    process_pid=conn.pid or 0,
                    process_path=process_path,
                    dest_ip=dest_ip,
                    dest_port=dest_port,
                    dest_hostname=dest_hostname,
                    protocol=protocol,
                    bytes_sent=0,  # Would need continuous monitoring
                    bytes_received=0,
                    risk_score=0.0,
                    classification=ConnectionRisk.SAFE
                )
                
                connections.append(connection)
                
            except Exception as e:
                logger.debug(f"Error processing connection: {e}")
                continue
        
        return connections
    
    def _analyze_connection(self, connection: NetworkConnection) -> Dict:
        """تحليل الاتصال وتقييم المخاطر"""
        risk_score = 0.0
        
        # Component 1: Destination Reputation (40% weight)
        dest_reputation = self._check_destination_reputation(connection)
        if dest_reputation == 'malicious':
            risk_score += 80
        elif dest_reputation == 'suspicious':
            risk_score += 50
        elif dest_reputation == 'tracker':
            risk_score += 30
        elif dest_reputation == 'unknown':
            risk_score += 20
        # 'trusted' adds 0
        
        # Component 2: Process Behavior (30% weight)
        if connection.process_name in self.CRITICAL_PROCESSES:
            risk_score -= 10  # System process, lower risk
        elif 'temp' in connection.process_path.lower():
            risk_score += 20  # Running from temp folder
        elif 'download' in connection.process_path.lower():
            risk_score += 15  # Running from downloads
        
        # Component 3: Connection Characteristics (20% weight)
        if connection.dest_port not in [80, 443, 22, 25, 587, 53]:
            risk_score += 10  # Non-standard port
        
        if connection.protocol == 'UDP' and connection.dest_port not in [53, 123]:
            risk_score += 5  # Unusual UDP usage
        
        # Component 4: Timing and Volume (10% weight)
        current_hour = datetime.now().hour
        if current_hour >= 2 and current_hour <= 5:
            risk_score += 5  # Unusual time
        
        # Determine classification
        if risk_score > 70:
            classification = ConnectionRisk.MALICIOUS
        elif risk_score > 50:
            classification = ConnectionRisk.PRIVACY_LEAK
        elif risk_score > 30:
            classification = ConnectionRisk.SUSPICIOUS
        else:
            classification = ConnectionRisk.SAFE
        
        return {
            'risk_score': min(risk_score, 100),
            'classification': classification,
            'dest_reputation': dest_reputation,
            'explanation': self._generate_risk_explanation(connection, risk_score, classification)
        }
    
    def _check_destination_reputation(self, connection: NetworkConnection) -> str:
        """التحقق من سمعة الوجهة"""
        # Check if it's a known safe domain
        if connection.dest_hostname:
            for safe_domain in self.SAFE_DOMAINS:
                if safe_domain in connection.dest_hostname:
                    return 'trusted'
            
            # Check if it's a known tracker
            for tracker_domain in self.TRACKER_DOMAINS:
                if tracker_domain in connection.dest_hostname:
                    return 'tracker'
        
        # Check IP reputation (simplified)
        if connection.dest_ip.startswith('10.') or connection.dest_ip.startswith('192.168.'):
            return 'trusted'  # Local network
        
        # Check for known malicious patterns
        if self._is_ip_suspicious(connection.dest_ip):
            return 'suspicious'
        
        return 'unknown'
    
    def _is_ip_suspicious(self, ip_address: str) -> bool:
        """التحقق إذا كان IP مشبوهاً"""
        # Simple pattern matching
        suspicious_patterns = [
            '185.220.101',  # Known malicious range
            '45.9.148',     # Known malicious range
            '91.92.240'     # Known malicious range
        ]
        
        for pattern in suspicious_patterns:
            if ip_address.startswith(pattern):
                return True
        
        return False
    
    def _generate_risk_explanation(self, connection: NetworkConnection, 
                                 risk_score: float, classification: ConnectionRisk) -> str:
        """توليد تفسير للمخاطر"""
        explanations = {
            ConnectionRisk.SAFE: "اتصال آمن",
            ConnectionRisk.SUSPICIOUS: "اتصال مشبوه",
            ConnectionRisk.PRIVACY_LEAK: "تسريب خصوصية محتمل",
            ConnectionRisk.MALICIOUS: "اتصال خبيث"
        }
        
        explanation = explanations.get(classification, "اتصال غير معروف")
        
        if connection.dest_hostname:
            explanation += f" إلى {connection.dest_hostname}"
        else:
            explanation += f" إلى {connection.dest_ip}:{connection.dest_port}"
        
        explanation += f" من {connection.process_name}"
        
        return explanation
    
    def _log_connection(self, connection: NetworkConnection, risk_assessment: Dict):
        """تسجيل الاتصال"""
        # Update connection with risk assessment
        connection.risk_score = risk_assessment['risk_score']
        connection.classification = risk_assessment['classification']
        
        # Log to database
        self.db.log_event(
            event_type='network_connection',
            module_name='network_monitor',
            severity=self._get_severity_from_risk(risk_assessment['classification']),
            message=f"{connection.process_name} → {connection.dest_ip}:{connection.dest_port}",
            details={
                'connection': connection.__dict__,
                'risk_assessment': risk_assessment
            }
        )
        
        # Add to history
        if connection.process_name not in self.connection_history:
            self.connection_history[connection.process_name] = []
        
        self.connection_history[connection.process_name].append({
            'timestamp': connection.timestamp,
            'dest': f"{connection.dest_ip}:{connection.dest_port}",
            'risk_score': risk_assessment['risk_score'],
            'classification': risk_assessment['classification'].value
        })
        
        # Keep only last 100 entries per process
        if len(self.connection_history[connection.process_name]) > 100:
            self.connection_history[connection.process_name] = \
                self.connection_history[connection.process_name][-100:]
    
    def _get_severity_from_risk(self, classification: ConnectionRisk) -> str:
        """الحصول على مستوى الخطورة من التصنيف"""
        severity_map = {
            ConnectionRisk.SAFE: 'info',
            ConnectionRisk.SUSPICIOUS: 'warning',
            ConnectionRisk.PRIVACY_LEAK: 'warning',
            ConnectionRisk.MALICIOUS: 'error'
        }
        return severity_map.get(classification, 'info')
    
    def _handle_suspicious_connection(self, connection: NetworkConnection, 
                                    risk_assessment: Dict):
        """معالجة الاتصال المشبوه"""
        classification = risk_assessment['classification']
        
        if classification == ConnectionRisk.MALICIOUS:
            # Immediate action for malicious connections
            self._handle_malicious_connection(connection, risk_assessment)
            
        elif classification == ConnectionRisk.PRIVACY_LEAK:
            # Notify user for privacy leaks
            self._handle_privacy_leak(connection, risk_assessment)
    
    def _handle_malicious_connection(self, connection: NetworkConnection, 
                                   risk_assessment: Dict):
        """معالجة الاتصال الخبيث"""
        logger.warning(f"Malicious connection detected: {connection.process_name} → "
                      f"{connection.dest_ip}:{connection.dest_port}")
        
        # Publish event
        self.bus.publish(
            'network.malicious_connection',
            source_module='network_monitor',
            payload={
                'connection': connection.__dict__,
                'risk_assessment': risk_assessment,
                'action_required': True
            }
        )
        
        # Check if blocking is enabled
        block_enabled = self.config.get('modules.network_monitor.block_suspicious_connections', False)
        
        if block_enabled:
            # Try to block the connection
            self._block_connection(connection)
    
    def _handle_privacy_leak(self, connection: NetworkConnection, 
                           risk_assessment: Dict):
        """معالجة تسريب الخصوصية"""
        logger.info(f"Privacy leak detected: {connection.process_name} → "
                   f"{connection.dest_hostname or connection.dest_ip}")
        
        # Publish event for user notification
        self.bus.publish(
            'network.privacy_leak',
            source_module='network_monitor',
            payload={
                'connection': connection.__dict__,
                'risk_assessment': risk_assessment,
                'requires_user_approval': True
            }
        )
    
    def _block_connection(self, connection: NetworkConnection):
        """حظر الاتصال"""
        try:
            # Use Windows Firewall to block
            self._add_firewall_rule(connection)
            
            logger.info(f"Blocked connection: {connection.process_name} → "
                       f"{connection.dest_ip}:{connection.dest_port}")
            
        except Exception as e:
            logger.error(f"Error blocking connection: {e}")
    
    def _add_firewall_rule(self, connection: NetworkConnection):
        """إضافة قاعدة جدار حماية"""
        try:
            import subprocess
            
            # Create firewall rule name
            rule_name = f"KNOUX_Block_{connection.process_name}_{connection.dest_ip}"
            
            # PowerShell command to add firewall rule
            ps_command = f"""
            New-NetFirewallRule -DisplayName "{rule_name}" `
                -Direction Outbound `
                -Protocol {connection.protocol} `
                -RemoteAddress {connection.dest_ip} `
                -RemotePort {connection.dest_port} `
                -Program "{connection.process_path}" `
                -Action Block `
                -Enabled True
            """
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
        except Exception as e:
            raise Exception(f"Failed to add firewall rule: {e}")
    
    def get_connection_history(self, process_name: str = None) -> Dict:
        """الحصول على سجل الاتصالات"""
        if process_name:
            return self.connection_history.get(process_name, [])
        else:
            return self.connection_history
    
    def clear_history(self):
        """مسح السجل"""
        self.connection_history = {}
        logger.info("Connection history cleared")


# Global instance
_network_monitor_instance = None

def get_network_monitor() -> NetworkMonitor:
    """الحصول على instance الموديول"""
    global _network_monitor_instance
    if _network_monitor_instance is None:
        _network_monitor_instance = NetworkMonitor()
    return _network_monitor_instance