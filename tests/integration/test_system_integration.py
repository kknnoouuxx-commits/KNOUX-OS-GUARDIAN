#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KNOUX OS Guardian - Integration Tests
اختبارات التكامل للنظام الكامل
"""

import unittest
import sys
from pathlib import Path
import time
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.core.communication_bus import CommunicationBus
from src.core.config import ConfigManager
from src.core.database import DatabaseManager
from src.modules.disk_space_orchestrator import get_disk_orchestrator
from src.modules.network_monitor import get_network_monitor


class TestSystemIntegration(unittest.TestCase):
    """اختبارات تكامل النظام"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.temp_dir = tempfile.mkdtemp()
        self.bus = CommunicationBus()
        self.bus.start()
        self.config = ConfigManager()
        self.db = DatabaseManager(db_path=f"{self.temp_dir}/test.db")
    
    def tearDown(self):
        """تنظيف بعد الاختبار"""
        self.bus.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_module_communication(self):
        """اختبار التواصل بين الموديولات"""
        received_events = []
        
        def event_handler(message):
            received_events.append(message)
        
        # Subscribe to events
        self.bus.subscribe('disk.*', event_handler)
        
        # Create and start module
        disk_module = get_disk_orchestrator()
        disk_module.start()
        
        # Publish event
        self.bus.publish('disk.scan.complete', 'disk_space_orchestrator', {
            'total_space': 1000000,
            'used_space': 500000
        })
        
        time.sleep(0.5)
        
        # Verify event received
        self.assertGreater(len(received_events), 0)
        
        disk_module.stop()
    
    def test_multiple_modules(self):
        """اختبار تشغيل موديولات متعددة"""
        disk_module = get_disk_orchestrator()
        network_module = get_network_monitor()
        
        # Start modules
        disk_module.start()
        network_module.start()
        
        # Get status
        disk_status = disk_module.get_status()
        network_status = network_module.get_status()
        
        self.assertIsNotNone(disk_status)
        self.assertIsNotNone(network_status)
        
        # Stop modules
        disk_module.stop()
        network_module.stop()
    
    def test_event_logging(self):
        """اختبار تسجيل الأحداث"""
        # Log event
        event_id = self.db.log_event(
            event_type='module.start',
            module_name='disk_space_orchestrator',
            severity='info',
            message='Module started',
            details={'version': '1.0.0'}
        )
        
        self.assertIsNotNone(event_id)


class TestEndToEndWorkflow(unittest.TestCase):
    """اختبارات سير العمل الكامل"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.temp_dir = tempfile.mkdtemp()
        self.bus = CommunicationBus()
        self.bus.start()
        self.db = DatabaseManager(db_path=f"{self.temp_dir}/test.db")
    
    def tearDown(self):
        """تنظيف بعد الاختبار"""
        self.bus.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_module_lifecycle(self):
        """اختبار دورة حياة الموديول الكاملة"""
        module = get_disk_orchestrator()
        
        # 1. Start module
        module.start()
        self.db.log_event('module.start', 'disk_space_orchestrator', 'info', 'Started')
        
        # 2. Get status
        status = module.get_status()
        self.assertIsNotNone(status)
        
        # 3. Simulate work
        time.sleep(0.5)
        
        # 4. Stop module
        module.stop()
        self.db.log_event('module.stop', 'disk_space_orchestrator', 'info', 'Stopped')


if __name__ == '__main__':
    unittest.main()
