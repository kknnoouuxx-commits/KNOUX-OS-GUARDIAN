"""
Thermal Intelligence Controller
تحكم ذكي في حرارة النظام لمنع التلف الحراري
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
from src.core.database import get_database
from src.core.config import get_config

logger = logging.getLogger(__name__)


class ThermalStatus(Enum):
    """حالة الحرارة"""
    NORMAL = "normal"
    WARM = "warm"
    HOT = "hot"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """نوع المكون"""
    CPU = "cpu"
    GPU = "gpu"
    MOTHERBOARD = "motherboard"
    STORAGE = "storage"
    PSU = "psu"
    OTHER = "other"


@dataclass
class TemperatureReading:
    """قراءة درجة الحرارة"""
    component: ComponentType
    sensor_name: str
    temperature_celsius: float
    max_safe_temp: float
    status: ThermalStatus
    timestamp: datetime


@dataclass
class CoolingAction:
    """إجراء تبريد"""
    action_type: str  # throttle, fan_boost, shutdown, alert
    component: ComponentType
    target_temperature: float
    intensity: float  # 0.0-1.0
    estimated_effect_minutes: int
    power_impact_watts: float


class ThermalController:
    """
    متحكم الحرارة الذكي
    Thermal Intelligence Controller
    """
    
    def __init__(self):
        self.bus = get_bus()
        self.db = get_database()
        self.config = get_config()
        self.running = False
        self.monitor_thread = None
        
        # Temperature history
        self.temperature_history = {}
        
        # Emergency thresholds
        self.emergency_threshold = self.config.get('modules.thermal_controller.emergency_throttle_temp_celsius', 90)
        
        # Component-specific thresholds
        self.THRESHOLDS = {
            ComponentType.CPU: {
                'normal': 60,
                'warm': 70,
                'hot': 80,
                'critical': 90
            },
            ComponentType.GPU: {
                'normal': 65,
                'warm': 75,
                'hot': 85,
                'critical': 95
            },
            ComponentType.MOTHERBOARD: {
                'normal': 50,
                'warm': 60,
                'hot': 70,
                'critical': 80
            },
            ComponentType.STORAGE: {
                'normal': 45,
                'warm': 55,
                'hot': 65,
                'critical': 70
            },
            ComponentType.OTHER: {
                'normal': 55,
                'warm': 65,
                'hot': 75,
                'critical': 85
            }
        }
        
        logger.info("Thermal Controller initialized")
    
    def start(self):
        """بدء المراقبة"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitor_thread.start()
            
            logger.info("Thermal Controller started")
    
    def stop(self):
        """إيقاف المراقبة"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Thermal Controller stopped")
    
    def _monitoring_loop(self):
        """حلقة المراقبة الرئيسية"""
        monitor_interval = self.config.get('modules.thermal_controller.monitor_interval_seconds', 5)
        monitor_interval = max(2, int(monitor_interval))
        
        while self.running:
            try:
                # Collect temperature readings
                readings = self._collect_temperature_readings()
                
                # Analyze thermal state
                thermal_state = self._analyze_thermal_state(readings)
                
                # Take action if needed
                self._handle_thermal_state(thermal_state, readings)
                
                # Log thermal state
                self._log_thermal_state(thermal_state, readings)
                
                # Wait for next monitoring cycle
                time.sleep(monitor_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Wait 10 seconds on error
    
    def _collect_temperature_readings(self) -> List[TemperatureReading]:
        """جمع قراءات درجة الحرارة"""
        readings = []
        
        try:
            # Try to use OpenHardwareMonitor via WMI
            readings.extend(self._get_temperatures_via_wmi())
            
            # Fallback to basic system info
            if not readings:
                readings.extend(self._get_basic_temperatures())
            
        except Exception as e:
            logger.error(f"Error collecting temperature readings: {e}")
        
        return readings
    
    def _get_temperatures_via_wmi(self) -> List[TemperatureReading]:
        """الحصول على درجات الحرارة عبر WMI"""
        readings = []
        
        try:
            # Use PowerShell to query WMI for temperatures
            ps_command = """
            $temps = @()
            
            # Try to get CPU temperature
            try {
                $cpu = Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace "root/wmi" -ErrorAction SilentlyContinue
                if ($cpu) {
                    foreach ($zone in $cpu) {
                        $tempC = ($zone.CurrentTemperature / 10) - 273.15
                        $temps += @{
                            Component = "CPU"
                            Sensor = "CPU Zone $($zone.InstanceName)"
                            Temperature = [math]::Round($tempC, 1)
                        }
                    }
                }
            } catch {}
            
            # Try to get other temperatures via Win32_TemperatureProbe
            try {
                $probes = Get-WmiObject Win32_TemperatureProbe -ErrorAction SilentlyContinue
                if ($probes) {
                    foreach ($probe in $probes) {
                        $tempC = $probe.CurrentReading / 10
                        $temps += @{
                            Component = "Other"
                            Sensor = $probe.Name
                            Temperature = [math]::Round($tempC, 1)
                        }
                    }
                }
            } catch {}
            
            $temps | ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                temps_data = json.loads(result.stdout)
                
                for temp_data in temps_data:
                    # Determine component type
                    component_type = self._determine_component_type(temp_data['Component'], temp_data['Sensor'])
                    
                    # Get thresholds for this component
                    thresholds = self.THRESHOLDS.get(component_type, self.THRESHOLDS[ComponentType.OTHER])
                    
                    # Determine status
                    status = self._determine_thermal_status(temp_data['Temperature'], thresholds)
                    
                    # Create reading
                    reading = TemperatureReading(
                        component=component_type,
                        sensor_name=temp_data['Sensor'],
                        temperature_celsius=temp_data['Temperature'],
                        max_safe_temp=thresholds['critical'],
                        status=status,
                        timestamp=datetime.now()
                    )
                    
                    readings.append(reading)
        
        except Exception as e:
            logger.debug(f"WMI temperature query failed: {e}")
        
        return readings
    
    def _get_basic_temperatures(self) -> List[TemperatureReading]:
        """الحصول على درجات حرارة أساسية"""
        readings = []
        
        try:
            import psutil
            
            # Get CPU usage as proxy for temperature (very rough estimate)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Estimate CPU temperature based on usage
            # This is a very rough approximation
            base_temp = 40.0  # Base temperature at idle
            load_factor = cpu_percent / 100.0
            estimated_cpu_temp = base_temp + (load_factor * 30.0)  # +30C at full load
            
            # Create CPU reading
            cpu_reading = TemperatureReading(
                component=ComponentType.CPU,
                sensor_name="CPU (Estimated)",
                temperature_celsius=estimated_cpu_temp,
                max_safe_temp=self.THRESHOLDS[ComponentType.CPU]['critical'],
                status=self._determine_thermal_status(
                    estimated_cpu_temp,
                    self.THRESHOLDS[ComponentType.CPU]
                ),
                timestamp=datetime.now()
            )
            
            readings.append(cpu_reading)
            
            # Get disk temperature (if available)
            try:
                import wmi

                c = wmi.WMI()
                for disk in c.Win32_DiskDrive():
                    if hasattr(disk, 'Temperature') and disk.Temperature:
                        disk_temp = float(disk.Temperature)
                        
                        disk_reading = TemperatureReading(
                            component=ComponentType.STORAGE,
                            sensor_name=f"Disk {disk.Caption}",
                            temperature_celsius=disk_temp,
                            max_safe_temp=self.THRESHOLDS[ComponentType.STORAGE]['critical'],
                            status=self._determine_thermal_status(
                                disk_temp,
                                self.THRESHOLDS[ComponentType.STORAGE]
                            ),
                            timestamp=datetime.now()
                        )
                        
                        readings.append(disk_reading)
            except Exception as e:
                logger.debug(f"Disk temperature query failed: {e}")
            
        except Exception as e:
            logger.error(f"Error getting basic temperatures: {e}")
        
        return readings

    def _determine_component_type(self, component_name: str, sensor_name: str) -> ComponentType:
        """تحديد نوع المكون"""
        name_lower = (component_name or '').lower()
        sensor_lower = (sensor_name or '').lower()
        
        if 'cpu' in name_lower or 'cpu' in sensor_lower:
            return ComponentType.CPU
        elif 'gpu' in name_lower or 'gpu' in sensor_lower or 'graphics' in sensor_lower:
            return ComponentType.GPU
        elif 'motherboard' in name_lower or 'system' in sensor_lower or 'pch' in sensor_lower:
            return ComponentType.MOTHERBOARD
        elif 'disk' in name_lower or 'hdd' in sensor_lower or 'ssd' in sensor_lower:
            return ComponentType.STORAGE
        elif 'psu' in name_lower or 'power' in sensor_lower:
            return ComponentType.PSU
        else:
            return ComponentType.OTHER
    
    def _determine_thermal_status(self, temperature: float, thresholds: Dict) -> ThermalStatus:
        """تحديد حالة الحرارة"""
        if temperature >= thresholds['critical']:
            return ThermalStatus.CRITICAL
        elif temperature >= thresholds['hot']:
            return ThermalStatus.HOT
        elif temperature >= thresholds['warm']:
            return ThermalStatus.WARM
        elif temperature >= 0:
            return ThermalStatus.NORMAL
        else:
            return ThermalStatus.UNKNOWN
    
    def _analyze_thermal_state(self, readings: List[TemperatureReading]) -> Dict:
        """تحليل حالة الحرارة"""
        if not readings:
            return {'overall_status': ThermalStatus.UNKNOWN, 'hotspots': []}
        
        # Find hottest component
        hottest_reading = max(readings, key=lambda r: r.temperature_celsius)
        
        # Count components by status
        status_counts = {}
        for status in ThermalStatus:
            status_counts[status.value] = sum(1 for r in readings if r.status == status)
        
        # Identify hotspots (components above warm threshold)
        hotspots = []
        for reading in readings:
            if reading.status in [ThermalStatus.HOT, ThermalStatus.CRITICAL]:
                hotspots.append({
                    'component': reading.component.value,
                    'sensor': reading.sensor_name,
                    'temperature': reading.temperature_celsius,
                    'status': reading.status.value
                })
        
        # Calculate overall status (worst component)
        overall_status = hottest_reading.status
        
        return {
            'overall_status': overall_status,
            'hottest_component': {
                'type': hottest_reading.component.value,
                'sensor': hottest_reading.sensor_name,
                'temperature': hottest_reading.temperature_celsius,
                'status': hottest_reading.status.value
            },
            'status_counts': status_counts,
            'hotspots': hotspots,
            'average_temperature': sum(r.temperature_celsius for r in readings) / len(readings),
            'readings_count': len(readings)
        }
    
    def _handle_thermal_state(self, thermal_state: Dict, readings: List[TemperatureReading]):
        """معالجة حالة الحرارة"""
        overall_status = thermal_state['overall_status']
        
        if overall_status == ThermalStatus.CRITICAL:
            # Emergency action required
            self._handle_critical_temperature(thermal_state, readings)
            
        elif overall_status == ThermalStatus.HOT:
            # Aggressive cooling needed
            self._handle_hot_temperature(thermal_state, readings)
            
        elif overall_status == ThermalStatus.WARM:
            # Moderate cooling
            self._handle_warm_temperature(thermal_state, readings)
    
    def _handle_critical_temperature(self, thermal_state: Dict, readings: List[TemperatureReading]):
        """معالجة درجة حرارة حرجة"""
        hottest = thermal_state['hottest_component']
        
        logger.critical(f"CRITICAL temperature detected: {hottest['type']} at {hottest['temperature']}°C")
        
        # Emergency actions
        actions = []
        
        # Action 1: Immediate CPU throttling
        cpu_readings = [r for r in readings if r.component == ComponentType.CPU]
        if cpu_readings:
            action = CoolingAction(
                action_type="throttle",
                component=ComponentType.CPU,
                target_temperature=self.THRESHOLDS[ComponentType.CPU]['hot'] - 5,
                intensity=1.0,  # Maximum throttling
                estimated_effect_minutes=2,
                power_impact_watts=-30.0  # Power reduction
            )
            actions.append(action)
        
        # Action 2: Maximum fan speed
        action = CoolingAction(
            action_type="fan_boost",
            component=ComponentType.OTHER,
            target_temperature=hottest['temperature'] - 10,
            intensity=1.0,
            estimated_effect_minutes=5,
            power_impact_watts=5.0  # Fans use power
        )
        actions.append(action)
        
        # Action 3: System shutdown warning
        if hottest['temperature'] >= self.emergency_threshold + 5:
            component_type = self._determine_component_type(hottest.get('type', ''), hottest.get('sensor', ''))
            action = CoolingAction(
                action_type="shutdown_warning",
                component=component_type,
                target_temperature=self.emergency_threshold,
                intensity=1.0,
                estimated_effect_minutes=1,
                power_impact_watts=0.0
            )
            actions.append(action)
        
        # Execute actions
        for action in actions:
            self._execute_cooling_action(action)
        
        # Publish critical event
        self.bus.publish(
            'thermal.critical',
            source_module='thermal_controller',
            payload={
                'thermal_state': thermal_state,
                'actions_taken': [a.__dict__ for a in actions],
                'requires_immediate_attention': True
            }
        )
    
    def _handle_hot_temperature(self, thermal_state: Dict, readings: List[TemperatureReading]):
        """معالجة درجة حرارة مرتفعة"""
        hottest = thermal_state['hottest_component']
        
        logger.warning(f"Hot temperature detected: {hottest['type']} at {hottest['temperature']}°C")
        
        # Moderate cooling actions
        actions = []
        
        # Action 1: Moderate CPU throttling
        cpu_readings = [r for r in readings if r.component == ComponentType.CPU]
        if cpu_readings:
            action = CoolingAction(
                action_type="throttle",
                component=ComponentType.CPU,
                target_temperature=self.THRESHOLDS[ComponentType.CPU]['warm'],
                intensity=0.5,  # Moderate throttling
                estimated_effect_minutes=3,
                power_impact_watts=-15.0
            )
            actions.append(action)
        
        # Action 2: Increased fan speed
        action = CoolingAction(
            action_type="fan_boost",
            component=ComponentType.OTHER,
            target_temperature=hottest['temperature'] - 5,
            intensity=0.7,
            estimated_effect_minutes=5,
            power_impact_watts=3.0
        )
        actions.append(action)
        
        # Execute actions
        for action in actions:
            self._execute_cooling_action(action)
        
        # Publish warning event
        self.bus.publish(
            'thermal.hot',
            source_module='thermal_controller',
            payload={
                'thermal_state': thermal_state,
                'actions_taken': [a.__dict__ for a in actions],
                'requires_user_attention': True
            }
        )
    
    def _handle_warm_temperature(self, thermal_state: Dict, readings: List[TemperatureReading]):
        """معالجة درجة حرارة دافئة"""
        # Mild cooling actions
        actions = []
        
        # Action 1: Mild fan adjustment
        action = CoolingAction(
            action_type="fan_adjust",
            component=ComponentType.OTHER,
            target_temperature=thermal_state['average_temperature'] - 3,
            intensity=0.3,
            estimated_effect_minutes=5,
            power_impact_watts=1.0
        )
        actions.append(action)
        
        # Execute actions
        for action in actions:
            self._execute_cooling_action(action)
        
        # Log only, no user notification
        logger.info(f"Warm temperature: {thermal_state['average_temperature']:.1f}°C")
    
    def _execute_cooling_action(self, action: CoolingAction):
        """تنفيذ إجراء تبريد"""
        try:
            if action.action_type == "throttle":
                self._throttle_cpu(action.intensity)
                
            elif action.action_type in ["fan_boost", "fan_adjust"]:
                self._adjust_fan_speed(action.intensity)
                
            elif action.action_type == "shutdown_warning":
                self._issue_shutdown_warning(action.component)
            
            # Log action
            self.db.log_event(
                event_type='thermal_action',
                module_name='thermal_controller',
                severity='warning' if action.intensity > 0.5 else 'info',
                message=f"Thermal action: {action.action_type} for {action.component}",
                details=action.__dict__
            )
            
        except Exception as e:
            logger.error(f"Error executing cooling action: {e}")
    
    def _throttle_cpu(self, intensity: float):
        """تقليل سرعة المعالج"""
        try:
            intensity = max(0.0, min(1.0, float(intensity)))
            max_proc = int(round((1.0 - intensity) * 100))
            max_proc = max(5, min(100, max_proc))
            
            # Use PowerShell to adjust power plan
            # This is a simplified implementation
            ps_command = f"""
            # Adjust processor performance
            powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX {max_proc}
            powercfg -setactive SCHEME_CURRENT
            """
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            logger.info(f"CPU throttled to {intensity * 100:.0f}% intensity")
            
        except Exception as e:
            logger.error(f"Error throttling CPU: {e}")
    
    def _adjust_fan_speed(self, intensity: float):
        """ضبط سرعة المروحة"""
        try:
            intensity = max(0.0, min(1.0, float(intensity)))

            # Use Windows power policy as a real, hardware-agnostic cooling control.
            # SYSTEMCOOLINGPOLICY: 0=Active, 1=Passive
            cooling_policy = 0 if intensity >= 0.5 else 1
            max_proc = 100 if intensity < 0.5 else int(round(85 - (intensity * 25)))
            max_proc = max(30, min(100, max_proc))

            ps_command = f"""
            powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR SYSTEMCOOLINGPOLICY {cooling_policy}
            powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX {max_proc}
            powercfg -setactive SCHEME_CURRENT
            """

            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )

            logger.info(f"Cooling policy applied (policy={cooling_policy}, max_proc={max_proc})")
            
        except Exception as e:
            logger.error(f"Error adjusting fan speed: {e}")
    
    def _issue_shutdown_warning(self, component):
        """إصدار تحذير إيقاف التشغيل"""
        # Create system notification
        component_name = component.value if hasattr(component, 'value') else str(component)
        notification = {
            'title': '⚠️ Critical Temperature Warning',
            'message': f'{component_name} temperature is critically high. System may shut down to prevent damage.',
            'urgency': 'critical',
            'actions': ['acknowledge', 'override']
        }
        
        # Publish notification
        self.bus.publish(
            'system.notification',
            source_module='thermal_controller',
            payload=notification
        )
    
    def _log_thermal_state(self, thermal_state: Dict, readings: List[TemperatureReading]):
        """تسجيل حالة الحرارة"""
        # Store in history
        timestamp = datetime.now()
        self.temperature_history[timestamp] = {
            'state': thermal_state,
            'readings': [r.__dict__ for r in readings]
        }
        
        # Keep only last 1000 entries
        if len(self.temperature_history) > 1000:
            oldest = min(self.temperature_history.keys())
            del self.temperature_history[oldest]
        
        # Log to database if status is not normal
        if thermal_state['overall_status'] != ThermalStatus.NORMAL:
            self.db.log_event(
                event_type='thermal_state',
                module_name='thermal_controller',
                severity='warning' if thermal_state['overall_status'] == ThermalStatus.CRITICAL else 'info',
                message=f"Thermal state: {thermal_state['overall_status'].value}",
                details=thermal_state
            )
    
    def get_thermal_report(self, hours_back: int = 1) -> Dict:
        """الحصول على تقرير حراري"""
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Filter history
        relevant_history = {}
        for timestamp, data in self.temperature_history.items():
            if start_time <= timestamp <= end_time:
                relevant_history[timestamp] = data
        
        # Calculate statistics
        if relevant_history:
            all_temps = []
            for data in relevant_history.values():
                for reading in data['readings']:
                    all_temps.append(reading['temperature_celsius'])
            
            stats = {
                'min_temperature': min(all_temps),
                'max_temperature': max(all_temps),
                'avg_temperature': sum(all_temps) / len(all_temps),
                'readings_count': len(all_temps)
            }
        else:
            stats = {}
        
        return {
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'history_entries': len(relevant_history),
            'statistics': stats,
            'current_state': self._analyze_thermal_state(self._collect_temperature_readings()) if self.running else {}
        }
    
    def get_temperature_trend(self, component: ComponentType = None) -> List[Dict]:
        """الحصول على اتجاه درجة الحرارة"""
        trends = []
        
        # Get recent history
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=30)
        
        for timestamp, data in sorted(self.temperature_history.items()):
            if start_time <= timestamp <= end_time:
                if component:
                    # Filter by component
                    component_readings = [r for r in data['readings'] if r['component'] == component.value]
                    if component_readings:
                        avg_temp = sum(r['temperature_celsius'] for r in component_readings) / len(component_readings)
                        trends.append({
                            'timestamp': timestamp.isoformat(),
                            'temperature': avg_temp,
                            'component': component.value
                        })
                else:
                    # Overall average
                    avg_temp = sum(r['temperature_celsius'] for r in data['readings']) / len(data['readings'])
                    trends.append({
                        'timestamp': timestamp.isoformat(),
                        'temperature': avg_temp,
                        'component': 'overall'
                    })
        
        return trends


# Global instance
_thermal_controller_instance = None

def get_thermal_controller() -> ThermalController:
    """الحصول على instance الموديول"""
    global _thermal_controller_instance
    if _thermal_controller_instance is None:
        _thermal_controller_instance = ThermalController()
    return _thermal_controller_instance
