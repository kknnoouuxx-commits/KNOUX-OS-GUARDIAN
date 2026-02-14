"""
Adaptive Performance Optimizer
تحسين أداء النظام تلقائياً من خلال تحليل أنماط الاستخدام
"""

import logging
import threading
import time
import psutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import deque
from enum import Enum

from src.core.communication_bus import get_bus
from src.core.database import get_database
from src.core.config import get_config

logger = logging.getLogger(__name__)


class ProcessPriority(Enum):
    """أولوية العملية"""
    IDLE = "idle"
    BELOW_NORMAL = "below_normal"
    NORMAL = "normal"
    ABOVE_NORMAL = "above_normal"
    HIGH = "high"
    REALTIME = "realtime"


@dataclass
class ProcessSnapshot:
    """لقطة للعملية"""
    pid: int
    name: str
    executable_path: str
    cpu_percent: float
    memory_mb: float
    io_bytes_per_sec: float
    thread_count: int
    handle_count: int
    priority_class: int
    is_foreground: bool
    parent_pid: int
    start_time: datetime


@dataclass
class SystemSnapshot:
    """لقطة للنظام"""
    timestamp: datetime
    cpu_usage_percent: float
    ram_total_mb: float
    ram_available_mb: float
    disk_queue_length: float
    network_throughput_mbps: float
    process_count: int
    thread_count: int
    handle_count: int
    temperature_celsius: float


class PerformanceOptimizer:
    """
    محسن الأداء التكيفي
    Adaptive Performance Optimizer
    """
    
    def __init__(self):
        self.bus = get_bus()
        self.db = get_database()
        self.config = get_config()
        self.running = False
        self.monitor_thread = None
        
        # Process monitoring
        self.process_snapshots = {}
        self.system_snapshots = deque(maxlen=720)  # 6 hours at 30-sec intervals
        
        # User activity tracking
        self.user_activity = deque(maxlen=1000)
        
        # Critical processes (never optimize)
        self.CRITICAL_PROCESSES = [
            'System', 'Registry', 'smss.exe', 'csrss.exe', 'wininit.exe',
            'services.exe', 'lsass.exe', 'winlogon.exe', 'explorer.exe',
            'dwm.exe'  # Desktop Window Manager
        ]
        
        logger.info("Performance Optimizer initialized")
    
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
            self.bus.subscribe('system.high_cpu', self.handle_high_cpu)
            self.bus.subscribe('system.low_memory', self.handle_low_memory)
            self.bus.subscribe('user.activity', self.handle_user_activity)
            
            logger.info("Performance Optimizer started")
    
    def stop(self):
        """إيقاف المراقبة"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance Optimizer stopped")
    
    def _monitoring_loop(self):
        """حلقة المراقبة الرئيسية"""
        monitor_interval = self.config.get('modules.performance_optimizer.monitor_interval_seconds', 30)
        monitor_interval = max(5, int(monitor_interval))
        
        while self.running:
            try:
                # Collect system snapshot
                system_snapshot = self._collect_system_snapshot()
                self.system_snapshots.append(system_snapshot)
                
                # Collect process snapshots
                process_snapshots = self._collect_process_snapshots()
                for snapshot in process_snapshots:
                    if snapshot.pid not in self.process_snapshots:
                        self.process_snapshots[snapshot.pid] = deque(maxlen=120)  # 1 hour history
                    self.process_snapshots[snapshot.pid].append(snapshot)
                
                # Detect resource pressure
                self._detect_resource_pressure(system_snapshot)
                
                # Optimize if needed
                auto_optimize = self.config.get('modules.performance_optimizer.auto_optimize', False)
                if auto_optimize:
                    self._optimize_processes(process_snapshots, system_snapshot)
                
                # Log system state
                self._log_system_state(system_snapshot, len(process_snapshots))
                
                # Wait for next monitoring cycle
                time.sleep(monitor_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _collect_system_snapshot(self) -> SystemSnapshot:
        """جمع لقطة للنظام"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory
        memory = psutil.virtual_memory()
        
        # Disk
        disk_io = psutil.disk_io_counters()
        disk_queue = 0.0  # Would need WMI for accurate disk queue
        
        # Network
        net_io = psutil.net_io_counters()
        network_mbps = (net_io.bytes_sent + net_io.bytes_recv) / (1024**2) / 60  # MB per minute
        
        # Temperature (would need hardware monitoring)
        temperature = 0.0
        
        snapshot = SystemSnapshot(
            timestamp=datetime.now(),
            cpu_usage_percent=cpu_percent,
            ram_total_mb=memory.total / (1024**2),
            ram_available_mb=memory.available / (1024**2),
            disk_queue_length=disk_queue,
            network_throughput_mbps=network_mbps,
            process_count=len(psutil.pids()),
            thread_count=sum(p.num_threads() for p in psutil.process_iter(['pid'])),
            handle_count=self._get_system_handle_count(),
            temperature_celsius=temperature
        )
        
        return snapshot
    
    def _collect_process_snapshots(self) -> List[ProcessSnapshot]:
        """جمع لقطات للعمليات"""
        snapshots = []
        
        # Get foreground process (Windows-specific)
        foreground_pid = self._get_foreground_process_id()
        
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_info', 
                                         'num_threads', 'create_time', 'ppid']):
            try:
                info = proc.info
                
                # Skip if missing critical info
                if not info['pid'] or not info['name']:
                    continue
                
                # Check if process is critical
                if self._is_process_critical(info['name']):
                    continue
                
                # Get process details
                memory_mb = info['memory_info'].rss / (1024**2) if info['memory_info'] else 0
                
                snapshot = ProcessSnapshot(
                    pid=info['pid'],
                    name=info['name'],
                    executable_path=info['exe'] or '',
                    cpu_percent=info['cpu_percent'] or 0.0,
                    memory_mb=memory_mb,
                    io_bytes_per_sec=self._get_process_io_rate(info['pid']),
                    thread_count=info['num_threads'],
                    handle_count=self._get_process_handle_count(info['pid']),
                    priority_class=self._get_process_priority(info['pid']),
                    is_foreground=(info['pid'] == foreground_pid),
                    parent_pid=info['ppid'],
                    start_time=datetime.fromtimestamp(info['create_time'])
                )
                
                snapshots.append(snapshot)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return snapshots
    
    def _get_foreground_process_id(self) -> Optional[int]:
        """الحصول على معرف العملية الأمامية"""
        try:
            import ctypes
            from ctypes import wintypes
            
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            pid = wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            
            return pid.value
        except:
            return None
    
    def _get_process_io_rate(self, pid: int) -> float:
        """الحصول على معدل I/O للعملية"""
        try:
            proc = psutil.Process(pid)
            io_counters = proc.io_counters()
            return io_counters.read_bytes + io_counters.write_bytes
        except:
            return 0.0
    
    def _get_process_handle_count(self, pid: int) -> int:
        """الحصول على عدد المقابض للعملية"""
        try:
            proc = psutil.Process(pid)
            return proc.num_handles()
        except:
            return 0
    
    def _get_process_priority(self, pid: int) -> int:
        """الحصول على أولوية العملية"""
        try:
            proc = psutil.Process(pid)
            return proc.nice()
        except:
            return psutil.NORMAL_PRIORITY_CLASS
    
    def _get_system_handle_count(self) -> int:
        """الحصول على عدد مقابض النظام"""
        try:
            total = 0
            for proc in psutil.process_iter(['pid']):
                try:
                    total += proc.num_handles()
                except:
                    continue
            return total
        except:
            return 0
    
    def _is_process_critical(self, process_name: str) -> bool:
        """التحقق إذا كانت العملية حرجة"""
        return process_name.lower() in [p.lower() for p in self.CRITICAL_PROCESSES]
    
    def _detect_resource_pressure(self, snapshot: SystemSnapshot):
        """كشف ضغط الموارد"""
        # CPU pressure
        if snapshot.cpu_usage_percent > 80:
            self.bus.publish(
                'system.high_cpu',
                source_module='performance_optimizer',
                payload={
                    'cpu_percent': snapshot.cpu_usage_percent,
                    'threshold': 80
                }
            )
        
        # Memory pressure
        if snapshot.ram_available_mb < 1024:  # Less than 1GB available
            self.bus.publish(
                'system.low_memory',
                source_module='performance_optimizer',
                payload={
                    'available_mb': snapshot.ram_available_mb,
                    'threshold': 1024
                }
            )
        
        # Thermal pressure
        if snapshot.temperature_celsius > 80:
            self.bus.publish(
                'system.high_temperature',
                source_module='performance_optimizer',
                payload={
                    'temperature': snapshot.temperature_celsius,
                    'threshold': 80
                }
            )
    
    def _optimize_processes(self, process_snapshots: List[ProcessSnapshot], 
                           system_snapshot: SystemSnapshot):
        """تحسين العمليات"""
        # Sort processes by CPU usage (descending)
        sorted_processes = sorted(
            [p for p in process_snapshots if not p.is_foreground and not self._is_process_critical(p.name)],
            key=lambda p: p.cpu_percent,
            reverse=True
        )
        
        # Optimize top CPU consumers
        for process in sorted_processes[:5]:  # Top 5
            if process.cpu_percent > 10:  # Using >10% CPU
                self._optimize_process(process, system_snapshot)
    
    def _optimize_process(self, process: ProcessSnapshot, system_snapshot: SystemSnapshot):
        """تحسين عملية معينة"""
        # Calculate optimal priority
        optimal_priority = self._calculate_optimal_priority(process, system_snapshot)
        
        # Get current priority
        current_priority = process.priority_class
        
        # Apply optimization if different
        if optimal_priority != current_priority:
            try:
                self._set_process_priority(process.pid, optimal_priority)
                
                logger.info(f"Optimized process {process.name} (PID {process.pid}): "
                           f"Priority {current_priority} -> {optimal_priority}")
                
                # Log optimization
                self.db.log_event(
                    event_type='process_optimized',
                    module_name='performance_optimizer',
                    severity='info',
                    message=f"Optimized {process.name} priority",
                    details={
                        'pid': process.pid,
                        'process_name': process.name,
                        'old_priority': current_priority,
                        'new_priority': optimal_priority,
                        'cpu_percent': process.cpu_percent,
                        'memory_mb': process.memory_mb
                    }
                )
                
            except Exception as e:
                logger.error(f"Error optimizing process {process.name}: {e}")
    
    def _calculate_optimal_priority(self, process: ProcessSnapshot, 
                                   system_snapshot: SystemSnapshot) -> int:
        """حساب الأولوية المثلى للعملية"""
        import psutil
        
        # Base priority
        priority_score = 50
        
        # Factor 1: Is process in foreground? (50% weight)
        if process.is_foreground:
            priority_score += 25
        elif process.cpu_percent > 5:
            priority_score += 10
        else:
            priority_score -= 20
        
        # Factor 2: System resource pressure (30% weight)
        if system_snapshot.cpu_usage_percent > 80:
            # CPU congestion - lower background priority
            if not process.is_foreground:
                priority_score -= 15
        
        if system_snapshot.ram_available_mb < 1024:
            # RAM pressure - aggressively lower idle processes
            if process.memory_mb > 200 and not process.is_foreground:
                priority_score -= 20
        
        # Factor 3: Process behavior (20% weight)
        if process.cpu_percent > 20:
            priority_score -= 10  # CPU hog
        
        if process.memory_mb > 500:
            priority_score -= 5  # Memory hog
        
        # Map score to Windows priority class
        if priority_score < 20:
            return psutil.IDLE_PRIORITY_CLASS
        elif priority_score < 40:
            return psutil.BELOW_NORMAL_PRIORITY_CLASS
        elif priority_score < 60:
            return psutil.NORMAL_PRIORITY_CLASS
        elif priority_score < 80:
            return psutil.ABOVE_NORMAL_PRIORITY_CLASS
        else:
            return psutil.HIGH_PRIORITY_CLASS
    
    def _set_process_priority(self, pid: int, priority: int):
        """تعيين أولوية العملية"""
        try:
            proc = psutil.Process(pid)
            proc.nice(priority)
        except Exception as e:
            raise Exception(f"Failed to set priority: {e}")
    
    def _log_system_state(self, snapshot: SystemSnapshot, process_count: int):
        """تسجيل حالة النظام"""
        self.db.log_event(
            event_type='system_performance_snapshot',
            module_name='performance_optimizer',
            severity='info',
            message=f"System performance: CPU {snapshot.cpu_usage_percent:.1f}%, "
                   f"RAM {snapshot.ram_available_mb:.0f}MB free",
            details={
                'cpu_percent': snapshot.cpu_usage_percent,
                'ram_available_mb': snapshot.ram_available_mb,
                'process_count': process_count,
                'thread_count': snapshot.thread_count,
                'temperature': snapshot.temperature_celsius
            }
        )
    
    def handle_high_cpu(self, message):
        """معالجة حدث ارتفاع استخدام CPU"""
        payload = message.payload
        cpu_percent = payload['cpu_percent']
        
        logger.warning(f"High CPU usage detected: {cpu_percent:.1f}%")
        
        # Take emergency actions
        self._emergency_cpu_optimization()
    
    def handle_low_memory(self, message):
        """معالجة حدث انخفاض الذاكرة"""
        payload = message.payload
        available_mb = payload['available_mb']
        
        logger.warning(f"Low memory detected: {available_mb:.0f}MB available")
        
        # Take emergency actions
        self._emergency_memory_optimization()
    
    def handle_user_activity(self, message):
        """معالجة حدث نشاط المستخدم"""
        payload = message.payload
        activity_type = payload.get('type', 'unknown')
        
        # Track user activity
        self.user_activity.append({
            'timestamp': datetime.now(),
            'type': activity_type
        })
    
    def _emergency_cpu_optimization(self):
        """تحسين طارئ لـ CPU"""
        logger.info("Performing emergency CPU optimization")
        
        # Get current process snapshots
        process_snapshots = self._collect_process_snapshots()
        
        # Sort by CPU usage
        cpu_hogs = sorted(
            [p for p in process_snapshots if not p.is_foreground and not self._is_process_critical(p.name)],
            key=lambda p: p.cpu_percent,
            reverse=True
        )
        
        # Throttle top CPU hogs
        for process in cpu_hogs[:3]:  # Top 3
            if process.cpu_percent > 5:
                try:
                    self._set_process_priority(process.pid, psutil.IDLE_PRIORITY_CLASS)
                    logger.info(f"Emergency throttled {process.name} (PID {process.pid})")
                except Exception as e:
                    logger.debug(f"Emergency CPU throttle failed for PID {process.pid}: {e}")
    
    def _emergency_memory_optimization(self):
        """تحسين طارئ للذاكرة"""
        logger.info("Performing emergency memory optimization")
        
        # Get current process snapshots
        process_snapshots = self._collect_process_snapshots()
        
        # Sort by memory usage
        memory_hogs = sorted(
            [p for p in process_snapshots if not p.is_foreground and not self._is_process_critical(p.name)],
            key=lambda p: p.memory_mb,
            reverse=True
        )
        
        # Trim working set of top memory hogs
        for process in memory_hogs[:3]:  # Top 3
            if process.memory_mb > 200:
                try:
                    self._trim_process_working_set(process.pid)
                    logger.info(f"Emergency trimmed {process.name} working set")
                except Exception as e:
                    logger.debug(f"Emergency memory trim failed for PID {process.pid}: {e}")
    
    def _trim_process_working_set(self, pid: int):
        """تقليص working set للعملية"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Open process
            PROCESS_SET_QUOTA = 0x0100
            PROCESS_QUERY_INFORMATION = 0x0400
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION,
                False,
                pid
            )
            
            if handle:
                # Empty working set
                ctypes.windll.psapi.EmptyWorkingSet(handle)
                ctypes.windll.kernel32.CloseHandle(handle)
                
        except Exception as e:
            logger.error(f"Error trimming working set: {e}")


# Global instance
_performance_optimizer_instance = None

def get_performance_optimizer() -> PerformanceOptimizer:
    """الحصول على instance الموديول"""
    global _performance_optimizer_instance
    if _performance_optimizer_instance is None:
        _performance_optimizer_instance = PerformanceOptimizer()
    return _performance_optimizer_instance
