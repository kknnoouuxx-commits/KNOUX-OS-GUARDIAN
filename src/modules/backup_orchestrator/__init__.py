"""
Cognitive Backup Orchestrator
تخطيط وتنفيذ ذكي للنسخ الاحتياطي بناءً على أنماط الاستخدام
"""

import logging
import os
import threading
import time
import subprocess
import json
import shutil
import zipfile
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


class BackupType(Enum):
    """نوع النسخ الاحتياطي"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SELECTIVE = "selective"


class BackupPriority(Enum):
    """أولوية النسخ الاحتياطي"""
    CRITICAL = "critical"  # System files, documents
    HIGH = "high"          # User data, settings
    MEDIUM = "medium"      # Applications, media
    LOW = "low"           # Cache, temporary files


@dataclass
class BackupItem:
    """عنوان النسخ الاحتياطي"""
    path: str
    priority: BackupPriority
    item_type: str  # file, directory, registry
    size_mb: float
    last_modified: datetime
    change_frequency: float  # 0.0-1.0


@dataclass
class BackupPlan:
    """خطة النسخ الاحتياطي"""
    plan_id: str
    backup_type: BackupType
    items: List[BackupItem]
    destination: str
    schedule: Dict  # cron-like schedule
    retention_days: int
    compression_level: int  # 0-9
    encryption_enabled: bool


class BackupOrchestrator:
    """
    منسق النسخ الاحتياطي المعرفي
    Cognitive Backup Orchestrator
    """
    
    def __init__(self):
        self.bus = get_bus()
        self.db = get_database()
        self.config = get_config()
        self.running = False
        self.orchestrator_thread = None
        
        # Backup plans
        self.backup_plans = {}
        
        # Backup history
        self.backup_history = []
        
        # Critical paths to always backup
        self.CRITICAL_PATHS = [
            r'C:\Users\{username}\Documents',
            r'C:\Users\{username}\Desktop',
            r'C:\Users\{username}\Pictures',
            r'C:\Users\{username}\Videos',
            r'C:\Users\{username}\Music',
        ]
        
        # System paths to consider
        self.SYSTEM_PATHS = [
            r'C:\Windows\System32\config',  # Registry
            r'C:\ProgramData',  # Application data
            r'C:\Users\{username}\AppData',  # User application data
        ]
        
        logger.info("Backup Orchestrator initialized")
    
    def start(self):
        """بدء التنسيق"""
        if not self.running:
            self.running = True
            self.orchestrator_thread = threading.Thread(
                target=self._orchestration_loop,
                daemon=True
            )
            self.orchestrator_thread.start()
            
            logger.info("Backup Orchestrator started")
    
    def stop(self):
        """إيقاف التنسيق"""
        self.running = False
        if self.orchestrator_thread:
            self.orchestrator_thread.join(timeout=5)
        logger.info("Backup Orchestrator stopped")
    
    def _orchestration_loop(self):
        """حلقة التنسيق الرئيسية"""
        backup_frequency = self.config.get('modules.backup_orchestrator.backup_frequency', 'daily')
        
        while self.running:
            try:
                # Check if it's time for backup
                if self._should_run_backup(backup_frequency):
                    # Create backup plan
                    backup_plan = self._create_backup_plan()
                    
                    # Execute backup
                    if backup_plan:
                        self._execute_backup(backup_plan)
                
                # Cleanup old backups
                self._cleanup_old_backups()
                
                # Wait for next check
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _should_run_backup(self, frequency: str) -> bool:
        """التحقق إذا كان الوقت مناسباً للنسخ الاحتياطي"""
        try:
            # Get last backup time
            last_backup = self._get_last_backup_time()
            
            if not last_backup:
                return True  # Never backed up
            
            current_time = datetime.now()
            time_since_last = current_time - last_backup
            
            if frequency == 'hourly':
                return time_since_last.total_seconds() >= 3600
            elif frequency == 'daily':
                return time_since_last.days >= 1
            elif frequency == 'weekly':
                return time_since_last.days >= 7
            elif frequency == 'monthly':
                return time_since_last.days >= 30
            else:
                return time_since_last.days >= 1  # Default daily
        
        except Exception as e:
            logger.error(f"Error checking backup schedule: {e}")
            return False
    
    def _get_last_backup_time(self) -> Optional[datetime]:
        """الحصول على وقت آخر نسخ احتياطي"""
        if self.backup_history:
            # Sort by timestamp descending
            sorted_history = sorted(self.backup_history, key=lambda x: x['timestamp'], reverse=True)
            return sorted_history[0]['timestamp']
        return None
    
    def _create_backup_plan(self) -> Optional[BackupPlan]:
        """إنشاء خطة نسخ احتياطي"""
        logger.info("Creating backup plan...")
        
        try:
            # Analyze system for backup items
            backup_items = self._analyze_system_for_backup()
            
            if not backup_items:
                logger.warning("No backup items found")
                return None
            
            # Determine backup type
            backup_type = self._determine_backup_type()
            
            # Get destination
            destination = self._get_backup_destination()
            
            if not destination:
                logger.error("No backup destination configured")
                return None
            
            # Create plan
            plan = BackupPlan(
                plan_id=f"BACKUP_{int(time.time())}",
                backup_type=backup_type,
                items=backup_items,
                destination=destination,
                schedule={
                    'frequency': self.config.get('modules.backup_orchestrator.backup_frequency', 'daily'),
                    'time': '02:00'  # 2 AM
                },
                retention_days=30,
                compression_level=6,
                encryption_enabled=False  # Would require encryption key
            )
            
            # Log plan creation
            self.db.log_event(
                event_type='backup_plan_created',
                module_name='backup_orchestrator',
                severity='info',
                message=f"Created backup plan with {len(backup_items)} items",
                details={
                    'plan_id': plan.plan_id,
                    'backup_type': plan.backup_type.value,
                    'total_size_mb': sum(item.size_mb for item in backup_items),
                    'destination': plan.destination
                }
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"Error creating backup plan: {e}")
            return None
    
    def _analyze_system_for_backup(self) -> List[BackupItem]:
        """تحليل النظام لعنوانات النسخ الاحتياطي"""
        items = []
        
        try:
            # Get current username
            import getpass
            username = getpass.getuser()
            
            # Analyze user documents
            docs_path = f'C:\\Users\\{username}\\Documents'
            if os.path.exists(docs_path):
                docs_item = self._analyze_directory(docs_path, BackupPriority.CRITICAL)
                if docs_item:
                    items.append(docs_item)
            
            # Analyze desktop
            desktop_path = f'C:\\Users\\{username}\\Desktop'
            if os.path.exists(desktop_path):
                desktop_item = self._analyze_directory(desktop_path, BackupPriority.CRITICAL)
                if desktop_item:
                    items.append(desktop_item)
            
            # Analyze pictures
            pictures_path = f'C:\\Users\\{username}\\Pictures'
            if os.path.exists(pictures_path):
                pictures_item = self._analyze_directory(pictures_path, BackupPriority.HIGH)
                if pictures_item:
                    items.append(pictures_item)
            
            # Analyze important application data
            appdata_path = f'C:\\Users\\{username}\\AppData'
            if os.path.exists(appdata_path):
                # Only backup specific important folders
                important_folders = ['Roaming\\Microsoft', 'Local\\Google', 'Roaming\\Mozilla']
                
                for folder in important_folders:
                    folder_path = os.path.join(appdata_path, folder)
                    if os.path.exists(folder_path):
                        folder_item = self._analyze_directory(folder_path, BackupPriority.HIGH)
                        if folder_item:
                            items.append(folder_item)
            
            # Analyze system configuration
            system_items = self._analyze_system_configuration()
            items.extend(system_items)
            
        except Exception as e:
            logger.error(f"Error analyzing system for backup: {e}")
        
        return items
    
    def _analyze_directory(self, directory_path: str, priority: BackupPriority) -> Optional[BackupItem]:
        """تحليل الدليل للنسخ الاحتياطي"""
        try:
            if not os.path.exists(directory_path):
                return None
            
            # Calculate directory size
            total_size = 0
            last_modified = datetime.fromtimestamp(0)
            
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        total_size += stat.st_size
                        
                        file_mtime = datetime.fromtimestamp(stat.st_mtime)
                        if file_mtime > last_modified:
                            last_modified = file_mtime
                    except (OSError, PermissionError):
                        continue
            
            # Estimate change frequency (simplified)
            change_frequency = 0.5  # Default
            
            # Create backup item
            item = BackupItem(
                path=directory_path,
                priority=priority,
                item_type="directory",
                size_mb=total_size / (1024 * 1024),
                last_modified=last_modified,
                change_frequency=change_frequency
            )
            
            return item
            
        except Exception as e:
            logger.error(f"Error analyzing directory {directory_path}: {e}")
            return None
    
    def _analyze_system_configuration(self) -> List[BackupItem]:
        """تحليل تكوين النظام للنسخ الاحتياطي"""
        items = []
        
        try:
            # Backup registry
            registry_item = BackupItem(
                path="HKLM\\SOFTWARE",
                priority=BackupPriority.CRITICAL,
                item_type="registry",
                size_mb=10.0,  # Estimated
                last_modified=datetime.now(),
                change_frequency=0.1
            )
            items.append(registry_item)
            
            # Backup system drivers
            drivers_item = BackupItem(
                path="C:\\Windows\\System32\\drivers",
                priority=BackupPriority.HIGH,
                item_type="directory",
                size_mb=100.0,  # Estimated
                last_modified=datetime.now(),
                change_frequency=0.05
            )
            items.append(drivers_item)
            
        except Exception as e:
            logger.error(f"Error analyzing system configuration: {e}")
        
        return items
    
    def _determine_backup_type(self) -> BackupType:
        """تحديد نوع النسخ الاحتياطي"""
        incremental_enabled = self.config.get('modules.backup_orchestrator.incremental_backup', True)
        
        if incremental_enabled:
            # Check if we have a recent full backup
            last_full_backup = self._get_last_full_backup()
            
            if last_full_backup:
                days_since_full = (datetime.now() - last_full_backup).days
                
                if days_since_full < 7:
                    return BackupType.INCREMENTAL
                else:
                    return BackupType.FULL
            else:
                return BackupType.FULL
        else:
            return BackupType.FULL
    
    def _get_last_full_backup(self) -> Optional[datetime]:
        """الحصول على وقت آخر نسخ احتياطي كامل"""
        full_backups = [entry for entry in self.backup_history 
                       if entry.get('backup_type') == 'full']
        
        if full_backups:
            sorted_backups = sorted(full_backups, key=lambda x: x['timestamp'], reverse=True)
            return sorted_backups[0]['timestamp']
        
        return None
    
    def _get_backup_destination(self) -> Optional[str]:
        """الحصول على وجهة النسخ الاحتياطي"""
        destination = self.config.get('modules.backup_orchestrator.backup_destination', '')
        
        if destination:
            # Check if destination exists
            if os.path.exists(destination):
                return destination
            else:
                # Try to create directory
                try:
                    os.makedirs(destination, exist_ok=True)
                    return destination
                except Exception as e:
                    logger.error(f"Cannot create backup destination {destination}: {e}")
        
        # Default destination
        default_dest = Path.cwd() / 'data' / 'backups'
        default_dest.mkdir(parents=True, exist_ok=True)
        
        return str(default_dest)
    
    def _execute_backup(self, plan: BackupPlan):
        """تنفيذ النسخ الاحتياطي"""
        logger.info(f"Executing backup: {plan.plan_id}")
        
        try:
            # Create backup directory
            backup_dir = Path(plan.destination) / plan.plan_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup metadata
            metadata = {
                'plan_id': plan.plan_id,
                'backup_type': plan.backup_type.value,
                'timestamp': datetime.now().isoformat(),
                'items': [item.__dict__ for item in plan.items],
                'total_size_mb': sum(item.size_mb for item in plan.items)
            }
            
            # Save metadata
            with open(backup_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Backup each item
            successful_items = []
            failed_items = []
            
            for item in plan.items:
                try:
                    if self._backup_item(item, backup_dir, plan):
                        successful_items.append(item)
                    else:
                        failed_items.append(item)
                except Exception as e:
                    logger.error(f"Error backing up item {item.path}: {e}")
                    failed_items.append(item)
            
            # Create backup archive
            archive_path = self._create_backup_archive(backup_dir, plan)
            
            # Update backup history
            backup_entry = {
                'plan_id': plan.plan_id,
                'timestamp': datetime.now(),
                'backup_type': plan.backup_type.value,
                'archive_path': archive_path,
                'successful_items': len(successful_items),
                'failed_items': len(failed_items),
                'total_size_mb': metadata['total_size_mb']
            }
            
            self.backup_history.append(backup_entry)
            
            # Log backup completion
            self.db.log_event(
                event_type='backup_completed',
                module_name='backup_orchestrator',
                severity='info' if not failed_items else 'warning',
                message=f"Backup completed: {len(successful_items)}/{len(plan.items)} items",
                details=backup_entry
            )
            
            # Publish backup event
            self.bus.publish(
                'backup.completed',
                source_module='backup_orchestrator',
                payload={
                    'plan': plan.__dict__,
                    'result': backup_entry,
                    'requires_user_notification': len(failed_items) > 0
                }
            )
            
            logger.info(f"Backup {plan.plan_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error executing backup: {e}")
            
            # Log backup failure
            self.db.log_event(
                event_type='backup_failed',
                module_name='backup_orchestrator',
                severity='error',
                message=f"Backup failed: {e}",
                details={'plan_id': plan.plan_id, 'error': str(e)}
            )
    
    def _backup_item(self, item: BackupItem, backup_dir: Path, plan: BackupPlan) -> bool:
        """نسخ احتياطي لعنوان معين"""
        try:
            if item.item_type == "directory":
                return self._backup_directory(item.path, backup_dir, plan)
            
            elif item.item_type == "registry":
                return self._backup_registry(item.path, backup_dir)
            
            else:
                logger.warning(f"Unknown item type: {item.item_type}")
                return False
            
        except Exception as e:
            logger.error(f"Error backing up item {item.path}: {e}")
            return False
    
    def _backup_directory(self, directory_path: str, backup_dir: Path, plan: BackupPlan) -> bool:
        """نسخ احتياطي للدليل"""
        try:
            # Create relative path in backup
            rel_path = os.path.relpath(directory_path, 'C:\\')
            target_dir = backup_dir / 'files' / rel_path
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy directory
            shutil.copytree(directory_path, target_dir, dirs_exist_ok=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Error backing up directory {directory_path}: {e}")
            return False
    
    def _backup_registry(self, registry_path: str, backup_dir: Path) -> bool:
        """نسخ احتياطي للسجل"""
        try:
            # Create registry backup directory
            reg_dir = backup_dir / 'registry'
            reg_dir.mkdir(exist_ok=True)
            
            # Generate safe filename
            safe_name = registry_path.replace('\\', '_').replace(':', '')
            reg_file = reg_dir / f"{safe_name}.reg"
            
            # Export registry key
            subprocess.run(
                ['reg', 'export', registry_path, str(reg_file), '/y'],
                check=True,
                timeout=30
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error backing up registry {registry_path}: {e}")
            return False
    
    def _create_backup_archive(self, backup_dir: Path, plan: BackupPlan) -> str:
        """إنشاء أرشيف النسخ الاحتياطي"""
        try:
            # Create archive filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_name = f"backup_{plan.plan_id}_{timestamp}.zip"
            archive_path = Path(plan.destination) / archive_name
            
            # Create zip archive
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files from backup directory
                for root, dirs, files in os.walk(backup_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_dir.parent)
                        zipf.write(file_path, arcname)
            
            # Cleanup temporary directory
            shutil.rmtree(backup_dir)
            
            return str(archive_path)
            
        except Exception as e:
            logger.error(f"Error creating backup archive: {e}")
            return ""
    
    def _cleanup_old_backups(self):
        """تنظيف النسخ الاحتياطي القديمة"""
        try:
            retention_days = 30  # Default retention
            
            current_time = datetime.now()
            backups_to_keep = []
            backups_to_delete = []
            
            for backup in self.backup_history:
                backup_age = (current_time - backup['timestamp']).days
                
                if backup_age <= retention_days:
                    backups_to_keep.append(backup)
                else:
                    backups_to_delete.append(backup)
            
            # Delete old backup files
            for backup in backups_to_delete:
                archive_path = backup.get('archive_path')
                if archive_path and os.path.exists(archive_path):
                    try:
                        os.remove(archive_path)
                        logger.info(f"Deleted old backup: {archive_path}")
                    except Exception as e:
                        logger.error(f"Error deleting backup file {archive_path}: {e}")
            
            # Update history
            self.backup_history = backups_to_keep
            
            # Log cleanup
            if backups_to_delete:
                self.db.log_event(
                    event_type='backup_cleanup',
                    module_name='backup_orchestrator',
                    severity='info',
                    message=f"Cleaned up {len(backups_to_delete)} old backups",
                    details={'deleted_count': len(backups_to_delete)}
                )
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def get_backup_status(self) -> Dict:
        """الحصول على حالة النسخ الاحتياطي"""
        # Get last backup
        last_backup = None
        if self.backup_history:
            sorted_history = sorted(self.backup_history, key=lambda x: x['timestamp'], reverse=True)
            last_backup = sorted_history[0]
        
        # Calculate statistics
        total_backups = len(self.backup_history)
        total_size_gb = sum(b.get('total_size_mb', 0) for b in self.backup_history) / 1024
        
        return {
            'last_backup': last_backup['timestamp'].isoformat() if last_backup else None,
            'last_backup_type': last_backup.get('backup_type') if last_backup else None,
            'total_backups': total_backups,
            'total_size_gb': round(total_size_gb, 2),
            'next_scheduled': self._get_next_scheduled_backup(),
            'destination': self._get_backup_destination()
        }
    
    def _get_next_scheduled_backup(self) -> str:
        """الحصول على موعد النسخ الاحتياطي التالي"""
        frequency = self.config.get('modules.backup_orchestrator.backup_frequency', 'daily')
        
        if frequency == 'hourly':
            next_time = datetime.now() + timedelta(hours=1)
        elif frequency == 'daily':
            next_time = datetime.now() + timedelta(days=1)
        elif frequency == 'weekly':
            next_time = datetime.now() + timedelta(days=7)
        elif frequency == 'monthly':
            next_time = datetime.now() + timedelta(days=30)
        else:
            next_time = datetime.now() + timedelta(days=1)
        
        return next_time.strftime('%Y-%m-%d %H:%M:%S')
    
    def run_manual_backup(self, backup_type: str = "selective") -> Dict:
        """تشغيل نسخ احتياطي يدوي"""
        logger.info(f"Running manual backup: {backup_type}")
        
        try:
            # Create manual backup plan
            if backup_type == "full":
                plan = self._create_full_backup_plan()
            elif backup_type == "selective":
                plan = self._create_selective_backup_plan()
            else:
                plan = self._create_backup_plan()
            
            if plan:
                # Execute backup
                self._execute_backup(plan)
                
                return {
                    'success': True,
                    'plan_id': plan.plan_id,
                    'message': 'Backup started successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to create backup plan'
                }
            
        except Exception as e:
            logger.error(f"Error running manual backup: {e}")
            return {
                'success': False,
                'message': f'Backup failed: {e}'
            }
    
    def _create_full_backup_plan(self) -> BackupPlan:
        """إنشاء خطة نسخ احتياطي كامل"""
        # Similar to _create_backup_plan but always full
        backup_items = self._analyze_system_for_backup()
        
        plan = BackupPlan(
            plan_id=f"FULL_{int(time.time())}",
            backup_type=BackupType.FULL,
            items=backup_items,
            destination=self._get_backup_destination(),
            schedule={'manual': True},
            retention_days=90,  # Longer retention for manual backups
            compression_level=6,
            encryption_enabled=False
        )
        
        return plan
    
    def _create_selective_backup_plan(self) -> BackupPlan:
        """إنشاء خطة نسخ احتياطي انتقائي"""
        # Focus on critical items only
        import getpass
        username = getpass.getuser()
        
        critical_paths = [
            f'C:\\Users\\{username}\\Documents',
            f'C:\\Users\\{username}\\Desktop',
            f'C:\\Users\\{username}\\Pictures',
        ]
        
        backup_items = []
        for path in critical_paths:
            if os.path.exists(path):
                item = self._analyze_directory(path, BackupPriority.CRITICAL)
                if item:
                    backup_items.append(item)
        
        plan = BackupPlan(
            plan_id=f"SELECTIVE_{int(time.time())}",
            backup_type=BackupType.SELECTIVE,
            items=backup_items,
            destination=self._get_backup_destination(),
            schedule={'manual': True},
            retention_days=60,
            compression_level=6,
            encryption_enabled=False
        )
        
        return plan


# Global instance
_backup_orchestrator_instance = None

def get_backup_orchestrator() -> BackupOrchestrator:
    """الحصول على instance الموديول"""
    global _backup_orchestrator_instance
    if _backup_orchestrator_instance is None:
        _backup_orchestrator_instance = BackupOrchestrator()
    return _backup_orchestrator_instance