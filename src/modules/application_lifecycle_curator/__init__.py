"""
Application Lifecycle Curator
إدارة ذكية لدورة حياة التطبيقات وتنظيف التطبيقات المهجورة
"""

import logging
import threading
import time
import subprocess
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.communication_bus import get_bus
from src.core.safe_execution import safe_execute
from src.core.database import get_database
from src.core.config import get_config

logger = logging.getLogger(__name__)


class AppCategory(Enum):
    """فئة التطبيق"""
    PRODUCTIVITY = "productivity"
    DEVELOPMENT = "development"
    MEDIA = "media"
    GAME = "game"
    UTILITY = "utility"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class AppStatus(Enum):
    """حالة التطبيق"""
    ACTIVE = "active"
    IDLE = "idle"
    ABANDONED = "abandoned"
    PROBLEMATIC = "problematic"
    UNKNOWN = "unknown"


@dataclass
class ApplicationInfo:
    """معلومات التطبيق"""
    name: str
    display_name: str
    version: str
    publisher: str
    install_date: datetime
    install_size_mb: float
    last_used: Optional[datetime]
    usage_count: int
    total_usage_hours: float
    category: AppCategory
    status: AppStatus
    executable_path: str
    uninstall_string: str


@dataclass
class AppAction:
    """إجراء على التطبيق"""
    app_name: str
    action_type: str  # uninstall, update, repair, disable
    reason: str
    impact: str
    estimated_time_minutes: int
    requires_user_approval: bool


class ApplicationCurator:
    """
    منسق دورة حياة التطبيقات
    Application Lifecycle Curator
    """
    
    def __init__(self):
        self.bus = get_bus()
        self.db = get_database()
        self.config = get_config()
        self.running = False
        self.curator_thread = None
        
        # Application usage tracking
        self.usage_tracking = {}
        
        # Critical applications (never suggest uninstall)
        self.CRITICAL_APPS = [
            'Microsoft Windows',
            'Microsoft .NET Framework',
            'Microsoft Visual C++',
            'Microsoft Edge',
            'Windows Defender',
            'Windows Security'
        ]
        
        # System components (never touch)
        self.SYSTEM_COMPONENTS = [
            'Microsoft Windows',
            'Windows',
            'Driver',
            'Update',
            'Security',
            'Framework'
        ]
        
        logger.info("Application Curator initialized")
    
    def start(self):
        """بدء الإدارة"""
        if not self.running:
            self.running = True
            self.curator_thread = threading.Thread(
                target=self._curation_loop,
                daemon=True
            )
            self.curator_thread.start()
            
            # Subscribe to events
            self.bus.subscribe('application.launched', self.handle_app_launch)
            self.bus.subscribe('application.closed', self.handle_app_close)
            
            logger.info("Application Curator started")
    
    def stop(self):
        """إيقاف الإدارة"""
        self.running = False
        if self.curator_thread:
            self.curator_thread.join(timeout=5)
        logger.info("Application Curator stopped")
    
    def _curation_loop(self):
        """حلقة الإدارة الرئيسية"""
        track_usage = self.config.get('modules.application_curator.track_usage', True)
        
        while self.running:
            try:
                if track_usage:
                    # Update application usage tracking
                    self._update_usage_tracking()
                
                # Analyze installed applications
                self._analyze_applications()
                
                # Wait for next curation cycle
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in curation loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _update_usage_tracking(self):
        """تحديث تتبع استخدام التطبيقات"""
        logger.debug("Updating application usage tracking...")
        
        try:
            # Get currently running applications
            running_apps = self._get_running_applications()
            
            # Update usage tracking
            current_time = datetime.now()
            
            for app_name in running_apps:
                if app_name not in self.usage_tracking:
                    self.usage_tracking[app_name] = {
                        'first_seen': current_time,
                        'last_seen': current_time,
                        'total_sessions': 1,
                        'total_hours': 0.0,
                        'current_session_start': current_time
                    }
                else:
                    # Update existing app
                    tracking = self.usage_tracking[app_name]
                    tracking['last_seen'] = current_time
                    
                    # Check if this is a new session
                    time_since_last_seen = (current_time - tracking['last_seen']).total_seconds()
                    if time_since_last_seen > 300:  # 5 minutes gap = new session
                        tracking['total_sessions'] += 1
                        tracking['current_session_start'] = current_time
            
            # Calculate session durations for apps that are no longer running
            all_tracked_apps = list(self.usage_tracking.keys())
            for app_name in all_tracked_apps:
                if app_name not in running_apps:
                    tracking = self.usage_tracking[app_name]
                    
                    # Check if app was running in previous cycle
                    if 'current_session_start' in tracking:
                        session_duration = (current_time - tracking['current_session_start']).total_seconds()
                        tracking['total_hours'] += session_duration / 3600
                        tracking.pop('current_session_start', None)
        
        except Exception as e:
            logger.error(f"Error updating usage tracking: {e}")
    
    def _get_running_applications(self) -> List[str]:
        """الحصول على التطبيقات قيد التشغيل"""
        running_apps = []
        
        try:
            import psutil
            
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    info = proc.info
                    
                    # Skip system processes
                    if info['name'].lower() in ['system', 'svchost.exe', 'csrss.exe', 'wininit.exe']:
                        continue
                    
                    # Get application name from executable path
                    if info['exe']:
                        app_name = Path(info['exe']).stem
                        running_apps.append(app_name)
                    else:
                        running_apps.append(info['name'])
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        except Exception as e:
            logger.error(f"Error getting running applications: {e}")
        
        return running_apps
    
    def _analyze_applications(self):
        """تحليل التطبيقات المثبتة"""
        logger.debug("Analyzing installed applications...")
        
        try:
            # Get all installed applications
            installed_apps = self._get_installed_applications()
            
            # Analyze each application
            for app in installed_apps:
                # Update app status based on usage
                self._update_app_status(app)
                
                # Check for problematic apps
                if app.status == AppStatus.PROBLEMATIC:
                    self._handle_problematic_app(app)
                
                # Check for abandoned apps
                elif app.status == AppStatus.ABANDONED:
                    self._handle_abandoned_app(app)
            
            # Generate application report
            self._generate_app_report(installed_apps)
            
        except Exception as e:
            logger.error(f"Error analyzing applications: {e}")
    
    def _get_installed_applications(self) -> List[ApplicationInfo]:
        """الحصول على التطبيقات المثبتة"""
        apps = []
        
        try:
            # Use PowerShell to get installed applications
            ps_command = """
            $apps = @()
            
            # Get from Uninstall registry keys
            $paths = @(
                "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*",
                "HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*",
                "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*"
            )
            
            foreach ($path in $paths) {
                $items = Get-ItemProperty $path -ErrorAction SilentlyContinue
                foreach ($item in $items) {
                    if ($item.DisplayName -and $item.DisplayName -notmatch "^Update for|^Security Update") {
                        $app = @{
                            Name = $item.PSChildName
                            DisplayName = $item.DisplayName
                            Version = $item.DisplayVersion
                            Publisher = $item.Publisher
                            InstallDate = $item.InstallDate
                            InstallLocation = $item.InstallLocation
                            UninstallString = $item.UninstallString
                            EstimatedSizeMB = if ($item.EstimatedSize) { [math]::Round($item.EstimatedSize / 1024, 2) } else { 0 }
                        }
                        $apps += $app
                    }
                }
            }
            
            $apps | ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                apps_data = json.loads(result.stdout)
                
                for app_data in apps_data:
                    # Parse install date
                    install_date = None
                    if app_data['InstallDate']:
                        try:
                            # Format: YYYYMMDD
                            date_str = app_data['InstallDate']
                            if len(date_str) == 8:
                                year = int(date_str[0:4])
                                month = int(date_str[4:6])
                                day = int(date_str[6:8])
                                install_date = datetime(year, month, day)
                        except:
                            install_date = None
                    
                    # Get usage info
                    usage_info = self.usage_tracking.get(app_data['DisplayName'], {})
                    
                    # Determine category
                    category = self._determine_app_category(
                        app_data['DisplayName'],
                        app_data['Publisher'],
                        app_data['InstallLocation']
                    )
                    
                    # Determine status
                    status = self._determine_app_status(
                        app_data['DisplayName'],
                        install_date,
                        usage_info
                    )
                    
                    # Create application info
                    app = ApplicationInfo(
                        name=app_data['Name'],
                        display_name=app_data['DisplayName'],
                        version=app_data['Version'] or 'Unknown',
                        publisher=app_data['Publisher'] or 'Unknown',
                        install_date=install_date or datetime.now(),
                        install_size_mb=app_data['EstimatedSizeMB'],
                        last_used=usage_info.get('last_seen'),
                        usage_count=usage_info.get('total_sessions', 0),
                        total_usage_hours=usage_info.get('total_hours', 0.0),
                        category=category,
                        status=status,
                        executable_path=app_data['InstallLocation'] or '',
                        uninstall_string=app_data['UninstallString'] or ''
                    )
                    
                    apps.append(app)
        
        except Exception as e:
            logger.error(f"Error getting installed applications: {e}")
        
        return apps
    
    def _determine_app_category(self, display_name: str, publisher: str, install_location: str) -> AppCategory:
        """تحديد فئة التطبيق"""
        name_lower = display_name.lower()
        publisher_lower = (publisher or '').lower()
        location_lower = (install_location or '').lower()
        
        # Productivity
        if any(keyword in name_lower for keyword in ['office', 'word', 'excel', 'powerpoint', 'outlook', 'onenote']):
            return AppCategory.PRODUCTIVITY
        
        # Development
        elif any(keyword in name_lower for keyword in ['visual studio', 'pycharm', 'intellij', 'eclipse', 'vscode', 'git', 'python', 'node.js']):
            return AppCategory.DEVELOPMENT
        
        # Media
        elif any(keyword in name_lower for keyword in ['media', 'video', 'audio', 'photo', 'image', 'player', 'vlc', 'spotify']):
            return AppCategory.MEDIA
        
        # Games
        elif any(keyword in name_lower for keyword in ['game', 'steam', 'epic', 'ubisoft', 'ea', 'battle.net']):
            return AppCategory.GAME
        
        # System
        elif any(keyword in name_lower for keyword in ['microsoft', 'windows', 'driver', 'update', 'security', 'framework']):
            return AppCategory.SYSTEM
        
        # Utilities
        elif any(keyword in name_lower for keyword in ['utility', 'tool', 'manager', 'cleaner', 'optimizer', 'zip', 'rar']):
            return AppCategory.UTILITY
        
        else:
            return AppCategory.UNKNOWN
    
    def _determine_app_status(self, display_name: str, install_date: datetime, usage_info: Dict) -> AppStatus:
        """تحديد حالة التطبيق"""
        # Check if critical app
        for critical_app in self.CRITICAL_APPS:
            if critical_app.lower() in display_name.lower():
                return AppStatus.ACTIVE
        
        # Check if system component
        for system_component in self.SYSTEM_COMPONENTS:
            if system_component.lower() in display_name.lower():
                return AppStatus.ACTIVE
        
        # Check usage
        if usage_info:
            last_used = usage_info.get('last_seen')
            total_sessions = usage_info.get('total_sessions', 0)
            
            if last_used:
                days_since_last_use = (datetime.now() - last_used).days
                
                if days_since_last_use > 90:  # Not used in 3 months
                    return AppStatus.ABANDONED
                elif days_since_last_use > 30:  # Not used in 1 month
                    return AppStatus.IDLE
                elif total_sessions == 0:  # Never used
                    return AppStatus.ABANDONED
                else:
                    return AppStatus.ACTIVE
        
        # Check install age
        if install_date:
            days_since_install = (datetime.now() - install_date).days
            
            if days_since_install > 180 and not usage_info:  # 6 months old, never used
                return AppStatus.ABANDONED
        
        return AppStatus.UNKNOWN
    
    def _update_app_status(self, app: ApplicationInfo):
        """تحديث حالة التطبيق"""
        # Update status based on current analysis
        new_status = self._determine_app_status(
            app.display_name,
            app.install_date,
            self.usage_tracking.get(app.display_name, {})
        )
        
        if app.status != new_status:
            app.status = new_status
            
            # Log status change
            self.db.log_event(
                event_type='app_status_change',
                module_name='application_curator',
                severity='info',
                message=f"App status changed: {app.display_name} -> {new_status.value}",
                details={
                    'app': app.__dict__,
                    'old_status': app.status.value,
                    'new_status': new_status.value
                }
            )
    
    def _handle_problematic_app(self, app: ApplicationInfo):
        """معالجة التطبيق المشكل"""
        logger.warning(f"Problematic app detected: {app.display_name}")
        
        # Check for common issues
        issues = self._identify_app_issues(app)
        
        if issues:
            # Create repair action
            action = AppAction(
                app_name=app.display_name,
                action_type="repair",
                reason=f"Detected issues: {', '.join(issues)}",
                impact="Will attempt to repair application installation",
                estimated_time_minutes=5,
                requires_user_approval=True
            )
            
            # Publish for user approval
            self.bus.publish(
                'app.problematic',
                source_module='application_curator',
                payload={
                    'app': app.__dict__,
                    'issues': issues,
                    'action': action.__dict__,
                    'requires_user_approval': True
                }
            )
    
    def _handle_abandoned_app(self, app: ApplicationInfo):
        """معالجة التطبيق المهجور"""
        logger.info(f"Abandoned app detected: {app.display_name}")
        
        # Check if we should suggest uninstall
        suggest_uninstall = self.config.get('modules.application_curator.suggest_uninstall_abandoned', True)
        
        if suggest_uninstall and not self._is_app_critical(app):
            # Create uninstall action
            action = AppAction(
                app_name=app.display_name,
                action_type="uninstall",
                reason=f"Not used in {(datetime.now() - (app.last_used or app.install_date)).days} days",
                impact=f"Will free {app.install_size_mb:.1f} MB of disk space",
                estimated_time_minutes=2,
                requires_user_approval=True
            )
            
            # Publish for user approval
            self.bus.publish(
                'app.abandoned',
                source_module='application_curator',
                payload={
                    'app': app.__dict__,
                    'action': action.__dict__,
                    'requires_user_approval': True
                }
            )
    
    def _identify_app_issues(self, app: ApplicationInfo) -> List[str]:
        """تحديد مشاكل التطبيق"""
        issues = []
        
        # Check 1: Missing executable
        if app.executable_path and not os.path.exists(app.executable_path):
            issues.append("Missing executable file")
        
        # Check 2: Outdated version
        if app.version == 'Unknown' or not app.version:
            issues.append("Unknown version")
        
        # Check 3: Large size with low usage
        if app.install_size_mb > 500 and app.usage_count < 3:
            issues.append("Large size with minimal usage")
        
        # Check 4: No publisher info
        if app.publisher == 'Unknown':
            issues.append("Unknown publisher")
        
        return issues
    
    def _is_app_critical(self, app: ApplicationInfo) -> bool:
        """التحقق إذا كان التطبيق حرجاً"""
        # Check against critical apps list
        for critical_app in self.CRITICAL_APPS:
            if critical_app.lower() in app.display_name.lower():
                return True
        
        # Check against system components
        for system_component in self.SYSTEM_COMPONENTS:
            if system_component.lower() in app.display_name.lower():
                return True
        
        return False
    
    def _generate_app_report(self, apps: List[ApplicationInfo]):
        """توليد تقرير التطبيقات"""
        # Calculate statistics
        total_apps = len(apps)
        active_apps = sum(1 for app in apps if app.status == AppStatus.ACTIVE)
        idle_apps = sum(1 for app in apps if app.status == AppStatus.IDLE)
        abandoned_apps = sum(1 for app in apps if app.status == AppStatus.ABANDONED)
        problematic_apps = sum(1 for app in apps if app.status == AppStatus.PROBLEMATIC)
        
        # Calculate total disk space
        total_size_mb = sum(app.install_size_mb for app in apps)
        abandoned_size_mb = sum(app.install_size_mb for app in apps if app.status == AppStatus.ABANDONED)
        
        # Log report
        self.db.log_event(
            event_type='app_report',
            module_name='application_curator',
            severity='info',
            message=f"Application report: {total_apps} apps ({abandoned_apps} abandoned)",
            details={
                'total_apps': total_apps,
                'active_apps': active_apps,
                'idle_apps': idle_apps,
                'abandoned_apps': abandoned_apps,
                'problematic_apps': problematic_apps,
                'total_size_mb': total_size_mb,
                'abandoned_size_mb': abandoned_size_mb
            }
        )
    
    def handle_app_launch(self, message):
        """معالجة حدث تشغيل التطبيق"""
        payload = message.payload
        app_name = payload.get('app_name', 'Unknown')
        
        logger.debug(f"Application launched: {app_name}")
        
        # Update usage tracking
        current_time = datetime.now()
        if app_name not in self.usage_tracking:
            self.usage_tracking[app_name] = {
                'first_seen': current_time,
                'last_seen': current_time,
                'total_sessions': 1,
                'total_hours': 0.0,
                'current_session_start': current_time
            }
        else:
            tracking = self.usage_tracking[app_name]
            tracking['last_seen'] = current_time
            tracking['current_session_start'] = current_time
    
    def handle_app_close(self, message):
        """معالجة حدث إغلاق التطبيق"""
        payload = message.payload
        app_name = payload.get('app_name', 'Unknown')
        
        logger.debug(f"Application closed: {app_name}")
        
        # Update usage tracking
        if app_name in self.usage_tracking and 'current_session_start' in self.usage_tracking[app_name]:
            current_time = datetime.now()
            session_start = self.usage_tracking[app_name]['current_session_start']
            session_duration = (current_time - session_start).total_seconds()
            
            self.usage_tracking[app_name]['total_hours'] += session_duration / 3600
            self.usage_tracking[app_name].pop('current_session_start', None)
    
    def get_application_report(self) -> Dict:
        """الحصول على تقرير التطبيقات"""
        apps = self._get_installed_applications()
        
        # Calculate statistics
        stats = {
            'total_apps': len(apps),
            'by_category': {},
            'by_status': {},
            'disk_usage_mb': sum(app.install_size_mb for app in apps),
            'abandoned_disk_usage_mb': sum(app.install_size_mb for app in apps if app.status == AppStatus.ABANDONED)
        }
        
        # Count by category
        for category in AppCategory:
            count = sum(1 for app in apps if app.category == category)
            stats['by_category'][category.value] = count
        
        # Count by status
        for status in AppStatus:
            count = sum(1 for app in apps if app.status == status)
            stats['by_status'][status.value] = count
        
        # Get top 10 largest apps
        largest_apps = sorted(apps, key=lambda x: x.install_size_mb, reverse=True)[:10]
        stats['largest_apps'] = [
            {
                'name': app.display_name,
                'size_mb': app.install_size_mb,
                'status': app.status.value
            }
            for app in largest_apps
        ]
        
        # Get abandoned apps
        abandoned_apps = [app for app in apps if app.status == AppStatus.ABANDONED]
        stats['abandoned_apps'] = [
            {
                'name': app.display_name,
                'size_mb': app.install_size_mb,
                'last_used': app.last_used.isoformat() if app.last_used else None,
                'install_date': app.install_date.isoformat()
            }
            for app in abandoned_apps[:10]  # Top 10 abandoned
        ]
        
        return stats
    
    def uninstall_application(self, app_name: str) -> bool:
        """إلغاء تثبيت تطبيق"""
        try:
            # Get app info
            apps = self._get_installed_applications()
            target_app = next((app for app in apps if app.display_name == app_name), None)
            
            if not target_app or not target_app.uninstall_string:
                logger.error(f"Cannot uninstall {app_name}: No uninstall string")
                return False
            
            # Execute uninstall
            def do_uninstall():
                # Parse uninstall string
                uninstall_cmd = target_app.uninstall_string
                
                # Run uninstall command
                result = subprocess.run(
                    uninstall_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                
                if result.returncode == 0:
                    return True
                else:
                    raise Exception(f"Uninstall failed: {result.stderr}")
            
            # Use safe execution
            success = safe_execute(
                do_uninstall,
                description=f"Uninstall {app_name}",
                create_snapshot=True,
                rollback_on_failure=True
            )
            
            if success:
                logger.info(f"Successfully uninstalled: {app_name}")
                
                # Remove from usage tracking
                self.usage_tracking.pop(app_name, None)
                
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error uninstalling application: {e}")
            return False


# Global instance
_application_curator_instance = None

def get_application_curator() -> ApplicationCurator:
    """الحصول على instance الموديول"""
    global _application_curator_instance
    if _application_curator_instance is None:
        _application_curator_instance = ApplicationCurator()
    return _application_curator_instance