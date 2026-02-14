# KNOUX OS Guardian - API Documentation

## نظرة عامة
توثيق شامل لواجهة برمجة التطبيقات (API) الخاصة بنظام KNOUX OS Guardian.

## معلومات عامة

### Base URL
```
http://localhost:8000/api/v1
```

### المصادقة
جميع نقاط النهاية (باستثناء `/health` و `/auth/login`) تتطلب مصادقة JWT.

**رأس المصادقة:**
```
Authorization: Bearer <access_token>
```

### الأدوار والصلاحيات

#### Admin (مدير النظام)
- الوصول الكامل لجميع نقاط النهاية
- تنفيذ جميع الموديولات
- الوصول إلى سجلات التدقيق
- إدارة الإعدادات

#### Analyst (محلل النظام)
- تنفيذ معظم الموديولات
- عرض حالة الموديولات
- الوصول إلى سجلات التدقيق
- **لا يمكن:** تنفيذ SecurityHardener/harden

#### Viewer (مستعرض النظام)
- عرض حالة الموديولات فقط
- **لا يمكن:** تنفيذ أي موديول
- **لا يمكن:** الوصول إلى سجلات التدقيق

## نقاط النهاية

### 1. المصادقة

#### تسجيل الدخول
```http
POST /api/v1/auth/login
```

**الطلب:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**الاستجابة:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**أكواد الحالة:**
- `200`: نجح تسجيل الدخول
- `401`: بيانات اعتماد غير صحيحة

---

### 2. الصحة والنظام

#### فحص صحة النظام
```http
GET /api/v1/health
```

**الاستجابة:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-12T10:30:00Z",
  "version": "1.0.0",
  "modules_available": 12
}
```

**لا يتطلب مصادقة**

#### عرض جميع الموديولات
```http
GET /api/v1/modules
```

**الاستجابة:**
```json
[
  {
    "module_name": "DiskSpaceOrchestrator",
    "enabled": true,
    "last_run": "2026-02-12T09:15:00Z",
    "status": "healthy",
    "health_score": 85.5
  },
  ...
]
```

**الأدوار المطلوبة:** admin, analyst, viewer

---

### 3. تنفيذ الموديولات

#### تنفيذ موديول
```http
POST /api/v1/modules/{module_name}/execute
```

**المعاملات:**
- `module_name`: اسم الموديول (مثل: DiskSpaceOrchestrator)

**الطلب:**
```json
{
  "run_mode": "immediate",
  "parameters": {
    "volumes": ["C:", "D:"],
    "threshold_percent": 20,
    "simulate_cleanup": true
  },
  "priority": "normal"
}
```

**حقول الطلب:**
- `run_mode`: "immediate" أو "async"
- `parameters`: معاملات خاصة بالموديول
- `priority`: "low", "normal", "high", "critical"

**الاستجابة (immediate):**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "module_name": "DiskSpaceOrchestrator",
  "status": "completed",
  "run_mode": "immediate",
  "started_at": "2026-02-12T10:30:00Z",
  "completed_at": "2026-02-12T10:30:05Z",
  "severity": "medium",
  "details": {
    "volumes": [...],
    "recommendations": [...]
  },
  "message": "Module DiskSpaceOrchestrator executed successfully"
}
```

**الاستجابة (async):**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "module_name": "DiskSpaceOrchestrator",
  "status": "running",
  "run_mode": "async",
  "started_at": "2026-02-12T10:30:00Z",
  "completed_at": null,
  "severity": "info",
  "details": {
    "message": "Async execution scheduled"
  },
  "message": "Module DiskSpaceOrchestrator scheduled for async execution"
}
```

**أكواد الحالة:**
- `200`: تنفيذ فوري ناجح
- `202`: تنفيذ غير متزامن مجدول
- `400`: طلب غير صحيح
- `403`: صلاحيات غير كافية
- `404`: موديول غير موجود

**الأدوار المطلوبة:** admin, analyst

---

### 4. حالة الموديول

#### الحصول على حالة موديول
```http
GET /api/v1/modules/{module_name}/status
```

**الاستجابة:**
```json
{
  "module_name": "DiskSpaceOrchestrator",
  "enabled": true,
  "last_run": "2026-02-12T09:15:00Z",
  "status": "healthy",
  "health_score": 85.5
}
```

**الأدوار المطلوبة:** admin, analyst, viewer

---

### 5. نتائج التنفيذ

#### الحصول على نتيجة تنفيذ
```http
GET /api/v1/modules/{module_name}/runs/{run_id}
```

**الاستجابة:**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "module_name": "DiskSpaceOrchestrator",
  "status": "completed",
  "run_mode": "async",
  "started_at": "2026-02-12T10:30:00Z",
  "completed_at": "2026-02-12T10:30:05Z",
  "severity": "medium",
  "details": {...},
  "message": "Async execution completed for DiskSpaceOrchestrator"
}
```

**الأدوار المطلوبة:** admin, analyst, viewer

---

### 6. المهام غير المتزامنة

#### الحصول على حالة مهمة غير متزامنة
```http
GET /api/v1/async/tasks/{run_id}
```

**الاستجابة:**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "module_name": "DiskSpaceOrchestrator",
  "status": "running",
  "progress": 65.5,
  "started_at": "2026-02-12T10:30:00Z",
  "estimated_completion": "2026-02-12T10:32:00Z",
  "result": null
}
```

**حالات المهمة:**
- `running`: قيد التنفيذ
- `completed`: مكتمل
- `failed`: فشل

**الأدوار المطلوبة:** admin, analyst

---

### 7. سجلات التدقيق

#### الحصول على سجلات التدقيق
```http
GET /api/v1/audit/logs
```

**معاملات الاستعلام:**
- `module_name`: تصفية حسب الموديول
- `action`: تصفية حسب الإجراء
- `severity`: تصفية حسب الخطورة
- `page`: رقم الصفحة (افتراضي: 1)
- `page_size`: حجم الصفحة (افتراضي: 20)

**الاستجابة:**
```json
{
  "items": [
    {
      "audit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "timestamp": "2026-02-12T10:30:00Z",
      "module_name": "DiskSpaceOrchestrator",
      "action": "execute",
      "run_id": "550e8400-e29b-41d4-a716-446655440000",
      "actor": "admin",
      "actor_role": "admin",
      "severity": "medium",
      "status": "success",
      "metadata": {
        "source_ip": "192.168.1.100",
        "user_agent": "KNOUX-OS-Guardian-Postman/1.0.0",
        "parameters": {...},
        "run_mode": "immediate"
      }
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

**الأدوار المطلوبة:** admin, analyst

#### الحصول على تفاصيل سجل تدقيق
```http
GET /api/v1/audit/logs/{audit_id}
```

**الأدوار المطلوبة:** admin, analyst

---

## معاملات الموديولات

### DiskSpaceOrchestrator
```json
{
  "volumes": ["C:", "D:", "E:"],
  "threshold_percent": 20,
  "simulate_cleanup": true
}
```

### NetworkMonitor
```json
{
  "duration_seconds": 300,
  "capture_packets": false,
  "analyze_connections": true,
  "privacy_mode": "strict"
}
```

### SecurityHardener
```json
{
  "cis_profile": "enterprise",
  "remediate_automatically": false,
  "scan_registry": true,
  "scan_services": true
}
```

### PerformanceOptimizer
```json
{
  "optimize_memory": true,
  "optimize_cpu": true,
  "clean_temp_files": true,
  "defragment_drives": false
}
```

### UpdateGuardian
```json
{
  "check_updates": true,
  "assess_risks": true,
  "deploy_strategy": "review_first",
  "exclude_kbs": ["KB1234567"]
}
```

### DriverHealthManager
```json
{
  "scan_all_drivers": true,
  "check_crashes": true,
  "update_recommendations": true,
  "driver_categories": ["display", "network", "storage"]
}
```

### ForensicAnalyzer
```json
{
  "time_range_hours": 24,
  "analyze_bsod": true,
  "analyze_crashes": true,
  "collect_logs": true,
  "root_cause_depth": "deep"
}
```

### ThermalController
```json
{
  "monitor_interval_seconds": 30,
  "critical_temp_celsius": 90,
  "warning_temp_celsius": 80,
  "control_fans": true,
  "throttle_cpu": true
}
```

### PowerManager
```json
{
  "power_plan": "balanced",
  "optimize_battery": true,
  "screen_timeout_minutes": 10,
  "sleep_timeout_minutes": 30,
  "hibernate_enabled": true
}
```

### ApplicationCurator
```json
{
  "scan_abandoned_days": 90,
  "scan_idle_days": 30,
  "suggest_removals": true,
  "cleanup_temp": true,
  "categories": ["toolbars", "trialware", "bloatware"]
}
```

### RegistryGuardian
```json
{
  "scan_hives": ["HKLM", "HKCU"],
  "detect_malware": true,
  "detect_bloat": true,
  "quarantine_mode": "auto",
  "backup_before_changes": true
}
```

### BackupOrchestrator
```json
{
  "backup_type": "incremental",
  "include_folders": ["C:\\Users", "C:\\Documents"],
  "exclude_patterns": ["*.tmp", "*.log"],
  "destination": "D:\\Backups",
  "compression": true,
  "encryption": false
}
```

---

## أكواد الأخطاء

### أكواد HTTP
- `200`: نجح الطلب
- `202`: تم قبول الطلب (للتنفيذ غير المتزامن)
- `400`: طلب غير صحيح
- `401`: غير مصادق
- `403`: صلاحيات غير كافية
- `404`: المورد غير موجود
- `500`: خطأ في الخادم

### أكواد الخطورة
- `info`: معلومات عامة
- `low`: خطورة منخفضة
- `medium`: خطورة متوسطة
- `high`: خطورة عالية
- `critical`: خطورة حرجة

---

## أمثلة الاستخدام

### مثال 1: تسجيل الدخول وتنفيذ موديول
```bash
# 1. تسجيل الدخول
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# الاستجابة: {"access_token":"eyJ...","token_type":"bearer","expires_in":1800}

# 2. تنفيذ موديول
curl -X POST http://localhost:8000/api/v1/modules/DiskSpaceOrchestrator/execute \
  -H "Authorization: Bearer eyJ..." \
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

### مثال 2: تنفيذ غير متزامن ومتابعة الحالة
```bash
# 1. تنفيذ غير متزامن
curl -X POST http://localhost:8000/api/v1/modules/NetworkMonitor/execute \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "run_mode": "async",
    "parameters": {
      "duration_seconds": 300,
      "privacy_mode": "strict"
    }
  }'

# الاستجابة: {"run_id":"550e8400-...","status":"running",...}

# 2. متابعة الحالة
curl -X GET http://localhost:8000/api/v1/async/tasks/550e8400-... \
  -H "Authorization: Bearer eyJ..."

# 3. الحصول على النتيجة
curl -X GET http://localhost:8000/api/v1/modules/NetworkMonitor/runs/550e8400-... \
  -H "Authorization: Bearer eyJ..."
```

### مثال 3: الحصول على سجلات التدقيق
```bash
curl -X GET "http://localhost:8000/api/v1/audit/logs?module_name=DiskSpaceOrchestrator&page=1&page_size=10" \
  -H "Authorization: Bearer eyJ..."
```

---

## ملاحظات مهمة

### الأمان
- جميع الاتصالات يجب أن تكون عبر HTTPS في بيئة الإنتاج
- رموز JWT تنتهي صلاحيتها بعد 30 دقيقة
- يجب تغيير `JWT_SECRET_KEY` في بيئة الإنتاج

### الأداء
- التنفيذ غير المتزامن موصى به للعمليات الطويلة
- استخدم التصفية والترقيم لسجلات التدقيق

### الخصوصية
- جميع البيانات تعالج محليًا
- لا توجد اتصالات خارجية
- سجلات التدقيق تحتوي على IP و User-Agent للأمان فقط

---

**آخر تحديث:** 2026-02-12  
**الإصدار:** 1.0.0