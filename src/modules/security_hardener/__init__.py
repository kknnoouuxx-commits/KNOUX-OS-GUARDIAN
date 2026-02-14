"""
Autonomous Security Hardener
تحليل وتقوية الإعدادات الأمنية للنظام تلقائياً
"""

import logging
import threading
import time
import subprocess
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.communication_bus import get_bus
from src.core.safe_execution import safe_execute
from src.core.database import get_database
from src.core.config import get_config

logger = logging.getLogger(__name__)


class Severity(Enum):
    """خطورة المشكلة الأمنية"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SettingCategory(Enum):
    """فئة الإعداد"""
    SERVICE = "service"
    REGISTRY = "registry"
    FIREWALL = "firewall"
    USER_RIGHTS = "user_rights"
    AUDIT_POLICY = "audit_policy"
    FILE_PERMISSION = "file_permission"


@dataclass
class SecurityFinding:
    """نتيجة فحص أمني"""
    rule_id: str
    title: str
    description: str
    category: SettingCategory
    severity: Severity
    current_value: str
    expected_value: str
    compliant: bool
    remediation_action: str
    impact: str


class SecurityHardener:
    """
    محسن الأمان المستقل
    Autonomous Security Hardener
    """
    
    def __init__(self):
        self.bus = get_bus()
        self.db = get_database()
        self.config = get_config()
        self.running = False
        self.scan_thread = None
        
        # Security rules database
        self.security_rules = self._load_security_rules()
        
        # Critical services (never disable)
        self.CRITICAL_SERVICES = [
            'wuauserv',  # Windows Update
            'BITS',  # Background Intelligent Transfer
            'CryptSvc',  # Cryptographic Services
            'EventLog',  # Windows Event Log
            'PlugPlay',  # Plug and Play
            'RpcSs',  # Remote Procedure Call
            'Schedule',  # Task Scheduler
            'LanmanServer',  # Server (file sharing)
            'Winmgmt'  # Windows Management Instrumentation
        ]
        
        logger.info("Security Hardener initialized")
    
    def start(self):
        """بدء الفحوصات الأمنية"""
        if not self.running:
            self.running = True
            self.scan_thread = threading.Thread(
                target=self._scanning_loop,
                daemon=True
            )
            self.scan_thread.start()
            
            logger.info("Security Hardener started")
    
    def stop(self):
        """إيقاف الفحوصات الأمنية"""
        self.running = False
        if self.scan_thread:
            self.scan_thread.join(timeout=5)
        logger.info("Security Hardener stopped")
    
    def _scanning_loop(self):
        """حلقة الفحص الأمني"""
        scan_interval_days = self.config.get('modules.security_hardener.scan_interval_days', 7)
        scan_interval_seconds = max(3600, float(scan_interval_days) * 86400)
        
        while self.running:
            try:
                # Run security audit
                self._run_security_audit()
                
                # Wait for next scan
                time.sleep(scan_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in scanning loop: {e}")
                time.sleep(3600)  # Wait 1 hour on error
    
    def _run_security_audit(self):
        """تشغيل تدقيق أمني"""
        logger.info("Running security audit...")
        
        try:
            # Collect system configuration
            system_config = self._collect_system_configuration()
            
            # Run all security checks
            findings = []
            for rule in self.security_rules:
                try:
                    finding = self._check_security_rule(rule, system_config)
                    findings.append(finding)
                except Exception as e:
                    logger.error(f"Error checking rule {rule['id']}: {e}")
            
            # Calculate security score
            total_rules = len(findings)
            compliant_rules = sum(1 for f in findings if f.compliant)
            security_score = (compliant_rules / total_rules) * 100 if total_rules > 0 else 100
            
            logger.info(f"Security audit complete: {security_score:.1f}% "
                       f"({compliant_rules}/{total_rules} checks passed)")
            
            # Log audit results
            self._log_audit_results(findings, security_score)
            
            # Take action based on findings
            self._handle_security_findings(findings)
            
        except Exception as e:
            logger.error(f"Error running security audit: {e}")
    
    def _collect_system_configuration(self) -> Dict:
        """جمع تكوين النظام"""
        config = {
            'services': self._enumerate_services(),
            'firewall_rules': self._get_firewall_status(),
            'registry_settings': self._get_security_registry_settings(),
            'user_accounts': self._get_user_accounts(),
            'audit_policies': self._get_audit_policies(),
            'installed_software': self._get_installed_software()
        }
        
        return config
    
    def _enumerate_services(self) -> List[Dict]:
        """تعداد الخدمات"""
        services = []
        
        try:
            # Use PowerShell to get services
            ps_command = """
            Get-Service | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                services_data = json.loads(result.stdout)
                
                for service in services_data:
                    services.append({
                        'name': service['Name'],
                        'display_name': service['DisplayName'],
                        'status': service['Status'],
                        'start_type': service['StartType']
                    })
        
        except Exception as e:
            logger.error(f"Error enumerating services: {e}")
        
        return services
    
    def _get_firewall_status(self) -> Dict:
        """الحصول على حالة جدار الحماية"""
        firewall_status = {
            'domain': 'unknown',
            'private': 'unknown',
            'public': 'unknown'
        }
        
        try:
            # Use netsh to get firewall status
            result = subprocess.run(
                ["netsh", "advfirewall", "show", "allprofiles", "state"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                if 'ON' in output:
                    firewall_status['domain'] = 'enabled'
                    firewall_status['private'] = 'enabled'
                    firewall_status['public'] = 'enabled'
                elif 'OFF' in output:
                    firewall_status['domain'] = 'disabled'
                    firewall_status['private'] = 'disabled'
                    firewall_status['public'] = 'disabled'
        
        except Exception as e:
            logger.error(f"Error getting firewall status: {e}")
        
        return firewall_status
    
    def _get_security_registry_settings(self) -> Dict:
        """الحصول على إعدادات السجل الأمنية"""
        registry_settings = {}
        
        # Check common security settings
        registry_checks = [
            (r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System', 'EnableLUA', '1'),  # UAC
            (r'HKLM\SYSTEM\CurrentControlSet\Control\Lsa', 'LimitBlankPasswordUse', '1'),
            (r'HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management', 'ClearPageFileAtShutdown', '1')
        ]
        
        for key, value_name, expected in registry_checks:
            try:
                result = subprocess.run(
                    ['reg', 'query', key, '/v', value_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 3:
                        # Extract value
                        value_line = lines[2]
                        if 'REG_DWORD' in value_line:
                            value = value_line.split('REG_DWORD')[1].strip()
                            registry_settings[f"{key}\\{value_name}"] = value
        
            except Exception:
                registry_settings[f"{key}\\{value_name}"] = 'not_found'
        
        return registry_settings
    
    def _get_user_accounts(self) -> List[Dict]:
        """الحصول على حسابات المستخدمين"""
        user_accounts = []
        
        try:
            # Use PowerShell to get user accounts
            ps_command = """
            Get-LocalUser | Select-Object Name, Enabled, PasswordRequired, PasswordChangeableDate | ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                users_data = json.loads(result.stdout)
                
                for user in users_data:
                    user_accounts.append({
                        'name': user['Name'],
                        'enabled': user['Enabled'],
                        'password_required': user['PasswordRequired'],
                        'last_password_change': user['PasswordChangeableDate']
                    })
        
        except Exception as e:
            logger.error(f"Error getting user accounts: {e}")
        
        return user_accounts
    
    def _get_audit_policies(self) -> Dict:
        """الحصول على سياسات التدقيق"""
        audit_policies = {}
        
        try:
            # Use auditpol to get audit policies
            result = subprocess.run(
                ['auditpol', '/get', '/category:*'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                
                for line in lines:
                    if 'Success' in line or 'Failure' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            category = ' '.join(parts[:-2])
                            setting = parts[-1]
                            audit_policies[category] = setting
        
        except Exception as e:
            logger.error(f"Error getting audit policies: {e}")
        
        return audit_policies
    
    def _get_installed_software(self) -> List[Dict]:
        """الحصول على البرامج المثبتة"""
        installed_software = []
        
        try:
            # Use PowerShell to get installed software
            ps_command = """
            Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | 
            Select-Object DisplayName, DisplayVersion, Publisher, InstallDate | 
            Where-Object {$_.DisplayName -ne $null} | 
            ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                software_data = json.loads(result.stdout)
                
                for software in software_data:
                    installed_software.append({
                        'name': software['DisplayName'],
                        'version': software['DisplayVersion'],
                        'publisher': software['Publisher'],
                        'install_date': software['InstallDate']
                    })
        
        except Exception as e:
            logger.error(f"Error getting installed software: {e}")
        
        return installed_software
    
    def _load_security_rules(self) -> List[Dict]:
        """تحميل قواعد الأمان"""
        # Basic security rules (CIS Benchmarks inspired)
        rules = [
            {
                'id': 'CIS-2.3.10.1',
                'title': 'تعطيل حساب الضيف',
                'description': 'حساب الضيف يسمح بالوصول غير المصرح به',
                'category': SettingCategory.USER_RIGHTS,
                'severity': Severity.HIGH,
                'check_function': self._check_guest_account,
                'remediation_function': self._disable_guest_account,
                'expected_value': 'معطل',
                'impact': 'حساب الضيف سيكون معطلاً'
            },
            {
                'id': 'CIS-9.1.1',
                'title': 'تفعيل جدار حماية Windows',
                'description': 'جدار الحماية يمنع الاتصالات غير المصرح بها',
                'category': SettingCategory.FIREWALL,
                'severity': Severity.CRITICAL,
                'check_function': self._check_firewall_enabled,
                'remediation_function': self._enable_firewall,
                'expected_value': 'مفعل',
                'impact': 'جدار الحماية سيكون مفعلاً'
            },
            {
                'id': 'CIS-2.3.1.1',
                'title': 'تعطيل SMBv1',
                'description': 'SMBv1 بروتوكول قديم مع ثغرات أمنية',
                'category': SettingCategory.SERVICE,
                'severity': Severity.HIGH,
                'check_function': self._check_smbv1_status,
                'remediation_function': self._disable_smbv1,
                'expected_value': 'معطل',
                'impact': 'SMBv1 سيكون معطلاً'
            },
            {
                'id': 'CIS-2.3.17.2',
                'title': 'تعطيل Remote Desktop',
                'description': 'Remote Desktop يسمح بالوصول عن بعد',
                'category': SettingCategory.SERVICE,
                'severity': Severity.MEDIUM,
                'check_function': self._check_remote_desktop,
                'remediation_function': self._disable_remote_desktop,
                'expected_value': 'معطل',
                'impact': 'Remote Desktop سيكون معطلاً'
            }
        ]
        
        return rules
    
    def _check_security_rule(self, rule: Dict, system_config: Dict) -> SecurityFinding:
        """فحص قاعدة أمنية"""
        # Run check function
        current_value = rule['check_function'](system_config)
        
        # Determine if compliant
        compliant = (current_value == rule['expected_value'])
        
        # Create finding
        finding = SecurityFinding(
            rule_id=rule['id'],
            title=rule['title'],
            description=rule['description'],
            category=rule['category'],
            severity=rule['severity'],
            current_value=current_value,
            expected_value=rule['expected_value'],
            compliant=compliant,
            remediation_action='تطبيق' if not compliant else 'لا شيء',
            impact=rule['impact']
        )
        
        return finding
    
    def _check_guest_account(self, system_config: Dict) -> str:
        """فحص حالة حساب الضيف"""
        try:
            # Use PowerShell to check guest account
            ps_command = """
            $guest = Get-LocalUser -Name "Guest" -ErrorAction SilentlyContinue
            if ($guest -and $guest.Enabled) { "مفعل" } else { "معطل" }
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
        
        except Exception as e:
            logger.error(f"Error checking guest account: {e}")
        
        return "غير معروف"
    
    def _check_firewall_enabled(self, system_config: Dict) -> str:
        """فحص حالة جدار الحماية"""
        firewall_status = system_config.get('firewall_rules', {})
        
        if all(status == 'enabled' for status in firewall_status.values()):
            return "مفعل"
        elif any(status == 'disabled' for status in firewall_status.values()):
            return "معطل جزئياً"
        else:
            return "معطل"
    
    def _check_smbv1_status(self, system_config: Dict) -> str:
        """فحص حالة SMBv1"""
        try:
            # Use PowerShell to check SMBv1
            ps_command = """
            $smbv1 = Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -ErrorAction SilentlyContinue
            if ($smbv1 -and $smbv1.State -eq "Enabled") { "مفعل" } else { "معطل" }
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
        
        except Exception as e:
            logger.error(f"Error checking SMBv1: {e}")
        
        return "غير معروف"
    
    def _check_remote_desktop(self, system_config: Dict) -> str:
        """فحص حالة Remote Desktop"""
        try:
            # Use PowerShell to check Remote Desktop
            ps_command = """
            $rdp = Get-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name fDenyTSConnections -ErrorAction SilentlyContinue
            if ($rdp -and $rdp.fDenyTSConnections -eq 0) { "مفعل" } else { "معطل" }
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
        
        except Exception as e:
            logger.error(f"Error checking Remote Desktop: {e}")
        
        return "غير معروف"
    
    def _disable_guest_account(self):
        """تعطيل حساب الضيف"""
        try:
            ps_command = 'Disable-LocalUser -Name "Guest"'
            subprocess.run(["powershell", "-Command", ps_command], check=True, timeout=10)
            return True
        except Exception as e:
            logger.error(f"Error disabling guest account: {e}")
            return False
    
    def _enable_firewall(self):
        """تفعيل جدار الحماية"""
        try:
            profiles = ['domain', 'private', 'public']
            for profile in profiles:
                subprocess.run(
                    ["netsh", "advfirewall", "set", f"{profile}profile", "state", "on"],
                    check=True,
                    timeout=10
                )
            return True
        except Exception as e:
            logger.error(f"Error enabling firewall: {e}")
            return False
    
    def _disable_smbv1(self):
        """تعطيل SMBv1"""
        try:
            ps_command = 'Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart'
            subprocess.run(["powershell", "-Command", ps_command], check=True, timeout=30)
            return True
        except Exception as e:
            logger.error(f"Error disabling SMBv1: {e}")
            return False
    
    def _disable_remote_desktop(self):
        """تعطيل Remote Desktop"""
        try:
            ps_command = 'Set-ItemProperty -Path "HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server" -Name fDenyTSConnections -Value 1'
            subprocess.run(["powershell", "-Command", ps_command], check=True, timeout=10)
            return True
        except Exception as e:
            logger.error(f"Error disabling Remote Desktop: {e}")
            return False
    
    def _log_audit_results(self, findings: List[SecurityFinding], security_score: float):
        """تسجيل نتائج التدقيق"""
        # Log summary
        self.db.log_event(
            event_type='security_audit_complete',
            module_name='security_hardener',
            severity='info',
            message=f"Security audit: {security_score:.1f}% compliant",
            details={
                'security_score': security_score,
                'total_findings': len(findings),
                'compliant_findings': sum(1 for f in findings if f.compliant),
                'critical_findings': sum(1 for f in findings if f.severity == Severity.CRITICAL and not f.compliant),
                'high_findings': sum(1 for f in findings if f.severity == Severity.HIGH and not f.compliant)
            }
        )
        
        # Log individual findings
        for finding in findings:
            if not finding.compliant:
                self.db.log_event(
                    event_type='security_finding',
                    module_name='security_hardener',
                    severity=finding.severity.value,
                    message=f"{finding.title}: {finding.current_value} (expected: {finding.expected_value})",
                    details=finding.__dict__
                )
    
    def _handle_security_findings(self, findings: List[SecurityFinding]):
        """معالجة النتائج الأمنية"""
        # Separate findings by severity
        critical_findings = [f for f in findings if f.severity == Severity.CRITICAL and not f.compliant]
        high_findings = [f for f in findings if f.severity == Severity.HIGH and not f.compliant]
        medium_findings = [f for f in findings if f.severity == Severity.MEDIUM and not f.compliant]
        
        # Check if auto-fix is enabled for critical issues
        auto_fix_critical = self.config.get('modules.security_hardener.auto_fix_critical', False)
        
        if auto_fix_critical and critical_findings:
            logger.info(f"Auto-fixing {len(critical_findings)} critical security issues")
            
            for finding in critical_findings:
                self._apply_security_fix(finding)
        
        # Publish findings for user review
        if high_findings or medium_findings:
            self.bus.publish(
                'security.findings',
                source_module='security_hardener',
                payload={
                    'critical_findings': [f.__dict__ for f in critical_findings],
                    'high_findings': [f.__dict__ for f in high_findings],
                    'medium_findings': [f.__dict__ for f in medium_findings],
                    'requires_user_approval': True
                }
            )
    
    def _apply_security_fix(self, finding: SecurityFinding):
        """تطبيق إصلاح أمني"""
        logger.info(f"Applying security fix: {finding.title}")
        
        # Find the rule
        rule = next((r for r in self.security_rules if r['id'] == finding.rule_id), None)
        
        if rule and rule.get('remediation_function'):
            try:
                # Apply fix
                success = rule['remediation_function']()
                
                if success:
                    logger.info(f"Successfully applied fix for: {finding.title}")
                    
                    # Log fix
                    self.db.log_event(
                        event_type='security_fix_applied',
                        module_name='security_hardener',
                        severity='info',
                        message=f"Fixed: {finding.title}",
                        details={
                            'finding': finding.__dict__,
                            'success': True
                        }
                    )
                else:
                    logger.error(f"Failed to apply fix for: {finding.title}")
                    
            except Exception as e:
                logger.error(f"Error applying security fix: {e}")


# Global instance
_security_hardener_instance = None

def get_security_hardener() -> SecurityHardener:
    """الحصول على instance الموديول"""
    global _security_hardener_instance
    if _security_hardener_instance is None:
        _security_hardener_instance = SecurityHardener()
    return _security_hardener_instance
