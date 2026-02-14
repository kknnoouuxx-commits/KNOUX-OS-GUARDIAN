# KNOUX OS Guardian - REST API

## نظرة عامة
واجهة برمجة التطبيقات (REST API) لنظام KNOUX OS Guardian، توفر وصولاً كاملاً لجميع الموديولات الـ 12 مع مصادقة JWT وتحكم في الصلاحيات.

---

## الميزات الرئيسية

### 🔐 المصادقة والأمان
- مصادقة JWT (JSON Web Tokens)
- ثلاثة أدوار: Admin, Analyst, Viewer
- تحكم دقيق في الصلاحيات (RBAC)
- انتهاء صلاحية تلقائي للرموز (30 دقيقة)

### ⚡ التنفيذ غير المتزامن
- دعم التنفيذ الفوري (immediate)
- دعم التنفيذ غير المتزامن (async)
- متابعة حالة المهام
- أولويات التنفيذ

### 📊 التدقيق والمراقبة
- تسجيل شامل لجميع العمليات
- تتبع IP المصدر و User-Agent
- ربط العمليات بـ run_id
- تصفية وترقيم السجلات

### 🔧 12 موديول متكامل
- DiskSpaceOrchestrator
- UpdateGuardian
- PerformanceOptimizer
- NetworkMonitor
- SecurityHardener
- DriverHealthManager
- ForensicAnalyzer
- ThermalController
- PowerManager
- ApplicationCurator
- RegistryGuardian
- BackupOrchestrator

---

## التثبيت السريع

### 1. تثبيت المكتبات
```powershell
cd api
pip install -r requirements.txt
```

### 2. تشغيل API
```powershell
# تطوير
python main.py

# أو باستخدام uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# إنتاج
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. التحقق من التشغيل
```powershell
curl http://localhost:8000/api/v1/health
```

---

## الاستخدام السريع

### 1. تسجيل الدخول
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**الاستجابة:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. عرض الموديولات
```bash
curl http://localhost:8000/api/v1/modules \
  -H "Authorization: Bearer <your_token>"
```

### 3. تنفيذ موديول
```bash
curl -X POST http://localhost:8000/api/v1/modules/DiskSpaceOrchestrator/execute \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "run_mode": "immediate",
    "parameters": {
      "volumes": ["C:", "D:"],
      "threshold_percent": 20
    },
    "priority": "normal"
  }'
```

---

## البنية

```
api/
├── main.py                                    # نقطة الدخول الرئيسية
├── requirements.txt                           # المكتبات المطلوبة
├── README.md                                  # هذا الملف
├── knoux_os_guardian_postman_collection.json # مجموعة Postman (قيد الإعداد)
└── KNOUX_OS_Guardian_Postman_Collection.json # مجموعة Postman (قيد الإعداد)
```

---

## نقاط النهاية الرئيسية

### المصادقة
- `POST /api/v1/auth/login` - تسجيل الدخول

### النظام
- `GET /api/v1/health` - فحص الصحة
- `GET /api/v1/modules` - عرض جميع الموديولات

### الموديولات
- `GET /api/v1/modules/{module_name}/status` - حالة موديول
- `POST /api/v1/modules/{module_name}/execute` - تنفيذ موديول
- `GET /api/v1/modules/{module_name}/runs/{run_id}` - نتيجة التنفيذ

### المهام غير المتزامنة
- `GET /api/v1/async/tasks/{run_id}` - حالة مهمة

### التدقيق
- `GET /api/v1/audit/logs` - سجلات التدقيق
- `GET /api/v1/audit/logs/{audit_id}` - تفاصيل سجل

---

## الأدوار والصلاحيات

### Admin (مدير النظام)
✅ عرض حالة جميع الموديولات  
✅ تنفيذ جميع الموديولات  
✅ الوصول إلى سجلات التدقيق  
✅ تنفيذ SecurityHardener/harden  

### Analyst (محلل النظام)
✅ عرض حالة جميع الموديولات  
✅ تنفيذ معظم الموديولات  
✅ الوصول إلى سجلات التدقيق  
❌ تنفيذ SecurityHardener/harden  

### Viewer (مستعرض النظام)
✅ عرض حالة جميع الموديولات  
❌ تنفيذ أي موديول  
❌ الوصول إلى سجلات التدقيق  

---

## الحسابات الافتراضية

| المستخدم | كلمة المرور | الدور |
|---------|-------------|-------|
| admin | admin123 | Admin |
| analyst | analyst123 | Analyst |
| viewer | viewer123 | Viewer |

⚠️ **تحذير:** غيّر كلمات المرور في بيئة الإنتاج!

---

## التكوين

### متغيرات البيئة
```powershell
# مفتاح JWT (غيّره في الإنتاج!)
$env:JWT_SECRET_KEY = "your-secret-key-here"

# المنفذ
$env:API_PORT = "8000"

# المضيف
$env:API_HOST = "0.0.0.0"
```

### في الكود
```python
# في main.py
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-key")
```

---

## اختبار API

### استخدام Postman
1. استيراد المجموعة: `KNOUX_OS_Guardian_Postman_Collection.json`
2. تعيين متغير البيئة: `base_url = http://localhost:8000`
3. تسجيل الدخول للحصول على رمز
4. اختبار نقاط النهاية

### استخدام curl
```bash
# فحص الصحة
curl http://localhost:8000/api/v1/health

# تسجيل الدخول
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# عرض الموديولات
curl http://localhost:8000/api/v1/modules \
  -H "Authorization: Bearer <token>"
```

### استخدام Python
```python
import requests

# تسجيل الدخول
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = response.json()["access_token"]

# عرض الموديولات
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/v1/modules",
    headers=headers
)
print(response.json())
```

---

## التنفيذ غير المتزامن

### 1. بدء التنفيذ
```bash
curl -X POST http://localhost:8000/api/v1/modules/NetworkMonitor/execute \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "run_mode": "async",
    "parameters": {
      "duration_seconds": 300
    }
  }'
```

**الاستجابة:**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "run_mode": "async"
}
```

### 2. متابعة الحالة
```bash
curl http://localhost:8000/api/v1/async/tasks/550e8400-... \
  -H "Authorization: Bearer <token>"
```

### 3. الحصول على النتيجة
```bash
curl http://localhost:8000/api/v1/modules/NetworkMonitor/runs/550e8400-... \
  -H "Authorization: Bearer <token>"
```

---

## سجلات التدقيق

### عرض السجلات
```bash
curl "http://localhost:8000/api/v1/audit/logs?page=1&page_size=20" \
  -H "Authorization: Bearer <token>"
```

### التصفية
```bash
# حسب الموديول
curl "http://localhost:8000/api/v1/audit/logs?module_name=DiskSpaceOrchestrator" \
  -H "Authorization: Bearer <token>"

# حسب الإجراء
curl "http://localhost:8000/api/v1/audit/logs?action=execute" \
  -H "Authorization: Bearer <token>"

# حسب الخطورة
curl "http://localhost:8000/api/v1/audit/logs?severity=high" \
  -H "Authorization: Bearer <token>"
```

---

## الأمان

### في التطوير
- استخدام HTTP مقبول
- كلمات مرور افتراضية
- CORS مفعّل للجميع

### في الإنتاج
⚠️ **يجب تطبيق:**
1. استخدام HTTPS فقط
2. تغيير `JWT_SECRET_KEY`
3. تغيير كلمات المرور الافتراضية
4. تقييد CORS
5. استخدام جدار حماية
6. تفعيل rate limiting

```python
# مثال: تقييد CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## استكشاف الأخطاء

### المشكلة: API لا يبدأ
```powershell
# تحقق من المنفذ
netstat -ano | findstr :8000

# غيّر المنفذ
uvicorn main:app --port 8001
```

### المشكلة: خطأ 401
```
# تأكد من صحة الرمز
# الرموز تنتهي بعد 30 دقيقة
# احصل على رمز جديد
```

### المشكلة: خطأ 403
```
# تحقق من دورك
# بعض العمليات تتطلب Admin
```

---

## الوثائق التفاعلية

### Swagger UI
```
http://localhost:8000/api/v1/docs
```

### ReDoc
```
http://localhost:8000/api/v1/redoc
```

### OpenAPI JSON
```
http://localhost:8000/api/v1/openapi.json
```

---

## الأداء

### التوصيات
- استخدم التنفيذ غير المتزامن للعمليات الطويلة
- استخدم التصفية والترقيم للسجلات
- استخدم عدة workers في الإنتاج

### مثال: عدة workers
```powershell
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

---

## المساهمة

### إضافة نقطة نهاية جديدة
1. أضف الدالة في `main.py`
2. أضف نموذج Pydantic إذا لزم الأمر
3. أضف التوثيق
4. أضف الاختبارات في Postman

### إضافة موديول جديد
1. أنشئ الموديول في `src/modules/`
2. استورده في `main.py`
3. أضف نقطة نهاية التنفيذ
4. حدّث الوثائق

---

## الموارد

### الوثائق
- [API Documentation](../docs/API_DOCUMENTATION.md)
- [Deployment Guide](../docs/DEPLOYMENT.md)
- [Troubleshooting](../docs/TROUBLESHOOTING.md)

### الأدوات
- [Postman](https://www.postman.com/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [JWT.io](https://jwt.io/)

---

**آخر تحديث:** 2026-02-12  
**الإصدار:** 1.0.0  
**الحالة:** جاهز للاستخدام (في انتظار مجموعة Postman النهائية)