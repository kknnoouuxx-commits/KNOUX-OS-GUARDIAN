#!/usr/bin/env python3
"""
KNOUX OS Guardian - Environment Setup Script
إعداد بيئة التشغيل للنظام
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """التحقق من إصدار Python"""
    print("🔍 التحقق من إصدار Python...")
    if sys.version_info < (3, 11):
        print(f"❌ إصدار Python الحالي: {sys.version_info.major}.{sys.version_info.minor}")
        print("⚠️  يتطلب النظام Python 3.11 أو أعلى")
        return False
    print(f"✅ إصدار Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_os():
    """التحقق من نظام التشغيل"""
    print("🔍 التحقق من نظام التشغيل...")
    system = platform.system()
    if system != "Windows":
        print(f"❌ نظام التشغيل الحالي: {system}")
        print("⚠️  النظام مصمم حصريًا لنظام Windows")
        return False
    print(f"✅ نظام التشغيل: Windows {platform.release()}")
    return True

def install_dependencies():
    """تثبيت المكتبات المطلوبة"""
    print("📦 تثبيت المكتبات المطلوبة...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ ملف requirements.txt غير موجود")
        return False
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ تم تثبيت المكتبات بنجاح")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ فشل تثبيت المكتبات: {e}")
        return False

def create_directories():
    """إنشاء المجلدات المطلوبة"""
    print("📁 إنشاء المجلدات المطلوبة...")
    
    directories = [
        "data/logs",
        "data/snapshots", 
        "database",
        "models/onnx",
        "models/training",
        "scripts",
        "tests/unit",
        "tests/integration"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ تم إنشاء: {directory}")
        else:
            print(f"  ⏭️  موجود مسبقًا: {directory}")
    
    return True

def setup_database():
    """إعداد قاعدة البيانات"""
    print("🗄️  إعداد قاعدة البيانات...")
    
    db_path = Path("database/knoux_guardian.db")
    if db_path.exists():
        print("  ⏭️  قاعدة البيانات موجودة مسبقًا")
        return True
    
    # سيتم إنشاء قاعدة البيانات تلقائيًا عند التشغيل الأول
    print("  ✅ سيتم إنشاء قاعدة البيانات عند التشغيل الأول")
    return True

def setup_configuration():
    """إعداد ملف الإعدادات"""
    print("⚙️  التحقق من ملف الإعدادات...")
    
    config_path = Path("config/config.yaml")
    if config_path.exists():
        print("  ✅ ملف الإعدادات موجود")
        return True
    
    print("  ⚠️  ملف الإعدادات غير موجود - سيتم إنشاؤه عند التشغيل الأول")
    return True

def run_basic_tests():
    """تشغيل الاختبارات الأساسية"""
    print("🧪 تشغيل الاختبارات الأساسية...")
    
    try:
        result = subprocess.run([sys.executable, "test_basic.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ جميع الاختبارات الأساسية ناجحة")
            return True
        else:
            print("❌ فشل بعض الاختبارات الأساسية")
            print(f"الإخراج: {result.stdout}")
            if result.stderr:
                print(f"الأخطاء: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ فشل تشغيل الاختبارات: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("KNOUX OS Guardian - إعداد بيئة التشغيل")
    print("=" * 60)
    
    # تغيير المسار إلى مجلد المشروع
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"📂 مجلد المشروع: {project_root}")
    
    # تنفيذ خطوات الإعداد
    steps = [
        ("التحقق من Python", check_python_version),
        ("التحقق من نظام التشغيل", check_os),
        ("إنشاء المجلدات", create_directories),
        ("تثبيت المكتبات", install_dependencies),
        ("إعداد قاعدة البيانات", setup_database),
        ("إعداد ملف الإعدادات", setup_configuration),
        ("تشغيل الاختبارات", run_basic_tests)
    ]
    
    results = []
    for step_name, step_func in steps:
        print(f"\n📋 الخطوة: {step_name}")
        result = step_func()
        results.append(result)
    
    # عرض النتائج النهائية
    print("\n" + "=" * 60)
    print("نتائج الإعداد")
    print("=" * 60)
    
    success_count = sum(results)
    total_steps = len(results)
    
    if success_count == total_steps:
        print("🎉 تم إعداد البيئة بنجاح!")
        print("\n📝 التعليمات التالية:")
        print("1. تشغيل النظام: python main.py")
        print("2. تشغيل الاختبارات: python test_basic.py")
        print("3. تشغيل سكريبت سريع: run.bat")
    else:
        print(f"⚠️  تم إكمال {success_count} من {total_steps} خطوات")
        print("\n🔧 خطوات استكشاف الأخطاء:")
        print("1. تأكد من تثبيت Python 3.11+")
        print("2. تأكد من صلاحيات الكتابة في المجلدات")
        print("3. جرب: pip install --upgrade pip")
        print("4. تحقق من اتصال الإنترنت لتثبيت المكتبات")
    
    return success_count == total_steps

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ تم إلغاء العملية")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ خطأ غير متوقع: {e}")
        sys.exit(1)