# دليل التثبيت والتشغيل
# KNOUX OS Guardian - Installation Guide

## المتطلبات الأساسية

### نظام التشغيل
- Windows 10/11 (64-bit)
- أو Linux (للتطوير)

### Python
- Python 3.11 أو أحدث
- pip (مدير الحزم)

## خطوات التثبيت

### 1. تثبيت Python
قم بتحميل Python من الموقع الرسمي:
```
https://www.python.org/downloads/
```

تأكد من تحديد خيار "Add Python to PATH" أثناء التثبيت.

### 2. تثبيت المكتبات المطلوبة

افتح PowerShell أو Command Prompt في مجلد المشروع:

```powershell
# الانتقال لمجلد المشروع
cd F:\KNOUX_OS_Guardian

# تثبيت المكتبات
pip install -r requirements.txt
```

### 3. التحقق من التثبيت

```powershell
# التحقق من نسخة Python
python --version

# التحقق من المكتبات المثبتة
pip list
```

## التشغيل

### تشغيل النظام

```powershell
# تشغيل النظام الأساسي
python main.py
```

### إيقاف النظام

اضغط `Ctrl+C` لإيقاف النظام بشكل آمن.

## الإعدادات

يمكنك تعديل الإعدادات من ملف:
```
config/config.yaml
```

### إعدادات مهمة:

```yaml
# تفعيل/تعطيل الموديولات
modules:
  disk_space_orchestrator:
    enabled: true
    auto_cleanup_enabled: false  # يتطلب موافقة المستخدم
  
  security_hardener:
    enabled: true
    auto_fix_critical: false  # يتطلب موافقة المستخدم

# التليمتري (معطل افتراضياً)
telemetry:
  enabled: false  # يجب تفعيله يدوياً
```

## البنية الأساسية

بعد التشغيل الأول، سيتم إنشاء المجلدات التالية:

```
KNOUX_OS_Guardian/
├── data/
│   ├── logs/              # سجلات النظام
│   └── snapshots/         # اللقطات الاحتياطية
├── database/              # قاعدة البيانات
│   └── knoux_guardian.db
└── models/                # نماذج ML (سيتم إضافتها لاحقاً)
```

## استكشاف الأخطاء

### خطأ: "Module not found"
```powershell
# تأكد من تثبيت جميع المكتبات
pip install -r requirements.txt --upgrade
```

### خطأ: "Permission denied"
```powershell
# قم بتشغيل PowerShell كمسؤول (Run as Administrator)
```

### خطأ في قاعدة البيانات
```powershell
# احذف قاعدة البيانات وسيتم إنشاؤها من جديد
del database\knoux_guardian.db
python main.py
```

## الخطوات التالية

1. ✅ تم إنشاء البنية الأساسية
2. ⏳ سيتم إضافة الموديولات الـ 12 تدريجياً
3. ⏳ سيتم إضافة نماذج ML
4. ⏳ سيتم إضافة واجهة المستخدم

## الدعم

للمساعدة أو الإبلاغ عن مشاكل، يرجى التواصل مع فريق KNOUX.

---
© 2026 KNOUX OS Guardian
