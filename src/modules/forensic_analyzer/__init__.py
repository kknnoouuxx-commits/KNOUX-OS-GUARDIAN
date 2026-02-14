"""
Forensic System Analyzer
تحليل نظامي شرعي لكشف جذور المشاكل والأعطال
"""

import logging
import threading
import time
import subprocess
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.communication_bus import get_bus
from src.core.database import get_database
from src.core.config import get_config
from src.core.serialization import safe_json_dumps

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """نوع التحليل"""
    CRASH = "crash"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STABILITY = "stability"
    BOOT = "boot"


class Severity(Enum):
    """خطورة النتيجة"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ForensicFinding:
    """نتيجة تحليل شرعي"""
    analysis_id: str
    analysis_type: AnalysisType
    title: str
    description: str
    severity: Severity
    confidence: float  # 0.0-1.0
    evidence: List[str]
    root_cause: str
    remediation: str
    affected_components: List[str]
    timestamp: datetime


@dataclass
class SystemEvent:
    """حدث نظام"""
    event_id: int
    event_type: str
    source: str
    timestamp: datetime
    message: str
    details: Dict


class ForensicAnalyzer:
    """
    محلل النظام الشرعي
    Forensic System Analyzer
    """
    
    def __init__(self):
        self.bus = get_bus()
        self.db = get_database()
        self.config = get_config()
        self.running = False
        self.analyzer_thread = None
        
        # Analysis patterns
        self.analysis_patterns = self._load_analysis_patterns()
        
        # Event history
        self.event_history = []
        
        logger.info("Forensic Analyzer initialized")
    
    def start(self):
        """بدء التحليل"""
        if not self.running:
            self.running = True
            self.analyzer_thread = threading.Thread(
                target=self._analysis_loop,
                daemon=True
            )
            self.analyzer_thread.start()
            
            # Subscribe to events
            self.bus.subscribe('system.crash', self.handle_system_crash)
            self.bus.subscribe('system.performance_issue', self.handle_performance_issue)
            self.bus.subscribe('system.security_incident', self.handle_security_incident)
            
            logger.info("Forensic Analyzer started")
    
    def stop(self):
        """إيقاف التحليل"""
        self.running = False
        if self.analyzer_thread:
            self.analyzer_thread.join(timeout=5)
        logger.info("Forensic Analyzer stopped")
    
    def _analysis_loop(self):
        """حلقة التحليل الرئيسية"""
        auto_analyze = self.config.get('modules.forensic_analyzer.auto_analyze_crashes', True)
        
        while self.running:
            try:
                if auto_analyze:
                    # Check for recent crashes
                    self._analyze_recent_crashes()
                
                # Check system stability
                self._analyze_system_stability()
                
                # Wait for next analysis
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _analyze_recent_crashes(self):
        """تحليل الأعطال الحديثة"""
        logger.debug("Analyzing recent crashes...")
        
        try:
            # Get recent crash events
            crash_events = self._get_crash_events()
            
            for event in crash_events:
                # Analyze crash
                findings = self._analyze_crash_event(event)
                
                for finding in findings:
                    # Log finding
                    self._log_forensic_finding(finding)
                    
                    # Take action if critical
                    if finding.severity in [Severity.CRITICAL, Severity.HIGH]:
                        self._handle_critical_finding(finding)
            
        except Exception as e:
            logger.error(f"Error analyzing crashes: {e}")
    
    def _get_crash_events(self) -> List[SystemEvent]:
        """الحصول على أحداث الأعطال"""
        events = []
        
        try:
            # Get system crash events from Event Log
            ps_command = """
            Get-WinEvent -FilterHashtable @{
                LogName='System'
                Level=1,2  # Critical, Error
            } -MaxEvents 20 | 
            Select-Object Id, LevelDisplayName, ProviderName, TimeCreated, Message |
            ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                events_data = json.loads(result.stdout)
                
                # Ensure events_data is a list
                if isinstance(events_data, dict):
                    events_data = [events_data]
                elif not isinstance(events_data, list):
                    events_data = []
                
                for event_data in events_data:
                    if not isinstance(event_data, dict):
                        continue
                    ts_str = event_data.get('TimeCreated', '')
                    if ts_str.startswith('/Date(') and ts_str.endswith(')/'):
                        try:
                            ticks = int(ts_str[6:-2])
                            timestamp = datetime.fromtimestamp(ticks / 1000)
                        except (ValueError, OSError):
                            continue
                    else:
                        try:
                            timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                        except ValueError:
                            continue
                    event = SystemEvent(
                        event_id=event_data.get('Id', 0),
                        event_type=event_data.get('LevelDisplayName', ''),
                        source=event_data.get('ProviderName', ''),
                        timestamp=timestamp,
                        message=event_data.get('Message', ''),
                        details={'raw_event': event_data}
                    )
                    
                    events.append(event)
        
        except Exception as e:
            logger.error(f"Error getting crash events: {e}")
        
        return events
    
    def _analyze_crash_event(self, event: SystemEvent) -> List[ForensicFinding]:
        """تحليل حدث عطل"""
        findings = []
        
        # Pattern 1: Blue Screen (BSOD) analysis
        if '0x' in event.message and any(keyword in event.message for keyword in ['STOP', 'BugCheck', 'KMODE']):
            finding = self._analyze_bsod(event)
            findings.append(finding)
        
        # Pattern 2: Application crash
        elif any(keyword in event.message for keyword in ['Application Error', 'Faulting application', 'stopped working']):
            finding = self._analyze_application_crash(event)
            findings.append(finding)
        
        # Pattern 3: Service crash
        elif any(keyword in event.message for keyword in ['service terminated unexpectedly', 'service crashed']):
            finding = self._analyze_service_crash(event)
            findings.append(finding)
        
        # Pattern 4: Driver crash
        elif any(keyword in event.message for keyword in ['Driver', 'driver', 'atapi.sys', 'ntoskrnl.exe']):
            finding = self._analyze_driver_crash(event)
            findings.append(finding)
        
        # Pattern 5: Memory corruption
        elif any(keyword in event.message for keyword in ['memory', 'corruption', 'access violation']):
            finding = self._analyze_memory_corruption(event)
            findings.append(finding)
        
        return findings
    
    def _analyze_bsod(self, event: SystemEvent) -> ForensicFinding:
        """تحليل شاشة الموت الزرقاء"""
        # Extract bugcheck code
        bugcheck_code = "Unknown"
        if '0x' in event.message:
            import re
            match = re.search(r'0x[0-9A-Fa-f]+', event.message)
            if match:
                bugcheck_code = match.group(0)
        
        # Determine root cause based on bugcheck code
        root_cause = self._determine_bsod_root_cause(bugcheck_code)
        
        # Create finding
        finding = ForensicFinding(
            analysis_id=f"BSOD_{int(time.time())}",
            analysis_type=AnalysisType.CRASH,
            title=f"Blue Screen of Death: {bugcheck_code}",
            description=f"System experienced a critical crash with bugcheck code {bugcheck_code}",
            severity=Severity.CRITICAL,
            confidence=0.8,
            evidence=[event.message[:500]],  # First 500 chars
            root_cause=root_cause,
            remediation=self._get_bsod_remediation(bugcheck_code),
            affected_components=['Kernel', 'Drivers', 'Hardware'],
            timestamp=datetime.now()
        )
        
        return finding
    
    def _determine_bsod_root_cause(self, bugcheck_code: str) -> str:
        """تحديد السبب الجذري لـ BSOD"""
        bsod_patterns = {
            '0x0000000A': 'IRQL_NOT_LESS_OR_EQUAL - Driver issue or memory corruption',
            '0x0000001E': 'KMODE_EXCEPTION_NOT_HANDLED - Driver compatibility issue',
            '0x0000003B': 'SYSTEM_SERVICE_EXCEPTION - System service failure',
            '0x00000050': 'PAGE_FAULT_IN_NONPAGED_AREA - Memory or driver issue',
            '0x0000007B': 'INACCESSIBLE_BOOT_DEVICE - Storage/driver issue during boot',
            '0x0000007E': 'SYSTEM_THREAD_EXCEPTION_NOT_HANDLED - Driver or system file issue',
            '0x000000D1': 'DRIVER_IRQL_NOT_LESS_OR_EQUAL - Driver memory access violation',
            '0x000000EA': 'THREAD_STUCK_IN_DEVICE_DRIVER - Display driver issue',
            '0x00000124': 'WHEA_UNCORRECTABLE_ERROR - Hardware failure',
            '0x00000133': 'DPC_WATCHDOG_VIOLATION - Driver taking too long',
            '0x00000139': 'KERNEL_SECURITY_CHECK_FAILURE - Memory corruption',
        }
        
        return bsod_patterns.get(bugcheck_code, 'Unknown system crash - requires further investigation')
    
    def _get_bsod_remediation(self, bugcheck_code: str) -> str:
        """الحصول على إصلاح لـ BSOD"""
        remediation_patterns = {
            '0x0000000A': '1. Update drivers (especially graphics and chipset)\n2. Run memory diagnostic\n3. Check for overheating',
            '0x0000001E': '1. Update problematic drivers\n2. Check for software conflicts\n3. Run system file checker (sfc /scannow)',
            '0x0000003B': '1. Update Windows\n2. Check antivirus software\n3. Disable overclocking',
            '0x00000050': '1. Check RAM with Windows Memory Diagnostic\n2. Update drivers\n3. Check disk for errors',
            '0x0000007B': '1. Check boot order in BIOS\n2. Update storage drivers\n3. Check disk connections',
            '0x0000007E': '1. Update display drivers\n2. Check for BIOS updates\n3. Disable hardware acceleration',
            '0x000000D1': '1. Update network/storage drivers\n2. Check for malware\n3. Disable antivirus temporarily',
            '0x000000EA': '1. Update graphics driver\n2. Lower display settings\n3. Check GPU temperature',
            '0x00000124': '1. Check CPU/GPU temperature\n2. Test RAM\n3. Check power supply',
            '0x00000133': '1. Update all drivers\n2. Disable USB devices\n3. Check for BIOS updates',
            '0x00000139': '1. Run memory diagnostic\n2. Update drivers\n3. Check for corrupt system files',
        }
        
        return remediation_patterns.get(bugcheck_code, 
            '1. Update Windows to latest version\n2. Update all drivers\n3. Run system diagnostics\n4. Check hardware components')
    
    def _analyze_application_crash(self, event: SystemEvent) -> ForensicFinding:
        """تحليل تعطل التطبيق"""
        # Extract application name
        app_name = "Unknown Application"
        if 'Faulting application' in event.message:
            lines = event.message.split('\n')
            for line in lines:
                if 'Faulting application' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        app_name = parts[1].strip()
                        break
        
        # Create finding
        finding = ForensicFinding(
            analysis_id=f"APP_CRASH_{int(time.time())}",
            analysis_type=AnalysisType.CRASH,
            title=f"Application Crash: {app_name}",
            description=f"Application {app_name} crashed unexpectedly",
            severity=Severity.HIGH,
            confidence=0.7,
            evidence=[event.message[:500]],
            root_cause="Application compatibility issue, missing dependencies, or memory corruption",
            remediation=f"1. Update {app_name}\n2. Reinstall application\n3. Check for Windows updates\n4. Run application in compatibility mode",
            affected_components=[app_name, 'User Profile', 'Application Dependencies'],
            timestamp=datetime.now()
        )
        
        return finding
    
    def _analyze_service_crash(self, event: SystemEvent) -> ForensicFinding:
        """تحليل تعطل الخدمة"""
        # Extract service name
        service_name = "Unknown Service"
        if 'service' in event.message.lower():
            lines = event.message.split('\n')
            for line in lines:
                if 'service' in line.lower():
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.lower() == 'service' and i > 0:
                            service_name = parts[i-1]
                            break
        
        # Create finding
        finding = ForensicFinding(
            analysis_id=f"SVC_CRASH_{int(time.time())}",
            analysis_type=AnalysisType.CRASH,
            title=f"Service Crash: {service_name}",
            description=f"System service {service_name} terminated unexpectedly",
            severity=Severity.HIGH,
            confidence=0.6,
            evidence=[event.message[:500]],
            root_cause="Service dependency issue, configuration error, or permission problem",
            remediation=f"1. Restart {service_name} service\n2. Check service dependencies\n3. Verify service permissions\n4. Check event logs for related errors",
            affected_components=[service_name, 'Service Control Manager', 'System Services'],
            timestamp=datetime.now()
        )
        
        return finding
    
    def _analyze_driver_crash(self, event: SystemEvent) -> ForensicFinding:
        """تحليل تعطل التعريف"""
        # Extract driver name
        driver_name = "Unknown Driver"
        if 'Driver' in event.message:
            lines = event.message.split('\n')
            for line in lines:
                if 'Driver' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'Driver' and i + 1 < len(parts):
                            driver_name = parts[i + 1].strip('"\'')
                            break
        
        # Create finding
        finding = ForensicFinding(
            analysis_id=f"DRV_CRASH_{int(time.time())}",
            analysis_type=AnalysisType.CRASH,
            title=f"Driver Crash: {driver_name}",
            description=f"Driver {driver_name} caused a system crash",
            severity=Severity.CRITICAL,
            confidence=0.75,
            evidence=[event.message[:500]],
            root_cause="Driver bug, compatibility issue, or hardware failure",
            remediation=f"1. Update {driver_name} driver\n2. Rollback to previous driver version\n3. Check for hardware issues\n4. Disable driver temporarily",
            affected_components=[driver_name, 'Kernel', 'Hardware'],
            timestamp=datetime.now()
        )
        
        return finding
    
    def _analyze_memory_corruption(self, event: SystemEvent) -> ForensicFinding:
        """تحليل فساد الذاكرة"""
        finding = ForensicFinding(
            analysis_id=f"MEM_CORRUPT_{int(time.time())}",
            analysis_type=AnalysisType.CRASH,
            title="Memory Corruption Detected",
            description="System detected memory corruption or access violation",
            severity=Severity.CRITICAL,
            confidence=0.8,
            evidence=[event.message[:500]],
            root_cause="Faulty RAM, driver memory leak, or software bug",
            remediation="1. Run Windows Memory Diagnostic\n2. Update all drivers\n3. Check for overheating\n4. Test RAM modules individually",
            affected_components=['RAM', 'Kernel', 'Drivers'],
            timestamp=datetime.now()
        )
        
        return finding
    
    def _analyze_system_stability(self):
        """تحليل استقرار النظام"""
        logger.debug("Analyzing system stability...")
        
        try:
            # Check system uptime
            uptime = self._get_system_uptime()
            
            # Check recent crash frequency
            crash_frequency = self._calculate_crash_frequency()
            
            # Check resource usage patterns
            resource_patterns = self._analyze_resource_patterns()
            
            # Generate stability assessment
            stability_score = self._calculate_stability_score(uptime, crash_frequency, resource_patterns)
            
            # Log stability assessment
            self.db.log_event(
                event_type='system_stability_assessment',
                module_name='forensic_analyzer',
                severity='info',
                message=f"System stability: {stability_score}/100",
                details={
                    'uptime_hours': uptime,
                    'crash_frequency': crash_frequency,
                    'stability_score': stability_score,
                    'resource_patterns': resource_patterns
                }
            )
            
            # Take action if stability is low
            if stability_score < 50:
                self._handle_low_stability(uptime, crash_frequency, resource_patterns)
            
        except Exception as e:
            logger.error(f"Error analyzing system stability: {e}")
    
    def _get_system_uptime(self) -> float:
        """الحصول على وقت تشغيل النظام"""
        try:
            import psutil
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            return uptime_seconds / 3600  # Convert to hours
        except:
            return 0.0
    
    def _calculate_crash_frequency(self) -> Dict:
        """حساب تواتر الأعطال"""
        try:
            # Get crash events from last 24 hours
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            # Count crashes by type
            crash_counts = {
                'bsod': 0,
                'application': 0,
                'service': 0,
                'driver': 0,
                'other': 0
            }

            recent_events = self.db.fetch_events(
                start_time=start_time,
                end_time=end_time,
                limit=2000
            )

            for evt in recent_events:
                try:
                    event_type = (evt.get('event_type') or '').lower()
                    module_name = (evt.get('module_name') or '').lower()
                    message = (evt.get('message') or '').lower()
                except AttributeError:
                    # If evt is not a dict, skip
                    continue

                if 'bsod' in event_type or 'bugcheck' in message or 'blue screen' in message:
                    crash_counts['bsod'] += 1
                elif 'driver' in event_type or 'driver' in module_name or 'driver crash' in message:
                    crash_counts['driver'] += 1
                elif 'service' in message or 'service' in event_type:
                    crash_counts['service'] += 1
                elif 'application' in message or 'app' in event_type:
                    crash_counts['application'] += 1
                elif event_type.endswith('failed') or (evt.get('severity') or '').lower() in ['error', 'critical']:
                    crash_counts['other'] += 1

            return crash_counts
            
        except Exception as e:
            logger.error(f"Error calculating crash frequency: {e}")
            return {}
    
    def _analyze_resource_patterns(self) -> Dict:
        """تحليل أنماط استخدام الموارد"""
        try:
            import psutil
            
            patterns = {
                'cpu_spikes': 0,
                'memory_leaks': 0,
                'disk_high_usage': 0,
                'network_bursts': 0
            }
            
            # Check CPU spikes
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            avg_cpu = sum(cpu_percent) / len(cpu_percent)
            if avg_cpu > 80:
                patterns['cpu_spikes'] = 1
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                patterns['memory_leaks'] = 1
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                patterns['disk_high_usage'] = 1
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing resource patterns: {e}")
            return {}
    
    def _calculate_stability_score(self, uptime: float, crash_frequency: Dict, resource_patterns: Dict) -> float:
        """حساب درجة استقرار النظام"""
        score = 100.0
        
        # Factor 1: Uptime (40% weight)
        if uptime < 1:  # Less than 1 hour
            score -= 40
        elif uptime < 24:  # Less than 1 day
            score -= 20
        elif uptime < 168:  # Less than 1 week
            score -= 10
        # More than 1 week adds 0
        
        # Factor 2: Crash frequency (40% weight)
        total_crashes = sum(crash_frequency.values())
        if total_crashes > 10:
            score -= 40
        elif total_crashes > 5:
            score -= 30
        elif total_crashes > 2:
            score -= 20
        elif total_crashes > 0:
            score -= 10
        
        # Factor 3: Resource patterns (20% weight)
        resource_issues = sum(resource_patterns.values())
        if resource_issues >= 3:
            score -= 20
        elif resource_issues >= 2:
            score -= 15
        elif resource_issues >= 1:
            score -= 5
        
        return max(0.0, min(100.0, score))
    
    def _handle_low_stability(self, uptime: float, crash_frequency: Dict, resource_patterns: Dict):
        """معالجة انخفاض استقرار النظام"""
        logger.warning(f"Low system stability detected (uptime: {uptime:.1f}h)")
        
        # Create stability finding
        finding = ForensicFinding(
            analysis_id=f"STABILITY_{int(time.time())}",
            analysis_type=AnalysisType.STABILITY,
            title="Low System Stability",
            description=f"System showing signs of instability with {uptime:.1f} hours uptime",
            severity=Severity.HIGH,
            confidence=0.7,
            evidence=[f"Uptime: {uptime:.1f}h", f"Crash patterns: {crash_frequency}"],
            root_cause="Frequent crashes, resource issues, or hardware problems",
            remediation="1. Run system diagnostics\n2. Update all drivers\n3. Check hardware health\n4. Consider system restore",
            affected_components=['System Stability', 'Hardware', 'Drivers'],
            timestamp=datetime.now()
        )
        
        # Log finding
        self._log_forensic_finding(finding)
        
        # Publish event
        self.bus.publish(
            'system.low_stability',
            source_module='forensic_analyzer',
            payload={
                'finding': finding.__dict__,
                'uptime': uptime,
                'crash_frequency': crash_frequency,
                'requires_user_attention': True
            }
        )
    
    def _log_forensic_finding(self, finding: ForensicFinding):
        """تسجيل نتيجة التحليل الشرعي"""
        self.db.log_event(
            event_type='forensic_finding',
            module_name='forensic_analyzer',
            severity=finding.severity.value,
            message=f"{finding.title}: {finding.description[:100]}...",
            details=finding.__dict__
        )
    
    def _handle_critical_finding(self, finding: ForensicFinding):
        """معالجة النتيجة الحرجة"""
        logger.warning(f"Critical forensic finding: {finding.title}")
        
        # Publish for immediate attention
        self.bus.publish(
            'forensic.critical_finding',
            source_module='forensic_analyzer',
            payload={
                'finding': finding.__dict__,
                'requires_immediate_action': True
            }
        )
    
    def handle_system_crash(self, message):
        """معالجة حدث عطل النظام"""
        payload = message.payload
        crash_type = payload.get('type', 'unknown')
        
        logger.info(f"System crash event: {crash_type}")
        
        # Trigger immediate analysis
        self._analyze_recent_crashes()
    
    def handle_performance_issue(self, message):
        """معالجة حدث مشكلة أداء"""
        payload = message.payload
        issue_type = payload.get('type', 'unknown')
        
        logger.info(f"Performance issue: {issue_type}")
        
        # Analyze performance patterns
        self._analyze_performance_issues()
    
    def handle_security_incident(self, message):
        """معالجة حدث أمني"""
        payload = message.payload
        incident_type = payload.get('type', 'unknown')
        
        logger.warning(f"Security incident: {incident_type}")
        
        # Analyze security implications
        self._analyze_security_incident(payload)
    
    def _analyze_performance_issues(self):
        """تحليل مشاكل الأداء"""
        try:
            import psutil

            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent

            findings = []

            if cpu >= 90:
                findings.append(ForensicFinding(
                    analysis_id=f"PERF_CPU_{int(time.time())}",
                    analysis_type=AnalysisType.PERFORMANCE,
                    title="High CPU Pressure",
                    description=f"CPU usage is high ({cpu:.1f}%)",
                    severity=Severity.HIGH,
                    confidence=0.7,
                    evidence=[f"cpu_percent={cpu:.1f}"],
                    root_cause="Sustained CPU pressure from background processes",
                    remediation="Identify top CPU processes, disable unnecessary startup apps, scan for malware",
                    affected_components=['CPU', 'Processes'],
                    timestamp=datetime.now()
                ))

            if mem >= 90:
                findings.append(ForensicFinding(
                    analysis_id=f"PERF_MEM_{int(time.time())}",
                    analysis_type=AnalysisType.PERFORMANCE,
                    title="High Memory Pressure",
                    description=f"Memory usage is high ({mem:.1f}%)",
                    severity=Severity.HIGH,
                    confidence=0.7,
                    evidence=[f"memory_percent={mem:.1f}"],
                    root_cause="Low available RAM due to heavy workload or memory leaks",
                    remediation="Close heavy apps, check for runaway processes, consider increasing page file",
                    affected_components=['RAM', 'Processes'],
                    timestamp=datetime.now()
                ))

            if disk >= 95:
                findings.append(ForensicFinding(
                    analysis_id=f"PERF_DISK_{int(time.time())}",
                    analysis_type=AnalysisType.PERFORMANCE,
                    title="Disk Nearly Full",
                    description=f"Disk usage is very high ({disk:.1f}%)",
                    severity=Severity.HIGH,
                    confidence=0.8,
                    evidence=[f"disk_percent={disk:.1f}"],
                    root_cause="Insufficient free space causing performance degradation",
                    remediation="Free up disk space, uninstall unused apps, clear temporary files",
                    affected_components=['Disk'],
                    timestamp=datetime.now()
                ))

            for f in findings:
                self._log_forensic_finding(f)

        except Exception as e:
            logger.error(f"Error analyzing performance issues: {e}")
    
    def _analyze_security_incident(self, incident_data: Dict):
        """تحليل الحادث الأمني"""
        try:
            incident_type = incident_data.get('type', 'unknown')
            description = incident_data.get('description', '')

            finding = ForensicFinding(
                analysis_id=f"SEC_{int(time.time())}",
                analysis_type=AnalysisType.SECURITY,
                title=f"Security Incident: {incident_type}",
                description=description or "Security incident event received",
                severity=Severity.HIGH,
                confidence=0.6,
                evidence=[safe_json_dumps(incident_data, ensure_ascii=False)[:500]],
                root_cause="Potential malicious activity or risky configuration",
                remediation="Review event details, isolate suspicious processes, run antivirus scan, inspect firewall rules",
                affected_components=['Security'],
                timestamp=datetime.now()
            )

            self._log_forensic_finding(finding)

            self.bus.publish(
                'forensic.security_finding',
                source_module='forensic_analyzer',
                payload={
                    'finding': finding.__dict__,
                    'requires_user_attention': True
                }
            )

        except Exception as e:
            logger.error(f"Error analyzing security incident: {e}")
    
    def _load_analysis_patterns(self) -> Dict:
        """تحميل أنماط التحليل"""
        try:
            patterns_path = Path(__file__).parent / 'analysis_patterns.json'
            if patterns_path.exists():
                with open(patterns_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
        except Exception as e:
            logger.debug(f"Could not load analysis patterns: {e}")

        return {}
    
    def get_forensic_report(self, hours_back: int = 24) -> Dict:
        """الحصول على تقرير شرعي"""
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        findings_events = self.db.fetch_events(
            start_time=start_time,
            end_time=end_time,
            event_type='forensic_finding',
            module_name='forensic_analyzer',
            limit=2000
        )

        total_findings = len(findings_events)
        critical_findings = 0
        recommendations = []

        for evt in findings_events:
            sev = (evt.get('severity') or '').lower()
            if sev in ['critical']:
                critical_findings += 1

        stability = self.db.fetch_events(
            start_time=start_time,
            end_time=end_time,
            event_type='system_stability_assessment',
            module_name='forensic_analyzer',
            limit=1
        )

        stability_score = 0.0
        if stability:
            try:
                details_json = stability[0].get('details_json')
                if details_json:
                    details = json.loads(details_json)
                    stability_score = float(details.get('stability_score', 0.0) or 0.0)
            except Exception:
                stability_score = 0.0

        if critical_findings > 0:
            recommendations.append('Investigate critical findings immediately and consider rollback actions')
        if stability_score and stability_score < 50:
            recommendations.append('Run full diagnostics and review driver/thermal/power events')

        return {
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'total_findings': total_findings,
            'critical_findings': critical_findings,
            'stability_score': stability_score,
            'recommendations': recommendations
        }


# Global instance
_forensic_analyzer_instance = None

def get_forensic_analyzer() -> ForensicAnalyzer:
    """الحصول على instance الموديول"""
    global _forensic_analyzer_instance
    if _forensic_analyzer_instance is None:
        _forensic_analyzer_instance = ForensicAnalyzer()
    return _forensic_analyzer_instance
