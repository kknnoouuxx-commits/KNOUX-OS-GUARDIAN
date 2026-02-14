# KNOUX OS Guardian - Final Setup Checklist
# قائمة التحقق النهائية للإعداد

## ✅ قائمة التحقق قبل النشر

### 1. البيئة والمكتبات

- [ ] Python 3.11+ مثبت
  ```powershell
  python --version
  ```

- [ ] تثبيت المكتبات الأساسية
  ```powershell
  pip install -r requirements.txt
  ```

- [ ] تثبيت مكتبات API (اختياري)
  ```powershell
  pip install -r api/requirements.txt
  ```

### 2. الإعدادات

- [ ] مراجعة `config/config.yaml`
- [ ] تعيين `offline_first: true` للعمل بدون إنترنت
- [ ] تفعيل/تعطيل الموديولات حسب الحاجة
- [ ] ضبط الفواصل الزمنية (intervals)
- [ ] ضبط العتبات (thresholds)

### 3. قاعدة البيانات

- [ ] التأكد من وجود مجلد `database/`
- [ ] اختبار إنشاء قاعدة البيانات
  ```powershell
  python test_basic.py
  ```

### 4. السجلات

- [ ] التأكد من وجود مجلد `data/logs/`
- [ ] التأكد من وجود مجلد `data/snapshots/`
- [ ] ضبط مستوى السجلات في `config.yaml`

### 5. الاختبارات

- [ ] تشغيل الاختبارات الأساسية
  ```powershell
  python test_basic.py
  ```

- [ ] تشغيل اختبارات الموديولات
  ```powershell
  python test_all_modules.py
  ```

- [ ] تشغيل جميع الاختبارات
  ```powershell
  python run_all_tests.py
  ```

### 6. الموديولات

- [ ] التحقق من جميع الـ 12 موديول
  ```powershell
  python test_all_modules.py
  ```

- [ ] التأكد من عمل كل موديول:
  - [ ] DiskSpaceOrchestrator
  - [ ] UpdateGuardian
  - [ ] PerformanceOptimizer
  - [ ] NetworkMonitor
  - [ ] SecurityHardener
  - [ ] DriverHealthManager
  - [ ] ForensicAnalyzer
  - [ ] ThermalController
  - [ ] PowerManager
  - [ ] ApplicationCurator
  - [ ] RegistryGuardian
  - [ ] BackupOrchestrator

### 7. API (اختياري)

- [ ] تثبيت FastAPI
  ```powershell
  pip install fastapi uvicorn
  ```

- [ ] تغيير JWT_SECRET_KEY في الإنتاج
  ```powershell
  set JWT_SECRET_KEY=your-secret-key-here
  ```

- [ ] تغيير كلمات المرور الافتراضية
  - [ ] admin:admin123 → كلمة مرور قوية
  - [ ] analyst:analyst123 → كلمة مرور قوية
  - [ ] viewer:viewer123 → كلمة مرور قوية

- [ ] اختبار API
  ```powershell
  cd api
  python main.py
  # في نافذة أخرى:
  curl http://localhost:8000/api/v1/health
  ```

### 8. الأمان

- [ ] تغيير جميع كلمات المرور الافتراضية
- [ ] تعيين JWT_SECRET_KEY فريد
- [ ] تفعيل HTTPS في الإنتاج
- [ ] تقييد CORS في الإنتاج
- [ ] مراجعة أذونات الملفات
- [ ] تفعيل Rate Limiting (اختياري)

### 9. نماذج ML (اختياري)

- [ ] وضع نماذج ONNX في `models/onnx/`
- [ ] التحقق من صحة النماذج
  ```powershell
  python scripts/manage_models.py list
  ```

- [ ] اختبار تحميل النماذج
  ```powershell
  python scripts/ml_integration_example.py
  ```

### 10. الوثائق

- [ ] قراءة `README.md`
- [ ] قراءة `INSTALLATION.md`
- [ ] قراءة `QUICKSTART.md`
- [ ] مراجعة `docs/ARCHITECTURE.md`
- [ ] مراجعة `docs/API_DOCUMENTATION.md` (إذا كنت تستخدم API)
- [ ] مراجعة `docs/TROUBLESHOOTING.md`

### 11. التشغيل

- [ ] تشغيل النظام الأساسي
  ```powershell
  python main.py
  ```
  أو
  ```powershell
  .\run.bat
  ```

- [ ] التحقق من السجلات في `data/logs/`
- [ ] التحقق من قاعدة البيانات في `database/`

### 12. المراقبة

- [ ] تشغيل مراقب النظام
  ```powershell
  python scripts/system_monitor.py
  ```

- [ ] التحقق من حالة المشروع
  ```powershell
  python scripts/project_status.py summary
  ```

## 🔧 إعدادات الإنتاج

### متغيرات البيئة

```powershell
# Windows
set JWT_SECRET_KEY=your-production-secret-key
set DATABASE_PATH=C:\path\to\production\database
set LOG_LEVEL=INFO

# أو في ملف .env
JWT_SECRET_KEY=your-production-secret-key
DATABASE_PATH=C:\path\to\production\database
LOG_LEVEL=INFO
```

### ملف config.yaml للإنتاج

```yaml
system:
  offline_first: true
  log_level: "INFO"
  database_path: "C:\\production\\database\\knoux_guardian.db"
  
security:
  require_approval: true
  max_risk_level: "medium"
  
telemetry:
  enabled: false  # أو true مع موافقة المستخدم
```

## 🚀 البدء السريع

### للتطوير

```powershell
# 1. تثبيت المكتبات
pip install -r requirements.txt

# 2. تشغيل الاختبارات
python test_basic.py

# 3. تشغيل النظام
python main.py
```

### للإنتاج

```powershell
# 1. تثبيت المكتبات
pip install -r requirements.txt

# 2. تغيير الإعدادات
# تحرير config/config.yaml

# 3. تغيير كلمات المرور
# تحرير api/main.py (إذا كنت تستخدم API)

# 4. تشغيل الاختبارات
python run_all_tests.py

# 5. تشغيل النظام
python main.py
```

## 📊 التحقق من الحالة

### فحص سريع

```powershell
python scripts/project_status.py summary
```

### فحص شامل

```powershell
# 1. حالة المشروع
python scripts/project_status.py detailed

# 2. الاختبارات
python run_all_tests.py

# 3. مراقبة النظام
python scripts/system_monitor.py

# 4. حالة النماذج
python scripts/manage_models.py list
```

## ⚠️ مشاكل شائعة

### 1. فشل الاستيراد

```powershell
# الحل: تأكد من تثبيت المكتبات
pip install -r requirements.txt
```

### 2. خطأ في قاعدة البيانات

```powershell
# الحل: حذف قاعدة البيانات وإعادة إنشائها
del database\knoux_guardian.db
python test_basic.py
```

### 3. خطأ في الأذونات

```powershell
# الحل: تشغيل كمسؤول
# انقر بزر الماوس الأيمن على PowerShell → Run as Administrator
```

### 4. API لا يعمل

```powershell
# الحل: تثبيت FastAPI
pip install fastapi uvicorn httpx
```

## 📞 الدعم

إذا واجهت مشاكل:

1. راجع `docs/TROUBLESHOOTING.md`
2. تحقق من السجلات في `data/logs/`
3. شغل الاختبارات: `python run_all_tests.py`
4. افتح issue في GitHub

## ✅ قائمة التحقق النهائية

قبل النشر، تأكد من:

- [x] جميع الاختبارات تنجح
- [ ] جميع كلمات المرور تم تغييرها
- [ ] JWT_SECRET_KEY تم تغييره
- [ ] config.yaml تم ضبطه للإنتاج
- [ ] السجلات تعمل بشكل صحيح
- [ ] قاعدة البيانات تعمل
- [ ] جميع الموديولات تعمل
- [ ] API يعمل (إذا كنت تستخدمه)
- [ ] الوثائق تم مراجعتها
- [ ] النسخ الاحتياطي تم إعداده

## 🎉 جاهز للنشر!

إذا تم تحديد جميع العناصر أعلاه، فأنت جاهز لنشر KNOUX OS Guardian!

```powershell
# تشغيل النظام
python main.py

# أو
.\run.bat
```

---

**آخر تحديث:** 2026-02-12  
**الحالة:** ✅ جاهز للنشر  
**الإصدار:** 1.0.0
