#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KNOUX OS Guardian - Unit Tests for Core Components
اختبارات الوحدة للمكونات الأساسية
"""

import unittest
import sys
from pathlib import Path
import tempfile
import shutil
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.core.communication_bus import CommunicationBus, Message, MessageType
from src.core.config import ConfigManager
from src.core.database import DatabaseManager
from src.core.safe_execution import SnapshotManager


class TestCommunicationBus(unittest.TestCase):
    """اختبارات ناقل الاتصال"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.bus = CommunicationBus()
        self.bus.start()
        self.received_messages = []
    
    def tearDown(self):
        """تنظيف بعد الاختبار"""
        self.bus.stop()
    
    def test_publish_subscribe(self):
        """اختبار النشر والاشتراك"""
        def callback(message):
            self.received_messages.append(message)
        
        self.bus.subscribe('test.event', callback)
        self.bus.publish('test.event', 'test_module', {'data': 'test'})
        
        time.sleep(0.5)  # Wait for processing
        
        self.assertEqual(len(self.received_messages), 1)
        self.assertEqual(self.received_messages[0].topic, 'test.event')
    
    def test_wildcard_subscription(self):
        """اختبار الاشتراك بالبدل"""
        def callback(message):
            self.received_messages.append(message)
        
        self.bus.subscribe('test.*', callback)
        self.bus.publish('test.event1', 'test_module', {})
        self.bus.publish('test.event2', 'test_module', {})
        
        time.sleep(0.5)
        
        self.assertEqual(len(self.received_messages), 2)
    
    def test_unsubscribe(self):
        """اختبار إلغاء الاشتراك"""
        def callback(message):
            self.received_messages.append(message)
        
        self.bus.subscribe('test.event', callback)
        self.bus.unsubscribe('test.event', callback)
        self.bus.publish('test.event', 'test_module', {})
        
        time.sleep(0.5)
        
        self.assertEqual(len(self.received_messages), 0)


class TestConfigManager(unittest.TestCase):
    """اختبارات مدير الإعدادات"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.config = ConfigManager()
    
    def test_get_config(self):
        """اختبار قراءة الإعدادات"""
        offline_first = self.config.get('system.offline_first', True)
        self.assertIsInstance(offline_first, bool)
    
    def test_module_enabled(self):
        """اختبار حالة تفعيل الموديول"""
        enabled = self.config.is_module_enabled('disk_space_orchestrator')
        self.assertIsInstance(enabled, bool)
    
    def test_default_value(self):
        """اختبار القيمة الافتراضية"""
        value = self.config.get('nonexistent.key', 'default')
        self.assertEqual(value, 'default')


class TestDatabaseManager(unittest.TestCase):
    """اختبارات مدير قاعدة البيانات"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.temp_dir = tempfile.mkdtemp()
        self.db = DatabaseManager(db_path=f"{self.temp_dir}/test.db")
    
    def tearDown(self):
        """تنظيف بعد الاختبار"""
        shutil.rmtree(self.temp_dir)
    
    def test_log_event(self):
        """اختبار تسجيل حدث"""
        event_id = self.db.log_event(
            event_type='test',
            module_name='test_module',
            severity='info',
            message='Test event',
            details={'test': True}
        )
        self.assertIsNotNone(event_id)
    
    def test_context_manager(self):
        """اختبار مدير السياق"""
        with self.db as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)


class TestSnapshotManager(unittest.TestCase):
    """اختبارات مدير اللقطات"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.temp_dir = tempfile.mkdtemp()
        self.snapshot_mgr = SnapshotManager(snapshot_dir=self.temp_dir)
    
    def tearDown(self):
        """تنظيف بعد الاختبار"""
        shutil.rmtree(self.temp_dir)
    
    def test_create_snapshot(self):
        """اختبار إنشاء لقطة"""
        snapshot_id = self.snapshot_mgr.create_snapshot("Test snapshot")
        self.assertIsNotNone(snapshot_id)
    
    def test_list_snapshots(self):
        """اختبار قائمة اللقطات"""
        self.snapshot_mgr.create_snapshot("Test 1")
        self.snapshot_mgr.create_snapshot("Test 2")
        
        snapshots = self.snapshot_mgr.list_snapshots()
        self.assertGreaterEqual(len(snapshots), 2)
    
    def test_cleanup_old_snapshots(self):
        """اختبار تنظيف اللقطات القديمة"""
        for i in range(10):
            self.snapshot_mgr.create_snapshot(f"Test {i}")
        
        self.snapshot_mgr.cleanup_old_snapshots(keep_last_n=5)
        snapshots = self.snapshot_mgr.list_snapshots()
        self.assertLessEqual(len(snapshots), 5)


if __name__ == '__main__':
    unittest.main()
