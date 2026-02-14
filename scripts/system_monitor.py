#!/usr/bin/env python3
"""
KNOUX OS Guardian - مراقب النظام
جمع مقاييس النظام لاستخدامها في نماذج التعلم الآلي
"""

import os
import sys
import time
import json
import psutil
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import colorama
from colorama import Fore, Style

colorama.init()

class SystemMonitor:
    """مراقب النظام لجمع المقاييس"""
    
    def __init__(self, output_dir: str = "data/monitoring"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_history = []
        self.max_history = 1000  # أقصى عدد من القياسات المخزنة
    
    def collect_all_metrics(self) -> Dict:
        """جمع جميع مقاييس النظام"""
        timestamp = datetime.now().isoformat()
        
        metrics = {
            "timestamp": timestamp,
            "system": self._collect_system_info(),
            "cpu": self._collect_cpu_metrics(),
            "memory": self._collect_memory_metrics(),
            "disk": self._collect_disk_metrics(),
            "network": self._collect_network_metrics(),
            "processes": self._collect_process_metrics(),
            "thermal": self._collect_thermal_metrics(),
            "power": self._collect_power_metrics()
        }
        
        # إضافة إلى السجل
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
        
        return metrics
    
    def _collect_system_info(self) -> Dict:
        """جمع معلومات النظام"""
        try:
            return {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor(),
                "hostname": platform.node(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "users": [u.name for u in psutil.users()],
                "python_version": platform.python_version()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _collect_cpu_metrics(self) -> Dict:
        """جمع مقاييس المعالج"""
        try:
            cpu_times = psutil.cpu_times_percent(interval=0.1)
            cpu_freq = psutil.cpu_freq()
            
            return {
                "usage_percent": psutil.cpu_percent(interval=0.1),
                "usage_per_core": psutil.cpu_percent(interval=0.1, percpu=True),
                "user_percent": cpu_times.user,
                "system_percent": cpu_times.system,
                "idle_percent": cpu_times.idle,
                "frequency_mhz": cpu_freq.current if cpu_freq else None,
                "frequency_max_mhz": cpu_freq.max if cpu_freq else None,
                "frequency_min_mhz": cpu_freq.min if cpu_freq else None,
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "load_average": self._get_load_average()
            }
        except Exception as e:
            return {"error": str(e), "usage_percent": 0}
    
    def _collect_memory_metrics(self) -> Dict:
        """جمع مقاييس الذاكرة"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "used_percent": memory.percent,
                "free_gb": round(memory.free / (1024**3), 2),
                "free_percent": 100 - memory.percent,
                "swap_total_gb": round(swap.total / (1024**3), 2),
                "swap_used_gb": round(swap.used / (1024**3), 2),
                "swap_used_percent": swap.percent,
                "swap_free_gb": round(swap.free / (1024**3), 2),
                "cached_gb": round(getattr(memory, 'cached', 0) / (1024**3), 2),
                "buffers_gb": round(getattr(memory, 'buffers', 0) / (1024**3), 2)
            }
        except Exception as e:
            return {"error": str(e), "used_percent": 0}
    
    def _collect_disk_metrics(self) -> Dict:
        """جمع مقاييس التخزين"""
        try:
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "used_percent": usage.percent
                    })
                except:
                    continue
            
            return {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "used_percent": disk_usage.percent,
                "read_bytes": disk_io.read_bytes if disk_io else 0,
                "write_bytes": disk_io.write_bytes if disk_io else 0,
                "read_count": disk_io.read_count if disk_io else 0,
                "write_count": disk_io.write_count if disk_io else 0,
                "read_time_ms": disk_io.read_time if disk_io else 0,
                "write_time_ms": disk_io.write_time if disk_io else 0,
                "partitions": partitions
            }
        except Exception as e:
            return {"error": str(e), "used_percent": 0}
    
    def _collect_network_metrics(self) -> Dict:
        """جمع مقاييس الشبكة"""
        try:
            net_io = psutil.net_io_counters()
            net_connections = psutil.net_connections()
            
            # جمع معلومات الواجهات
            interfaces = []
            for interface, addrs in psutil.net_if_addrs().items():
                stats = psutil.net_if_stats().get(interface, {})
                interfaces.append({
                    "name": interface,
                    "addresses": [addr.address for addr in addrs],
                    "is_up": getattr(stats, 'isup', False),
                    "speed_mbps": getattr(stats, 'speed', 0),
                    "mtu": getattr(stats, 'mtu', 1500)
                })
            
            # تحليل الاتصالات
            connection_types = {}
            for conn in net_connections:
                conn_type = conn.type.name if hasattr(conn.type, 'name') else str(conn.type)
                connection_types[conn_type] = connection_types.get(conn_type, 0) + 1
            
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout,
                "total_connections": len(net_connections),
                "connection_types": connection_types,
                "interfaces": interfaces
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _collect_process_metrics(self) -> Dict:
        """جمع مقاييس العمليات"""
        try:
            processes = []
            total_processes = 0
            total_threads = 0
            total_handles = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    process_info = proc.info
                    processes.append({
                        "pid": process_info['pid'],
                        "name": process_info['name'],
                        "cpu_percent": process_info.get('cpu_percent', 0),
                        "memory_percent": process_info.get('memory_percent', 0)
                    })
                    
                    total_processes += 1
                    
                    # جمع معلومات إضافية للعمليات الرئيسية
                    if process_info.get('cpu_percent', 0) > 1.0 or process_info.get('memory_percent', 0) > 1.0:
                        try:
                            with proc.oneshot():
                                total_threads += proc.num_threads()
                                total_handles += proc.num_handles()
                        except:
                            pass
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # ترتيب العمليات حسب استخدام الموارد
            top_cpu = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:10]
            top_memory = sorted(processes, key=lambda x: x.get('memory_percent', 0), reverse=True)[:10]
            
            return {
                "total_processes": total_processes,
                "total_threads": total_threads,
                "total_handles": total_handles,
                "top_cpu_processes": top_cpu,
                "top_memory_processes": top_memory,
                "sample_count": len(processes)
            }
        except Exception as e:
            return {"error": str(e), "total_processes": 0}
    
    def _collect_thermal_metrics(self) -> Dict:
        """جمع مقاييس الحرارة"""
        try:
            temperatures = []
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                for name, entries in temps.items():
                    for entry in entries:
                        temperatures.append({
                            "sensor": name,
                            "label": entry.label or name,
                            "current_c": entry.current,
                            "high_c": entry.high,
                            "critical_c": entry.critical
                        })
            
            fans = []
            if hasattr(psutil, "sensors_fans"):
                fan_data = psutil.sensors_fans()
                for name, entries in fan_data.items():
                    for entry in entries:
                        fans.append({
                            "sensor": name,
                            "label": entry.label or name,
                            "current_rpm": entry.current
                        })
            
            return {
                "temperatures": temperatures,
                "fans": fans,
                "has_thermal_data": len(temperatures) > 0
            }
        except Exception as e:
            return {"error": str(e), "temperatures": []}
    
    def _collect_power_metrics(self) -> Dict:
        """جمع مقاييس الطاقة"""
        try:
            battery_info = {}
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    battery_info = {
                        "percent": battery.percent,
                        "secsleft": battery.secsleft,
                        "power_plugged": battery.power_plugged,
                        "is_charging": battery.power_plugged and battery.percent < 100
                    }
            
            return {
                "battery": battery_info,
                "has_battery": bool(battery_info)
            }
        except Exception as e:
            return {"error": str(e), "battery": {}}
    
    def _get_load_average(self) -> Optional[List[float]]:
        """الحصول على متوسط الحمل (لأنظمة Unix)"""
        try:
            if hasattr(os, 'getloadavg'):
                return list(os.getloadavg())
        except:
            pass
        return None
    
    def save_metrics(self, metrics: Dict, filename: Optional[str] = None):
        """حفظ المقاييس في ملف"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.json"
        
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def monitor_continuously(self, interval_seconds: int = 60, duration_minutes: int = 5):
        """مراقبة مستمرة للنظام"""
        print(f"{Fore.CYAN}🔍 بدء المراقبة المستمرة{Style.RESET_ALL}")
        print(f"⏱️  الفاصل: {interval_seconds} ثانية")
        print(f"⏳ المدة: {duration_minutes} دقيقة")
        print(f"📁 الحفظ في: {self.output_dir}")
        print()
        
        end_time = time.time() + (duration_minutes * 60)
        iteration = 0
        
        try:
            while time.time() < end_time:
                iteration += 1
                print(f"{Fore.BLUE}🌀 التكرار {iteration}{Style.RESET_ALL}")
                
                # جمع المقاييس
                metrics = self.collect_all_metrics()
                
                # عرض ملخص
                self._print_summary(metrics)
                
                # حفظ المقاييس
                filename = f"monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                saved_path = self.save_metrics(metrics, filename)
                print(f"💾 تم الحفظ: {saved_path.name}")
                
                print(f"{Fore.YELLOW}⏳ الانتظار {interval_seconds} ثانية...{Style.RESET_ALL}")
                print("-" * 60)
                
                # الانتظار للفاصل التالي
                if time.time() + interval_seconds < end_time:
                    time.sleep(interval_seconds)
                else:
                    break
                    
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⏹️  تم إيقاف المراقبة{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}❌ خطأ في المراقبة: {e}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}✅ اكتملت المراقبة{Style.RESET_ALL}")
        print(f"📊 عدد القياسات: {len(self.metrics_history)}")
        
        # حفظ السجل الكامل
        if self.metrics_history:
            history_file = self.output_dir / f"monitor_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics_history, f, indent=2, ensure_ascii=False)
            print(f"📚 تم حفظ السجل: {history_file.name}")
    
    def _print_summary(self, metrics: Dict):
        """طباعة ملخص المقاييس"""
        cpu = metrics.get("cpu", {})
        memory = metrics.get("memory", {})
        disk = metrics.get("disk", {})
        
        print(f"⏰ الوقت: {metrics.get('timestamp', 'غير معروف')}")
        print(f"💻 المعالج: {cpu.get('usage_percent', 0):.1f}%")
        print(f"🧠 الذاكرة: {memory.get('used_percent', 0):.1f}% ({memory.get('used_gb', 0):.1f} GB)")
        print(f"💾 التخزين: {disk.get('used_percent', 0):.1f}% ({disk.get('used_gb', 0):.1f} GB)")
        
        # عرض العمليات الأعلى استخدامًا
        processes = metrics.get("processes", {})
        top_cpu = processes.get("top_cpu_processes", [])[:3]
        if top_cpu:
            print(f"🔥 أعلى عمليات المعالج:")
            for proc in top_cpu:
                print(f"  • {proc.get('name', 'غير معروف')}: {proc.get('cpu_percent', 0):.1f}%")
        
        # عرض الحرارة إذا كانت متاحة
        thermal = metrics.get("thermal", {})
        temps = thermal.get("temperatures", [])
        if temps:
            hottest = max(temps, key=lambda x: x.get('current_c', 0))
            print(f"🌡️  أعلى حرارة: {hottest.get('label', 'غير معروف')} - {hottest.get('current_c', 0):.1f}°C")

def main():
    """الدالة الرئيسية"""
    import argparse
    
    parser = argparse.ArgumentParser(description="مراقب النظام - KNOUX OS Guardian")
    parser.add_argument("action", choices=["single", "monitor", "summary"],
                       help="الإجراء المطلوب")
    parser.add_argument("--interval", type=int, default=60,
                       help="فاصل المراقبة بالثواني")
    parser.add_argument("--duration", type=int, default=5,
                       help="مدة المراقبة بالدقائق")
    parser.add_argument("--output", default="data/monitoring",
                       help="مجلد الحفظ")
    
    args = parser.parse_args()
    
    monitor = SystemMonitor(args.output)
    
    if args.action == "single":
        print(f"{Fore.CYAN}📊 جمع قياس واحد{Style.RESET_ALL}")
        metrics = monitor.collect_all_metrics()
        
        # حفظ القياس
        filename = f"single_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        saved_path = monitor.save_metrics(metrics, filename)
        
        print(f"✅ تم جمع القياسات")
        print(f"💾 تم الحفظ في: {saved_path}")
        
        # عرض ملخص
        monitor._print_summary(metrics)
    
    elif args.action == "monitor":
        monitor.monitor_continuously(args.interval, args.duration)
    
    elif args.action == "summary":
        print(f"{Fore.CYAN}📈 ملخص النظام الحالي{Style.RESET_ALL}")
        metrics = monitor.collect_all_metrics()
        monitor._print_summary(metrics)
    
    else:
        print(f"{Fore.RED}❌ إجراء غير معروف{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⏹️  تم إلغاء العملية{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}❌ خطأ غير متوقع: {e}{Style.RESET_ALL}")
        sys.exit(1)