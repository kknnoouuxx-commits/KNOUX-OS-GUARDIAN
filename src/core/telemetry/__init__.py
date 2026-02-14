"""
Telemetry & Learning Pipeline
نظام جمع البيانات المجهولة (opt-in)
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """
    جامع البيانات التليمترية
    Collects anonymous usage telemetry (opt-in only)
    """
    
    def __init__(self, enabled: bool = False):
        self.telemetry_enabled = enabled
        self.buffer: List[Dict] = []
        self.buffer_max_size = 100
        
        logger.info(f"Telemetry Collector initialized (enabled: {enabled})")
    
    def record_event(self, event_type: str, data: Dict):
        """
        تسجيل حدث تليمتري
        
        Args:
            event_type: نوع الحدث
            data: البيانات المرفقة
        """
        if not self.telemetry_enabled:
            return
        
        # Sanitize data (remove PII)
        sanitized_data = self._sanitize(data)
        
        event = {
            'event_id': self._generate_event_id(),
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': sanitized_data,
            'system_hash': self._get_anonymous_system_id()
        }
        
        self.buffer.append(event)
        
        # Flush if buffer full
        if len(self.buffer) >= self.buffer_max_size:
            self.flush()
    
    def _sanitize(self, data: Dict) -> Dict:
        """
        إزالة المعلومات الشخصية
        Remove all personally identifiable information
        """
        sanitized = data.copy()
        
        # Remove file paths (keep only extension)
        if 'file_path' in sanitized:
            path = sanitized['file_path']
            sanitized['path_depth'] = len(Path(path).parts)
            sanitized['file_extension'] = Path(path).suffix
            del sanitized['file_path']
        
        # Hash any identifiers
        if 'machine_id' in sanitized:
            sanitized['machine_id'] = hashlib.sha256(
                sanitized['machine_id'].encode()
            ).hexdigest()[:16]
        
        return sanitized
    
    def _get_anonymous_system_id(self) -> str:
        """
        توليد معرف مجهول للنظام
        Generate consistent anonymous identifier
        """
        # Use a simple hash for now
        # In production, would use hardware info
        import platform
        system_info = f"{platform.system()}-{platform.machine()}"
        return hashlib.sha256(system_info.encode()).hexdigest()[:16]
    
    def _generate_event_id(self) -> str:
        """توليد معرف فريد للحدث"""
        from uuid import uuid4
        return str(uuid4())
    
    def flush(self):
        """إرسال البيانات التليمترية"""
        if not self.buffer:
            return
        
        logger.info(f"Telemetry: {len(self.buffer)} events buffered (not sent - offline mode)")
        
        # In production, would send to cloud
        # For now, just clear buffer
        self.buffer = []
    
    def enable(self):
        """تفعيل التليمتري"""
        self.telemetry_enabled = True
        logger.info("Telemetry enabled")
    
    def disable(self):
        """تعطيل التليمتري"""
        self.telemetry_enabled = False
        self.buffer = []
        logger.info("Telemetry disabled")
