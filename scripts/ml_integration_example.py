#!/usr/bin/env python3
"""
KNOUX OS Guardian - مثال تكامل نماذج التعلم الآلي
يوضح كيفية دمج نماذج ONNX في نظام KNOUX OS Guardian
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
import onnxruntime as ort

class MLModelManager:
    """مدير نماذج التعلم الآلي للتكامل مع النظام"""
    
    def __init__(self, models_dir: str = "models/onnx"):
        self.models_dir = Path(models_dir)
        self.models = {}
        self.metadata = self._load_metadata()
        
    def _load_metadata(self) -> Dict:
        """تحميل بيانات النماذج"""
        metadata_file = self.models_dir / "models_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"models": {}, "version": "1.0.0"}
    
    def load_model(self, model_name: str) -> bool:
        """تحميل نموذج ONNX"""
        model_path = self.models_dir / f"{model_name}.onnx"
        
        if not model_path.exists():
            print(f"❌ النموذج غير موجود: {model_name}")
            return False
        
        try:
            # تكوين جلسة ONNX Runtime
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            
            # تحميل النموذج
            session = ort.InferenceSession(
                str(model_path),
                session_options,
                providers=['CPUExecutionProvider']  # استخدام CPU فقط للخصوصية
            )
            
            self.models[model_name] = {
                "session": session,
                "input_name": session.get_inputs()[0].name,
                "output_name": session.get_outputs()[0].name,
                "input_shape": session.get_inputs()[0].shape,
                "output_shape": session.get_outputs()[0].shape,
                "path": str(model_path)
            }
            
            print(f"✅ تم تحميل النموذج: {model_name}")
            print(f"   📥 الإدخال: {self.models[model_name]['input_shape']}")
            print(f"   📤 الإخراج: {self.models[model_name]['output_shape']}")
            
            return True
            
        except Exception as e:
            print(f"❌ فشل تحميل النموذج {model_name}: {e}")
            return False
    
    def predict_disk_usage(self, disk_metrics: Dict) -> Dict:
        """التنبؤ باستخدام مساحة التخزين"""
        if "disk_usage_predictor" not in self.models:
            if not self.load_model("disk_usage_predictor"):
                return self._fallback_disk_prediction(disk_metrics)
        
        try:
            # تحضير بيانات الإدخال
            input_data = self._prepare_disk_input(disk_metrics)
            
            # التنبؤ
            session = self.models["disk_usage_predictor"]["session"]
            input_name = self.models["disk_usage_predictor"]["input_name"]
            output_name = self.models["disk_usage_predictor"]["output_name"]
            
            result = session.run([output_name], {input_name: input_data})
            prediction = result[0][0]
            
            # تفسير النتائج
            return self._interpret_disk_prediction(prediction, disk_metrics)
            
        except Exception as e:
            print(f"❌ خطأ في التنبؤ بمساحة التخزين: {e}")
            return self._fallback_disk_prediction(disk_metrics)
    
    def _prepare_disk_input(self, disk_metrics: Dict) -> np.ndarray:
        """تحضير بيانات إدخال مساحة التخزين"""
        # بيانات عينة (يجب استبدالها ببيانات حقيقية)
        features = [
            disk_metrics.get("free_percent", 50.0) / 100.0,
            disk_metrics.get("used_gb", 100.0) / 500.0,
            disk_metrics.get("read_speed_mbps", 100.0) / 1000.0,
            disk_metrics.get("write_speed_mbps", 50.0) / 1000.0,
            disk_metrics.get("fragmentation", 10.0) / 100.0,
            disk_metrics.get("age_days", 365.0) / 1000.0,
            disk_metrics.get("file_count", 10000.0) / 100000.0,
            disk_metrics.get("temp_files_gb", 5.0) / 50.0,
            disk_metrics.get("cache_size_gb", 2.0) / 20.0,
            disk_metrics.get("io_errors", 0.0) / 100.0
        ]
        
        return np.array([features], dtype=np.float32)
    
    def _interpret_disk_prediction(self, prediction: np.ndarray, disk_metrics: Dict) -> Dict:
        """تفسير نتائج التنبؤ بمساحة التخزين"""
        # prediction[0]: احتمال النفاد خلال 7 أيام
        # prediction[1]: احتمال النفاد خلال 30 يومًا
        # prediction[2]: مستوى الخطورة (0-1)
        
        risk_7_days = float(prediction[0]) * 100
        risk_30_days = float(prediction[1]) * 100
        severity_score = float(prediction[2])
        
        # تحديد مستوى الخطورة
        if severity_score > 0.8:
            severity = "حرج"
            action = "تنظيف فوري مطلوب"
        elif severity_score > 0.6:
            severity = "عالي"
            action = "تنظيف خلال 24 ساعة"
        elif severity_score > 0.4:
            severity = "متوسط"
            action = "مراقبة وتنظيف مخطط"
        else:
            severity = "منخفض"
            action = "مراقبة روتينية"
        
        return {
            "module": "DiskSpaceOrchestrator",
            "prediction": {
                "risk_7_days_percent": round(risk_7_days, 1),
                "risk_30_days_percent": round(risk_30_days, 1),
                "severity_score": round(severity_score, 3),
                "severity_level": severity,
                "recommended_action": action
            },
            "metrics_used": list(disk_metrics.keys()),
            "model_version": self.metadata.get("models", {}).get("disk_usage_predictor", {}).get("version", "1.0.0"),
            "confidence": round(min(risk_7_days, risk_30_days) / 100, 3)
        }
    
    def _fallback_disk_prediction(self, disk_metrics: Dict) -> Dict:
        """تنبؤ احتياطي (عند عدم وجود نموذج)"""
        free_percent = disk_metrics.get("free_percent", 50.0)
        
        if free_percent < 10:
            severity = "حرج"
            risk = 95.0
        elif free_percent < 20:
            severity = "عالي"
            risk = 75.0
        elif free_percent < 30:
            severity = "متوسط"
            risk = 50.0
        else:
            severity = "منخفض"
            risk = 25.0
        
        return {
            "module": "DiskSpaceOrchestrator",
            "prediction": {
                "risk_7_days_percent": risk,
                "risk_30_days_percent": risk * 1.2,
                "severity_score": (100 - free_percent) / 100,
                "severity_level": severity,
                "recommended_action": f"المساحة الحرة: {free_percent}%",
                "is_fallback": True
            },
            "metrics_used": ["free_percent"],
            "model_version": "fallback-1.0",
            "confidence": 0.7
        }
    
    def predict_performance_anomaly(self, performance_metrics: Dict) -> Dict:
        """كشف الشذوذ في الأداء"""
        if "performance_anomaly_detector" not in self.models:
            if not self.load_model("performance_anomaly_detector"):
                return self._fallback_performance_prediction(performance_metrics)
        
        try:
            # تحضير بيانات الإدخال
            input_data = self._prepare_performance_input(performance_metrics)
            
            # التنبؤ
            session = self.models["performance_anomaly_detector"]["session"]
            input_name = self.models["performance_anomaly_detector"]["input_name"]
            output_name = self.models["performance_anomaly_detector"]["output_name"]
            
            result = session.run([output_name], {input_name: input_data})
            prediction = result[0][0]
            
            # تفسير النتائج
            return self._interpret_performance_prediction(prediction, performance_metrics)
            
        except Exception as e:
            print(f"❌ خطأ في كشف شذوذ الأداء: {e}")
            return self._fallback_performance_prediction(performance_metrics)
    
    def _prepare_performance_input(self, metrics: Dict) -> np.ndarray:
        """تحضير بيانات إدخال الأداء"""
        features = [
            metrics.get("cpu_usage", 50.0) / 100.0,
            metrics.get("memory_usage", 60.0) / 100.0,
            metrics.get("disk_usage", 70.0) / 100.0,
            metrics.get("network_usage", 30.0) / 100.0,
            metrics.get("response_time_ms", 100.0) / 1000.0,
            metrics.get("process_count", 100.0) / 500.0,
            metrics.get("thread_count", 1500.0) / 10000.0,
            metrics.get("handle_count", 50000.0) / 200000.0,
            metrics.get("uptime_hours", 24.0) / 720.0,
            metrics.get("temperature_c", 60.0) / 100.0
        ]
        
        return np.array([features], dtype=np.float32)
    
    def _interpret_performance_prediction(self, prediction: np.ndarray, metrics: Dict) -> Dict:
        """تفسير نتائج كشف شذوذ الأداء"""
        # prediction[0]: احتمال وجود شذوذ
        # prediction[1]: نوع الشذوذ (0: طبيعي، 1: ذاكرة، 2: معالج، 3: قرص)
        
        anomaly_prob = float(prediction[0]) * 100
        anomaly_type = int(prediction[1])
        
        anomaly_types = {
            0: "طبيعي",
            1: "مشكلة في الذاكرة",
            2: "مشكلة في المعالج",
            3: "مشكلة في القرص",
            4: "مشكلة في الشبكة"
        }
        
        anomaly_name = anomaly_types.get(anomaly_type, "غير معروف")
        
        if anomaly_prob > 80:
            severity = "حرج"
            action = "تدخل فوري مطلوب"
        elif anomaly_prob > 60:
            severity = "عالي"
            action = "تحقيق وتدخل"
        elif anomaly_prob > 40:
            severity = "متوسط"
            action = "مراقبة مكثفة"
        else:
            severity = "منخفض"
            action = "مراقبة روتينية"
        
        return {
            "module": "PerformanceOptimizer",
            "prediction": {
                "anomaly_probability_percent": round(anomaly_prob, 1),
                "anomaly_type": anomaly_name,
                "anomaly_type_code": anomaly_type,
                "severity_level": severity,
                "recommended_action": action,
                "affected_component": anomaly_name.split()[-1] if anomaly_name != "طبيعي" else "لا شيء"
            },
            "metrics_used": list(metrics.keys()),
            "model_version": self.metadata.get("models", {}).get("performance_anomaly_detector", {}).get("version", "1.0.0"),
            "confidence": round(anomaly_prob / 100, 3)
        }
    
    def _fallback_performance_prediction(self, metrics: Dict) -> Dict:
        """كشف احتياطي للأداء"""
        cpu_usage = metrics.get("cpu_usage", 50.0)
        memory_usage = metrics.get("memory_usage", 60.0)
        
        max_usage = max(cpu_usage, memory_usage)
        
        if max_usage > 90:
            severity = "حرج"
            anomaly_prob = 90.0
            anomaly_type = "مشكلة في الموارد"
        elif max_usage > 80:
            severity = "عالي"
            anomaly_prob = 70.0
            anomaly_type = "ارتفاع في الاستخدام"
        elif max_usage > 70:
            severity = "متوسط"
            anomaly_prob = 50.0
            anomaly_type = "استخدام مرتفع"
        else:
            severity = "منخفض"
            anomaly_prob = 30.0
            anomaly_type = "طبيعي"
        
        return {
            "module": "PerformanceOptimizer",
            "prediction": {
                "anomaly_probability_percent": anomaly_prob,
                "anomaly_type": anomaly_type,
                "severity_level": severity,
                "recommended_action": f"الاستخدام الأعلى: {max_usage}%",
                "is_fallback": True
            },
            "metrics_used": ["cpu_usage", "memory_usage"],
            "model_version": "fallback-1.0",
            "confidence": 0.6
        }
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """الحصول على معلومات النموذج"""
        if model_name in self.models:
            model = self.models[model_name]
            return {
                "name": model_name,
                "input_shape": model["input_shape"],
                "output_shape": model["output_shape"],
                "path": model["path"],
                "loaded": True
            }
        elif model_name in self.metadata.get("models", {}):
            return {
                "name": model_name,
                "metadata": self.metadata["models"][model_name],
                "loaded": False
            }
        return None
    
    def list_loaded_models(self) -> List[str]:
        """عرض قائمة النماذج المحملة"""
        return list(self.models.keys())

def example_usage():
    """مثال على استخدام مدير النماذج"""
    print("🔧 مثال تكامل نماذج التعلم الآلي")
    print("=" * 60)
    
    # إنشاء مدير النماذج
    manager = MLModelManager()
    
    # تحميل النماذج
    print("\n📥 تحميل النماذج...")
    manager.load_model("disk_usage_predictor")
    manager.load_model("performance_anomaly_detector")
    
    # مثال 1: التنبؤ بمساحة التخزين
    print("\n💾 مثال التنبؤ بمساحة التخزين:")
    disk_metrics = {
        "free_percent": 15.5,
        "used_gb": 425.0,
        "read_speed_mbps": 120.5,
        "write_speed_mbps": 45.2,
        "fragmentation": 25.3,
        "age_days": 180,
        "file_count": 25000,
        "temp_files_gb": 8.7,
        "cache_size_gb": 3.2,
        "io_errors": 2
    }
    
    disk_prediction = manager.predict_disk_usage(disk_metrics)
    print(json.dumps(disk_prediction, indent=2, ensure_ascii=False))
    
    # مثال 2: كشف شذوذ الأداء
    print("\n⚡ مثال كشف شذوذ الأداء:")
    performance_metrics = {
        "cpu_usage": 92.5,
        "memory_usage": 85.3,
        "disk_usage": 65.7,
        "network_usage": 42.1,
        "response_time_ms": 250.8,
        "process_count": 156,
        "thread_count": 2345,
        "handle_count": 87543,
        "uptime_hours": 168,
        "temperature_c": 72.5
    }
    
    performance_prediction = manager.predict_performance_anomaly(performance_metrics)
    print(json.dumps(performance_prediction, indent=2, ensure_ascii=False))
    
    # عرض معلومات النماذج
    print("\n📋 معلومات النماذج المحملة:")
    for model_name in manager.list_loaded_models():
        info = manager.get_model_info(model_name)
        if info:
            print(f"  • {model_name}:")
            print(f"    الإدخال: {info['input_shape']}")
            print(f"    الإخراج: {info['output_shape']}")
    
    print("\n✅ اكتمل مثال التكامل")

if __name__ == "__main__":
    # تغيير المسار إلى مجلد المشروع
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    try:
        example_usage()
    except Exception as e:
        print(f"❌ خطأ في تشغيل المثال: {e}")
        sys.exit(1)