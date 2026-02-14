# KNOUX OS Guardian
## نظام الحماية والذكاء المدمج على مستوى نظام التشغيل

### 🎯 نظرة عامة
KNOUX OS Guardian هو نظام ذكاء اصطناعي مدمج على مستوى Windows، مصمم لإدارة صحة النظام بشكل استباقي وآمن.

### ✨ المميزات الرئيسية
- ✅ **Offline-First**: يعمل بالكامل دون اتصال بالإنترنت
- 🛡️ **Zero Trust Execution**: كل عملية تتطلب تأكيد وآلية rollback
- 🧠 **Explainable AI**: كل قرار مدعوم بتفسير واضح
- 🔒 **Privacy by Design**: لا جمع بيانات بدون موافقة صريحة

### 📦 الوحدات الأساسية (12 Modules)
1. **Disk Space Orchestrator** - إدارة المساحة التخزينية
2. **Update Guardian** - إدارة التحديثات الذكية
3. **Performance Optimizer** - تحسين الأداء
4. **Network Monitor** - مراقبة الشبكة
5. **Security Hardener** - تعزيز الأمان
6. **Driver Health Manager** - إدارة التعريفات
7. **Forensic Analyzer** - التحليل الجنائي
8. **Thermal Controller** - إدارة الحرارة
9. **Power Manager** - إدارة الطاقة
10. **Application Lifecycle Curator** - إدارة التطبيقات
11. **Registry Guardian** - حماية السجل
12. **Backup Orchestrator** - إدارة النسخ الاحتياطي

### 🚀 التثبيت والتشغيل

#### الطريقة السريعة (Windows)
```powershell
# تشغيل مباشر
run.bat

# أو اختبار النظام أولاً
test.bat
```

#### الطريقة اليدوية
```powershell
# 1. تثبيت المكتبات
pip install -r requirements.txt

# 2. اختبار النظام
python test_basic.py

# 3. تشغيل النظام
python main.py
```

📖 **للمزيد**: راجع [دليل التثبيت](INSTALLATION.md) و [دليل البدء السريع](QUICKSTART.md)

### 📁 البنية الهيكلية
```
KNOUX_OS_Guardian/
├── src/
│   ├── core/              # البنية التحتية الأساسية
│   │   ├── decision_engine/
│   │   ├── communication_bus/
│   │   ├── safe_execution/
│   │   └── telemetry/
│   └── modules/           # الوحدات الـ 12
├── models/                # نماذج ONNX
├── database/              # قاعدة بيانات SQLite
├── config/                # ملفات الإعدادات
├── data/                  # البيانات والسجلات
├── tests/                 # الاختبارات
└── docs/                  # التوثيق
```

### 🔧 التقنيات المستخدمة
- **Language**: Python 3.11+
- **ML Runtime**: ONNX Runtime
- **Database**: SQLite
- **OS Integration**: WMI, PowerShell, Win32 APIs

### 📝 الترخيص
Proprietary - KNOUX OS Guardian © 2026

### 👥 المطور
KNOUX Team
