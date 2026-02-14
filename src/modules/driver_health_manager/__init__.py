"""
Smart Driver Health Manager
إدارة ذكية لصحة تعريفات الأجهزة
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


class DriverStatus(Enum):
    """حالة التعريف"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class DriverType(Enum):
    """نوع التعريف"""
    DISPLAY = "display"
    NETWORK = "network"
    AUDIO = "audio"
    STORAGE = "storage"
    CHIPSET = "chipset"
    USB = "usb"
    OTHER = "other"


@dataclass
class DriverInfo:
    """معلومات التعريف"""
    device_name: str
    driver_name: str
    driver_version: str
    driver_date: datetime
    provider: str
    driver_type: DriverType
    status: DriverStatus
    crash_count: int
    last_crash: Optional[datetime]
    device_id: str
    hardware_id: str


@dataclass
class DriverAction:
    """إجراء على التعريف"""
    device_name: str
    driver_name: str
    action_type: str  # update, rollback, reinstall
    risk_level: str  # low, medium, high
    reason: str
    estimated_time_minutes: int
    download_size_mb: float


class DriverHealthManager:
    """
    مدير صحة التعريفات الذكي
    Smart Driver Health Manager
    """
    
    def __init__(self):
        self.bus = get_bus()
        self.db = get_database()
        self.config = get_config()
        self.running = False
        self.monitor_thread = None
        
        # Driver crash history
        self.crash_history = {}
        
        # Critical drivers (never auto-update)
        self.CRITICAL_DRIVERS = [
            'BasicDisplay', 'BasicRender',
            'Microsoft Basic Display Adapter',
            'Microsoft Basic Render Driver'
        ]
        
        logger.info("Driver Health Manager initialized")
    
    def start(self):
        """بدء المراقبة"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitor_thread.start()
            
            # Subscribe to events
            self.bus.subscribe('system.driver_crash', self.handle_driver_crash)
            
            logger.info("Driver Health Manager started")
    
    def stop(self):
        """إيقاف المراقبة"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Driver Health Manager stopped")
    
    def _monitoring_loop(self):
        """حلقة المراقبة الرئيسية"""
        monitor_crashes = self.config.get('modules.driver_manager.monitor_crashes', True)
        
        while self.running:
            try:
                if monitor_crashes:
                    # Check for driver crashes
                    self._check_driver_crashes()
                
                # Check driver health
                self._check_driver_health()
                
                # Wait for next check
                time.sleep(600)  # Check every 10 minutes
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _check_driver_crashes(self):
        """التحقق من تعطل التعريفات"""
        logger.debug("Checking for driver crashes...")
        
        try:
            # Get system event logs for driver crashes
            driver_crashes = self._get_driver_crash_events()
            
            for crash in driver_crashes:
                # Process crash event
                self._process_driver_crash(crash)
            
        except Exception as e:
            logger.error(f"Error checking driver crashes: {e}")
    
    def _get_driver_crash_events(self) -> List[Dict]:
        """الحصول على أحداث تعطل التعريفات"""
        crashes = []
        
        try:
            # Use PowerShell to get driver crash events
            ps_command = """
            Get-WinEvent -FilterHashtable @{
                LogName='System'
                ProviderName='Microsoft-Windows-Kernel-Power'
                ID=41
            } -MaxEvents 10 | Select-Object TimeCreated, Message | ConvertTo-Json
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
            
            for event in events_data:
                if not isinstance(event, dict):
                    continue
                ts_str = event.get('TimeCreated', '')
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
                crash = {
                    'timestamp': timestamp,
                    'message': event.get('Message', ''),
                    'type': 'kernel_power'
                }
                crashes.append(crash)
        
        except Exception as e:
            logger.error(f"Error getting crash events: {e}")
        
        return crashes
    
    def _process_driver_crash(self, crash: Dict):
        """معالجة حدث تعطل التعريف"""
        # Extract driver info from crash message
        driver_name = self._extract_driver_from_crash(crash['message'])
        
        if driver_name:
            # Update crash history
            if driver_name not in self.crash_history:
                self.crash_history[driver_name] = []
            
            self.crash_history[driver_name].append({
                'timestamp': crash['timestamp'],
                'type': crash['type']
            })
            
            # Keep only last 10 crashes
            if len(self.crash_history[driver_name]) > 10:
                self.crash_history[driver_name] = self.crash_history[driver_name][-10:]
            
            # Log crash
            self.db.log_event(
                event_type='driver_crash',
                module_name='driver_health_manager',
                severity='error',
                message=f"Driver crash detected: {driver_name}",
                details={
                    'driver_name': driver_name,
                    'crash': crash,
                    'crash_count': len(self.crash_history[driver_name])
                }
            )
            
            # Publish event
            self.bus.publish(
                'driver.crash',
                source_module='driver_health_manager',
                payload={
                    'driver_name': driver_name,
                    'crash_count': len(self.crash_history[driver_name]),
                    'last_crash': crash['timestamp'].isoformat()
                }
            )
            
            # Check if auto-rollback is enabled
            auto_rollback = self.config.get('modules.driver_manager.auto_rollback_problematic', False)
            
            if auto_rollback and len(self.crash_history[driver_name]) >= 3:
                # Multiple crashes detected - consider rollback
                self._handle_problematic_driver(driver_name)
    
    def _extract_driver_from_crash(self, crash_message: str) -> Optional[str]:
        """استخراج اسم التعريف من رسالة التعطل"""
        # Simple pattern matching
        patterns = [
            'Driver ',
            'driver ',
            ' at ',
            ' failed'
        ]
        
        for pattern in patterns:
            if pattern in crash_message:
                # Try to extract driver name
                lines = crash_message.split('\n')
                for line in lines:
                    if 'Driver' in line or 'driver' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.lower() == 'driver' and i + 1 < len(parts):
                                return parts[i + 1].strip('"\'')
        
        return None
    
    def _handle_problematic_driver(self, driver_name: str):
        """معالجة التعريف المشكل"""
        logger.warning(f"Problematic driver detected: {driver_name}")
        
        # Get driver info
        driver_info = self._get_driver_info(driver_name)
        
        if driver_info:
            # Create rollback plan
            rollback_plan = self._create_rollback_plan(driver_info)
            
            # Publish for user approval
            self.bus.publish(
                'driver.problematic',
                source_module='driver_health_manager',
                payload={
                    'driver_info': driver_info.__dict__,
                    'rollback_plan': rollback_plan.__dict__,
                    'requires_user_approval': True
                }
            )
    
    def _check_driver_health(self):
        """فحص صحة التعريفات"""
        logger.debug("Checking driver health...")
        
        try:
            # Get all drivers
            drivers = self._enumerate_drivers()
            
            for driver in drivers:
                # Assess driver health
                health_assessment = self._assess_driver_health(driver)
                
                # Log assessment
                if health_assessment['status'] != DriverStatus.HEALTHY:
                    self.db.log_event(
                        event_type='driver_health_check',
                        module_name='driver_health_manager',
                        severity='warning',
                        message=f"Driver {driver.device_name}: {health_assessment['status'].value}",
                        details={
                            'driver': driver.__dict__,
                            'assessment': health_assessment
                        }
                    )
                
                # Check for updates if needed
                if health_assessment['status'] == DriverStatus.WARNING:
                    self._check_driver_updates(driver, health_assessment)
            
        except Exception as e:
            logger.error(f"Error checking driver health: {e}")
    
    def _enumerate_drivers(self) -> List[DriverInfo]:
        """تعداد التعريفات"""
        drivers = []
        
        try:
            # Use PowerShell to get driver information
            ps_command = """
            Get-WmiObject Win32_PnPSignedDriver | 
            Where-Object {$_.DeviceName -ne $null} |
            Select-Object DeviceName, DriverName, DriverVersion, DriverDate, DeviceClass, Manufacturer, DeviceID, HardwareID |
            ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                drivers_data = json.loads(result.stdout)
                
                for driver_data in drivers_data:
                    # Parse driver date
                    driver_date = None
                    if driver_data['DriverDate']:
                        try:
                            # Convert WMI date format
                            date_str = driver_data['DriverDate']
                            if len(date_str) >= 8:
                                year = int(date_str[0:4])
                                month = int(date_str[4:6])
                                day = int(date_str[6:8])
                                driver_date = datetime(year, month, day)
                        except:
                            driver_date = None
                    
                    # Determine driver type
                    driver_type = self._determine_driver_type(
                        driver_data['DeviceClass'],
                        driver_data['DeviceName']
                    )
                    
                    # Get crash count
                    crash_count = len(self.crash_history.get(driver_data['DriverName'], []))
                    
                    # Get last crash
                    last_crash = None
                    if crash_count > 0:
                        last_crash = self.crash_history[driver_data['DriverName']][-1]['timestamp']
                    
                    # Create driver info
                    driver = DriverInfo(
                        device_name=driver_data['DeviceName'],
                        driver_name=driver_data['DriverName'],
                        driver_version=driver_data['DriverVersion'] or 'Unknown',
                        driver_date=driver_date,
                        provider=driver_data['Manufacturer'] or 'Unknown',
                        driver_type=driver_type,
                        status=DriverStatus.UNKNOWN,
                        crash_count=crash_count,
                        last_crash=last_crash,
                        device_id=driver_data['DeviceID'] or '',
                        hardware_id=driver_data['HardwareID'] or ''
                    )
                    
                    drivers.append(driver)
        
        except Exception as e:
            logger.error(f"Error enumerating drivers: {e}")
        
        return drivers
    
    def _determine_driver_type(self, device_class: str, device_name: str) -> DriverType:
        """تحديد نوع التعريف"""
        if not device_class:
            device_class = ''
        
        device_class_lower = device_class.lower()
        device_name_lower = device_name.lower()
        
        if 'display' in device_class_lower or 'graphics' in device_name_lower:
            return DriverType.DISPLAY
        elif 'net' in device_class_lower or 'network' in device_name_lower:
            return DriverType.NETWORK
        elif 'media' in device_class_lower or 'audio' in device_name_lower:
            return DriverType.AUDIO
        elif 'disk' in device_class_lower or 'storage' in device_name_lower:
            return DriverType.STORAGE
        elif 'system' in device_class_lower or 'chipset' in device_name_lower:
            return DriverType.CHIPSET
        elif 'usb' in device_class_lower or 'usb' in device_name_lower:
            return DriverType.USB
        else:
            return DriverType.OTHER
    
    def _assess_driver_health(self, driver: DriverInfo) -> Dict:
        """تقييم صحة التعريف"""
        status = DriverStatus.HEALTHY
        issues = []
        
        # Check 1: Crash history
        if driver.crash_count >= 3:
            status = DriverStatus.CRITICAL
            issues.append(f"Multiple crashes ({driver.crash_count})")
        elif driver.crash_count >= 1:
            status = DriverStatus.WARNING
            issues.append(f"Recent crash")
        
        # Check 2: Driver age
        if driver.driver_date:
            age_days = (datetime.now() - driver.driver_date).days
            
            if age_days > 365:  # Older than 1 year
                if status == DriverStatus.HEALTHY:
                    status = DriverStatus.WARNING
                issues.append(f"Outdated ({age_days} days old)")
        
        # Check 3: Generic drivers
        if 'Microsoft Basic' in driver.driver_name:
            if status == DriverStatus.HEALTHY:
                status = DriverStatus.WARNING
            issues.append("Generic Microsoft driver")
        
        # Check 4: Unknown provider
        if driver.provider.lower() in ['unknown', 'standard', 'generic']:
            if status == DriverStatus.HEALTHY:
                status = DriverStatus.WARNING
            issues.append("Unknown/generic provider")
        
        return {
            'status': status,
            'issues': issues,
            'explanation': self._generate_health_explanation(driver, status, issues)
        }
    
    def _generate_health_explanation(self, driver: DriverInfo, status: DriverStatus, issues: List[str]) -> str:
        """توليد تفسير لصحة التعريف"""
        if status == DriverStatus.HEALTHY:
            return f"{driver.device_name}: صحة جيدة"
        elif status == DriverStatus.WARNING:
            return f"{driver.device_name}: تحذير - {', '.join(issues)}"
        elif status == DriverStatus.CRITICAL:
            return f"{driver.device_name}: حرج - {', '.join(issues)}"
        else:
            return f"{driver.device_name}: حالة غير معروفة"
    
    def _check_driver_updates(self, driver: DriverInfo, health_assessment: Dict):
        """التحقق من وجود تحديثات للتعريف"""
        # Skip critical drivers
        if driver.driver_name in self.CRITICAL_DRIVERS:
            return
        
        # Check if driver is outdated
        if driver.driver_date:
            age_days = (datetime.now() - driver.driver_date).days
            
            if age_days > 180:  # Older than 6 months
                # Look for updates
                update_info = self._find_driver_updates(driver)
                
                if update_info:
                    # Create update plan
                    update_plan = self._create_update_plan(driver, update_info, health_assessment)
                    
                    # Publish for user approval
                    self.bus.publish(
                        'driver.update_available',
                        source_module='driver_health_manager',
                        payload={
                            'driver': driver.__dict__,
                            'update_info': update_info,
                            'update_plan': update_plan.__dict__,
                            'requires_user_approval': True
                        }
                    )
    
    def _find_driver_updates(self, driver: DriverInfo) -> Optional[Dict]:
        """البحث عن تحديثات للتعريف"""
        try:
            # Use PowerShell to check for driver updates
            ps_command = f"""
            $device = Get-WmiObject Win32_PnPSignedDriver | 
                Where-Object {{$_.DeviceName -eq "{driver.device_name}"}} |
                Select-Object -First 1
            
            if ($device) {{
                $update = $device | Get-WindowsDriver -Online -ErrorAction SilentlyContinue
                if ($update) {{
                    @{{
                        Available = $true
                        Version = $update.Version
                        Date = $update.Date
                        SizeMB = [math]::Round($update.Size / 1MB, 2)
                    }}
                }} else {{
                    @{{Available = $false}}
                }}
            }} else {{
                @{{Available = $false}}
            }}
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                update_data = json.loads(result.stdout)
                
                if update_data['Available']:
                    return {
                        'version': update_data['Version'],
                        'date': update_data['Date'],
                        'size_mb': update_data['SizeMB']
                    }
        
        except Exception as e:
            logger.error(f"Error finding driver updates: {e}")
        
        return None
    
    def _create_update_plan(self, driver: DriverInfo, update_info: Dict, health_assessment: Dict) -> DriverAction:
        """إنشاء خطة تحديث"""
        # Determine risk level
        if driver.driver_type in [DriverType.DISPLAY, DriverType.CHIPSET]:
            risk_level = "high"
        elif driver.driver_type in [DriverType.NETWORK, DriverType.STORAGE]:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Create action
        action = DriverAction(
            device_name=driver.device_name,
            driver_name=driver.driver_name,
            action_type="update",
            risk_level=risk_level,
            reason=f"Outdated driver ({health_assessment['explanation']})",
            estimated_time_minutes=5,
            download_size_mb=update_info['size_mb']
        )
        
        return action
    
    def _create_rollback_plan(self, driver_info: DriverInfo) -> DriverAction:
        """إنشاء خطة استعادة"""
        action = DriverAction(
            device_name=driver_info.device_name,
            driver_name=driver_info.driver_name,
            action_type="rollback",
            risk_level="medium",
            reason=f"Multiple crashes detected ({driver_info.crash_count} crashes)",
            estimated_time_minutes=3,
            download_size_mb=0.0
        )
        
        return action
    
    def _get_driver_info(self, driver_name: str) -> Optional[DriverInfo]:
        """الحصول على معلومات التعريف"""
        drivers = self._enumerate_drivers()
        
        for driver in drivers:
            if driver.driver_name == driver_name:
                return driver
        
        return None
    
    def handle_driver_crash(self, message):
        """معالجة حدث تعطل التعريف"""
        payload = message.payload
        driver_name = payload['driver_name']
        crash_count = payload['crash_count']
        
        logger.warning(f"Driver crash event: {driver_name} (count: {crash_count})")
        
        # Check if immediate action is needed
        if crash_count >= 5:
            self._emergency_driver_rollback(driver_name)
    
    def _emergency_driver_rollback(self, driver_name: str):
        """استعادة طارئة للتعريف"""
        logger.warning(f"Emergency driver rollback for: {driver_name}")
        
        try:
            # Use PowerShell to rollback driver
            ps_command = f"""
            $device = Get-WmiObject Win32_PnPSignedDriver | 
                Where-Object {{$_.DriverName -eq "{driver_name}"}} |
                Select-Object -First 1
            
            if ($device) {{
                $device | Rollback-Driver -Confirm:$false
                "Rollback initiated"
            }} else {{
                "Driver not found"
            }}
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Emergency rollback initiated for: {driver_name}")
                
                # Log action
                self.db.log_event(
                    event_type='driver_emergency_rollback',
                    module_name='driver_health_manager',
                    severity='warning',
                    message=f"Emergency rollback for {driver_name}",
                    details={
                        'driver_name': driver_name,
                        'success': True,
                        'output': result.stdout
                    }
                )
        
        except Exception as e:
            logger.error(f"Error during emergency rollback: {e}")
    
    def get_driver_health_report(self) -> Dict:
        """الحصول على تقرير صحة التعريفات"""
        drivers = self._enumerate_drivers()
        
        healthy_count = 0
        warning_count = 0
        critical_count = 0
        
        for driver in drivers:
            assessment = self._assess_driver_health(driver)
            if assessment['status'] == DriverStatus.HEALTHY:
                healthy_count += 1
            elif assessment['status'] == DriverStatus.WARNING:
                warning_count += 1
            elif assessment['status'] == DriverStatus.CRITICAL:
                critical_count += 1
        
        return {
            'total_drivers': len(drivers),
            'healthy': healthy_count,
            'warning': warning_count,
            'critical': critical_count,
            'crash_history': self.crash_history
        }


# Global instance
_driver_manager_instance = None

def get_driver_manager() -> DriverHealthManager:
    """الحصول على instance الموديول"""
    global _driver_manager_instance
    if _driver_manager_instance is None:
        _driver_manager_instance = DriverHealthManager()
    return _driver_manager_instance