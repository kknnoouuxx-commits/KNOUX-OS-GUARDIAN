#!/usr/bin/env python3
"""
KNOUX OS Guardian - حالة المشروع
عرض حالة المشروع الكاملة والإحصائيات
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import colorama
from colorama import Fore, Style

colorama.init()

class ProjectStatus:
    """عرض حالة المشروع"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.stats = self._collect_stats()
    
    def _collect_stats(self) -> Dict:
        """جمع إحصائيات المشروع"""
        return {
            "timestamp": datetime.now().isoformat(),
            "directories": self._count_directories(),
            "files": self._count_files(),
            "modules": self._analyze_modules(),
            "config": self._analyze_config(),
            "scripts": self._analyze_scripts(),
            "tests": self._analyze_tests(),
            "documentation": self._analyze_documentation(),
            "size": self._calculate_size()
        }
    
    def _count_directories(self) -> Dict:
        """عد المجلدات"""
        directories = [
            ".kiro", ".project", ".vscode", "api", "config", "data",
            "database", "docs", "files", "models", "scripts", "src",
            "tests", "data/logs", "data/snapshots", "models/onnx",
            "models/training", "tests/unit", "tests/integration",
            "src/core", "src/modules"
        ]
        
        existing = []
        missing = []
        
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                existing.append(dir_name)
            else:
                missing.append(dir_name)
        
        return {
            "total": len(directories),
            "existing": len(existing),
            "missing": len(missing),
            "existing_list": existing,
            "missing_list": missing
        }
    
    def _count_files(self) -> Dict:
        """عد الملفات"""
        file_patterns = {
            "python": ["*.py"],
            "config": ["*.yaml", "*.yml", "*.json"],
            "documentation": ["*.md", "*.txt"],
            "scripts": ["*.bat", "*.sh"],
            "database": ["*.db", "*.sqlite"],
            "models": ["*.onnx", "*.pth", "*.h5"]
        }
        
        counts = {}
        for category, patterns in file_patterns.items():
            count = 0
            for pattern in patterns:
                count += len(list(self.project_root.rglob(pattern)))
            counts[category] = count
        
        counts["total"] = sum(counts.values())
        
        # الملفات الرئيسية المهمة
        important_files = [
            "main.py", "requirements.txt", "config/config.yaml",
            "README.md", "INSTALLATION.md", "run.bat", "test.bat",
            "test_basic.py", "test_all_modules.py"
        ]
        
        existing_important = []
        missing_important = []
        
        for file_name in important_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                existing_important.append(file_name)
            else:
                missing_important.append(file_name)
        
        counts["important_files"] = {
            "total": len(important_files),
            "existing": len(existing_important),
            "missing": len(missing_important),
            "existing_list": existing_important,
            "missing_list": missing_important
        }
        
        return counts
    
    def _analyze_modules(self) -> Dict:
        """تحليل الموديولات"""
        modules_dir = self.project_root / "src" / "modules"
        
        if not modules_dir.exists():
            return {
                "total": 0,
                "existing": 0,
                "missing": 12,
                "modules": []
            }
        
        # الموديولات المطلوبة
        required_modules = [
            "disk_space_orchestrator",
            "update_guardian", 
            "performance_optimizer",
            "network_monitor",
            "security_hardener",
            "driver_health_manager",
            "forensic_analyzer",
            "thermal_controller",
            "power_manager",
            "application_lifecycle_curator",
            "registry_guardian",
            "backup_orchestrator"
        ]
        
        modules = []
        for module_name in required_modules:
            module_dir = modules_dir / module_name
            init_file = module_dir / "__init__.py"
            
            exists = module_dir.exists() and init_file.exists()
            modules.append({
                "name": module_name,
                "exists": exists,
                "has_init": init_file.exists() if module_dir.exists() else False,
                "path": str(module_dir.relative_to(self.project_root))
            })
        
        existing_count = sum(1 for m in modules if m["exists"])
        
        return {
            "total": len(required_modules),
            "existing": existing_count,
            "missing": len(required_modules) - existing_count,
            "completion_percent": round((existing_count / len(required_modules)) * 100, 1),
            "modules": modules
        }
    
    def _analyze_config(self) -> Dict:
        """تحليل الإعدادات"""
        config_path = self.project_root / "config" / "config.yaml"
        
        if not config_path.exists():
            return {
                "exists": False,
                "valid": False,
                "modules_configured": 0
            }
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # عد الموديولات المفعّلة
            modules_config = config.get("modules", {})
            enabled_modules = sum(1 for m in modules_config.values() if m.get("enabled", False))
            
            return {
                "exists": True,
                "valid": True,
                "modules_configured": len(modules_config),
                "modules_enabled": enabled_modules,
                "has_system_config": "system" in config,
                "has_api_config": "api" in config,
                "has_ml_config": "ml_models" in config
            }
            
        except Exception as e:
            return {
                "exists": True,
                "valid": False,
                "error": str(e)
            }
    
    def _analyze_scripts(self) -> Dict:
        """تحليل السكريبتات"""
        scripts_dir = self.project_root / "scripts"
        
        if not scripts_dir.exists():
            return {
                "exists": False,
                "count": 0,
                "scripts": []
            }
        
        scripts = []
        for script_file in scripts_dir.glob("*.py"):
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                scripts.append({
                    "name": script_file.name,
                    "size_kb": round(script_file.stat().st_size / 1024, 2),
                    "lines": content.count('\n') + 1,
                    "has_shebang": content.startswith('#!/'),
                    "has_docstring": '"""' in content[:500] or "'''" in content[:500]
                })
            except:
                scripts.append({
                    "name": script_file.name,
                    "error": "فشل القراءة"
                })
        
        return {
            "exists": True,
            "count": len(scripts),
            "scripts": scripts
        }
    
    def _analyze_tests(self) -> Dict:
        """تحليل الاختبارات"""
        test_files = {
            "basic": self.project_root / "test_basic.py",
            "all_modules": self.project_root / "test_all_modules.py",
            "unit_dir": self.project_root / "tests" / "unit",
            "integration_dir": self.project_root / "tests" / "integration"
        }
        
        results = {}
        for test_name, test_path in test_files.items():
            if isinstance(test_path, Path):
                results[test_name] = {
                    "exists": test_path.exists(),
                    "is_file": test_path.is_file() if test_path.exists() else False,
                    "is_dir": test_path.is_dir() if test_path.exists() else False
                }
                
                if test_path.exists() and test_path.is_dir():
                    py_files = list(test_path.glob("test_*.py"))
                    results[test_name]["test_files"] = len(py_files)
                    results[test_name]["file_list"] = [f.name for f in py_files]
        
        # حساب الإجمالي
        total_tests = 0
        if results.get("unit_dir", {}).get("exists"):
            total_tests += results["unit_dir"].get("test_files", 0)
        if results.get("integration_dir", {}).get("exists"):
            total_tests += results["integration_dir"].get("test_files", 0)
        
        results["total_test_files"] = total_tests
        
        return results
    
    def _analyze_documentation(self) -> Dict:
        """تحليل الوثائق"""
        doc_files = [
            "README.md",
            "INSTALLATION.md",
            "QUICKSTART.md",
            "STATUS.md",
            "PROJECT_SUMMARY.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "LICENSE",
            "docs/ARCHITECTURE.md"
        ]
        
        docs = []
        for doc_file in doc_files:
            doc_path = self.project_root / doc_file
            exists = doc_path.exists()
            
            if exists:
                try:
                    size_kb = round(doc_path.stat().st_size / 1024, 2)
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    lines = content.count('\n') + 1
                except:
                    size_kb = 0
                    lines = 0
            else:
                size_kb = 0
                lines = 0
            
            docs.append({
                "name": doc_file,
                "exists": exists,
                "size_kb": size_kb,
                "lines": lines
            })
        
        existing_count = sum(1 for d in docs if d["exists"])
        
        return {
            "total": len(doc_files),
            "existing": existing_count,
            "missing": len(doc_files) - existing_count,
            "completion_percent": round((existing_count / len(doc_files)) * 100, 1),
            "documents": docs
        }
    
    def _calculate_size(self) -> Dict:
        """حساب حجم المشروع"""
        total_size = 0
        file_count = 0
        
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                    file_count += 1
                except:
                    pass
        
        return {
            "total_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "average_kb": round(total_size / file_count / 1024, 2) if file_count > 0 else 0
        }
    
    def print_summary(self):
        """طباعة ملخص المشروع"""
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'KNOUX OS Guardian - حالة المشروع':^70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"⏰ الوقت: {self.stats['timestamp']}")
        print(f"📁 مجلد المشروع: {self.project_root}")
        print()
        
        # المجلدات
        dirs = self.stats["directories"]
        print(f"{Fore.BLUE}📂 المجلدات:{Style.RESET_ALL}")
        print(f"  الإجمالي: {dirs['total']} | ✅ موجود: {dirs['existing']} | ❌ مفقود: {dirs['missing']}")
        
        if dirs["missing"] > 0:
            print(f"  {Fore.YELLOW}المجلدات المفقودة:{Style.RESET_ALL}")
            for missing_dir in dirs["missing_list"][:5]:  # عرض أول 5 فقط
                print(f"    • {missing_dir}")
            if len(dirs["missing_list"]) > 5:
                print(f"    ... و{len(dirs['missing_list']) - 5} أخرى")
        print()
        
        # الملفات
        files = self.stats["files"]
        print(f"{Fore.BLUE}📄 الملفات:{Style.RESET_ALL}")
        print(f"  الإجمالي: {files['total']} ملف")
        print(f"  Python: {files['python']} | إعدادات: {files['config']} | وثائق: {files['documentation']}")
        
        important = files["important_files"]
        print(f"  {Fore.CYAN}الملفات المهمة:{Style.RESET_ALL} {important['existing']}/{important['total']}")
        
        if important["missing"] > 0:
            print(f"  {Fore.YELLOW}الملفات المفقودة:{Style.RESET_ALL}")
            for missing_file in important["missing_list"]:
                print(f"    • {missing_file}")
        print()
        
        # الموديولات
        modules = self.stats["modules"]
        print(f"{Fore.BLUE}🔧 الموديولات:{Style.RESET_ALL}")
        print(f"  {modules['existing']}/{modules['total']} ({modules['completion_percent']}%)")
        
        if modules["missing"] > 0:
            missing_modules = [m["name"] for m in modules["modules"] if not m["exists"]]
            print(f"  {Fore.YELLOW}الموديولات المفقودة:{Style.RESET_ALL}")
            for missing_module in missing_modules[:5]:
                print(f"    • {missing_module}")
            if len(missing_modules) > 5:
                print(f"    ... و{len(missing_modules) - 5} أخرى")
        print()
        
        # الإعدادات
        config = self.stats["config"]
        if config["exists"]:
            if config["valid"]:
                print(f"{Fore.GREEN}⚙️  الإعدادات: صحيحة{Style.RESET_ALL}")
                print(f"  الموديولات المضبوطة: {config['modules_configured']}")
                print(f"  الموديولات المفعلة: {config['modules_enabled']}")
            else:
                print(f"{Fore.RED}⚙️  الإعدادات: غير صحيحة{Style.RESET_ALL}")
                print(f"  الخطأ: {config.get('error', 'غير معروف')}")
        else:
            print(f"{Fore.RED}⚙️  الإعدادات: غير موجودة{Style.RESET_ALL}")
        print()
        
        # السكريبتات
        scripts = self.stats["scripts"]
        if scripts["exists"]:
            print(f"{Fore.BLUE}📜 السكريبتات: {scripts['count']}{Style.RESET_ALL}")
            for script in scripts["scripts"][:3]:  # عرض أول 3 فقط
                if "error" not in script:
                    print(f"  • {script['name']} ({script['lines']} سطر)")
            if scripts["count"] > 3:
                print(f"  ... و{scripts['count'] - 3} أخرى")
        else:
            print(f"{Fore.YELLOW}📜 السكريبتات: غير موجودة{Style.RESET_ALL}")
        print()
        
        # الاختبارات
        tests = self.stats["tests"]
        print(f"{Fore.BLUE}🧪 الاختبارات:{Style.RESET_ALL}")
        print(f"  ملفات الاختبار: {tests.get('total_test_files', 0)}")
        
        if tests.get("basic", {}).get("exists"):
            print(f"  ✅ test_basic.py: موجود")
        else:
            print(f"  ❌ test_basic.py: مفقود")
        
        if tests.get("all_modules", {}).get("exists"):
            print(f"  ✅ test_all_modules.py: موجود")
        else:
            print(f"  ❌ test_all_modules.py: مفقود")
        print()
        
        # الوثائق
        docs = self.stats["documentation"]
        print(f"{Fore.BLUE}📚 الوثائق:{Style.RESET_ALL}")
        print(f"  {docs['existing']}/{docs['total']} ({docs['completion_percent']}%)")
        
        if docs["missing"] > 0:
            missing_docs = [d["name"] for d in docs["documents"] if not d["exists"]]
            print(f"  {Fore.YELLOW}الوثائق المفقودة:{Style.RESET_ALL}")
            for missing_doc in missing_docs[:3]:
                print(f"    • {missing_doc}")
            if len(missing_docs) > 3:
                print(f"    ... و{len(missing_docs) - 3} أخرى")
        print()
        
        # الحجم
        size = self.stats["size"]
        print(f"{Fore.BLUE}📊 الحجم:{Style.RESET_ALL}")
        print(f"  الإجمالي: {size['total_mb']} MB")
        print(f"  عدد الملفات: {size['file_count']}")
        print(f"  متوسط الحجم: {size['average_kb']} KB")
        print()
        
        # التقدير العام
        print(f"{Fore.CYAN}📈 التقدير العام:{Style.RESET_ALL}")
        
        completion_scores = []
        
        # الموديولات (40%)
        module_score = modules["completion_percent"] * 0.4
        completion_scores.append(("الموديولات", module_score))
        
        # الوثائق (20%)
        doc_score = docs["completion_percent"] * 0.2
        completion_scores.append(("الوثائق", doc_score))
        
        # الاختبارات (20%)
        test_score = 0
        if tests.get("basic", {}).get("exists"):
            test_score += 10
        if tests.get("all_modules", {}).get("exists"):
            test_score += 10
        completion_scores.append(("الاختبارات", test_score))
        
        # الإعدادات (10%)
        config_score = 0
        if config["exists"] and config["valid"]:
            config_score = 10
        completion_scores.append(("الإعدادات", config_score))
        
        # السكريبتات (10%)
        script_score = 0
        if scripts["exists"] and scripts["count"] >= 3:
            script_score = 10
        completion_scores.append(("السكريبتات", script_score))
        
        total_score = sum(score for _, score in completion_scores)
        
        print(f"  النتيجة الإجمالية: {total_score:.1f}/100")
        print()
        
        for category, score in completion_scores:
            bar_length = 20
            filled = int(bar_length * score / 10)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"  {category:15} {bar} {score:5.1f}/10")
        
        print()
        
        if total_score >= 90:
            print(f"{Fore.GREEN}🎉 المشروع في حالة ممتازة!{Style.RESET_ALL}")
        elif total_score >= 70:
            print(f"{Fore.GREEN}✅ المشروع في حالة جيدة{Style.RESET_ALL}")
        elif total_score >= 50:
            print(f"{Fore.YELLOW}⚠️  المشروع يحتاج إلى تحسينات{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ المشروع يحتاج إلى عمل كبير{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    
    def save_report(self, output_file: str = "project_status_report.json"):
        """حفظ التقرير في ملف"""
        output_path = self.project_root / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        print(f"{Fore.GREEN}✅ تم حفظ التقرير في: {output_path}{Style.RESET_ALL}")
        return output_path

def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(description="عرض حالة مشروع KNOUX OS Guardian")
    parser.add_argument("--save", action="store_true",
                       help="حفظ التقرير في ملف")
    parser.add_argument("--output", default="project_status_report.json",
                       help="ملف حفظ التقرير")
    parser.add_argument("--project-dir", default=".",
                       help="مجلد المشروع")
    
    args = parser.parse_args()
    
    try:
        status = ProjectStatus(args.project_dir)
        status.print_summary()
        
        if args.save:
            status.save_report(args.output)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⏹️  تم إلغاء العملية{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}❌ خطأ غير متوقع: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    main()