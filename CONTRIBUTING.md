# دليل المساهمة
# Contributing to KNOUX OS Guardian

شكراً لاهتمامك بالمساهمة في KNOUX OS Guardian! 🎉

## 📋 جدول المحتويات

1. [كيفية المساهمة](#how-to-contribute)
2. [معايير الكود](#code-standards)
3. [عملية التطوير](#development-process)
4. [الإبلاغ عن المشاكل](#reporting-issues)
5. [اقتراح ميزات جديدة](#suggesting-features)

## 🤝 كيفية المساهمة

### المجالات المفتوحة للمساهمة

1. **تنفيذ الموديولات** (أولوية عالية)
   - Disk Space Orchestrator
   - Performance Optimizer
   - Update Guardian
   - الموديولات الـ 9 المتبقية

2. **نماذج ML**
   - تدريب النماذج
   - تحويل إلى ONNX
   - تحسين الدقة

3. **الاختبارات**
   - Unit tests
   - Integration tests
   - Performance tests

4. **الوثائق**
   - تحسين الوثائق الموجودة
   - إضافة أمثلة
   - ترجمة

5. **واجهة المستخدم**
   - Dashboard design
   - System tray agent
   - Visualization

## 💻 معايير الكود

### Python Style Guide

نتبع [PEP 8](https://www.python.org/dev/peps/pep-0008/) مع بعض التعديلات:

```python
# ✅ جيد
def calculate_risk_score(system_state: Dict) -> float:
    """
    حساب درجة المخاطر
    
    Args:
        system_state: حالة النظام الحالية
        
    Returns:
        درجة المخاطر (0-100)
    """
    score = 0.0
    
    if system_state['cpu_usage'] > 80:
        score += 30
    
    return score

# ❌ سيء
def calc(s):
    x=0
    if s['cpu']>80:x+=30
    return x
```

### التوثيق

- كل دالة يجب أن تحتوي على docstring
- استخدم type hints
- أضف تعليقات للكود المعقد
- وثق القرارات المهمة

```python
def process_data(input_data: List[Dict], 
                 threshold: float = 0.5) -> List[Dict]:
    """
    معالجة البيانات وتصفيتها
    
    Args:
        input_data: قائمة البيانات المدخلة
        threshold: عتبة التصفية (افتراضي: 0.5)
        
    Returns:
        قائمة البيانات المعالجة
        
    Raises:
        ValueError: إذا كانت البيانات فارغة
    """
    if not input_data:
        raise ValueError("Input data cannot be empty")
    
    # تصفية البيانات بناءً على العتبة
    filtered = [item for item in input_data 
                if item.get('score', 0) >= threshold]
    
    return filtered
```

### هيكل الموديول

عند إضافة موديول جديد:

```
src/modules/module_name/
├── __init__.py           # الواجهة العامة
├── core.py               # المنطق الأساسي
├── models.py             # نماذج البيانات
├── utils.py              # دوال مساعدة
└── tests/
    ├── test_core.py
    └── test_utils.py
```

### Commit Messages

استخدم تنسيق واضح:

```
✅ جيد:
feat: إضافة Disk Space Orchestrator
fix: إصلاح memory leak في Communication Bus
docs: تحديث دليل التثبيت
test: إضافة اختبارات للـ Safe Execution

❌ سيء:
update
fixed bug
changes
```

أنواع الـ commits:
- `feat`: ميزة جديدة
- `fix`: إصلاح خطأ
- `docs`: تحديث وثائق
- `test`: إضافة/تحديث اختبارات
- `refactor`: إعادة هيكلة كود
- `perf`: تحسين أداء
- `chore`: مهام صيانة

## 🔄 عملية التطوير

### 1. إعداد بيئة التطوير

```powershell
# استنساخ المشروع
git clone [repository-url]
cd KNOUX_OS_Guardian

# إنشاء بيئة افتراضية
python -m venv venv
venv\Scripts\activate

# تثبيت المكتبات
pip install -r requirements.txt

# تشغيل الاختبارات
python test_basic.py
```

### 2. إنشاء فرع جديد

```bash
# للميزات الجديدة
git checkout -b feat/module-name

# للإصلاحات
git checkout -b fix/issue-description

# للوثائق
git checkout -b docs/update-description
```

### 3. التطوير

1. اكتب الكود
2. أضف اختبارات
3. وثق التغييرات
4. شغل الاختبارات
5. تأكد من عدم وجود أخطاء

### 4. الاختبار

```powershell
# اختبارات أساسية
python test_basic.py

# اختبارات محددة (عند إضافتها)
python -m pytest tests/

# فحص الكود
pylint src/
```

### 5. إرسال التغييرات

```bash
# إضافة التغييرات
git add .

# commit مع رسالة واضحة
git commit -m "feat: إضافة Disk Space Orchestrator"

# push للفرع
git push origin feat/module-name
```

### 6. Pull Request

1. افتح Pull Request على GitHub
2. اشرح التغييرات بوضوح
3. أضف screenshots إن أمكن
4. انتظر المراجعة

## 🐛 الإبلاغ عن المشاكل

### قبل الإبلاغ

1. تحقق من المشاكل الموجودة
2. تأكد من استخدام آخر نسخة
3. جرب إعادة إنتاج المشكلة

### تنسيق البلاغ

```markdown
## وصف المشكلة
وصف واضح ومختصر للمشكلة

## خطوات إعادة الإنتاج
1. افتح '...'
2. اضغط على '...'
3. شاهد الخطأ

## السلوك المتوقع
ما كان يجب أن يحدث

## السلوك الفعلي
ما حدث فعلاً

## البيئة
- OS: Windows 11
- Python: 3.11.0
- Version: 1.0.0-alpha

## Screenshots
إن أمكن

## سجلات
```
[أضف السجلات من data/logs/]
```

## معلومات إضافية
أي معلومات أخرى مفيدة
```

## 💡 اقتراح ميزات جديدة

### تنسيق الاقتراح

```markdown
## الميزة المقترحة
وصف واضح للميزة

## المشكلة التي تحلها
لماذا نحتاج هذه الميزة؟

## الحل المقترح
كيف يمكن تنفيذها؟

## البدائل المدروسة
هل هناك طرق أخرى؟

## معلومات إضافية
mockups، أمثلة، إلخ
```

## 📝 قائمة التحقق

قبل إرسال Pull Request:

- [ ] الكود يتبع معايير المشروع
- [ ] أضفت اختبارات للميزات الجديدة
- [ ] جميع الاختبارات تنجح
- [ ] وثقت التغييرات
- [ ] حدثت CHANGELOG.md
- [ ] لا توجد أخطاء في الكود
- [ ] الكود يعمل على Windows

## 🎯 الأولويات الحالية

### عالية الأولوية
1. تنفيذ Disk Space Orchestrator
2. تنفيذ Performance Optimizer
3. إضافة اختبارات شاملة

### متوسطة الأولوية
1. تنفيذ Update Guardian
2. تحسين Decision Engine
3. إضافة ML models

### منخفضة الأولوية
1. واجهة المستخدم
2. Cloud integration
3. Advanced analytics

## 🤔 أسئلة؟

إذا كان لديك أي أسئلة:

1. راجع الوثائق في `docs/`
2. ابحث في المشاكل المغلقة
3. افتح issue جديد للنقاش

## 🙏 شكراً

شكراً لمساهمتك في جعل KNOUX OS Guardian أفضل!

---
© 2026 KNOUX OS Guardian
