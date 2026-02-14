"""
Safe Execution Framework
إطار التنفيذ الآمن مع snapshot/rollback
"""

import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Callable, Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class SnapshotManager:
    """
    مدير اللقطات الاحتياطية
    Creates and manages system snapshots
    """
    
    def __init__(self, snapshots_dir: str = None):
        if snapshots_dir is None:
            snapshots_dir = Path.cwd() / 'data' / 'snapshots'
        
        self.snapshots_directory = Path(snapshots_dir)
        self.snapshots_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Snapshot Manager initialized: {self.snapshots_directory}")
    
    def create_snapshot(self, description: str, include_files: List[str] = None) -> str:
        """
        إنشاء لقطة احتياطية
        
        Args:
            description: وصف اللقطة
            include_files: قائمة الملفات للنسخ الاحتياطي
            
        Returns:
            معرف اللقطة
        """
        snapshot_id = str(uuid4())
        snapshot_dir = self.snapshots_directory / snapshot_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_metadata = {
            'snapshot_id': snapshot_id,
            'created_at': datetime.now().isoformat(),
            'description': description,
            'type': 'full' if include_files else 'metadata_only'
        }
        
        # Backup files if specified
        if include_files:
            files_backup_path = snapshot_dir / 'files'
            files_backup_path.mkdir(exist_ok=True)
            
            backed_up = []
            for file_path in include_files:
                if os.path.exists(file_path):
                    try:
                        # Preserve directory structure
                        rel_path = os.path.relpath(file_path, '/')
                        backup_path = files_backup_path / rel_path
                        backup_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        shutil.copy2(file_path, backup_path)
                        backed_up.append(file_path)
                    except Exception as e:
                        logger.warning(f"Could not backup {file_path}: {e}")
            
            snapshot_metadata['backed_up_files'] = backed_up
        
        # Save metadata
        with open(snapshot_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(snapshot_metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created snapshot: {snapshot_id} - {description}")
        return snapshot_id
    
    def rollback_snapshot(self, snapshot_id: str) -> bool:
        """
        استعادة النظام من لقطة احتياطية
        
        Args:
            snapshot_id: معرف اللقطة
            
        Returns:
            True إذا نجحت العملية
        """
        snapshot_dir = self.snapshots_directory / snapshot_id
        
        if not snapshot_dir.exists():
            logger.error(f"Snapshot not found: {snapshot_id}")
            return False
        
        # Load metadata
        with open(snapshot_dir / 'metadata.json', 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        logger.info(f"Rolling back to snapshot: {snapshot_id}")
        
        try:
            # Restore files if any
            if 'backed_up_files' in metadata:
                files_backup_path = snapshot_dir / 'files'
                
                for backed_up_file in metadata['backed_up_files']:
                    rel_path = os.path.relpath(backed_up_file, '/')
                    backup_path = files_backup_path / rel_path
                    
                    if backup_path.exists():
                        os.makedirs(os.path.dirname(backed_up_file), exist_ok=True)
                        shutil.copy2(backup_path, backed_up_file)
            
            logger.info(f"Successfully rolled back to snapshot: {snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return False
    
    def cleanup_old_snapshots(self, keep_last_n: int = 10):
        """حذف اللقطات القديمة"""
        snapshots = sorted(
            self.snapshots_directory.iterdir(),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for snapshot in snapshots[keep_last_n:]:
            if snapshot.is_dir():
                shutil.rmtree(snapshot)
                logger.info(f"Cleaned up old snapshot: {snapshot.name}")


def safe_execute(action_function: Callable,
                description: str,
                create_snapshot: bool = True,
                rollback_on_failure: bool = True) -> Any:
    """
    تنفيذ آمن لعملية مع إمكانية الاستعادة
    
    Args:
        action_function: الدالة المراد تنفيذها
        description: وصف العملية
        create_snapshot: إنشاء لقطة احتياطية قبل التنفيذ
        rollback_on_failure: استعادة اللقطة عند الفشل
        
    Returns:
        نتيجة تنفيذ الدالة
    """
    snapshot_id = None
    
    try:
        # Create snapshot if requested
        if create_snapshot:
            snapshot_manager = SnapshotManager()
            snapshot_id = snapshot_manager.create_snapshot(description)
        
        # Execute action
        result = action_function()
        
        logger.info(f"Successfully executed: {description}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute: {description} - {e}")
        
        # Rollback if requested and snapshot exists
        if rollback_on_failure and snapshot_id:
            logger.info(f"Rolling back to snapshot: {snapshot_id}")
            snapshot_manager.rollback_snapshot(snapshot_id)
        
        raise
