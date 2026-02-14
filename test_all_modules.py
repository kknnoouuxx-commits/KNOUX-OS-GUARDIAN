#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test all 12 modules of KNOUX OS Guardian
اختبار جميع الـ 12 موديول لنظام KNOUX OS Guardian
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 60)
print("KNOUX OS Guardian - Test All 12 Modules")
print("=" * 60)

# Test imports
modules_to_test = [
    ("Disk Space Orchestrator", "src.modules.disk_space_orchestrator", "get_disk_orchestrator"),
    ("Update Guardian", "src.modules.update_guardian", "get_update_guardian"),
    ("Performance Optimizer", "src.modules.performance_optimizer", "get_performance_optimizer"),
    ("Network Monitor", "src.modules.network_monitor", "get_network_monitor"),
    ("Security Hardener", "src.modules.security_hardener", "get_security_hardener"),
    ("Driver Health Manager", "src.modules.driver_health_manager", "get_driver_manager"),
    ("Forensic Analyzer", "src.modules.forensic_analyzer", "get_forensic_analyzer"),
    ("Thermal Controller", "src.modules.thermal_controller", "get_thermal_controller"),
    ("Power Manager", "src.modules.power_manager", "get_power_manager"),
    ("Application Curator", "src.modules.application_lifecycle_curator", "get_application_curator"),
    ("Registry Guardian", "src.modules.registry_guardian", "get_registry_guardian"),
    ("Backup Orchestrator", "src.modules.backup_orchestrator", "get_backup_orchestrator"),
]

success_count = 0
total_count = len(modules_to_test)

for module_name, module_path, function_name in modules_to_test:
    try:
        # Import module
        module = __import__(module_path, fromlist=[function_name])
        
        # Get the function
        get_function = getattr(module, function_name)
        
        # Try to get instance
        instance = get_function()
        
        print(f"✅ {module_name}: Import successful")
        success_count += 1
        
    except ImportError as e:
        print(f"❌ {module_name}: Import failed - {e}")
    except AttributeError as e:
        print(f"❌ {module_name}: Function {function_name} not found - {e}")
    except Exception as e:
        print(f"❌ {module_name}: Error - {e}")

print("=" * 60)
print(f"Test Results: {success_count}/{total_count} modules successful")
print("=" * 60)

if success_count == total_count:
    print("🎉 All 12 modules are working correctly!")
    sys.exit(0)
else:
    print(f"⚠️  {total_count - success_count} modules failed")
    sys.exit(1)