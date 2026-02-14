# دليل البدء السريع
# KNOUX OS Guardian - Quick Start Guide

## 🚀 البدء في 3 خطوات

### الخطوة 1: التثبيت
```powershell
# تثبيت المكتبات المطلوبة
pip install -r requirements.txt
```

### الخطوة 2: الاختبار
```powershell
# تشغيل الاختبارات الأساسية
python test_basic.py
```

أو استخدم:
```powershell
test.bat
```

### الخطوة 3: التشغيل
```powershell
# تشغيل النظام
python main.py
```

أو استخدم:
```powershell
run.bat
```

## ✅ ما تم إنجازه

تم إنشاء البنية الأساسية الكاملة لـ KNOUX OS Guardian:

### 1. المكونات الأساسية (Core Components)
- ✅ **Communication Bus** - نظام اتصال بين الموديولات
- ✅ **Decision Engine** - محرك اتخاذ القرارات
- ✅ **Safe Execution** - تنفيذ آمن مع snapshot/rollback
- ✅ **Telemetry** - جمع بيانات مجهولة (opt-in)
- ✅ **Config Manager** - إدارة الإعدادات
- ✅ **Database Manager** - قاعدة بيانات SQLite

### 2. البنية التحتية
```
KNOUX_OS_Guardian/
├── src/
│   ├── core/                    ✅ جاهز
│   │   ├── communication_bus/
│   │   ├── decision_engine/
│   │   ├── safe_execution/
│   │   ├── telemetry/
│   │   ├── config.py
│   │   └── database.py
│   └── modules/                 ⏳ سيتم إضافتها
├── config/
│   └── config.yaml              ✅ جاهز
├── database/                    ✅ جاهز
├── data/
│   ├── logs/                    ✅ جاهز
│   └── snapshots/               ✅ جاهز
├── models/                      ⏳ سيتم إضافتها
├── docs/                        ✅ جاهز
├── main.py                      ✅ جاهز
├── test_basic.py                ✅ جاهز
├── requirements.txt             ✅ جاهز
└── README.md                    ✅ جاهز
```

### 3. الوثائق
- ✅ `README.md` - نظرة عامة
- ✅ `INSTALLATION.md` - دليل التثبيت
- ✅ `ARCHITECTURE.md` - البنية المعمارية
- ✅ `STATUS.md` - حالة المشروع
- ✅ `QUICKSTART.md` - هذا الملف

## 🧪 الاختبار

عند تشغيل `test_basic.py`، ستحصل على:

```
============================================================
KNOUX OS Guardian - اختبارات أساسية
============================================================

🧪 اختبار الاستيراد...
   ✅ Communication Bus
   ✅ Decision Engine
   ✅ Safe Execution
   ✅ Telemetry
   ✅ Config Manager
   ✅ Database Manager

✅ جميع الاستيرادات نجحت!

🧪 اختبار نظام الإعدادات...
   ✅ Offline First: True
   ✅ Disk Module Enabled: True

✅ نظام الإعدادات يعمل!

🧪 اختبار قاعدة البيانات...
   ✅ تم إنشاء قاعدة البيانات
   ✅ تم تسجيل حدث اختباري

✅ قاعدة البيانات تعمل!

🧪 اختبار نظام اللقطات...
   ✅ تم إنشاء لقطة: [UUID]
   ✅ تم تنظيف اللقطات القديمة

✅ نظام اللقطات يعمل!

🧪 اختبار ناقل الاتصال...
   ✅ تم الاشتراك في حدث
   ✅ تم نشر حدث
   ✅ تم استقبال 1 حدث

✅ ناقل الاتصال يعمل!

============================================================
النتائج: ✅ 5 نجح | ❌ 0 فشل
============================================================
```

## 🎯 الخطوات التالية

### للمطورين:
1. إضافة الموديولات الـ 12 في `src/modules/`
2. تدريب وإضافة نماذج ML في `models/`
3. تطوير واجهة المستخدم

### للمستخدمين:
1. تعديل الإعدادات في `config/config.yaml`
2. تفعيل/تعطيل الموديولات حسب الحاجة
3. مراقبة السجلات في `data/logs/`

## 📚 الموارد

- **الوثيقة الهندسية الكاملة**: راجع الملف الأصلي للمواصفات التفصيلية
- **البنية المعمارية**: `docs/ARCHITECTURE.md`
- **حالة المشروع**: `STATUS.md`
- **دليل التثبيت**: `INSTALLATION.md`

## 🔧 الإعدادات المهمة

في `config/config.yaml`:

```yaml
# تفعيل/تعطيل الموديولات
modules:
  disk_space_orchestrator:
    enabled: true
    auto_cleanup_enabled: false  # يتطلب موافقة

# التليمتري (معطل افتراضياً)
telemetry:
  enabled: false  # يجب تفعيله يدوياً

# اللقطات الاحتياطية
snapshots:
  max_snapshots: 10
  snapshot_before_critical_actions: true
```

## 💡 نصائح

1. **الأمان أولاً**: جميع العمليات الحرجة تتطلب موافقة المستخدم
2. **Offline-First**: النظام يعمل بالكامل بدون إنترنت
3. **Snapshots**: يتم إنشاء لقطات احتياطية قبل أي تعديل
4. **الخصوصية**: لا جمع بيانات بدون موافقة صريحة

## 🆘 المساعدة

إذا واجهت مشاكل:

1. تحقق من السجلات في `data/logs/knoux_guardian.log`
2. راجع `INSTALLATION.md` لاستكشاف الأخطاء
3. تأكد من تثبيت جميع المكتبات المطلوبة

## 🎉 تهانينا!

لقد قمت بإعداد البنية الأساسية لـ KNOUX OS Guardian بنجاح!

النظام جاهز الآن لإضافة الموديولات والميزات المتقدمة.

---
© 2026 KNOUX OS Guardian
