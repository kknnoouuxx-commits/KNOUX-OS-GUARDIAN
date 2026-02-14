# نماذج التعلم الآلي - KNOUX OS Guardian

## نظرة عامة
يحتوي هذا المجلد على نماذج التعلم الآلي بتنسيق ONNX التي تعمل محليًا داخل نظام KNOUX OS Guardian.

## هيكل النماذج

### النماذج الأساسية المطلوبة
1. **disk_usage_predictor.onnx** - تنبؤ استخدام مساحة التخزين
2. **update_risk_predictor.onnx** - تقييم مخاطر التحديثات
3. **performance_anomaly_detector.onnx** - كشف الشذوذ في الأداء
4. **thermal_threshold_predictor.onnx** - تنبؤ درجات الحرارة الحرجة

### مواصفات النماذج
- **التنسيق**: ONNX (Open Neural Network Exchange)
- **الحجم**: أقل من 50 ميجابايت لكل نموذج
- **التشغيل**: محلي باستخدام ONNX Runtime
- **الذاكرة**: مصممة للعمل على أجهزة المستخدمين

## إضافة نماذج جديدة

### الخطوات:
1. تدريب النموذج باستخدام PyTorch أو TensorFlow
2. تحويل النموذج إلى تنسيق ONNX
3. نسخ النموذج إلى هذا المجلد
4. تسجيل النموذج باستخدام `scripts/manage_models.py`

### مثال تحويل PyTorch إلى ONNX:
```python
import torch
import torch.onnx

# تحميل النموذج المدرب
model = YourTrainedModel()
model.load_state_dict(torch.load('model.pth'))
model.eval()

# إنشاء بيانات عينة
dummy_input = torch.randn(1, input_size)

# التصدير إلى ONNX
torch.onnx.export(
    model,
    dummy_input,
    "your_model.onnx",
    export_params=True,
    opset_version=11,
    do_constant_folding=True,
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
)
```

## استخدام النماذج في الكود

### مثال الاستخدام:
```python
import onnxruntime as ort
import numpy as np

# تحميل النموذج
session = ort.InferenceSession("models/onnx/disk_usage_predictor.onnx")

# تحضير البيانات
input_data = np.random.randn(1, 10).astype(np.float32)

# التنبؤ
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name
result = session.run([output_name], {input_name: input_data})
```

## إدارة النماذج

### سكريبت الإدارة:
```bash
# عرض النماذج المتاحة
python scripts/manage_models.py list

# تسجيل نموذج جديد
python scripts/manage_models.py register --model path/to/model.onnx

# التحقق من سلامة النماذج
python scripts/manage_models.py validate

# إنشاء نماذج عينة (للتطوير)
python scripts/manage_models.py create-samples
```

## أفضل الممارسات

### 1. تحسين الأداء
- استخدام تنسيق FP16 لتقليل حجم النموذج
- تطبيق تقنيات التقليم (Pruning)
- استخدام التكمية (Quantization)

### 2. اختبار النماذج
- اختبار الدقة على بيانات الاختبار
- قياس وقت الاستجابة
- اختبار استخدام الذاكرة

### 3. التوثيق
- توثيق بنية النموذج
- توثيق تنسيق الإدخال/الإخراج
- توثيق أداء النموذج

## بيانات التدريب

### المجلد: `models/training/`
- بيانات التدريب (إذا كانت صغيرة الحجم)
- سكريبتات التدريب
- ملفات التكوين للتدريب

### ملاحظات:
- لا تخزن بيانات كبيرة في هذا المستودع
- استخدم روابط لبيانات التدريب الكبيرة
- احتفظ بنسخ احتياطية من البيانات

## الأمان والخصوصية

### متطلبات:
- لا تحتوي النماذج على بيانات مستخدمين
- جميع الحسابات تتم محليًا
- لا توجد اتصالات خارجية للنماذج

### التحقق:
- فحص النماذج بحثًا عن كود ضار
- التحقق من مصادر النماذج
- تحديث النماذب بانتظام

## الاستكشاف والأخطاء

### مشاكل شائعة:
1. **خطأ في تحميل النموذج**: تأكد من تنسيق ONNX
2. **عدم تطابق الأبعاد**: تحقق من شكل بيانات الإدخال
3. **أداء بطيء**: تحقق من إصدار ONNX Runtime

### أدوات المساعدة:
- `netron` - عرض بنية النماذج
- `onnx.checker` - التحقق من صحة النموذج
- `onnxruntime_perf_test` - اختبار الأداء

## التحديثات والصيانة

### جدول الصيانة:
- **أسبوعيًا**: التحقق من سلامة النماذج
- **شهريًا**: تحديث النماذج إذا لزم الأمر
- **ربع سنوي**: مراجعة أداء النماذج

### النسخ الاحتياطي:
- احتفظ بنسخ من النماذج في موقع آمن
- سجل إصدارات النماذج
- احتفظ بسجل التغييرات

---

**ملاحظة**: جميع النماذج تعمل محليًا ولا تتطلب اتصالاً بالإنترنت، مما يحافظ على خصوصية المستخدمين.