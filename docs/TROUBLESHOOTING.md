# KNOUX OS Guardian - دليل استكشاف الأخطاء

## نظرة عامة
دليل شامل لحل المشاكل الشائعة في نظام KNOUX OS Guardian.

---

## مشاكل التثبيت

### المشكلة: فشل تثبيت Python

**الأعراض:**
```
'python' is not recognized as an internal or external command
```

**الحلول:**
1. تأكد من تثبيت Python 3.11+
2. أضف Python إلى PATH:
   ```powershell
   # افتح System Properties > Environment Variables
   # أضف إلى Path: C:\Python311 و C:\Python311\Scripts
   ```
3. أعد تشغيل PowerShell/CMD
4. تحقق: `python --version`

---

### المشكلة: فشل تثبيت المكتبات

**الأعراض:**
```
ERROR: Could not build wheels for psutil
ERROR: Failed building wheel for pywin32
```

**الحلول:**

#### الحل 1: تحديث pip
```powershell
python -m pip install --upgrade pip setuptools wheel
```

#### الحل 2: تثبيت Visual C++ Build Tools
```powershell
# تحميل من:
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# أو استخدام winget
winget install Microsoft.VisualStudio.2022.BuildTools
```

#### الحل 3: تثبيت المكتبات واحدة تلو الأخرى
```powershell
pip install psutil
pip install pywin32
pip install pyyaml
# ... إلخ
```

#### الحل 4: استخدام ملفات wheel مسبقة البناء
```powershell
# تحميل من: https://www.lfd.uci.edu/~gohlke/pythonlibs/
pip install path\to\downloaded\wheel.whl
```

---

### المشكلة: خطأ في الصلاحيات

**الأعراض:**
```
PermissionError: [WinError 5] Access is denied
```

**الحلول:**
1. تشغيل PowerShell كمسؤول
2. تعطيل برنامج مكافحة الفيروسات مؤقتًا
3. التحقق من صلاحيات المجلد:
   ```powershell
   icacls C:\KNOUX_OS_Guardian /grant Users:F /T
   ```

---

## مشاكل التشغيل

### المشكلة: فشل بدء التشغيل

**الأعراض:**
```
ModuleNotFoundError: No module named 'src'
ImportError: cannot import name 'get_config'
```

**الحلول:**

#### الحل 1: التحقق من مسار العمل
```powershell
# تأكد من أنك في مجلد المشروع
cd C:\KNOUX_OS_Guardian
python main.py
```

#### الحل 2: إضافة المشروع إلى PYTHONPATH
```powershell
$env:PYTHONPATH = "C:\KNOUX_OS_Guardian"
python main.py
```

#### الحل 3: تفعيل البيئة الافتراضية
```powershell
.\venv\Scripts\activate
python main.py
```

---

### المشكلة: خطأ في قاعدة البيانات

**الأعراض:**
```
sqlite3.OperationalError: unable to open database file
sqlite3.DatabaseError: database disk image is malformed
```

**الحلول:**

#### الحل 1: إنشاء مجلد قاعدة البيانات
```powershell
mkdir database
python main.py
```

#### الحل 2: التحقق من الصلاحيات
```powershell
icacls database\knoux_guardian.db /grant Users:F
```

#### الحل 3: استعادة من نسخة احتياطية
```powershell
copy database\backups\knoux_guardian_backup_latest.db database\knoux_guardian.db
```

#### الحل 4: إعادة إنشاء قاعدة البيانات
```powershell
# احذف القاعدة التالفة
del database\knoux_guardian.db

# أعد التشغيل لإنشاء قاعدة جديدة
python main.py
```

---

### المشكلة: خطأ في ملف الإعدادات

**الأعراض:**
```
yaml.scanner.ScannerError: mapping values are not allowed here
FileNotFoundError: config/config.yaml not found
```

**الحلول:**

#### الحل 1: التحقق من صحة YAML
```powershell
# استخدام أداة التحقق عبر الإنترنت
# أو
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
```

#### الحل 2: إنشاء إعدادات افتراضية
```powershell
python scripts\config_manager.py summary
# سيُنشئ ملف إعدادات افتراضي إذا لم يكن موجودًا
```

#### الحل 3: استعادة من نسخة احتياطية
```powershell
copy config\backups\config_backup_latest.yaml config\config.yaml
```

---

## مشاكل API

### المشكلة: API لا يبدأ

**الأعراض:**
```
OSError: [WinError 10048] Only one usage of each socket address
uvicorn.error: Error loading ASGI app
```

**الحلول:**

#### الحل 1: تغيير المنفذ
```powershell
# في api/main.py أو عند التشغيل
uvicorn main:app --port 8001
```

#### الحل 2: إيقاف العملية المستخدمة للمنفذ
```powershell
# البحث عن العملية
netstat -ano | findstr :8000

# إيقاف العملية
taskkill /PID <process_id> /F
```

#### الحل 3: التحقق من جدار الحماية
```powershell
# السماح بالمنفذ
netsh advfirewall firewall add rule name="KNOUX API" dir=in action=allow protocol=TCP localport=8000
```

---

### المشكلة: خطأ 401 Unauthorized

**الأعراض:**
```json
{
  "detail": "Could not validate credentials"
}
```

**الحلول:**

#### الحل 1: التحقق من رمز JWT
```powershell
# تأكد من تضمين رمز صحيح
curl -H "Authorization: Bearer <your_token>" http://localhost:8000/api/v1/modules
```

#### الحل 2: تسجيل الدخول مجددًا
```powershell
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

#### الحل 3: التحقق من انتهاء صلاحية الرمز
```
# الرموز تنتهي بعد 30 دقيقة
# احصل على رمز جديد
```

---

### المشكلة: خطأ 403 Forbidden

**الأعراض:**
```json
{
  "detail": "Insufficient permissions"
}
```

**الحلول:**

#### الحل 1: التحقق من الدور
```
# تأكد من أن دورك يسمح بالعملية
# viewer: عرض فقط
# analyst: عرض + تنفيذ معظم الموديولات
# admin: وصول كامل
```

#### الحل 2: تسجيل الدخول بحساب مناسب
```powershell
# استخدم admin للعمليات الحساسة
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d '{"username":"admin","password":"admin123"}'
```

---

## مشاكل الموديولات

### المشكلة: فشل تحميل موديول

**الأعراض:**
```
ModuleNotFoundError: No module named 'src.modules.disk_space_orchestrator'
ImportError: cannot import name 'get_disk_orchestrator'
```

**الحلول:**

#### الحل 1: التحقق من وجود الموديول
```powershell
dir src\modules\disk_space_orchestrator\__init__.py
```

#### الحل 2: التحقق من بنية الموديول
```powershell
python test_all_modules.py
```

#### الحل 3: إعادة إنشاء الموديول
```powershell
# تأكد من وجود __init__.py في كل مجلد موديول
```

---

### المشكلة: فشل تنفيذ موديول

**الأعراض:**
```
RuntimeError: Module execution failed
Exception in module: disk_space_orchestrator
```

**الحلول:**

#### الحل 1: التحقق من السجلات
```powershell
Get-Content data\logs\knoux_guardian.log -Tail 50
```

#### الحل 2: تشغيل في وضع التصحيح
```yaml
# في config/config.yaml
system:
  log_level: DEBUG
```

#### الحل 3: اختبار الموديول منفردًا
```powershell
python -c "from src.modules.disk_space_orchestrator import get_disk_orchestrator; m = get_disk_orchestrator(); m.start()"
```

---

## مشاكل نماذج ML

### المشكلة: فشل تحميل نموذج ONNX

**الأعراض:**
```
onnxruntime.capi.onnxruntime_pybind11_state.RuntimeException
FileNotFoundError: models/onnx/disk_usage_predictor.onnx not found
```

**الحلول:**

#### الحل 1: التحقق من وجود النموذج
```powershell
dir models\onnx\*.onnx
```

#### الحل 2: إنشاء نماذج عينة
```powershell
python scripts\manage_models.py create-samples
```

#### الحل 3: تعطيل نماذج ML مؤقتًا
```yaml
# في config/config.yaml
ml_models:
  disk_usage_predictor:
    enabled: false
```

---

### المشكلة: خطأ في شكل الإدخال

**الأعراض:**
```
RuntimeError: Input shape mismatch
ValueError: Expected input shape [1, 10], got [1, 8]
```

**الحلول:**

#### الحل 1: التحقق من شكل الإدخال
```powershell
python scripts\ml_integration_example.py
```

#### الحل 2: تحديث النموذج
```powershell
# احصل على نموذج متوافق
python scripts\manage_models.py register --model path\to\new_model.onnx
```

---

## مشاكل الأداء

### المشكلة: استخدام عالي للذاكرة

**الأعراض:**
```
MemoryError: Unable to allocate memory
System becomes slow or unresponsive
```

**الحلول:**

#### الحل 1: تقليل عدد الـ workers
```yaml
# في config/config.yaml
system:
  max_workers: 2
  cache_size_mb: 256
```

#### الحل 2: تعطيل الموديولات غير المستخدمة
```yaml
modules:
  forensic_analyzer:
    enabled: false
  backup_orchestrator:
    enabled: false
```

#### الحل 3: زيادة فترات المسح
```yaml
modules:
  disk_space_orchestrator:
    scan_interval_minutes: 120  # بدلاً من 60
```

---

### المشكلة: استخدام عالي للمعالج

**الأعراض:**
```
CPU usage at 100%
System becomes slow
```

**الحلول:**

#### الحل 1: تقليل تكرار المراقبة
```yaml
modules:
  thermal_controller:
    monitor_interval_seconds: 60  # بدلاً من 30
  network_monitor:
    monitor_interval_seconds: 600  # بدلاً من 300
```

#### الحل 2: استخدام التنفيذ غير المتزامن
```json
{
  "run_mode": "async",
  "priority": "low"
}
```

---

## مشاكل الشبكة

### المشكلة: فشل الاتصال بـ API

**الأعراض:**
```
ConnectionRefusedError: [WinError 10061]
requests.exceptions.ConnectionError
```

**الحلول:**

#### الحل 1: التحقق من تشغيل API
```powershell
# تحقق من العملية
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# تحقق من المنفذ
netstat -ano | findstr :8000
```

#### الحل 2: التحقق من جدار الحماية
```powershell
# السماح بالاتصال
netsh advfirewall firewall add rule name="KNOUX API" dir=in action=allow protocol=TCP localport=8000
```

#### الحل 3: استخدام localhost بدلاً من 0.0.0.0
```
http://localhost:8000 بدلاً من http://0.0.0.0:8000
```

---

## مشاكل السجلات

### المشكلة: السجلات لا تُكتب

**الأعراض:**
```
No log files in data/logs/
Logs are empty
```

**الحلول:**

#### الحل 1: إنشاء مجلد السجلات
```powershell
mkdir data\logs
```

#### الحل 2: التحقق من الصلاحيات
```powershell
icacls data\logs /grant Users:F
```

#### الحل 3: التحقق من مستوى السجل
```yaml
# في config/config.yaml
system:
  log_level: INFO  # أو DEBUG
```

---

### المشكلة: السجلات كبيرة جدًا

**الأعراض:**
```
Log files consuming too much disk space
```

**الحلول:**

#### الحل 1: تفعيل التدوير التلقائي
```python
# في main.py - مفعّل افتراضيًا
# maxBytes=10MB, backupCount=5
```

#### الحل 2: حذف السجلات القديمة
```powershell
# حذف السجلات الأقدم من 30 يومًا
forfiles /p data\logs /s /m *.log /d -30 /c "cmd /c del @path"
```

#### الحل 3: تقليل مستوى السجل
```yaml
system:
  log_level: WARNING  # بدلاً من DEBUG
```

---

## مشاكل Windows محددة

### المشكلة: خطأ في WMI

**الأعراض:**
```
wmi.x_wmi: <x_wmi: Unexpected COM Error>
```

**الحلول:**

#### الحل 1: إعادة بناء مستودع WMI
```powershell
# تشغيل كمسؤول
net stop winmgmt
winmgmt /resetrepository
net start winmgmt
```

#### الحل 2: التحقق من خدمة WMI
```powershell
Get-Service Winmgmt
# إذا كانت متوقفة
Start-Service Winmgmt
```

---

### المشكلة: خطأ في الوصول إلى السجل

**الأعراض:**
```
PermissionError: Access to registry denied
```

**الحلول:**

#### الحل 1: تشغيل كمسؤول
```powershell
# انقر بزر الماوس الأيمن على PowerShell
# اختر "Run as Administrator"
```

#### الحل 2: تعطيل RegistryGuardian مؤقتًا
```yaml
modules:
  registry_guardian:
    enabled: false
```

---

## أدوات التشخيص

### 1. فحص شامل للنظام

```powershell
# تشغيل فحص شامل
python scripts\project_status.py --save

# عرض التقرير
notepad project_status_report.json
```

### 2. اختبار الاتصال

```powershell
# اختبار API
curl http://localhost:8000/api/v1/health

# اختبار قاعدة البيانات
python -c "from src.core.database import get_database; db = get_database(); print('OK')"
```

### 3. جمع معلومات التشخيص

```powershell
# جمع معلومات النظام
python scripts\system_monitor.py single > system_info.txt

# جمع السجلات
copy data\logs\knoux_guardian.log diagnostic_logs.txt

# جمع الإعدادات
copy config\config.yaml diagnostic_config.yaml
```

---

## الحصول على المساعدة

### قبل طلب المساعدة

1. **جمع المعلومات:**
   ```powershell
   python --version
   pip list > installed_packages.txt
   python scripts\project_status.py --save
   ```

2. **جمع السجلات:**
   ```powershell
   copy data\logs\knoux_guardian.log error_logs.txt
   ```

3. **وصف المشكلة:**
   - ما الذي كنت تحاول فعله؟
   - ما الخطأ الذي حدث؟
   - ما الخطوات لإعادة إنتاج المشكلة؟

### قنوات الدعم

- **GitHub Issues:** للإبلاغ عن الأخطاء
- **الوثائق:** `docs/` للمراجع
- **الأمثلة:** `examples/` للأمثلة العملية

---

**آخر تحديث:** 2026-02-12  
**الإصدار:** 1.0.0