"""
Power Efficiency Manager
إدارة ذكية لاستهلاك الطاقة وكفاءة البطارية
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


class PowerSource(Enum):
    """مصدر الطاقة"""
    BATTERY = "battery"
    AC = "ac"
    UNKNOWN = "unknown"


class PowerMode(Enum):
    """وضع الطاقة"""
    MAX_PERFORMANCE = "max_performance"
    BALANCED = "balanced"
    POWER_SAVER = "power_saver"
    ULTRA_SAVER = "ultra_saver"


@dataclass
class PowerStatus:
    """حالة الطاقة"""
    power_source: PowerSource
    battery_percent: float
    battery_time_remaining_minutes: int
    is_charging: bool
    discharge_rate_watts: float
    estimated_total_runtime_minutes: int
    power_mode: PowerMode


@dataclass
class PowerAction:
    """إجراء طاقة"""
    action_type: str  # mode_change, brightness, sleep, hibernate
    target_value: str
    estimated_power_saving_watts: float
    estimated_battery_gain_minutes: int
    performance_impact: float  # 0.0-1.0


class PowerManager:
    """
    مدير الطاقة الذكي
    Power Efficiency Manager
    """
    
    def __init__(self):
        self.bus = get_bus()
        self.db = get_database()
        self.config = get_config()
        self.running = False
        self.monitor_thread = None
        
        # Power history
        self.power_history = []
        
        # Current power mode
        self.current_mode = PowerMode.BALANCED
        
        # Configuration
        self.smart_charging = self.config.get('modules.power_manager.smart_charging', False)
        self.auto_brightness = self.config.get('modules.power_manager.auto_brightness', False)
        
        logger.info("Power Manager initialized")
    
    def start(self):
        """بدء المراقبة"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitor_thread.start()
            
            logger.info("Power Manager started")
    
    def stop(self):
        """إيقاف المراقبة"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Power Manager stopped")
    
    def _monitoring_loop(self):
        """حلقة المراقبة الرئيسية"""
        while self.running:
            try:
                # Get current power status
                power_status = self._get_power_status()
                
                # Analyze power efficiency
                efficiency_analysis = self._analyze_power_efficiency(power_status)
                
                # Take optimization actions
                self._optimize_power_usage(power_status, efficiency_analysis)
                
                # Log power status
                self._log_power_status(power_status, efficiency_analysis)
                
                # Wait for next monitoring cycle
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Wait 30 seconds on error
    
    def _get_power_status(self) -> PowerStatus:
        """الحصول على حالة الطاقة"""
        try:
            import psutil
            
            # Get battery info
            battery = psutil.sensors_battery()
            
            if battery:
                # Determine power source
                if battery.power_plugged:
                    power_source = PowerSource.AC
                    is_charging = battery.percent < 100
                else:
                    power_source = PowerSource.BATTERY
                    is_charging = False
                
                # Calculate discharge rate (estimated)
                discharge_rate = self._estimate_discharge_rate(battery)
                
                # Calculate estimated runtime
                runtime_minutes = self._estimate_runtime(battery, discharge_rate)
                
                # Get current power mode
                power_mode = self._get_current_power_mode()
                
                status = PowerStatus(
                    power_source=power_source,
                    battery_percent=battery.percent,
                    battery_time_remaining_minutes=int(battery.secsleft / 60) if battery.secsleft > 0 else 0,
                    is_charging=is_charging,
                    discharge_rate_watts=discharge_rate,
                    estimated_total_runtime_minutes=runtime_minutes,
                    power_mode=power_mode
                )
                
                return status
            
            else:
                # No battery detected (desktop)
                return PowerStatus(
                    power_source=PowerSource.AC,
                    battery_percent=100.0,
                    battery_time_remaining_minutes=0,
                    is_charging=False,
                    discharge_rate_watts=0.0,
                    estimated_total_runtime_minutes=0,
                    power_mode=PowerMode.MAX_PERFORMANCE
                )
                
        except Exception as e:
            logger.error(f"Error getting power status: {e}")
            
            # Return default status
            return PowerStatus(
                power_source=PowerSource.UNKNOWN,
                battery_percent=0.0,
                battery_time_remaining_minutes=0,
                is_charging=False,
                discharge_rate_watts=0.0,
                estimated_total_runtime_minutes=0,
                power_mode=PowerMode.BALANCED
            )
    
    def _estimate_discharge_rate(self, battery) -> float:
        """تقدير معدل التفريغ"""
        # This is a simplified estimation
        # In a real implementation, you would track power usage over time
        
        if battery.power_plugged:
            return 0.0  # Not discharging when plugged in
        
        # Base discharge rate based on system load
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Estimated power consumption (watts)
        base_power = 10.0  # Base system power
        cpu_power = cpu_percent * 0.3  # CPU power based on usage
        gpu_power = 5.0  # Estimated GPU power (if active)
        
        total_power = base_power + cpu_power + gpu_power
        
        return total_power
    
    def _estimate_runtime(self, battery, discharge_rate: float) -> int:
        """تقدير وقت التشغيل المتبقي"""
        if battery.power_plugged or discharge_rate <= 0:
            return 0  # Not running on battery or not discharging
        
        # Calculate runtime based on battery percentage and discharge rate
        # This is a simplified calculation
        battery_capacity_wh = 50.0  # Typical laptop battery capacity (Wh)
        remaining_energy_wh = (battery.percent / 100.0) * battery_capacity_wh
        
        if discharge_rate > 0:
            runtime_hours = remaining_energy_wh / discharge_rate
            return int(runtime_hours * 60)  # Convert to minutes
        else:
            return 0
    
    def _get_current_power_mode(self) -> PowerMode:
        """الحصول على وضع الطاقة الحالي"""
        try:
            # Use PowerShell to get current power plan
            ps_command = """
            powercfg /getactivescheme
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                if 'High performance' in output:
                    return PowerMode.MAX_PERFORMANCE
                elif 'Power saver' in output:
                    return PowerMode.POWER_SAVER
                elif 'Balanced' in output:
                    return PowerMode.BALANCED
                else:
                    return PowerMode.BALANCED
        
        except Exception as e:
            logger.error(f"Error getting power mode: {e}")
        
        return PowerMode.BALANCED
    
    def _analyze_power_efficiency(self, power_status: PowerStatus) -> Dict:
        """تحليل كفاءة الطاقة"""
        efficiency_score = 100.0
        issues = []
        recommendations = []
        
        # Check 1: Power mode appropriateness
        if power_status.power_source == PowerSource.BATTERY:
            if power_status.power_mode == PowerMode.MAX_PERFORMANCE:
                efficiency_score -= 30
                issues.append("Max performance mode on battery")
                recommendations.append("Switch to Balanced or Power Saver mode")
            
            elif power_status.battery_percent < 20 and power_status.power_mode != PowerMode.POWER_SAVER:
                efficiency_score -= 20
                issues.append("Low battery but not in Power Saver mode")
                recommendations.append("Switch to Power Saver mode")
        
        # Check 2: Charging optimization
        if power_status.power_source == PowerSource.AC and self.smart_charging:
            if power_status.battery_percent >= 80 and power_status.is_charging:
                efficiency_score -= 10
                issues.append("Battery above 80% but still charging")
                recommendations.append("Consider unplugging to preserve battery health")
        
        # Check 3: Display brightness
        if self.auto_brightness and power_status.power_source == PowerSource.BATTERY:
            current_brightness = self._get_display_brightness()
            if current_brightness > 70:
                efficiency_score -= 15
                issues.append("High display brightness on battery")
                recommendations.append("Reduce display brightness")
        
        # Check 4: Background processes
        background_power = self._check_background_power_usage()
        if background_power > 10:  # More than 10W from background
            efficiency_score -= 25
            issues.append(f"High background power usage ({background_power:.1f}W)")
            recommendations.append("Review and limit background applications")
        
        return {
            'efficiency_score': max(0.0, min(100.0, efficiency_score)),
            'issues': issues,
            'recommendations': recommendations,
            'background_power_watts': background_power
        }
    
    def _get_display_brightness(self) -> float:
        """الحصول على سطوع الشاشة"""
        try:
            # Use PowerShell to get brightness
            ps_command = """
            (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return float(result.stdout.strip())
        
        except Exception as e:
            logger.debug(f"Error getting display brightness: {e}")
        
        return 50.0  # Default
    
    def _check_background_power_usage(self) -> float:
        """التحقق من استهلاك الطاقة في الخلفية"""
        try:
            import psutil
            
            total_power = 0.0
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    info = proc.info
                    
                    # Skip system processes
                    if info['name'].lower() in ['system', 'svchost.exe', 'csrss.exe']:
                        continue
                    
                    # Estimate power based on CPU usage
                    cpu_usage = info['cpu_percent'] or 0.0
                    estimated_power = cpu_usage * 0.1  # Rough estimate
                    
                    total_power += estimated_power
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return total_power
            
        except Exception as e:
            logger.error(f"Error checking background power: {e}")
            return 0.0
    
    def _optimize_power_usage(self, power_status: PowerStatus, efficiency_analysis: Dict):
        """تحسين استخدام الطاقة"""
        # Only optimize if on battery
        if power_status.power_source != PowerSource.BATTERY:
            return
        
        # Check if optimization is needed
        if efficiency_analysis['efficiency_score'] < 70:
            logger.info(f"Low power efficiency: {efficiency_analysis['efficiency_score']:.1f}")
            
            # Create optimization plan
            optimization_plan = self._create_optimization_plan(power_status, efficiency_analysis)
            
            # Execute optimizations
            for action in optimization_plan:
                self._execute_power_action(action)
            
            # Publish optimization event
            self.bus.publish(
                'power.optimized',
                source_module='power_manager',
                payload={
                    'power_status': power_status.__dict__,
                    'efficiency_analysis': efficiency_analysis,
                    'optimization_plan': [a.__dict__ for a in optimization_plan]
                }
            )
    
    def _create_optimization_plan(self, power_status: PowerStatus, efficiency_analysis: Dict) -> List[PowerAction]:
        """إنشاء خطة تحسين الطاقة"""
        actions = []
        
        # Action 1: Adjust power mode
        if power_status.battery_percent < 30:
            # Switch to Power Saver
            action = PowerAction(
                action_type="mode_change",
                target_value="power_saver",
                estimated_power_saving_watts=15.0,
                estimated_battery_gain_minutes=45,
                performance_impact=0.3
            )
            actions.append(action)
        
        elif 'Max performance mode on battery' in efficiency_analysis['issues']:
            # Switch to Balanced
            action = PowerAction(
                action_type="mode_change",
                target_value="balanced",
                estimated_power_saving_watts=10.0,
                estimated_battery_gain_minutes=30,
                performance_impact=0.1
            )
            actions.append(action)
        
        # Action 2: Adjust display brightness
        if 'High display brightness on battery' in efficiency_analysis['issues']:
            action = PowerAction(
                action_type="brightness",
                target_value="50%",
                estimated_power_saving_watts=5.0,
                estimated_battery_gain_minutes=20,
                performance_impact=0.0
            )
            actions.append(action)
        
        # Action 3: Limit background processes
        if efficiency_analysis['background_power_watts'] > 10:
            action = PowerAction(
                action_type="background_limit",
                target_value="reduce",
                estimated_power_saving_watts=efficiency_analysis['background_power_watts'] * 0.5,
                estimated_battery_gain_minutes=30,
                performance_impact=0.1
            )
            actions.append(action)
        
        return actions
    
    def _execute_power_action(self, action: PowerAction):
        """تنفيذ إجراء طاقة"""
        try:
            if action.action_type == "mode_change":
                self._set_power_mode(action.target_value)
                
            elif action.action_type == "brightness":
                self._set_display_brightness(50)  # Set to 50%
                
            elif action.action_type == "background_limit":
                self._limit_background_processes()
            
            # Log action
            self.db.log_event(
                event_type='power_action',
                module_name='power_manager',
                severity='info',
                message=f"Power action: {action.action_type} -> {action.target_value}",
                details=action.__dict__
            )
            
            logger.info(f"Executed power action: {action.action_type}")
            
        except Exception as e:
            logger.error(f"Error executing power action: {e}")
    
    def _set_power_mode(self, mode: str):
        """تعيين وضع الطاقة"""
        try:
            # Map mode to power plan GUID
            mode_guids = {
                'max_performance': '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
                'balanced': '381b4222-f694-41f0-9685-ff5bb260df2e',
                'power_saver': 'a1841308-3541-4fab-bc81-f71556f20b4a'
            }
            
            guid = mode_guids.get(mode, mode_guids['balanced'])
            
            # Set power plan
            ps_command = f"powercfg /setactive {guid}"
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Update current mode
            if mode == 'max_performance':
                self.current_mode = PowerMode.MAX_PERFORMANCE
            elif mode == 'power_saver':
                self.current_mode = PowerMode.POWER_SAVER
            else:
                self.current_mode = PowerMode.BALANCED
            
        except Exception as e:
            logger.error(f"Error setting power mode: {e}")
    
    def _set_display_brightness(self, brightness: int):
        """تعيين سطوع الشاشة"""
        try:
            # Use PowerShell to set brightness
            ps_command = f"""
            (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {brightness})
            """
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=5
            )
            
        except Exception as e:
            logger.error(f"Error setting display brightness: {e}")
    
    def _limit_background_processes(self):
        """تقييد العمليات في الخلفية"""
        try:
            import psutil
            
            # Identify high-power background processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    info = proc.info
                    
                    # Skip critical processes
                    if info['name'].lower() in ['system', 'svchost.exe', 'csrss.exe', 'wininit.exe']:
                        continue
                    
                    # Check if process is using significant CPU
                    cpu_usage = info['cpu_percent'] or 0.0
                    if cpu_usage > 5.0:  # Using more than 5% CPU
                        # Lower process priority
                        proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                        logger.debug(f"Lowered priority for {info['name']} (PID {info['pid']})")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
        except Exception as e:
            logger.error(f"Error limiting background processes: {e}")
    
    def _log_power_status(self, power_status: PowerStatus, efficiency_analysis: Dict):
        """تسجيل حالة الطاقة"""
        # Store in history
        self.power_history.append({
            'timestamp': datetime.now(),
            'status': power_status.__dict__,
            'efficiency': efficiency_analysis
        })
        
        # Keep only last 1000 entries
        if len(self.power_history) > 1000:
            self.power_history = self.power_history[-1000:]
        
        # Log to database periodically
        current_minute = datetime.now().minute
        if current_minute % 15 == 0:  # Log every 15 minutes
            self.db.log_event(
                event_type='power_status',
                module_name='power_manager',
                severity='info',
                message=f"Power: {power_status.battery_percent:.0f}% ({power_status.power_source.value})",
                details={
                    'power_status': power_status.__dict__,
                    'efficiency_score': efficiency_analysis['efficiency_score']
                }
            )
    
    def get_power_report(self, hours_back: int = 24) -> Dict:
        """الحصول على تقرير الطاقة"""
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Filter history
        relevant_history = [entry for entry in self.power_history 
                          if start_time <= entry['timestamp'] <= end_time]
        
        # Calculate statistics
        if relevant_history:
            battery_levels = [entry['status']['battery_percent'] for entry in relevant_history]
            efficiency_scores = [entry['efficiency']['efficiency_score'] for entry in relevant_history]
            
            stats = {
                'min_battery': min(battery_levels),
                'max_battery': max(battery_levels),
                'avg_efficiency': sum(efficiency_scores) / len(efficiency_scores),
                'entries_count': len(relevant_history)
            }
        else:
            stats = {}
        
        # Get current status
        current_status = self._get_power_status()
        current_efficiency = self._analyze_power_efficiency(current_status)
        
        return {
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'statistics': stats,
            'current_status': current_status.__dict__,
            'current_efficiency': current_efficiency,
            'recommendations': current_efficiency.get('recommendations', [])
        }
    
    def enable_smart_charging(self, enable: bool = True):
        """تفعيل/تعطيل الشحن الذكي"""
        self.smart_charging = enable
        logger.info(f"Smart charging {'enabled' if enable else 'disabled'}")
    
    def enable_auto_brightness(self, enable: bool = True):
        """تفعيل/تعطيل السطوع التلقائي"""
        self.auto_brightness = enable
        logger.info(f"Auto brightness {'enabled' if enable else 'disabled'}")
    
    def get_battery_health(self) -> Dict:
        """الحصول على صحة البطارية"""
        try:
            # Use PowerShell to get battery health info
            ps_command = """
            $battery = Get-WmiObject Win32_Battery
            @{
                DesignCapacity = $battery.DesignCapacity
                FullChargeCapacity = $battery.FullChargeCapacity
                BatteryStatus = $battery.BatteryStatus
                HealthPercent = if ($battery.DesignCapacity -gt 0) { 
                    [math]::Round(($battery.FullChargeCapacity / $battery.DesignCapacity) * 100, 1) 
                } else { 0 }
            } | ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                health_data = json.loads(result.stdout)
                return health_data
        
        except Exception as e:
            logger.error(f"Error getting battery health: {e}")
        
        return {
            'DesignCapacity': 0,
            'FullChargeCapacity': 0,
            'BatteryStatus': 0,
            'HealthPercent': 0
        }


# Global instance
_power_manager_instance = None

def get_power_manager() -> PowerManager:
    """الحصول على instance الموديول"""
    global _power_manager_instance
    if _power_manager_instance is None:
        _power_manager_instance = PowerManager()
    return _power_manager_instance