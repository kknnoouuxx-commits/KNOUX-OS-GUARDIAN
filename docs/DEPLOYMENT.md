# KNOUX OS Guardian - دليل النشر

## نظرة عامة
دليل شامل لنشر نظام KNOUX OS Guardian في بيئات مختلفة.

---

## متطلبات النظام

### الحد الأدنى
- **نظام التشغيل:** Windows 10/11 (64-bit)
- **المعالج:** Intel Core i3 أو ما يعادله
- **الذاكرة:** 4 GB RAM
- **التخزين:** 2 GB مساحة حرة
- **Python:** 3.11 أو أعلى

### الموصى به
- **نظام التشغيل:** Windows 11 (64-bit)
- **المعالج:** Intel Core i5 أو أعلى
- **الذاكرة:** 8 GB RAM
- **التخزين:** 5 GB مساحة حرة (SSD)
- **Python:** 3.11 أو أعلى

---

## خطوات التثبيت

### 1. تحضير البيئة

#### تثبيت Python
```powershell
# تحميل Python 3.11+ من python.org
# أو استخدام winget
winget install Python.Python.3.11

# التحقق من التثبيت
python --version
```

#### تثبيت Git (اختياري)
```powershell
winget install Git.Git
```

### 2. تحميل المشروع

#### من Git
```powershell
git clone https://github.com/your-org/knoux-os-guardian.git
cd knoux-os-guardian
```

#### من ملف مضغوط
```powershell
# فك الضغط إلى مجلد
cd C:\KNOUX_OS_Guardian
```

### 3. إعداد البيئة الافتراضية

```powershell
# إنشاء بيئة افتراضية
python -m venv venv

# تفعيل البيئة الافتراضية
.\venv\Scripts\activate

# تحديث pip
python -m pip install --upgrade pip
```

### 4. تثبيت المكتبات

```powershell
# تثبيت المكتبات المطلوبة
pip install -r requirements.txt

# التحقق من التثبيت
pip list
```

### 5. إعداد الإعدادات

```powershell
# نسخ ملف الإعدادات الافتراضي (إذا لزم الأمر)
# الملف موجود في config/config.yaml

# تعديل الإعدادات حسب الحاجة
notepad config\config.yaml
```

### 6. تشغيل الاختبارات

```powershell
# اختبار أساسي
python test_basic.py

# اختبار جميع الموديولات
python test_all_modules.py

# اختبارات شاملة
python scripts\run_tests.py --types all
```

### 7. التشغيل الأول

```powershell
# تشغيل النظام
python main.py

# أو استخدام السكريبت السريع
.\run.bat
```

---

## نشر API

### 1. إعداد API

```powershell
# الانتقال إلى مجلد API
cd api

# تثبيت المكتبات الإضافية
pip install -r requirements.txt
```

### 2. تشغيل API (التطوير)

```powershell
# تشغيل مباشر
python main.py

# أو استخدام uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. تشغيل API (الإنتاج)

#### استخدام Uvicorn
```powershell
# تثبيت uvicorn مع workers
pip install uvicorn[standard]

# تشغيل مع عدة workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### استخدام Gunicorn (على Linux)
```bash
# تثبيت gunicorn
pip install gunicorn

# تشغيل
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 4. إعداد كخدمة Windows

#### إنشاء ملف خدمة
```powershell
# استخدام NSSM (Non-Sucking Service Manager)
# تحميل من: https://nssm.cc/download

# تثبيت الخدمة
nssm install KnouxOSGuardianAPI "C:\KNOUX_OS_Guardian\venv\Scripts\python.exe" "C:\KNOUX_OS_Guardian\api\main.py"

# تكوين الخدمة
nssm set KnouxOSGuardianAPI AppDirectory "C:\KNOUX_OS_Guardian\api"
nssm set KnouxOSGuardianAPI DisplayName "KNOUX OS Guardian API"
nssm set KnouxOSGuardianAPI Description "REST API for KNOUX OS Guardian"
nssm set KnouxOSGuardianAPI Start SERVICE_AUTO_START

# بدء الخدمة
nssm start KnouxOSGuardianAPI
```

---

## إعداد قاعدة البيانات

### 1. إنشاء قاعدة البيانات

```powershell
# قاعدة البيانات تُنشأ تلقائيًا عند التشغيل الأول
# الموقع: database/knoux_guardian.db
```

### 2. النسخ الاحتياطي

```powershell
# نسخ احتياطي يدوي
copy database\knoux_guardian.db database\backups\knoux_guardian_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db

# أو استخدام سكريبت
python scripts\backup_database.py
```

### 3. الاستعادة

```powershell
# إيقاف النظام أولاً
# ثم استعادة من نسخة احتياطية
copy database\backups\knoux_guardian_backup_20260212.db database\knoux_guardian.db
```

---

## إعداد نماذج ML

### 1. تحميل النماذج

```powershell
# إذا كانت النماذج متوفرة
# نسخها إلى models/onnx/

# أو إنشاء نماذج عينة للتطوير
python scripts\manage_models.py create-samples
```

### 2. التحقق من النماذج

```powershell
# عرض النماذج المتاحة
python scripts\manage_models.py list

# التحقق من سلامة النماذج
python scripts\manage_models.py validate
```

### 3. تسجيل نموذج جديد

```powershell
# تسجيل نموذج
python scripts\manage_models.py register --model path\to\model.onnx
```

---

## التكوين المتقدم

### 1. إعدادات الأداء

```yaml
# في config/config.yaml
system:
  max_workers: 4
  cache_size_mb: 512
  log_level: INFO
```

### 2. إعدادات الأمان

```yaml
api:
  auth_required: true
  jwt_secret_key: "your-secret-key-here"  # غيّر هذا!
  cors_enabled: false  # عطّل في الإنتاج
  allowed_origins: ["https://yourdomain.com"]
```

### 3. إعدادات الموديولات

```yaml
modules:
  disk_space_orchestrator:
    enabled: true
    scan_interval_minutes: 60
    cleanup_threshold_percent: 20
  
  network_monitor:
    enabled: true
    privacy_mode: strict
    log_suspicious: true
```

---

## المراقبة والصيانة

### 1. مراقبة السجلات

```powershell
# عرض السجلات الحية
Get-Content data\logs\knoux_guardian.log -Wait -Tail 50

# أو استخدام سكريبت المراقبة
python scripts\system_monitor.py monitor --interval 60 --duration 60
```

### 2. فحص الصحة

```powershell
# فحص صحة النظام
python scripts\project_status.py summary

# فحص صحة API
curl http://localhost:8000/api/v1/health
```

### 3. النسخ الاحتياطي التلقائي

```powershell
# إنشاء مهمة مجدولة للنسخ الاحتياطي
schtasks /create /tn "KNOUX Backup" /tr "python C:\KNOUX_OS_Guardian\scripts\backup_database.py" /sc daily /st 02:00
```

---

## استكشاف الأخطاء

### مشكلة: فشل تثبيت المكتبات

**الحل:**
```powershell
# تحديث pip
python -m pip install --upgrade pip

# تثبيت بناء الأدوات
pip install wheel setuptools

# إعادة المحاولة
pip install -r requirements.txt
```

### مشكلة: خطأ في الوصول إلى قاعدة البيانات

**الحل:**
```powershell
# التحقق من الصلاحيات
icacls database\knoux_guardian.db

# منح صلاحيات كاملة
icacls database\knoux_guardian.db /grant Users:F
```

### مشكلة: API لا يستجيب

**الحل:**
```powershell
# التحقق من المنفذ
netstat -ano | findstr :8000

# إيقاف العملية إذا لزم الأمر
taskkill /PID <process_id> /F

# إعادة التشغيل
python api\main.py
```

### مشكلة: استخدام عالي للذاكرة

**الحل:**
```yaml
# تقليل عدد الـ workers في config.yaml
system:
  max_workers: 2
  cache_size_mb: 256
```

---

## الأمان

### 1. تأمين API

```powershell
# تغيير مفتاح JWT
# في config/config.yaml أو متغيرات البيئة
$env:JWT_SECRET_KEY = "your-very-secure-random-key-here"
```

### 2. تشفير قاعدة البيانات

```powershell
# استخدام SQLCipher (اختياري)
pip install sqlcipher3

# تعديل الكود لاستخدام التشفير
```

### 3. جدار الحماية

```powershell
# السماح بـ API فقط من localhost
netsh advfirewall firewall add rule name="KNOUX API" dir=in action=allow protocol=TCP localport=8000 remoteip=127.0.0.1
```

---

## التحديثات

### 1. تحديث المكتبات

```powershell
# تحديث جميع المكتبات
pip install --upgrade -r requirements.txt

# أو تحديث مكتبة محددة
pip install --upgrade psutil
```

### 2. تحديث النظام

```powershell
# سحب آخر التحديثات (إذا كنت تستخدم Git)
git pull origin main

# تثبيت المكتبات الجديدة
pip install -r requirements.txt

# تشغيل الاختبارات
python test_basic.py
```

### 3. ترحيل قاعدة البيانات

```powershell
# إذا كانت هناك تغييرات في البنية
# سيتم التعامل معها تلقائيًا عند التشغيل
python main.py
```

---

## الأداء والتحسين

### 1. تحسين الأداء

```yaml
# في config/config.yaml
system:
  max_workers: 4  # حسب عدد الأنوية
  cache_size_mb: 1024  # زيادة الذاكرة المؤقتة
  
modules:
  # تقليل فترات المسح للموديولات غير الحرجة
  application_curator:
    scan_interval_days: 14  # بدلاً من 7
```

### 2. مراقبة الأداء

```powershell
# مراقبة استخدام الموارد
python scripts\system_monitor.py single

# تقرير الأداء
python scripts\project_status.py --save
```

---

## الإلغاء والإزالة

### 1. إيقاف الخدمات

```powershell
# إيقاف خدمة API
nssm stop KnouxOSGuardianAPI

# إزالة الخدمة
nssm remove KnouxOSGuardianAPI confirm
```

### 2. حفظ البيانات

```powershell
# نسخ احتياطي للبيانات المهمة
xcopy /E /I database database_backup
xcopy /E /I data\logs logs_backup
```

### 3. إزالة التثبيت

```powershell
# حذف البيئة الافتراضية
rmdir /S /Q venv

# حذف المجلد (بعد النسخ الاحتياطي)
cd ..
rmdir /S /Q KNOUX_OS_Guardian
```

---

## الدعم والمساعدة

### الموارد
- **الوثائق:** `docs/`
- **الأمثلة:** `examples/`
- **الاختبارات:** `tests/`

### الإبلاغ عن المشاكل
- افتح issue في GitHub
- أرفق السجلات من `data/logs/`
- صف الخطوات لإعادة إنتاج المشكلة

---

**آخر تحديث:** 2026-02-12  
**الإصدار:** 1.0.0