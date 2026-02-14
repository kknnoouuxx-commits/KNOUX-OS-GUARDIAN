#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KNOUX OS Guardian - Unit Tests for Modules
اختبارات الوحدة للموديولات
"""

import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.modules.disk_space_orchestrator import get_disk_orchestrator
from src.modules.update_guardian import get_update_guardian
from src.modules.performance_optimizer import get_performance_optimizer
from src.modules.network_monitor import get_network_monitor
from src.modules.security_hardener import get_security_hardener
from src.modules.driver_health_manager import get_driver_manager
from src.modules.forensic_analyzer import get_forensic_analyzer
from src.modules.thermal_controller import get_thermal_controller
from src.modules.power_manager import get_power_manager
from src.modules.application_lifecycle_curator import get_application_curator
from src.modules.registry_guardian import get_registry_guardian
from src.modules.backup_orchestrator import get_backup_orchestrator


class TestModuleInstantiation(unittest.TestCase):
    """اختبار إنشاء نسخ من الموديولات"""
    
    def test_disk_orchestrator(self):
        """اختبار Disk Space Orchestrator"""
        module = get_disk_orchestrator()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'start'))
        self.assertTrue(hasattr(module, 'stop'))
        self.assertTrue(hasattr(module, 'get_status'))
    
    def test_update_guardian(self):
        """اختبار Update Guardian"""
        module = get_update_guardian()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'start'))
        self.assertTrue(hasattr(module, 'stop'))
        self.assertTrue(hasattr(module, 'get_status'))
    
    def test_performance_optimizer(self):
        """اختبار Performance Optimizer"""
        module = get_performance_optimizer()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'start'))
        self.assertTrue(hasattr(module, 'stop'))
        self.assertTrue(hasattr(module, 'get_status'))
    
    def test_network_monitor(self):
        """اختبار Network Monitor"""
        module = get_network_monitor()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'start'))
        self.assertTrue(hasattr(module, 'stop'))
        self.assertTrue(hasattr(module, 'get_status'))
    
    def test_security_hardener(self):
        """اختبار Security Hardener"""
        module = get_security_hardener()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'start'))
        self.assertTrue(hasattr(module, 'stop'))
        self.assertTrue(hasattr(module, 'get_status'))
    
    def test_driver_manager(self):
        """اختبار Driver Health Manager"""
        module = get_driver_manager()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'start'))
        self.assertTrue(hasattr(module, 'stop'))
        self.assertTrue(hasattr(module, 'get_status'))
    
    def test_forensic_analyzer(self):
        """اختبار Forensic Analyzer"""
        module = get_forensic_analyzer()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'start'))
        self.assertTrue(hasattr(module, 'stop'))
        self.assertTrue(hasattr(module, 'get_status'))
    
    def test_thermal_controller(self):
        """اختبار Thermal Controller"""
        module = get_thermal_controller()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'start'))
        self.assertTrue(hasattr(module, 'stop'))
        self.assertTrue(hasattr(module, 'get_status'))
    
    def test_power_manager(self):
        """اختبار Power Manager"""
        module = get_power_manager()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'start'))
        self.assertTrue(hasattr(module, 'stop'))
        self.assertTrue(hasattr(module, 'get_status'))
    
    def test_application_curator(self):
        """اختبار Application Curator"""
        module = get_application_curator()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'start'))
        self.assertTrue(hasattr(module, 'stop'))
        self.assertTrue(hasattr(module, 'get_status'))
    
    def test_registry_guardian(self):
        """اختبار Registry Guardian"""
        module = get_registry_guardian()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'start'))
        self.assertTrue(hasattr(module, 'stop'))
        self.assertTrue(hasattr(module, 'get_status'))
    
    def test_backup_orchestrator(self):
        """اختبار Backup Orchestrator"""
        module = get_backup_orchestrator()
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'start'))
        self.assertTrue(hasattr(module, 'stop'))
        self.assertTrue(hasattr(module, 'get_status'))


class TestModuleLifecycle(unittest.TestCase):
    """اختبار دورة حياة الموديولات"""
    
    def test_module_start_stop(self):
        """اختبار بدء وإيقاف الموديول"""
        module = get_disk_orchestrator()
        
        # Test start
        module.start()
        status = module.get_status()
        self.assertIsNotNone(status)
        
        # Test stop
        module.stop()


if __name__ == '__main__':
    unittest.main()
