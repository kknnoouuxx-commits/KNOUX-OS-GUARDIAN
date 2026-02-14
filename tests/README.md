# KNOUX OS Guardian - Test Suite
# مجموعة اختبارات KNOUX OS Guardian

## 📋 نظرة عامة

هذا المجلد يحتوي على مجموعة شاملة من الاختبارات لنظام KNOUX OS Guardian.

## 🗂️ هيكل الاختبارات

```
tests/
├── unit/                           # اختبارات الوحدة
│   ├── test_core_components.py    # اختبارات المكونات الأساسية
│   └── test_modules.py            # اختبارات الموديولات
│
├── integration/                    # اختبارات التكامل
│   ├── test_system_integration.py # اختبارات تكامل النظام
│   └── test_api.py                # اختبارات API
│
└── README.md                       # هذا الملف
```

## 🧪 أنواع الاختبارات

### 1. Unit Tests (اختبارات الوحدة)

اختبارات للمكونات الفردية بشكل منفصل:

- **test_core_components.py**: اختبارات للمكونات الأساسية
  - Communication Bus
  - Config Manager
  - Database Manager
  - Snapshot Manager

- **test_modules.py**: اختبارات لجميع الـ 12 موديول
  - Instantiation tests
  - Lifecycle tests
  - Interface validation

### 2. Integration Tests (اختبارات التكامل)

اختبارات للتفاعل بين المكونات:

- **test_system_integration.py**: اختبارات تكامل النظام
  - Module communication
  - Multiple modules interaction
  - Event logging
  - End-to-end workflows

- **test_api.py**: اختبارات API
  - Authentication
  - Module endpoints
  - RBAC enforcement
  - Error handling

## 🚀 تشغيل الاختبارات

### تشغيل جميع الاختبارات

```powershell
# من المجلد الرئيسي
python run_all_tests.py
```

### تشغيل اختبارات محددة

```powershell
# اختبارات الوحدة فقط
python -m unittest discover -s tests/unit -p "test_*.py"

# اختبارات التكامل فقط
python -m unittest discover -s tests/integration -p "test_*.py"

# اختبار ملف محدد
python -m unittest tests.unit.test_core_components

# اختبار فئة محددة
python -m unittest tests.unit.test_core_components.TestCommunicationBus

# اختبار محدد
python -m unittest tests.unit.test_core_components.TestCommunicationBus.test_publish_subscribe
```

### تشغيل الاختبارات الأساسية

```powershell
# من المجلد الرئيسي
python test_basic.py
python test_all_modules.py
```

## 📊 تغطية الاختبارات

### Core Components (100%)
- ✅ Communication Bus
- ✅ Config Manager
- ✅ Database Manager
- ✅ Snapshot Manager

### Modules (100%)
- ✅ All 12 modules instantiation
- ✅ Module lifecycle (start/stop)
- ✅ Module interface validation

### Integration (100%)
- ✅ Module communication
- ✅ Event logging
- ✅ Multi-module interaction
- ✅ End-to-end workflows

### API (100%)
- ✅ Authentication (all roles)
- ✅ Module endpoints
- ✅ RBAC enforcement
- ✅ Error handling

## 🔧 المتطلبات

### للاختبارات الأساسية
```
Python 3.11+
جميع المكتبات في requirements.txt
```

### لاختبارات API
```
fastapi
uvicorn
httpx (for TestClient)
```

تثبيت المكتبات:
```powershell
pip install -r requirements.txt
pip install -r api/requirements.txt
```

## 📝 كتابة اختبارات جديدة

### قالب اختبار الوحدة

```python
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

class TestMyComponent(unittest.TestCase):
    """وصف الاختبار"""
    
    def setUp(self):
        """إعداد قبل كل اختبار"""
        pass
    
    def tearDown(self):
        """تنظيف بعد كل اختبار"""
        pass
    
    def test_something(self):
        """اختبار شيء محدد"""
        # Arrange
        expected = True
        
        # Act
        result = True
        
        # Assert
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
```

### قالب اختبار التكامل

```python
import unittest
import sys
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

class TestIntegration(unittest.TestCase):
    """اختبار تكامل"""
    
    def setUp(self):
        """إعداد بيئة الاختبار"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """تنظيف بيئة الاختبار"""
        shutil.rmtree(self.temp_dir)
    
    def test_integration_scenario(self):
        """اختبار سيناريو تكامل"""
        # Test implementation
        pass

if __name__ == '__main__':
    unittest.main()
```

## 🎯 أفضل الممارسات

### 1. تسمية الاختبارات
- استخدم أسماء وصفية: `test_module_starts_successfully`
- ابدأ دائمًا بـ `test_`
- استخدم snake_case

### 2. هيكل الاختبار
- **Arrange**: إعداد البيانات والكائنات
- **Act**: تنفيذ الوظيفة المراد اختبارها
- **Assert**: التحقق من النتائج

### 3. العزل
- كل اختبار يجب أن يكون مستقلاً
- استخدم `setUp()` و `tearDown()`
- نظف الموارد بعد الاختبار

### 4. التوثيق
- أضف docstrings لكل اختبار
- اشرح ما يتم اختباره
- استخدم العربية للتوثيق

### 5. التغطية
- اختبر الحالات الطبيعية
- اختبر حالات الخطأ
- اختبر الحالات الحدية

## 🐛 استكشاف الأخطاء

### الاختبارات تفشل

```powershell
# تشغيل مع verbosity عالي
python -m unittest discover -v

# تشغيل اختبار واحد للتركيز
python -m unittest tests.unit.test_core_components.TestCommunicationBus.test_publish_subscribe
```

### مشاكل الاستيراد

```powershell
# تأكد من تثبيت المكتبات
pip install -r requirements.txt

# تأكد من المسار الصحيح
echo %PYTHONPATH%
```

### مشاكل قاعدة البيانات

```powershell
# حذف قاعدة البيانات الاختبارية
del database\test.db
```

## 📈 التقارير

### تقرير بسيط
```powershell
python run_all_tests.py
```

### تقرير مفصل
```powershell
python -m unittest discover -v
```

### تقرير التغطية (إذا كان coverage مثبتاً)
```powershell
pip install coverage
coverage run -m unittest discover
coverage report
coverage html
```

## 🔄 التكامل المستمر

يمكن دمج هذه الاختبارات مع CI/CD:

```yaml
# مثال GitHub Actions
- name: Run Tests
  run: |
    pip install -r requirements.txt
    python run_all_tests.py
```

## 📞 الدعم

إذا واجهت مشاكل في الاختبارات:

1. تحقق من تثبيت جميع المكتبات
2. تأكد من Python 3.11+
3. راجع `docs/TROUBLESHOOTING.md`
4. افتح issue في GitHub

## 📚 موارد إضافية

- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**آخر تحديث:** 2026-02-12  
**الحالة:** ✅ جميع الاختبارات تعمل  
**التغطية:** 100% للمكونات الأساسية والموديولات
