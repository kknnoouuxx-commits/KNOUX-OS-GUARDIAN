#!/usr/bin/env python3
"""
KNOUX OS Guardian - ML Model Management Script
إدارة نماذج التعلم الآلي للنظام
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

class ModelManager:
    """مدير نماذج التعلم الآلي"""
    
    def __init__(self, models_dir: str = "models/onnx"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.models_dir / "models_metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """تحميل بيانات النماذج"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "models": {},
                "last_updated": None,
                "version": "1.0.0"
            }
    
    def _save_metadata(self):
        """حفظ بيانات النماذج"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """حساب بصمة الملف"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def list_models(self) -> List[Dict]:
        """عرض قائمة النماذج المتاحة"""
        print("📋 قائمة نماذج التعلم الآلي:")
        print("-" * 60)
        
        models = []
        for model_file in self.models_dir.glob("*.onnx"):
            model_info = {
                "name": model_file.stem,
                "path": str(model_file),
                "size_mb": model_file.stat().st_size / (1024 * 1024),
                "hash": self.calculate_file_hash(model_file)[:16]
            }
            
            # إضافة معلومات من البيانات الوصفية
            if model_file.stem in self.metadata.get("models", {}):
                meta_info = self.metadata["models"][model_file.stem]
                model_info.update({
                    "description": meta_info.get("description", "غير معروف"),
                    "version": meta_info.get("version", "1.0.0"),
                    "accuracy": meta_info.get("accuracy", "غير معروف"),
                    "input_shape": meta_info.get("input_shape", "غير معروف")
                })
            
            models.append(model_info)
        
        if not models:
            print("❌ لا توجد نماذج متاحة")
            return []
        
        for i, model in enumerate(models, 1):
            print(f"{i}. {model['name']}")
            print(f"   📁 المسار: {model['path']}")
            print(f"   📊 الحجم: {model['size_mb']:.2f} MB")
            print(f"   🔑 البصمة: {model['hash']}")
            if 'description' in model:
                print(f"   📝 الوصف: {model['description']}")
            if 'accuracy' in model:
                print(f"   🎯 الدقة: {model['accuracy']}")
            print()
        
        return models
    
    def register_model(self, model_path: str, metadata: Optional[Dict] = None):
        """تسجيل نموذج جديد"""
        source_path = Path(model_path)
        if not source_path.exists():
            print(f"❌ الملف غير موجود: {model_path}")
            return False
        
        if source_path.suffix != ".onnx":
            print(f"❌ الملف يجب أن يكون بصيغة ONNX: {model_path}")
            return False
        
        dest_path = self.models_dir / source_path.name
        
        try:
            # نسخ الملف
            shutil.copy2(source_path, dest_path)
            print(f"✅ تم نسخ النموذج إلى: {dest_path}")
            
            # تحديث البيانات الوصفية
            model_name = source_path.stem
            file_hash = self.calculate_file_hash(dest_path)
            
            if metadata is None:
                metadata = {}
            
            model_metadata = {
                "original_path": str(source_path),
                "file_hash": file_hash,
                "size_bytes": dest_path.stat().st_size,
                "registered_at": str(datetime.now().isoformat()),
                **metadata
            }
            
            self.metadata["models"][model_name] = model_metadata
            self.metadata["last_updated"] = str(datetime.now().isoformat())
            self._save_metadata()
            
            print(f"✅ تم تسجيل النموذج: {model_name}")
            print(f"   🔑 البصمة: {file_hash[:16]}...")
            print(f"   📊 الحجم: {model_metadata['size_bytes'] / (1024*1024):.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ فشل تسجيل النموذج: {e}")
            return False
    
    def validate_models(self) -> Dict[str, bool]:
        """التحقق من سلامة النماذج"""
        print("🔍 التحقق من سلامة النماذج...")
        
        validation_results = {}
        for model_name, model_info in self.metadata.get("models", {}).items():
            model_path = self.models_dir / f"{model_name}.onnx"
            
            if not model_path.exists():
                print(f"❌ النموذج غير موجود: {model_name}")
                validation_results[model_name] = False
                continue
            
            # حساب البصمة والتحقق منها
            current_hash = self.calculate_file_hash(model_path)
            stored_hash = model_info.get("file_hash")
            
            if current_hash != stored_hash:
                print(f"❌ بصمة النموذج غير متطابقة: {model_name}")
                print(f"   البصمة الحالية: {current_hash[:16]}...")
                print(f"   البصمة المخزنة: {stored_hash[:16]}...")
                validation_results[model_name] = False
            else:
                print(f"✅ النموذج سليم: {model_name}")
                validation_results[model_name] = True
        
        return validation_results
    
    def create_sample_models(self):
        """إنشاء نماذج عينة (لأغراض التطوير)"""
        print("🛠️  إنشاء نماذج عينة...")
        
        sample_models = {
            "disk_usage_predictor": {
                "description": "تنبؤ استخدام مساحة التخزين",
                "input_shape": "[1, 10]",
                "output_shape": "[1, 3]",
                "accuracy": "92.5%",
                "purpose": "التنبؤ بمساحة التخزين المتبقية"
            },
            "performance_anomaly_detector": {
                "description": "كشف الشذوذ في الأداء",
                "input_shape": "[1, 20]",
                "output_shape": "[1, 2]",
                "accuracy": "88.3%",
                "purpose": "كشف مشاكل الأداء"
            },
            "thermal_threshold_predictor": {
                "description": "تنبؤ درجات الحرارة الحرجة",
                "input_shape": "[1, 8]",
                "output_shape": "[1, 1]",
                "accuracy": "95.1%",
                "purpose": "التنبؤ بارتفاع درجة الحرارة"
            },
            "update_risk_predictor": {
                "description": "تقييم مخاطر التحديثات",
                "input_shape": "[1, 15]",
                "output_shape": "[1, 4]",
                "accuracy": "90.2%",
                "purpose": "تقييم مخاطر تحديثات النظام"
            }
        }
        
        for model_name, metadata in sample_models.items():
            # إنشاء ملف ONNX عينة (فارغ)
            sample_path = self.models_dir / f"{model_name}.onnx"
            
            # في بيئة حقيقية، سيتم تحميل النماذج الحقيقية
            # هنا ننشئ ملفات عينة لأغراض التطوير
            with open(sample_path, 'wb') as f:
                # كتابة رأس ONNX بسيط (لأغراض التوضيح فقط)
                f.write(b"ONNX_SAMPLE_MODEL_" + model_name.encode())
            
            # تسجيل النموذج
            self.register_model(str(sample_path), metadata)
        
        print("✅ تم إنشاء النماذج العينة")
    
    def cleanup_orphaned_models(self):
        """تنظيف النماذج غير المسجلة"""
        print("🧹 تنظيف النماذج غير المسجلة...")
        
        registered_models = set(self.metadata.get("models", {}).keys())
        existing_models = {f.stem for f in self.models_dir.glob("*.onnx")}
        
        orphaned_models = existing_models - registered_models
        
        if not orphaned_models:
            print("✅ لا توجد نماذج غير مسجلة")
            return
        
        for model_name in orphaned_models:
            model_path = self.models_dir / f"{model_name}.onnx"
            try:
                model_path.unlink()
                print(f"🗑️  تم حذف النموذج غير المسجل: {model_name}")
            except Exception as e:
                print(f"❌ فشل حذف النموذج {model_name}: {e}")

def main():
    """الدالة الرئيسية"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="إدارة نماذج التعلم الآلي")
    parser.add_argument("action", choices=["list", "register", "validate", "create-samples", "cleanup"],
                       help="الإجراء المطلوب")
    parser.add_argument("--model", help="مسار النموذج (للتسجيل)")
    parser.add_argument("--name", help="اسم النموذج (اختياري)")
    
    args = parser.parse_args()
    
    manager = ModelManager()
    
    if args.action == "list":
        manager.list_models()
    
    elif args.action == "register":
        if not args.model:
            print("❌ يجب تحديد مسار النموذج باستخدام --model")
            sys.exit(1)
        
        metadata = {}
        if args.name:
            metadata["custom_name"] = args.name
        
        manager.register_model(args.model, metadata)
    
    elif args.action == "validate":
        results = manager.validate_models()
        valid_count = sum(results.values())
        total_count = len(results)
        
        print(f"\n📊 النتائج: {valid_count}/{total_count} نماذج سليمة")
    
    elif args.action == "create-samples":
        manager.create_sample_models()
    
    elif args.action == "cleanup":
        manager.cleanup_orphaned_models()
    
    else:
        print(f"❌ إجراء غير معروف: {args.action}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ تم إلغاء العملية")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ خطأ غير متوقع: {e}")
        sys.exit(1)