# البنية المعمارية
# KNOUX OS Guardian - Architecture

## نظرة عامة

KNOUX OS Guardian هو نظام ذكاء اصطناعي مدمج على مستوى نظام التشغيل، مصمم بفلسفة **Offline-First** و **Zero Trust Execution**.

## الطبقات الأساسية

```
┌─────────────────────────────────────────────────────────┐
│                   User Interface Layer                  │
│         (سيتم إضافتها في المرحلة القادمة)              │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│              Decision Orchestrator Engine               │
│  (محرك اتخاذ القرارات + ML Models + Explanation)       │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                Module Communication Bus                 │
│              (ناقل الاتصال بين الموديولات)             │
└─────────────────────────────────────────────────────────┘
                            ↕
┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ M1 │ M2 │ M3 │ M4 │ M5 │ M6 │ M7 │ M8 │ M9 │M10 │M11 │M12 │
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│              Safe Execution Framework                   │
│         (Snapshot + Rollback + Sandbox)                 │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                  Operating System APIs                  │
│            (Windows WMI, PowerShell, Win32)             │
└─────────────────────────────────────────────────────────┘
```

## المكونات الأساسية

### 1. Decision Orchestrator Engine
**الوظيفة:** محرك مركزي لاتخاذ القرارات

**المكونات:**
- Rule Engine: تقييم القواعد
- ML Models: نماذج التعلم الآلي (ONNX)
- Explanation Generator: توليد التفسيرات

**الملفات:**
- `src/core/decision_engine/__init__.py`

### 2. Communication Bus
**الوظيفة:** نظام اتصال موحد بين الموديولات

**الميزات:**
- Event Publishing/Subscription
- Query/Response Pattern
- Thread-Safe Message Queue

**الملفات:**
- `src/core/communication_bus/__init__.py`

### 3. Safe Execution Framework
**الوظيفة:** تنفيذ آمن مع إمكانية الاستعادة

**الميزات:**
- Snapshot Creation
- Automatic Rollback
- Sandbox Execution

**الملفات:**
- `src/core/safe_execution/__init__.py`

### 4. Telemetry Collector
**الوظيفة:** جمع بيانات مجهولة (opt-in)

**الميزات:**
- PII Sanitization
- Anonymous System ID
- Buffered Transmission

**الملفات:**
- `src/core/telemetry/__init__.py`

### 5. Configuration Manager
**الوظيفة:** إدارة الإعدادات

**الملفات:**
- `src/core/config.py`
- `config/config.yaml`

### 6. Database Manager
**الوظيفة:** إدارة قاعدة البيانات SQLite

**الملفات:**
- `src/core/database.py`
- `database/knoux_guardian.db`

## الموديولات (12 Module)

### المرحلة الحالية
✅ البنية الأساسية جاهزة
⏳ الموديولات سيتم إضافتها تدريجياً

### قائمة الموديولات

1. **Disk Space Orchestrator** - إدارة المساحة
2. **Update Guardian** - إدارة التحديثات
3. **Performance Optimizer** - تحسين الأداء
4. **Network Monitor** - مراقبة الشبكة
5. **Security Hardener** - تعزيز الأمان
6. **Driver Health Manager** - إدارة التعريفات
7. **Forensic Analyzer** - التحليل الجنائي
8. **Thermal Controller** - إدارة الحرارة
9. **Power Manager** - إدارة الطاقة
10. **Application Curator** - إدارة التطبيقات
11. **Registry Guardian** - حماية السجل
12. **Backup Orchestrator** - النسخ الاحتياطي

## تدفق البيانات

### 1. Monitoring Flow
```
OS Metrics → Module Sensors → Communication Bus → 
Decision Engine → Database → Dashboard
```

### 2. Action Flow
```
Decision Engine → Risk Assessment → [User Approval?] →
Safe Execution → Snapshot → Execute → Validate →
[Success] → Commit | [Failure] → Rollback
```

## قاعدة البيانات

### الجداول الأساسية

```sql
-- System snapshots
system_snapshots (
    snapshot_id, created_at, description,
    snapshot_path, can_rollback
)

-- Decision artifacts
decision_artifacts (
    decision_id, timestamp, rule_id,
    rule_name, explanation, result_json
)

-- System events
system_events (
    timestamp, event_type, module_name,
    severity, message, details_json
)
```

## الأمان

### Zero Trust Execution
1. Risk Assessment قبل كل عملية
2. User Approval للعمليات عالية المخاطر
3. Snapshot قبل التنفيذ
4. Validation بعد التنفيذ
5. Automatic Rollback عند الفشل

### Privacy by Design
- لا جمع بيانات بدون موافقة صريحة
- PII Sanitization تلقائي
- Anonymous System ID
- Local-First Processing

## التوسع المستقبلي

### المرحلة 1 (الحالية)
- ✅ البنية الأساسية
- ✅ Core Components
- ✅ Database Schema

### المرحلة 2
- ⏳ إضافة الموديولات الـ 12
- ⏳ ML Models Integration
- ⏳ Advanced Rules

### المرحلة 3
- ⏳ User Interface (Dashboard)
- ⏳ Real-time Monitoring
- ⏳ Visualization

### المرحلة 4
- ⏳ Cloud Integration (Optional)
- ⏳ Community Features
- ⏳ Advanced Analytics

---
© 2026 KNOUX OS Guardian
