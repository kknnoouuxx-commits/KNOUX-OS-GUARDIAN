"""
Registry Integrity Guardian
حماية وتنظيف سجل النظام من التعديلات الضارة
"""

import logging
import threading
import time
import subprocess
import json
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.communication_bus import get_bus
from src.core.safe_execution import safe_execute
from src.core.database import get_database
from src.core.config import get_config

logger = logging.getLogger(__name__)


class RegistryIssueType(Enum):
    """نوع مشكلة السجل"""
    MALWARE = "malware"
    BLOATWARE = "bloatware"
    ORPHANED = "orphaned"
    INVALID = "invalid"
    DUPLICATE = "duplicate"
    SECURITY = "security"


class Severity(Enum):
    """خطورة المشكلة"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class RegistryIssue:
    """مشكلة في السجل"""
    issue_id: str
    issue_type: RegistryIssueType
    registry_path: str
    key_name: str
    current_value: str
    expected_value: str
    severity: Severity
    description: str
    detected_at: datetime
    source: str  # How this issue was detected


@dataclass
class RegistryAction:
    """إجراء على السجل"""
    issue: RegistryIssue
    action_type: str  # delete, modify, quarantine
    backup_required: bool
    risk_level: str  # low, medium, high
    estimated_time_seconds: int


class RegistryGuardian:
    """
    حارس سلامة السجل
    Registry Integrity Guardian
    """
    
    def __init__(self):
        self.bus = get_bus()
        self.db = get_database()
        self.config = get_config()
        self.running = False
        self.scan_thread = None
        
        # Known malware patterns
        self.MALWARE_PATTERNS = [
            r'\\Run\\[^\\]+\.(exe|dll|bat|cmd)$',
            r'\\RunOnce\\[^\\]+\.(exe|dll|bat|cmd)$',
            r'\\RunServices\\[^\\]+\.(exe|dll|bat|cmd)$',
            r'\\RunServicesOnce\\[^\\]+\.(exe|dll|bat|cmd)$',
        ]
        
        # Known bloatware keys
        self.BLOATWARE_KEYS = [
            r'\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\[^\\]+',
            r'\\Software\\Classes\\Installer\\Products\\[^\\]+',
            r'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\Run\\[^\\]+',
        ]
        
        # Critical registry paths (never modify)
        self.CRITICAL_PATHS = [
            r'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager',
            r'HKLM\\SYSTEM\\CurrentControlSet\\Services',
            r'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion',
            r'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
            r'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
        ]
        
        # Issue database
        self.issue_database = {}
        
        logger.info("Registry Guardian initialized")
    
    def start(self):
        """بدء الفحص"""
        if not self.running:
            self.running = True
            self.scan_thread = threading.Thread(
                target=self._scanning_loop,
                daemon=True
            )
            self.scan_thread.start()
            
            logger.info("Registry Guardian started")
    
    def stop(self):
        """إيقاف الفحص"""
        self.running = False
        if self.scan_thread:
            self.scan_thread.join(timeout=5)
        logger.info("Registry Guardian stopped")
    
    def _scanning_loop(self):
        """حلقة الفحص الرئيسية"""
        scan_interval_days = self.config.get('modules.registry_guardian.scan_interval_days', 7)
        scan_interval_seconds = max(3600, float(scan_interval_days) * 86400)
        
        while self.running:
            try:
                # Run registry scan
                self._scan_registry()
                
                # Wait for next scan
                time.sleep(scan_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in scanning loop: {e}")
                time.sleep(3600)  # Wait 1 hour on error
    
    def _scan_registry(self):
        """فحص السجل"""
        logger.info("Starting registry scan...")
        
        try:
            # Scan for different types of issues
            all_issues = []
            
            # Scan for malware entries
            malware_issues = self._scan_for_malware()
            all_issues.extend(malware_issues)
            
            # Scan for bloatware
            bloatware_issues = self._scan_for_bloatware()
            all_issues.extend(bloatware_issues)
            
            # Scan for orphaned entries
            orphaned_issues = self._scan_for_orphaned()
            all_issues.extend(orphaned_issues)
            
            # Scan for invalid entries
            invalid_issues = self._scan_for_invalid()
            all_issues.extend(invalid_issues)
            
            # Scan for security issues
            security_issues = self._scan_for_security()
            all_issues.extend(security_issues)
            
            # Process findings
            self._process_findings(all_issues)
            
            # Generate scan report
            self._generate_scan_report(all_issues)
            
            logger.info(f"Registry scan complete: Found {len(all_issues)} issues")
            
        except Exception as e:
            logger.error(f"Error scanning registry: {e}")
    
    def _scan_for_malware(self) -> List[RegistryIssue]:
        """فحص مدخلات البرامج الضارة"""
        issues = []
        
        try:
            # Scan common auto-start locations
            auto_start_paths = [
                r'HKLM\Software\Microsoft\Windows\CurrentVersion\Run',
                r'HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce',
                r'HKCU\Software\Microsoft\Windows\CurrentVersion\Run',
                r'HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce',
                r'HKLM\Software\Microsoft\Windows\CurrentVersion\RunServices',
                r'HKLM\Software\Microsoft\Windows\CurrentVersion\RunServicesOnce',
            ]
            
            for path in auto_start_paths:
                entries = self._enumerate_registry_keys(path)
                
                for entry in entries:
                    # Check for suspicious patterns
                    if self._is_suspicious_entry(entry):
                        issue = RegistryIssue(
                            issue_id=f"MAL_{int(time.time())}_{hash(entry['path'])}",
                            issue_type=RegistryIssueType.MALWARE,
                            registry_path=entry['path'],
                            key_name=entry['name'],
                            current_value=entry['value'],
                            expected_value="",  # Should be removed
                            severity=Severity.HIGH,
                            description="Suspicious auto-start entry detected",
                            detected_at=datetime.now(),
                            source="Malware pattern detection"
                        )
                        issues.append(issue)
        
        except Exception as e:
            logger.error(f"Error scanning for malware: {e}")
        
        return issues
    
    def _scan_for_bloatware(self) -> List[RegistryIssue]:
        """فحص مدخلات البرامج غير المرغوب فيها"""
        issues = []
        
        try:
            # Scan uninstall keys for orphaned entries
            uninstall_path = r'HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall'
            entries = self._enumerate_registry_keys(uninstall_path)
            
            for entry in entries:
                # Check if this is likely bloatware
                if self._is_bloatware_entry(entry):
                    issue = RegistryIssue(
                        issue_id=f"BLT_{int(time.time())}_{hash(entry['path'])}",
                        issue_type=RegistryIssueType.BLOATWARE,
                        registry_path=entry['path'],
                        key_name=entry['name'],
                        current_value=entry.get('DisplayName', 'Unknown'),
                        expected_value="",  # Should be removed
                        severity=Severity.MEDIUM,
                        description="Bloatware or unwanted software entry",
                        detected_at=datetime.now(),
                        source="Bloatware detection"
                    )
                    issues.append(issue)
        
        except Exception as e:
            logger.error(f"Error scanning for bloatware: {e}")
        
        return issues
    
    def _scan_for_orphaned(self) -> List[RegistryIssue]:
        """فحص المدخلات اليتيمة"""
        issues = []
        
        try:
            # Scan file associations for orphaned entries
            file_assoc_path = r'HKLM\Software\Classes'
            # This would be a more complex scan in reality
            # For now, return empty list
            
        except Exception as e:
            logger.error(f"Error scanning for orphaned entries: {e}")
        
        return issues
    
    def _scan_for_invalid(self) -> List[RegistryIssue]:
        """فحص المدخلات غير الصالحة"""
        issues = []
        
        try:
            # Scan for invalid file paths
            path_keys = [
                r'HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment\Path',
                r'HKCU\Environment\Path',
            ]
            
            for path_key in path_keys:
                entries = self._enumerate_registry_keys(path_key)
                
                for entry in entries:
                    # Check if path exists
                    if not self._is_valid_path(entry['value']):
                        issue = RegistryIssue(
                            issue_id=f"INV_{int(time.time())}_{hash(entry['path'])}",
                            issue_type=RegistryIssueType.INVALID,
                            registry_path=entry['path'],
                            key_name=entry['name'],
                            current_value=entry['value'],
                            expected_value="",  # Should be removed or corrected
                            severity=Severity.LOW,
                            description="Invalid or non-existent file path",
                            detected_at=datetime.now(),
                            source="Path validation"
                        )
                        issues.append(issue)
        
        except Exception as e:
            logger.error(f"Error scanning for invalid entries: {e}")
        
        return issues
    
    def _scan_for_security(self) -> List[RegistryIssue]:
        """فحص مشاكل الأمان"""
        issues = []
        
        try:
            # Check for weak security settings
            security_checks = [
                {
                    'path': r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System',
                    'key': 'EnableLUA',
                    'expected': '1',
                    'description': 'User Account Control disabled'
                },
                {
                    'path': r'HKLM\SYSTEM\CurrentControlSet\Control\Lsa',
                    'key': 'LimitBlankPasswordUse',
                    'expected': '1',
                    'description': 'Blank password use not limited'
                },
                {
                    'path': r'HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management',
                    'key': 'ClearPageFileAtShutdown',
                    'expected': '1',
                    'description': 'Page file not cleared at shutdown'
                },
            ]
            
            for check in security_checks:
                value = self._get_registry_value(check['path'], check['key'])
                
                if value and value != check['expected']:
                    issue = RegistryIssue(
                        issue_id=f"SEC_{int(time.time())}_{hash(check['path'])}",
                        issue_type=RegistryIssueType.SECURITY,
                        registry_path=check['path'],
                        key_name=check['key'],
                        current_value=value,
                        expected_value=check['expected'],
                        severity=Severity.HIGH,
                        description=check['description'],
                        detected_at=datetime.now(),
                        source="Security audit"
                    )
                    issues.append(issue)
        
        except Exception as e:
            logger.error(f"Error scanning for security issues: {e}")
        
        return issues
    
    def _enumerate_registry_keys(self, registry_path: str) -> List[Dict]:
        """تعداد مفاتيح السجل"""
        entries = []
        
        try:
            # Use PowerShell to enumerate registry keys
            ps_command = f"""
            $path = "{registry_path}"
            $items = Get-ItemProperty -Path "Registry::$path" -ErrorAction SilentlyContinue
            
            if ($items) {{
                $entries = @()
                $items.PSObject.Properties | Where-Object {{$_.Name -notmatch '^PS'}} | ForEach-Object {{
                    $val = if ($null -eq $_.Value) {{ "" }} else {{ [string]$_.Value }}
                    $entries += @{{
                        Path = $path
                        Name = $_.Name
                        Value = $val
                        Type = "String"
                    }}
                }}
                $entries | ConvertTo-Json
            }} else {{
                "[]"
            }}
            """
            timeout_seconds = int(self.config.get('modules.registry_guardian.powershell_timeout_seconds', 60))
            timeout_seconds = max(15, timeout_seconds)
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            
            if result.returncode == 0 and result.stdout:
                parsed = json.loads(result.stdout.strip() or "[]")
                if isinstance(parsed, dict):
                    parsed = [parsed]
                for item in parsed:
                    if not isinstance(item, dict):
                        continue
                    entries.append({
                        'path': item.get('Path', registry_path),
                        'name': item.get('Name', ''),
                        'value': item.get('Value', ''),
                        'type': item.get('Type', 'String')
                    })
        
        except Exception as e:
            logger.error(f"Error enumerating registry keys: {e}")
        
        return entries
    
    def _get_registry_value(self, registry_path: str, key_name: str) -> Optional[str]:
        """الحصول على قيمة السجل"""
        try:
            # Use reg command to get value
            result = subprocess.run(
                ['reg', 'query', registry_path, '/v', key_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 3:
                    # Extract value from line
                    value_line = lines[2]
                    if 'REG_' in value_line:
                        parts = value_line.split('REG_')
                        if len(parts) >= 2:
                            return parts[1].strip()
        
        except Exception as e:
            logger.debug(f"Error getting registry value: {e}")
        
        return None
    
    def _is_suspicious_entry(self, entry: Dict) -> bool:
        """التحقق إذا كان المدخل مشبوهاً"""
        value = entry['value'].lower()
        path = entry['path'].lower()
        
        # Check for common malware patterns
        suspicious_patterns = [
            'temp\\',
            'appdata\\local\\temp\\',
            'downloads\\',
            '.exe /s',
            '.exe -s',
            'silent',
            'install',
            'update',
            'powershell',
            'cmd.exe',
            'wscript',
            'cscript',
        ]
        
        for pattern in suspicious_patterns:
            if pattern in value:
                return True
        
        # Check path patterns
        for pattern in self.MALWARE_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        
        return False
    
    def _is_bloatware_entry(self, entry: Dict) -> bool:
        """التحقق إذا كان المدخل برنامجاً غير مرغوب فيه"""
        # Check common bloatware publishers
        bloatware_publishers = [
            'ask.com',
            'babylon',
            'conduit',
            'mywebsearch',
            'speedbit',
            'toolbar',
            'yahoo toolbar',
            'google toolbar',
        ]
        
        publisher = entry.get('Publisher', '').lower()
        display_name = entry.get('DisplayName', '').lower()
        
        for bloatware in bloatware_publishers:
            if bloatware in publisher or bloatware in display_name:
                return True
        
        # Check for toolbars and browser helpers
        if any(keyword in display_name for keyword in ['toolbar', 'bar', 'helper', 'plugin', 'addon']):
            return True
        
        return False
    
    def _is_valid_path(self, path_value: str) -> bool:
        """التحقق إذا كان المسار صالحاً"""
        import os
        
        # Extract paths from registry value
        paths = path_value.split(';')
        
        for path in paths:
            path = path.strip()
            if path and not os.path.exists(path):
                return False
        
        return True
    
    def _is_critical_path(self, registry_path: str) -> bool:
        """التحقق إذا كان المسار حرجاً"""
        for critical_path in self.CRITICAL_PATHS:
            if critical_path.lower() in registry_path.lower():
                return True
        return False
    
    def _process_findings(self, issues: List[RegistryIssue]):
        """معالجة النتائج"""
        # Group issues by severity
        critical_issues = [i for i in issues if i.severity == Severity.CRITICAL]
        high_issues = [i for i in issues if i.severity == Severity.HIGH]
        medium_issues = [i for i in issues if i.severity == Severity.MEDIUM]
        
        # Check if auto-fix is enabled
        auto_fix_safe = self.config.get('modules.registry_guardian.auto_fix_safe_issues', False)
        
        # Handle critical issues immediately
        if critical_issues:
            logger.warning(f"Found {len(critical_issues)} critical registry issues")
            
            for issue in critical_issues:
                self._handle_critical_issue(issue)
        
        # Handle high severity issues
        if high_issues:
            logger.warning(f"Found {len(high_issues)} high severity registry issues")
            
            for issue in high_issues:
                if auto_fix_safe and not self._is_critical_path(issue.registry_path):
                    self._fix_registry_issue(issue)
                else:
                    self._report_issue_to_user(issue)
        
        # Log medium and low issues
        if medium_issues:
            logger.info(f"Found {len(medium_issues)} medium severity registry issues")
            
            for issue in medium_issues:
                self._log_issue(issue)
    
    def _handle_critical_issue(self, issue: RegistryIssue):
        """معالجة المشكلة الحرجة"""
        logger.critical(f"Critical registry issue: {issue.registry_path}\\{issue.key_name}")
        
        # Create emergency action
        action = RegistryAction(
            issue=issue,
            action_type="quarantine",
            backup_required=True,
            risk_level="high",
            estimated_time_seconds=10
        )
        
        # Execute action
        self._execute_registry_action(action)
        
        # Publish critical event
        self.bus.publish(
            'registry.critical_issue',
            source_module='registry_guardian',
            payload={
                'issue': issue.__dict__,
                'action': action.__dict__,
                'requires_immediate_attention': True
            }
        )
    
    def _fix_registry_issue(self, issue: RegistryIssue):
        """إصلاح مشكلة السجل"""
        try:
            # Create action based on issue type
            if issue.issue_type == RegistryIssueType.MALWARE:
                action_type = "delete"
            elif issue.issue_type == RegistryIssueType.SECURITY:
                action_type = "modify"
            else:
                action_type = "delete"
            
            action = RegistryAction(
                issue=issue,
                action_type=action_type,
                backup_required=True,
                risk_level="medium",
                estimated_time_seconds=5
            )
            
            # Execute action
            self._execute_registry_action(action)
            
        except Exception as e:
            logger.error(f"Error fixing registry issue: {e}")
    
    def _report_issue_to_user(self, issue: RegistryIssue):
        """الإبلاغ عن المشكلة للمستخدم"""
        # Create action for user approval
        action = RegistryAction(
            issue=issue,
            action_type="modify" if issue.expected_value else "delete",
            backup_required=True,
            risk_level="medium",
            estimated_time_seconds=5
        )
        
        # Publish for user approval
        self.bus.publish(
            'registry.issue_detected',
            source_module='registry_guardian',
            payload={
                'issue': issue.__dict__,
                'action': action.__dict__,
                'requires_user_approval': True
            }
        )
    
    def _log_issue(self, issue: RegistryIssue):
        """تسجيل المشكلة"""
        self.db.log_event(
            event_type='registry_issue',
            module_name='registry_guardian',
            severity=issue.severity.value,
            message=f"Registry issue: {issue.registry_path}\\{issue.key_name}",
            details=issue.__dict__
        )
    
    def _execute_registry_action(self, action: RegistryAction):
        """تنفيذ إجراء على السجل"""
        try:
            if action.action_type == "delete":
                self._delete_registry_key(action.issue.registry_path, action.issue.key_name)
                
            elif action.action_type == "modify":
                self._set_registry_value(
                    action.issue.registry_path,
                    action.issue.key_name,
                    action.issue.expected_value
                )
            
            elif action.action_type == "quarantine":
                # Backup then delete
                self._backup_registry_key(action.issue.registry_path, action.issue.key_name)
                self._delete_registry_key(action.issue.registry_path, action.issue.key_name)
            
            # Log action
            self.db.log_event(
                event_type='registry_action',
                module_name='registry_guardian',
                severity='info',
                message=f"Registry action: {action.action_type} on {action.issue.registry_path}",
                details=action.__dict__
            )
            
            logger.info(f"Executed registry action: {action.action_type}")
            
        except Exception as e:
            logger.error(f"Error executing registry action: {e}")
    
    def _delete_registry_key(self, registry_path: str, key_name: str):
        """حذف مفتاح السجل"""
        try:
            # Use reg command to delete key
            subprocess.run(
                ['reg', 'delete', registry_path, '/v', key_name, '/f'],
                check=True,
                timeout=5
            )
            
        except Exception as e:
            raise Exception(f"Failed to delete registry key: {e}")
    
    def _set_registry_value(self, registry_path: str, key_name: str, value: str):
        """تعيين قيمة السجل"""
        try:
            # Use reg command to set value
            subprocess.run(
                ['reg', 'add', registry_path, '/v', key_name, '/d', value, '/f'],
                check=True,
                timeout=5
            )
            
        except Exception as e:
            raise Exception(f"Failed to set registry value: {e}")
    
    def _backup_registry_key(self, registry_path: str, key_name: str):
        """نسخ احتياطي لمفتاح السجل"""
        try:
            # Create backup directory
            backup_dir = Path(__file__).parent / 'registry_backups'
            backup_dir.mkdir(exist_ok=True)
            
            # Generate backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_path = registry_path.replace('\\', '_').replace(':', '')
            backup_file = backup_dir / f"{safe_path}_{key_name}_{timestamp}.reg"
            
            # Export registry key
            subprocess.run(
                ['reg', 'export', registry_path, str(backup_file), '/y'],
                check=True,
                timeout=10
            )
            
            logger.info(f"Backed up registry key to: {backup_file}")
            
        except Exception as e:
            logger.error(f"Error backing up registry key: {e}")
    
    def _generate_scan_report(self, issues: List[RegistryIssue]):
        """توليد تقرير الفحص"""
        # Count issues by type and severity
        stats = {
            'total_issues': len(issues),
            'by_type': {},
            'by_severity': {},
            'scan_timestamp': datetime.now().isoformat()
        }
        
        # Count by type
        for issue_type in RegistryIssueType:
            count = sum(1 for i in issues if i.issue_type == issue_type)
            stats['by_type'][issue_type.value] = count
        
        # Count by severity
        for severity in Severity:
            count = sum(1 for i in issues if i.severity == severity)
            stats['by_severity'][severity.value] = count
        
        # Log report
        self.db.log_event(
            event_type='registry_scan_report',
            module_name='registry_guardian',
            severity='info',
            message=f"Registry scan: {len(issues)} issues found",
            details=stats
        )
    
    def get_registry_report(self) -> Dict:
        """الحصول على تقرير السجل"""
        # Get recent scan results from database
        # For now, return basic statistics
        return {
            'last_scan': datetime.now().isoformat(),
            'total_issues_found': 0,
            'critical_issues': 0,
            'recommendations': [
                "Run full registry scan for detailed report"
            ]
        }
    
    def run_custom_scan(self, scan_type: str = "full") -> Dict:
        """تشغيل فحص مخصص"""
        logger.info(f"Running custom registry scan: {scan_type}")
        
        issues = []
        
        if scan_type == "malware":
            issues = self._scan_for_malware()
        elif scan_type == "security":
            issues = self._scan_for_security()
        elif scan_type == "bloatware":
            issues = self._scan_for_bloatware()
        elif scan_type == "full":
            issues.extend(self._scan_for_malware())
            issues.extend(self._scan_for_security())
            issues.extend(self._scan_for_bloatware())
            issues.extend(self._scan_for_invalid())
            issues.extend(self._scan_for_orphaned())
        
        # Process findings
        self._process_findings(issues)
        
        return {
            'scan_type': scan_type,
            'issues_found': len(issues),
            'critical_issues': sum(1 for i in issues if i.severity == Severity.CRITICAL),
            'high_issues': sum(1 for i in issues if i.severity == Severity.HIGH),
            'timestamp': datetime.now().isoformat()
        }


# Global instance
_registry_guardian_instance = None

def get_registry_guardian() -> RegistryGuardian:
    """الحصول على instance الموديول"""
    global _registry_guardian_instance
    if _registry_guardian_instance is None:
        _registry_guardian_instance = RegistryGuardian()
    return _registry_guardian_instance
