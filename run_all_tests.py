#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KNOUX OS Guardian - Comprehensive Test Runner
مشغل الاختبارات الشامل
"""

import sys
import unittest
from pathlib import Path
import time

# Add paths
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))


def run_test_suite(suite_name, test_loader, pattern):
    """تشغيل مجموعة اختبارات"""
    print(f"\n{'=' * 60}")
    print(f"🧪 {suite_name}")
    print('=' * 60)
    
    start_time = time.time()
    
    # Discover and run tests
    suite = test_loader.discover(
        start_dir=str(Path(__file__).parent / 'tests'),
        pattern=pattern
    )
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{'=' * 60}")
    print(f"⏱️  الوقت المستغرق: {elapsed_time:.2f} ثانية")
    print(f"✅ نجح: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ فشل: {len(result.failures)}")
    print(f"⚠️  أخطاء: {len(result.errors)}")
    print('=' * 60)
    
    return result


def main():
    """تشغيل جميع الاختبارات"""
    print("=" * 60)
    print("KNOUX OS Guardian - Comprehensive Test Suite")
    print("مجموعة الاختبارات الشاملة")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    all_results = []
    
    # 1. Run basic tests
    print("\n📦 المرحلة 1: الاختبارات الأساسية")
    try:
        import test_basic
        result = unittest.TextTestRunner(verbosity=2).run(
            loader.loadTestsFromModule(test_basic)
        )
        all_results.append(result)
    except Exception as e:
        print(f"⚠️  تخطي الاختبارات الأساسية: {e}")
    
    # 2. Run module tests
    print("\n📦 المرحلة 2: اختبارات الموديولات")
    try:
        import test_all_modules
        result = unittest.TextTestRunner(verbosity=2).run(
            loader.loadTestsFromModule(test_all_modules)
        )
        all_results.append(result)
    except Exception as e:
        print(f"⚠️  تخطي اختبارات الموديولات: {e}")
    
    # 3. Run unit tests
    print("\n📦 المرحلة 3: اختبارات الوحدة")
    try:
        result = run_test_suite(
            "Unit Tests - اختبارات الوحدة",
            loader,
            "test_*.py"
        )
        all_results.append(result)
    except Exception as e:
        print(f"⚠️  تخطي اختبارات الوحدة: {e}")
    
    # 4. Run integration tests
    print("\n📦 المرحلة 4: اختبارات التكامل")
    try:
        suite = loader.discover(
            start_dir=str(Path(__file__).parent / 'tests' / 'integration'),
            pattern='test_*.py'
        )
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        all_results.append(result)
    except Exception as e:
        print(f"⚠️  تخطي اختبارات التكامل: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ملخص النتائج النهائية")
    print("=" * 60)
    
    total_tests = sum(r.testsRun for r in all_results)
    total_failures = sum(len(r.failures) for r in all_results)
    total_errors = sum(len(r.errors) for r in all_results)
    total_success = total_tests - total_failures - total_errors
    
    print(f"إجمالي الاختبارات: {total_tests}")
    print(f"✅ نجح: {total_success}")
    print(f"❌ فشل: {total_failures}")
    print(f"⚠️  أخطاء: {total_errors}")
    
    if total_failures == 0 and total_errors == 0:
        print("\n🎉 جميع الاختبارات نجحت!")
        print("=" * 60)
        return 0
    else:
        print(f"\n⚠️  {total_failures + total_errors} اختبار فشل")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
