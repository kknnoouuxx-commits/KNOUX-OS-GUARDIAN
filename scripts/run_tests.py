#!/usr/bin/env python3
"""
KNOUX OS Guardian - Test Runner Script
تشغيل جميع اختبارات النظام
"""

import os
import sys
import time
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import colorama
from colorama import Fore, Style

colorama.init()

class TestRunner:
    """منظم تشغيل الاختبارات"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None,
            "duration": None,
            "test_suites": []
        }
    
    def print_header(self, text: str):
        """طباعة عنوان"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{text:^60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    def print_success(self, text: str):
        """طباعة نجاح"""
        print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")
    
    def print_error(self, text: str):
        """طباعة خطأ"""
        print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")
    
    def print_warning(self, text: str):
        """طباعة تحذير"""
        print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")
    
    def print_info(self, text: str):
        """طباعة معلومات"""
        print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")
    
    def run_basic_tests(self) -> Tuple[bool, str]:
        """تشغيل الاختبارات الأساسية"""
        self.print_header("الاختبارات الأساسية")
        
        test_file = self.project_root / "test_basic.py"
        if not test_file.exists():
            return False, "ملف الاختبارات الأساسية غير موجود"
        
        try:
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            duration = time.time() - start_time
            
            if result.returncode == 0:
                self.print_success(f"الاختبارات الأساسية ناجحة ({duration:.2f} ثانية)")
                return True, result.stdout
            else:
                self.print_error(f"فشل الاختبارات الأساسية ({duration:.2f} ثانية)")
                if result.stdout:
                    print(f"{Fore.YELLOW}الإخراج:{Style.RESET_ALL}\n{result.stdout}")
                if result.stderr:
                    print(f"{Fore.RED}الأخطاء:{Style.RESET_ALL}\n{result.stderr}")
                return False, result.stderr or result.stdout
                
        except Exception as e:
            return False, f"خطأ في تشغيل الاختبارات: {e}"
    
    def run_module_tests(self) -> Tuple[bool, str]:
        """تشغيل اختبارات الموديولات"""
        self.print_header("اختبارات الموديولات")
        
        test_file = self.project_root / "test_all_modules.py"
        if not test_file.exists():
            return False, "ملف اختبارات الموديولات غير موجود"
        
        try:
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            duration = time.time() - start_time
            
            if result.returncode == 0:
                self.print_success(f"اختبارات الموديولات ناجحة ({duration:.2f} ثانية)")
                return True, result.stdout
            else:
                self.print_error(f"فشل اختبارات الموديولات ({duration:.2f} ثانية)")
                if result.stdout:
                    print(f"{Fore.YELLOW}الإخراج:{Style.RESET_ALL}\n{result.stdout}")
                if result.stderr:
                    print(f"{Fore.RED}الأخطاء:{Style.RESET_ALL}\n{result.stderr}")
                return False, result.stderr or result.stdout
                
        except Exception as e:
            return False, f"خطأ في تشغيل اختبارات الموديولات: {e}"
    
    def run_unit_tests(self) -> Tuple[bool, str]:
        """تشغيل اختبارات الوحدات"""
        self.print_header("اختبارات الوحدات")
        
        unit_tests_dir = self.project_root / "tests" / "unit"
        if not unit_tests_dir.exists():
            self.print_warning("مجلد اختبارات الوحدات غير موجود - سيتم إنشاؤه")
            unit_tests_dir.mkdir(parents=True, exist_ok=True)
            return True, "تم إنشاء مجلد اختبارات الوحدات"
        
        # البحث عن ملفات الاختبار
        test_files = list(unit_tests_dir.glob("test_*.py"))
        if not test_files:
            self.print_warning("لا توجد ملفات اختبار وحدات")
            return True, "لا توجد اختبارات وحدات"
        
        results = []
        for test_file in test_files:
            try:
                start_time = time.time()
                result = subprocess.run(
                    [sys.executable, str(test_file)],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                duration = time.time() - start_time
                
                test_name = test_file.stem
                if result.returncode == 0:
                    self.print_success(f"{test_name}: ناجح ({duration:.2f} ثانية)")
                    results.append((test_name, True, duration))
                else:
                    self.print_error(f"{test_name}: فشل ({duration:.2f} ثانية)")
                    results.append((test_name, False, duration))
                    
            except Exception as e:
                self.print_error(f"{test_file.stem}: خطأ - {e}")
                results.append((test_file.stem, False, 0))
        
        # تحليل النتائج
        passed = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        if total == 0:
            return True, "لا توجد اختبارات وحدات"
        elif passed == total:
            return True, f"جميع اختبارات الوحدات ناجحة ({passed}/{total})"
        else:
            return False, f"فشل بعض اختبارات الوحدات ({passed}/{total})"
    
    def run_integration_tests(self) -> Tuple[bool, str]:
        """تشغيل اختبارات التكامل"""
        self.print_header("اختبارات التكامل")
        
        integration_tests_dir = self.project_root / "tests" / "integration"
        if not integration_tests_dir.exists():
            self.print_warning("مجلد اختبارات التكامل غير موجود - سيتم إنشاؤه")
            integration_tests_dir.mkdir(parents=True, exist_ok=True)
            return True, "تم إنشاء مجلد اختبارات التكامل"
        
        # البحث عن ملفات الاختبار
        test_files = list(integration_tests_dir.glob("test_*.py"))
        if not test_files:
            self.print_warning("لا توجد ملفات اختبار تكامل")
            return True, "لا توجد اختبارات تكامل"
        
        results = []
        for test_file in test_files:
            try:
                start_time = time.time()
                result = subprocess.run(
                    [sys.executable, str(test_file)],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                duration = time.time() - start_time
                
                test_name = test_file.stem
                if result.returncode == 0:
                    self.print_success(f"{test_name}: ناجح ({duration:.2f} ثانية)")
                    results.append((test_name, True, duration))
                else:
                    self.print_error(f"{test_name}: فشل ({duration:.2f} ثانية)")
                    results.append((test_name, False, duration))
                    
            except Exception as e:
                self.print_error(f"{test_file.stem}: خطأ - {e}")
                results.append((test_file.stem, False, 0))
        
        # تحليل النتائج
        passed = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        if total == 0:
            return True, "لا توجد اختبارات تكامل"
        elif passed == total:
            return True, f"جميع اختبارات التكامل ناجحة ({passed}/{total})"
        else:
            return False, f"فشل بعض اختبارات التكامل ({passed}/{total})"
    
    def check_system_health(self) -> Tuple[bool, str]:
        """فحص صحة النظام"""
        self.print_header("فحص صحة النظام")
        
        checks = [
            ("مجلد src/", self.project_root / "src"),
            ("مجلد modules/", self.project_root / "src" / "modules"),
            ("ملف main.py", self.project_root / "main.py"),
            ("ملف requirements.txt", self.project_root / "requirements.txt"),
            ("ملف config.yaml", self.project_root / "config" / "config.yaml"),
            ("مجلد database/", self.project_root / "database"),
            ("مجلد data/logs/", self.project_root / "data" / "logs"),
        ]
        
        all_healthy = True
        messages = []
        
        for check_name, check_path in checks:
            if check_path.exists():
                self.print_success(f"{check_name}: موجود")
            else:
                self.print_error(f"{check_name}: غير موجود")
                all_healthy = False
                messages.append(f"{check_name} غير موجود")
        
        # التحقق من عدد الموديولات
        modules_dir = self.project_root / "src" / "modules"
        if modules_dir.exists():
            module_count = len([d for d in modules_dir.iterdir() if d.is_dir()])
            if module_count == 12:
                self.print_success(f"الموديولات: {module_count}/12 (مكتمل)")
            else:
                self.print_warning(f"الموديولات: {module_count}/12 (ناقص)")
                messages.append(f"عدد الموديولات: {module_count}/12")
        
        if all_healthy:
            return True, "النظام سليم"
        else:
            return False, "; ".join(messages)
    
    def run_all_tests(self, test_types: List[str] = None) -> Dict:
        """تشغيل جميع الاختبارات"""
        if test_types is None:
            test_types = ["health", "basic", "modules", "unit", "integration"]
        
        self.results["start_time"] = datetime.now().isoformat()
        
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'KNOUX OS Guardian - تشغيل الاختبارات':^60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"⏰ وقت البدء: {self.results['start_time']}")
        print(f"📁 مجلد المشروع: {self.project_root}")
        print()
        
        # تشغيل الاختبارات حسب النوع
        test_functions = {
            "health": ("فحص صحة النظام", self.check_system_health),
            "basic": ("الاختبارات الأساسية", self.run_basic_tests),
            "modules": ("اختبارات الموديولات", self.run_module_tests),
            "unit": ("اختبارات الوحدات", self.run_unit_tests),
            "integration": ("اختبارات التكامل", self.run_integration_tests),
        }
        
        for test_type in test_types:
            if test_type in test_functions:
                test_name, test_func = test_functions[test_type]
                success, message = test_func()
                
                self.results["test_suites"].append({
                    "name": test_name,
                    "type": test_type,
                    "success": success,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })
                
                self.results["total"] += 1
                if success:
                    self.results["passed"] += 1
                else:
                    self.results["failed"] += 1
        
        self.results["end_time"] = datetime.now().isoformat()
        start_dt = datetime.fromisoformat(self.results["start_time"].replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(self.results["end_time"].replace('Z', '+00:00'))
        self.results["duration"] = (end_dt - start_dt).total_seconds()
        
        # عرض النتائج النهائية
        self.print_header("النتائج النهائية")
        
        print(f"📊 الإجمالي: {self.results['total']} مجموعة اختبار")
        print(f"✅ الناجحة: {self.results['passed']}")
        print(f"❌ الفاشلة: {self.results['failed']}")
        print(f"⏱️  المدة: {self.results['duration']:.2f} ثانية")
        print(f"⏰ وقت الانتهاء: {self.results['end_time']}")
        
        if self.results["failed"] == 0:
            print(f"\n{Fore.GREEN}{'🎉 جميع الاختبارات ناجحة!':^60}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}{f'⚠️  فشل {self.results["failed"]} اختبار':^60}{Style.RESET_ALL}")
        
        return self.results
    
    def save_results(self, output_file: str = "test_results.json"):
        """حفظ النتائج في ملف"""
        output_path = self.project_root / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        self.print_info(f"تم حفظ النتائج في: {output_path}")

def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(description="تشغيل اختبارات KNOUX OS Guardian")
    parser.add_argument("--types", nargs="+", 
                       choices=["health", "basic", "modules", "unit", "integration", "all"],
                       default=["health", "basic", "modules"],
                       help="أنواع الاختبارات المطلوبة")
    parser.add_argument("--output", default="test_results.json",
                       help="ملف حفظ النتائج")
    parser.add_argument("--project-dir", default=".",
                       help="مجلد المشروع")
    
    args = parser.parse_args()
    
    # معالجة "all"
    if "all" in args.types:
        args.types = ["health", "basic", "modules", "unit", "integration"]
    
    runner = TestRunner(args.project_dir)
    
    try:
        results = runner.run_all_tests(args.types)
        runner.save_results(args.output)
        
        # إرجاع كود الخروج
        sys.exit(0 if results["failed"] == 0 else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}تم إلغاء العملية{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}خطأ غير متوقع: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()