#!/usr/bin/env python3
"""
KNOUX OS Guardian - مدير الإعدادات
إدارة وتعديل إعدادات النظام
"""

import os
import sys
import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import colorama
from colorama import Fore, Style

colorama.init()

class ConfigManager:
    """مدير إعدادات النظام"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.backup_dir = Path("config/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict:
        """تحميل ملف الإعدادات"""
        if not self.config_path.exists():
            print(f"{Fore.YELLOW}⚠️  ملف الإعدادات غير موجود: {self.config_path}{Style.RESET_ALL}")
            return self._create_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"{Fore.RED}❌ خطأ في تحميل الإعدادات: {e}{Style.RESET_ALL}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """إنشاء إعدادات افتراضية"""
        default_config = {
            "system": {
                "name": "KNOUX OS Guardian",
                "version": "1.0.0",
                "language": "ar",
                "log_level": "INFO",
                "data_dir": "data",
                "database_path": "database/knoux_guardian.db"
            },
            "modules": {
                "disk_space_orchestrator": {
                    "enabled": True,
                    "scan_interval_minutes": 60,
                    "cleanup_threshold_percent": 20,
                    "max_temp_files_gb": 10
                },
                "update_guardian": {
                    "enabled": True,
                    "check_interval_hours": 24,
                    "auto_update": False,
                    "defer_security_updates": False
                },
                "performance_optimizer": {
                    "enabled": True,
                    "optimize_interval_minutes": 30,
                    "cpu_threshold_percent": 80,
                    "memory_threshold_percent": 85
                },
                "network_monitor": {
                    "enabled": True,
                    "monitor_interval_seconds": 300,
                    "privacy_mode": "strict",
                    "log_suspicious": True
                },
                "security_hardener": {
                    "enabled": True,
                    "scan_interval_hours": 168,  # أسبوع
                    "cis_profile": "enterprise",
                    "auto_remediate": False
                },
                "driver_health_manager": {
                    "enabled": True,
                    "check_interval_hours": 24,
                    "auto_update": False,
                    "backup_before_update": True
                },
                "forensic_analyzer": {
                    "enabled": True,
                    "analyze_on_crash": True,
                    "keep_logs_days": 30,
                    "deep_analysis": False
                },
                "thermal_controller": {
                    "enabled": True,
                    "monitor_interval_seconds": 30,
                    "critical_temp_celsius": 90,
                    "warning_temp_celsius": 80
                },
                "power_manager": {
                    "enabled": True,
                    "optimize_on_battery": True,
                    "screen_timeout_minutes": 10,
                    "sleep_timeout_minutes": 30
                },
                "application_curator": {
                    "enabled": True,
                    "scan_interval_days": 7,
                    "abandoned_threshold_days": 90,
                    "suggest_removal": True
                },
                "registry_guardian": {
                    "enabled": True,
                    "scan_interval_days": 30,
                    "backup_before_changes": True,
                    "quarantine_malware": True
                },
                "backup_orchestrator": {
                    "enabled": True,
                    "backup_interval_days": 7,
                    "keep_backups_count": 4,
                    "compression": True
                }
            },
            "ml_models": {
                "disk_usage_predictor": {
                    "enabled": True,
                    "confidence_threshold": 0.7,
                    "update_interval_days": 30
                },
                "performance_anomaly_detector": {
                    "enabled": True,
                    "sensitivity": "medium",
                    "alert_on_anomaly": True
                },
                "thermal_threshold_predictor": {
                    "enabled": True,
                    "prediction_horizon_hours": 2,
                    "alert_margin_celsius": 5
                },
                "update_risk_predictor": {
                    "enabled": True,
                    "risk_threshold": 0.6,
                    "defer_high_risk": True
                }
            },
            "api": {
                "enabled": True,
                "host": "0.0.0.0",
                "port": 8000,
                "auth_required": True,
                "cors_enabled": True
            },
            "telemetry": {
                "enabled": False,  # افتراضيًا معطل للخصوصية
                "anonymous_id": "",
                "opt_in_required": True,
                "data_retention_days": 7
            }
        }
        
        # حفظ الإعدادات الافتراضية
        self._save_config(default_config)
        print(f"{Fore.GREEN}✅ تم إنشاء إعدادات افتراضية{Style.RESET_ALL}")
        
        return default_config
    
    def _save_config(self, config: Dict) -> bool:
        """حفظ الإعدادات"""
        try:
            # إنشاء نسخة احتياطية
            self._create_backup()
            
            # حفظ الإعدادات الجديدة
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            print(f"{Fore.GREEN}✅ تم حفظ الإعدادات{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ خطأ في حفظ الإعدادات: {e}{Style.RESET_ALL}")
            return False
    
    def _create_backup(self) -> Optional[Path]:
        """إنشاء نسخة احتياطية"""
        if not self.config_path.exists():
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"config_backup_{timestamp}.yaml"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(self.config_path, backup_path)
            
            # الاحتفاظ بـ 10 نسخ احتياطية فقط
            backups = sorted(self.backup_dir.glob("config_backup_*.yaml"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
            
            return backup_path
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  فشل إنشاء نسخة احتياطية: {e}{Style.RESET_ALL}")
            return None
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """الحصول على قيمة من الإعدادات"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_value(self, key_path: str, value: Any) -> bool:
        """تعيين قيمة في الإعدادات"""
        keys = key_path.split('.')
        config = self.config
        
        # التنقل في الهيكل
        for i, key in enumerate(keys[:-1]):
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # تعيين القيمة
        last_key = keys[-1]
        old_value = config.get(last_key)
        config[last_key] = value
        
        # حفظ التغييرات
        if self._save_config(self.config):
            print(f"{Fore.GREEN}✅ تم تحديث: {key_path}{Style.RESET_ALL}")
            print(f"   القيمة القديمة: {old_value}")
            print(f"   القيمة الجديدة: {value}")
            return True
        else:
            return False
    
    def enable_module(self, module_name: str) -> bool:
        """تفعيل موديول"""
        module_key = f"modules.{module_name}.enabled"
        return self.set_value(module_key, True)
    
    def disable_module(self, module_name: str) -> bool:
        """تعطيل موديول"""
        module_key = f"modules.{module_name}.enabled"
        return self.set_value(module_key, False)
    
    def list_modules(self) -> List[Dict]:
        """عرض قائمة الموديولات"""
        modules = []
        
        for module_name, module_config in self.config.get("modules", {}).items():
            modules.append({
                "name": module_name,
                "enabled": module_config.get("enabled", False),
                "description": self._get_module_description(module_name),
                "config": module_config
            })
        
        return modules
    
    def _get_module_description(self, module_name: str) -> str:
        """الحصول على وصف الموديول"""
        descriptions = {
            "disk_space_orchestrator": "إدارة مساحة التخزين والتنظيف التلقائي",
            "update_guardian": "إدارة تحديثات النظام وتقييم المخاطر",
            "performance_optimizer": "تحسين أداء النظام والموارد",
            "network_monitor": "مراقبة الشبكة وكشف التهديدات",
            "security_hardener": "تعزيز أمان النظام والتوافق",
            "driver_health_manager": "إدارة صحة برامج التشغيل والتحديثات",
            "forensic_analyzer": "تحليل الأعطال والتحقيق في المشاكل",
            "thermal_controller": "التحكم في درجة الحرارة والتبريد",
            "power_manager": "إدارة الطاقة وتحسين الاستهلاك",
            "application_curator": "إدارة دورة حياة التطبيقات",
            "registry_guardian": "حماية السجل وكشف البرامج الضارة",
            "backup_orchestrator": "إدارة النسخ الاحتياطي والاستعادة"
        }
        
        return descriptions.get(module_name, "موديول النظام")
    
    def validate_config(self) -> Dict[str, List[str]]:
        """التحقق من صحة الإعدادات"""
        issues = {
            "warnings": [],
            "errors": []
        }
        
        # التحقق من الموديولات
        modules = self.config.get("modules", {})
        for module_name, module_config in modules.items():
            if not isinstance(module_config, dict):
                issues["errors"].append(f"إعدادات الموديول {module_name} غير صحيحة")
                continue
            
            if "enabled" not in module_config:
                issues["warnings"].append(f"الموديول {module_name} لا يحتوي على حقل enabled")
        
        # التحقق من المسارات
        system_config = self.config.get("system", {})
        if not system_config.get("data_dir"):
            issues["warnings"].append("مسار data_dir غير محدد")
        
        if not system_config.get("database_path"):
            issues["errors"].append("مسار قاعدة البيانات غير محدد")
        
        # التحقق من قيم النطاق
        for module_name, module_config in modules.items():
            if module_name == "thermal_controller":
                critical_temp = module_config.get("critical_temp_celsius")
                warning_temp = module_config.get("warning_temp_celsius")
                
                if critical_temp and warning_temp and critical_temp <= warning_temp:
                    issues["errors"].append(f"درجة الحرارة الحرجة يجب أن تكون أعلى من درجة التحذير في {module_name}")
        
        return issues
    
    def export_config(self, format: str = "json", output_path: Optional[str] = None) -> bool:
        """تصدير الإعدادات"""
        if format not in ["json", "yaml"]:
            print(f"{Fore.RED}❌ تنسيق غير مدعوم: {format}{Style.RESET_ALL}")
            return False
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"config_export_{timestamp}.{format}"
        
        output_file = Path(output_path)
        
        try:
            if format == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            else:  # yaml
                with open(output_file, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            print(f"{Fore.GREEN}✅ تم التصدير إلى: {output_file}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ خطأ في التصدير: {e}{Style.RESET_ALL}")
            return False
    
    def import_config(self, import_path: str, merge: bool = True) -> bool:
        """استيراد الإعدادات"""
        import_file = Path(import_path)
        
        if not import_file.exists():
            print(f"{Fore.RED}❌ ملف الاستيراد غير موجود: {import_path}{Style.RESET_ALL}")
            return False
        
        try:
            if import_file.suffix.lower() == '.json':
                with open(import_file, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
            else:  # yaml
                with open(import_file, 'r', encoding='utf-8') as f:
                    imported_config = yaml.safe_load(f)
            
            if merge:
                # دمج الإعدادات
                self._merge_configs(self.config, imported_config)
                print(f"{Fore.GREEN}✅ تم دمج الإعدادات{Style.RESET_ALL}")
            else:
                # استبدال كامل
                self.config = imported_config
                print(f"{Fore.GREEN}✅ تم استبدال الإعدادات{Style.RESET_ALL}")
            
            return self._save_config(self.config)
            
        except Exception as e:
            print(f"{Fore.RED}❌ خطأ في الاستيراد: {e}{Style.RESET_ALL}")
            return False
    
    def _merge_configs(self, base: Dict, new: Dict):
        """دمج إعدادين"""
        for key, value in new.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value
    
    def show_summary(self):
        """عرض ملخص الإعدادات"""
        print(f"{Fore.CYAN}📋 ملخص إعدادات KNOUX OS Guardian{Style.RESET_ALL}")
        print("=" * 60)
        
        # معلومات النظام
        system = self.config.get("system", {})
        print(f"🏷️  الاسم: {system.get('name', 'غير محدد')}")
        print(f"📦 الإصدار: {system.get('version', 'غير محدد')}")
        print(f"🌐 اللغة: {system.get('language', 'غير محدد')}")
        print(f"📁 مجلد البيانات: {system.get('data_dir', 'غير محدد')}")
        print()
        
        # الموديولات
        modules = self.config.get("modules", {})
        enabled_count = sum(1 for m in modules.values() if m.get("enabled", False))
        total_count = len(modules)
        
        print(f"🔧 الموديولات: {enabled_count}/{total_count} مفعل")
        print("الموديولات المفعلة:")
        for module_name, module_config in modules.items():
            if module_config.get("enabled", False):
                print(f"  • {module_name}: {self._get_module_description(module_name)}")
        print()
        
        # نماذج ML
        ml_models = self.config.get("ml_models", {})
        ml_enabled = sum(1 for m in ml_models.values() if m.get("enabled", False))
        ml_total = len(ml_models)
        
        print(f"🤖 نماذج ML: {ml_enabled}/{ml_total} مفعل")
        print()
        
        # API
        api_config = self.config.get("api", {})
        if api_config.get("enabled", False):
            print(f"🌐 API: مفعل على {api_config.get('host', 'غير محدد')}:{api_config.get('port', 'غير محدد')}")
        else:
            print(f"🌐 API: معطل")
        print()
        
        # التليمتري
        telemetry = self.config.get("telemetry", {})
        if telemetry.get("enabled", False):
            print(f"📊 التليمتري: مفعل (مجهول)")
        else:
            print(f"📊 التليمتري: معطل")
        
        print("=" * 60)

def main():
    """الدالة الرئيسية"""
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="مدير إعدادات KNOUX OS Guardian")
    parser.add_argument("action", choices=["show", "get", "set", "enable", "disable", 
                                         "list", "validate", "export", "import", "summary"],
                       help="الإجراء المطلوب")
    parser.add_argument("--key", help="مفتاح الإعداد (لـ get/set)")
    parser.add_argument("--value", help="القيمة (لـ set)")
    parser.add_argument("--module", help="اسم الموديول (لـ enable/disable)")
    parser.add_argument("--format", choices=["json", "yaml"], default="json",
                       help="تنسيق التصدير")
    parser.add_argument("--file", help="مسار الملف (لـ export/import)")
    parser.add_argument("--merge", action="store_true",
                       help="دمج بدلاً من الاستبدال (لـ import)")
    
    args = parser.parse_args()
    
    manager = ConfigManager()
    
    if args.action == "show":
        print(json.dumps(manager.config, indent=2, ensure_ascii=False))
    
    elif args.action == "get":
        if not args.key:
            print(f"{Fore.RED}❌ يجب تحديد المفتاح باستخدام --key{Style.RESET_ALL}")
            sys.exit(1)
        
        value = manager.get_value(args.key)
        print(f"{Fore.CYAN}{args.key}: {value}{Style.RESET_ALL}")
    
    elif args.action == "set":
        if not args.key or not args.value:
            print(f"{Fore.RED}❌ يجب تحديد المفتاح والقيمة باستخدام --key و --value{Style.RESET_ALL}")
            sys.exit(1)
        
        # محاولة تحويل القيمة إلى النوع المناسب
        try:
            if args.value.lower() in ["true", "false"]:
                value = args.value.lower() == "true"
            elif args.value.isdigit():
                value = int(args.value)
            elif args.value.replace('.', '', 1).isdigit():
                value = float(args.value)
            else:
                value = args.value
        except:
            value = args.value
        
        manager.set_value(args.key, value)
    
    elif args.action == "enable":
        if not args.module:
            print(f"{Fore.RED}❌ يجب تحديد الموديول باستخدام --module{Style.RESET_ALL}")
            sys.exit(1)
        
        manager.enable_module(args.module)
    
    elif args.action == "disable":
        if not args.module:
            print(f"{Fore.RED}❌ يجب تحديد الموديول باستخدام --module{Style.RESET_ALL}")
            sys.exit(1)
        
        manager.disable_module(args.module)
    
    elif args.action == "list":
        modules = manager.list_modules()
        for module in modules:
            status = "✅ مفعل" if module["enabled"] else "❌ معطل"
            print(f"{status} {module['name']}: {module['description']}")
    
    elif args.action == "validate":
        issues = manager.validate_config()
        
        if issues["errors"]:
            print(f"{Fore.RED}❌ أخطاء:{Style.RESET_ALL}")
            for error in issues["errors"]:
                print(f"  • {error}")
        
        if issues["warnings"]:
            print(f"{Fore.YELLOW}⚠️  تحذيرات:{Style.RESET_ALL}")
            for warning in issues["warnings"]:
                print(f"  • {warning}")
        
        if not issues["errors"] and not issues["warnings"]:
            print(f"{Fore.GREEN}✅ جميع الإعدادات صحيحة{Style.RESET_ALL}")
    
    elif args.action == "export":
        output_file = args.file or f"config_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.format}"
        manager.export_config(args.format, output_file)
    
    elif args.action == "import":
        if not args.file:
            print(f"{Fore.RED}❌ يجب تحديد ملف الاستيراد باستخدام --file{Style.RESET_ALL}")
            sys.exit(1)
        
        manager.import_config(args.file, args.merge)
    
    elif args.action == "summary":
        manager.show_summary()
    
    else:
        print(f"{Fore.RED}❌ إجراء غير م��روف: {args.action}{Style.RESET_ALL}")

if __name__ == "__main__":
    import argparse
    
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⏹️  تم إلغاء العملية{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}❌ خطأ غير متوقع: {e}{Style.RESET_ALL}")
        sys.exit(1)