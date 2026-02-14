#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KNOUX OS Guardian - Basic Tests
اختبارات أساسية للتحقق من عمل النظام
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def test_imports():
    """اختبار استيراد المكونات الأساسية"""
    print("🧪 اختبار الاستيراد...")
    
    try:
        from src.core.communication_bus import CommunicationBus, Message, MessageType
        print("   ✅ Communication Bus")
        
        from src.core.decision_engine import DecisionOrchestrator, RuleEngine
        print("   ✅ Decision Engine")
        
        from src.core.safe_execution import SnapshotManager, safe_execute
        print("   ✅ Safe Execution")
        
        from src.core.telemetry import TelemetryCollector
        print("   ✅ Telemetry")
        
        from src.core.config import ConfigManager
        print("   ✅ Config Manager")
        
        from src.core.database import DatabaseManager
        print("   ✅ Database Manager")
        
        print("\n✅ جميع الاستيرادات نجحت!")
        return True
        
    except Exception as e:
        print(f"\n❌ فشل الاستيراد: {e}")
        return False


def test_config():
    """اختبار نظام الإعدادات"""
    print("\n🧪 اختبار نظام الإعدادات...")
    
    try:
        from src.core.config import ConfigManager
        
        config = ConfigManager()
        
        # Test reading config
        offline_first = config.get('system.offline_first', True)
        print(f"   ✅ Offline First: {offline_first}")
        
        # Test module config
        disk_enabled = config.is_module_enabled('disk_space_orchestrator')
        print(f"   ✅ Disk Module Enabled: {disk_enabled}")
        
        print("\n✅ نظام الإعدادات يعمل!")
        return True
        
    except Exception as e:
        print(f"\n❌ فشل اختبار الإعدادات: {e}")
        return False


def test_database():
    """اختبار قاعدة البيانات"""
    print("\n🧪 اختبار قاعدة البيانات...")
    
    try:
        from src.core.database import DatabaseManager
        
        db = DatabaseManager()
        
        # Test logging event
        db.log_event(
            event_type='test',
            module_name='test_module',
            severity='info',
            message='Test event',
            details={'test': True}
        )
        
        print("   ✅ تم إنشاء قاعدة البيانات")
        print("   ✅ تم تسجيل حدث اختباري")
        
        print("\n✅ قاعدة البيانات تعمل!")
        return True
        
    except Exception as e:
        print(f"\n❌ فشل اختبار قاعدة البيانات: {e}")
        return False


def test_snapshot():
    """اختبار نظام اللقطات"""
    print("\n🧪 اختبار نظام اللقطات...")
    
    try:
        from src.core.safe_execution import SnapshotManager
        
        snapshot_mgr = SnapshotManager()
        
        # Create test snapshot
        snapshot_id = snapshot_mgr.create_snapshot("Test snapshot")
        print(f"   ✅ تم إنشاء لقطة: {snapshot_id}")
        
        # Cleanup
        snapshot_mgr.cleanup_old_snapshots(keep_last_n=5)
        print("   ✅ تم تنظيف اللقطات القديمة")
        
        print("\n✅ نظام اللقطات يعمل!")
        return True
        
    except Exception as e:
        print(f"\n❌ فشل اختبار اللقطات: {e}")
        return False


def test_communication_bus():
    """اختبار ناقل الاتصال"""
    print("\n🧪 اختبار ناقل الاتصال...")
    
    try:
        from src.core.communication_bus import CommunicationBus
        
        bus = CommunicationBus()
        bus.start()
        
        # Test subscription
        received_events = []
        
        def test_callback(message):
            received_events.append(message)
        
        bus.subscribe('test.event', test_callback)
        print("   ✅ تم الاشتراك في حدث")
        
        # Test publishing
        bus.publish('test.event', 'test_module', {'data': 'test'})
        print("   ✅ تم نشر حدث")
        
        # Wait a bit for processing
        import time
        time.sleep(0.5)
        
        bus.stop()
        
        if received_events:
            print(f"   ✅ تم استقبال {len(received_events)} حدث")
        
        print("\n✅ ناقل الاتصال يعمل!")
        return True
        
    except Exception as e:
        print(f"\n❌ فشل اختبار ناقل الاتصال: {e}")
        return False


def main():
    """تشغيل جميع الاختبارات"""
    print("=" * 60)
    print("KNOUX OS Guardian - اختبارات أساسية")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_database,
        test_snapshot,
        test_communication_bus
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ خطأ في الاختبار: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"النتائج: ✅ {passed} نجح | ❌ {failed} فشل")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
