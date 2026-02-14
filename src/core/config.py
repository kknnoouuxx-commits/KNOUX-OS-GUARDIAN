"""
Configuration Management
إدارة الإعدادات
"""

import yaml
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """مدير الإعدادات"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path.cwd() / 'config' / 'config.yaml'
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        logger.info(f"Configuration loaded from: {self.config_path}")
    
    def _load_config(self) -> dict:
        """تحميل ملف الإعدادات"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return {}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config or {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        الحصول على قيمة إعداد
        
        Args:
            key: مفتاح الإعداد (يدعم النقاط للوصول المتداخل)
            default: القيمة الافتراضية
            
        Returns:
            قيمة الإعداد
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        تعيين قيمة إعداد
        
        Args:
            key: مفتاح الإعداد
            value: القيمة الجديدة
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """حفظ الإعدادات"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def is_module_enabled(self, module_name: str) -> bool:
        """التحقق من تفعيل موديول"""
        return self.get(f'modules.{module_name}.enabled', False)


# Global config instance
_config_instance = None

def get_config() -> ConfigManager:
    """الحصول على instance الإعدادات العامة"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
