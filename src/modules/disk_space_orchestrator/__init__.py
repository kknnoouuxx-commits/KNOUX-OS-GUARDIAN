"""
Intelligent Disk Space Orchestrator
إدارة ذكية واستباقية لمساحة القرص
"""

import os
import json
import shutil
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.core.communication_bus import get_bus
from src.core.safe_execution import safe_execute
from src.core.database import get_database
from src.core.config import get_config

logger = logging.getLogger(__name__)


class FileCategory(Enum):
    """تصنيف الملفات"""
    TEMP = "temp"
    CACHE = "cache"
    LOG = "log"
    DOWNLOAD = "download"
    DOCUMENT = "document"
    MEDIA = "media"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ActionType(Enum):
    """نوع الإجراء"""
    DELETE = "delete"
    COMPRESS = "compress"
    MOVE = "move"
    ARCHIVE = "archive"


@dataclass
class FileMetadata:
    """بيانات الملف"""
    path: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    accessed_at: datetime
    category: FileCategory
    safety_score: float  # 0.0-1.0
    deletion_score: float  # حسابي


@dataclass
class FileAction:
    """إجراء على ملف"""
    file_path: str
    file_size_bytes: int
    action_type: ActionType
    risk_level: str  # low, medium, high
    reason: str
    estimated_time_seconds: int


class DiskSpaceOrchestrator:
    """
    منسق المساحة التخزينية الذكي
    Intelligent Disk Space Orchestrator
    """
    
    def __init__(self):
        self.bus = get_bus()
        self.db = get_database()
        self.config = get_config()
        self.running = False
        self.monitor_thread = None
        
        # Critical paths (never touch)
        self.CRITICAL_PATHS = [
            r'C:\Windows\System32',
            r'C:\Windows\SysWOW64',
            r'C:\Program Files\WindowsApps',
            r'C:\ProgramData\Microsoft\Windows\Start Menu'
        ]
        
        # Safe extensions
        self.SAFE_EXTENSIONS = ['.tmp', '.log', '.cache', '.bak', '.old']
        
        logger.info("Disk Space Orchestrator initialized")
    
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
            self.bus.subscribe('system.low_disk_space', self.handle_low_disk_space)
            
            logger.info("Disk Space Orchestrator started")
    
    def stop(self):
        """إيقاف المراقبة"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Disk Space Orchestrator stopped")
    
    def _monitoring_loop(self):
        """حلقة المراقبة الرئيسية"""
        scan_interval_hours = self.config.get('modules.disk_space_orchestrator.scan_interval_hours', 1)
        scan_interval_seconds = max(300, float(scan_interval_hours) * 3600)
        
        while self.running:
            try:
                # Check disk space
                self._check_disk_space()
                
                # Wait for next scan
                time.sleep(scan_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _check_disk_space(self):
        """فحص مساحة القرص"""
        import psutil
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        free_percent = (disk.free / disk.total) * 100
        free_gb = disk.free / (1024**3)
        
        # Log to database
        self.db.log_event(
            event_type='disk_space_check',
            module_name='disk_space_orchestrator',
            severity='info',
            message=f'Disk space: {free_percent:.1f}% free ({free_gb:.1f} GB)',
            details={'free_percent': free_percent, 'free_gb': free_gb}
        )
        
        # Check threshold
        threshold = self.config.get('modules.disk_space_orchestrator.low_space_threshold_percent', 10)
        
        if free_percent < threshold:
            logger.warning(f"Low disk space detected: {free_percent:.1f}% free")
            
            # Publish event
            self.bus.publish(
                'disk_space.low',
                source_module='disk_space_orchestrator',
                payload={
                    'free_percent': free_percent,
                    'free_gb': free_gb,
                    'threshold': threshold
                }
            )
            
            # Trigger cleanup if auto-cleanup enabled
            auto_cleanup = self.config.get('modules.disk_space_orchestrator.auto_cleanup_enabled', False)
            if auto_cleanup:
                self._trigger_cleanup(free_percent, free_gb)
    
    def _trigger_cleanup(self, free_percent: float, free_gb: float):
        """تشغيل عملية التنظيف"""
        logger.info(f"Triggering disk cleanup (free: {free_percent:.1f}%)")
        
        try:
            # Scan disk
            files = self._scan_disk()
            
            # Analyze and create plan
            plan = self._create_cleanup_plan(files, free_gb)
            
            # Execute plan
            if plan:
                self._execute_cleanup_plan(plan)
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _scan_disk(self) -> List[FileMetadata]:
        """مسح القرص وجمع معلومات الملفات"""
        logger.info("Scanning disk for file analysis...")
        
        files = []
        scan_paths = ['C:\\Users', 'C:\\Windows\\Temp', 'C:\\Temp']
        
        for scan_path in scan_paths:
            if os.path.exists(scan_path):
                for root, dirs, filenames in os.walk(scan_path):
                    for filename in filenames:
                        try:
                            file_path = os.path.join(root, filename)
                            
                            # Skip if path is critical
                            if self._is_path_critical(file_path):
                                continue
                            
                            # Get file stats
                            stat = os.stat(file_path)
                            
                            # Classify file
                            category = self._classify_file(file_path)
                            
                            # Calculate safety score
                            safety_score = self._calculate_safety_score(file_path, category)
                            
                            # Create metadata
                            metadata = FileMetadata(
                                path=file_path,
                                size_bytes=stat.st_size,
                                created_at=datetime.fromtimestamp(stat.st_ctime),
                                modified_at=datetime.fromtimestamp(stat.st_mtime),
                                accessed_at=datetime.fromtimestamp(stat.st_atime),
                                category=category,
                                safety_score=safety_score,
                                deletion_score=0.0  # Will be calculated later
                            )
                            
                            files.append(metadata)
                            
                        except (OSError, PermissionError):
                            continue
        
        logger.info(f"Scanned {len(files)} files")
        return files
    
    def _is_path_critical(self, file_path: str) -> bool:
        """التحقق إذا كان المسار حرجاً (لا يجب لمسه)"""
        file_path_lower = file_path.lower()
        for critical_path in self.CRITICAL_PATHS:
            if file_path_lower.startswith(critical_path.lower()):
                return True
        return False
    
    def _classify_file(self, file_path: str) -> FileCategory:
        """تصنيف الملف"""
        path_lower = file_path.lower()
        extension = Path(file_path).suffix.lower()
        
        # Rule-based classification
        if 'temp' in path_lower or extension in ['.tmp', '.temp']:
            return FileCategory.TEMP
        elif 'cache' in path_lower or extension == '.cache':
            return FileCategory.CACHE
        elif extension in ['.log', '.txt'] and 'log' in path_lower:
            return FileCategory.LOG
        elif 'downloads' in path_lower:
            return FileCategory.DOWNLOAD
        elif extension in ['.doc', '.docx', '.pdf', '.xlsx']:
            return FileCategory.DOCUMENT
        elif extension in ['.jpg', '.png', '.mp4', '.mp3']:
            return FileCategory.MEDIA
        elif 'windows' in path_lower or 'system32' in path_lower:
            return FileCategory.SYSTEM
        else:
            return FileCategory.UNKNOWN
    
    def _calculate_safety_score(self, file_path: str, category: FileCategory) -> float:
        """حساب درجة أمان الملف (1.0 = آمن للحذف، 0.0 = خطير)"""
        path_lower = file_path.lower()
        extension = Path(file_path).suffix.lower()
        
        # Unsafe paths
        unsafe_paths = [
            'c:\\windows\\system32',
            'c:\\program files',
            'c:\\programdata\\microsoft'
        ]
        
        for unsafe in unsafe_paths:
            if path_lower.startswith(unsafe):
                return 0.0
        
        # Safe extensions
        if extension in self.SAFE_EXTENSIONS:
            return 1.0
        
        # Safe paths
        safe_paths = [
            'appdata\\local\\temp',
            'appdata\\local\\microsoft\\windows\\inetcache',
            'windows\\temp'
        ]
        
        for safe in safe_paths:
            if safe in path_lower:
                return 0.9
        
        # Category-based scoring
        if category == FileCategory.TEMP:
            return 0.8
        elif category == FileCategory.CACHE:
            return 0.7
        elif category == FileCategory.LOG:
            return 0.6
        elif category == FileCategory.DOWNLOAD:
            return 0.5
        elif category == FileCategory.SYSTEM:
            return 0.1
        else:
            return 0.3
    
    def _calculate_deletion_score(self, metadata: FileMetadata) -> float:
        """حساب درجة أولوية الحذف"""
        score = 0.0
        
        # Size component (40% weight)
        size_gb = metadata.size_bytes / (1024**3)
        size_score = min(size_gb / 10.0, 1.0) * 40
        score += size_score
        
        # Age component (30% weight)
        age_days = (datetime.now() - metadata.modified_at).days
        age_score = min(age_days / 365.0, 1.0) * 30
        score += age_score
        
        # Safety component (30% weight)
        safety_score = metadata.safety_score * 30
        score += safety_score
        
        # Category modifiers
        if metadata.category == FileCategory.TEMP:
            score *= 1.5  # boost temp files
        elif metadata.category == FileCategory.SYSTEM:
            score *= 0.1  # heavily penalize system files
        
        return score
    
    def _create_cleanup_plan(self, files: List[FileMetadata], target_free_gb: float) -> List[FileAction]:
        """إنشاء خطة تنظيف"""
        logger.info("Creating cleanup plan...")
        
        # Calculate deletion scores
        for file in files:
            file.deletion_score = self._calculate_deletion_score(file)
        
        # Sort by deletion score (descending)
        files.sort(key=lambda x: x.deletion_score, reverse=True)
        
        # Create actions
        actions = []
        total_space_to_free = target_free_gb * 1.5  # Aim for 50% more than target
        
        space_freed_gb = 0
        for file in files:
            if space_freed_gb >= total_space_to_free:
                break
            
            # Skip if not safe enough
            if file.safety_score < 0.3:
                continue
            
            # Determine action type
            if file.category in [FileCategory.TEMP, FileCategory.CACHE, FileCategory.LOG]:
                action_type = ActionType.DELETE
                risk_level = "low"
                reason = f"{file.category.value} file, safe to delete"
            elif file.category == FileCategory.DOWNLOAD and file.safety_score > 0.5:
                action_type = ActionType.ARCHIVE
                risk_level = "medium"
                reason = "Old download, can be archived"
            else:
                continue
            
            # Create action
            action = FileAction(
                file_path=file.path,
                file_size_bytes=file.size_bytes,
                action_type=action_type,
                risk_level=risk_level,
                reason=reason,
                estimated_time_seconds=2
            )
            
            actions.append(action)
            space_freed_gb += file.size_bytes / (1024**3)
        
        logger.info(f"Cleanup plan created: {len(actions)} actions, {space_freed_gb:.1f} GB to free")
        return actions
    
    def _execute_cleanup_plan(self, plan: List[FileAction]):
        """تنفيذ خطة التنظيف"""
        logger.info(f"Executing cleanup plan with {len(plan)} actions")
        
        auto_cleanup = self.config.get('modules.disk_space_orchestrator.auto_cleanup_enabled', False)
        
        for action in plan:
            try:
                # Check if auto-cleanup is enabled for this risk level
                if action.risk_level == "low" and auto_cleanup:
                    # Auto-execute low risk actions
                    self._execute_action(action)
                else:
                    # For medium/high risk, publish for user approval
                    self.bus.publish(
                        'disk_cleanup.suggested',
                        source_module='disk_space_orchestrator',
                        payload={
                            'action': action.__dict__,
                            'requires_approval': True
                        }
                    )
                    
            except Exception as e:
                logger.error(f"Error executing action {action.file_path}: {e}")
    
    def _execute_action(self, action: FileAction):
        """تنفيذ إجراء على ملف"""
        def delete_file():
            os.remove(action.file_path)
            return True
        
        def archive_file():
            # Create archive directory
            archive_dir = Path("C:\\KNOUX_Archives")
            archive_dir.mkdir(exist_ok=True)
            
            # Move file to archive
            dest = archive_dir / Path(action.file_path).name
            shutil.move(action.file_path, dest)
            return True
        
        try:
            if action.action_type == ActionType.DELETE:
                result = safe_execute(
                    delete_file,
                    description=f"Deleting {action.file_path}",
                    create_snapshot=True,
                    rollback_on_failure=True
                )
                
                if result:
                    logger.info(f"Deleted: {action.file_path}")
                    self._log_cleanup_action(action, success=True)
                    
            elif action.action_type == ActionType.ARCHIVE:
                result = safe_execute(
                    archive_file,
                    description=f"Archiving {action.file_path}",
                    create_snapshot=True,
                    rollback_on_failure=True
                )
                
                if result:
                    logger.info(f"Archived: {action.file_path}")
                    self._log_cleanup_action(action, success=True)
                    
        except Exception as e:
            logger.error(f"Failed to execute action: {e}")
            self._log_cleanup_action(action, success=False, error=str(e))
    
    def _log_cleanup_action(self, action: FileAction, success: bool, error: str = None):
        """تسجيل إجراء التنظيف"""
        self.db.log_event(
            event_type='disk_cleanup_action',
            module_name='disk_space_orchestrator',
            severity='info' if success else 'error',
            message=f"{action.action_type.value}: {action.file_path}",
            details={
                'action': action.__dict__,
                'success': success,
                'error': error
            }
        )
    
    def handle_low_disk_space(self, message):
        """معالجة حدث انخفاض مساحة القرص"""
        payload = message.payload
        free_percent = payload['free_percent']
        free_gb = payload['free_gb']
        
        logger.warning(f"Handling low disk space event: {free_percent:.1f}% free")
        
        # Trigger cleanup
        self._trigger_cleanup(free_percent, free_gb)


# Global instance
_disk_orchestrator_instance = None

def get_disk_orchestrator() -> DiskSpaceOrchestrator:
    """الحصول على instance الموديول"""
    global _disk_orchestrator_instance
    if _disk_orchestrator_instance is None:
        _disk_orchestrator_instance = DiskSpaceOrchestrator()
    return _disk_orchestrator_instance
