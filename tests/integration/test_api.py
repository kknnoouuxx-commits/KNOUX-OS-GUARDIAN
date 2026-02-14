#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KNOUX OS Guardian - API Integration Tests
اختبارات تكامل API
"""

import unittest
import sys
from pathlib import Path
import json

# Add api to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from fastapi.testclient import TestClient
    from api.main import app
    
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    print("⚠️  FastAPI not installed. Skipping API tests.")


@unittest.skipIf(not API_AVAILABLE, "FastAPI not available")
class TestAPIAuthentication(unittest.TestCase):
    """اختبارات المصادقة في API"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """اختبار نقطة الصحة"""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
    
    def test_login_admin(self):
        """اختبار تسجيل دخول المسؤول"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
    
    def test_login_analyst(self):
        """اختبار تسجيل دخول المحلل"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "analyst",
            "password": "analyst123"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
    
    def test_login_viewer(self):
        """اختبار تسجيل دخول المشاهد"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "viewer",
            "password": "viewer123"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
    
    def test_login_invalid_credentials(self):
        """اختبار بيانات دخول خاطئة"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "invalid",
            "password": "invalid"
        })
        self.assertEqual(response.status_code, 401)
    
    def test_unauthorized_access(self):
        """اختبار الوصول غير المصرح"""
        response = self.client.get("/api/v1/modules")
        self.assertEqual(response.status_code, 401)


@unittest.skipIf(not API_AVAILABLE, "FastAPI not available")
class TestAPIModules(unittest.TestCase):
    """اختبارات موديولات API"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.client = TestClient(app)
        
        # Login as admin
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_modules(self):
        """اختبار قائمة الموديولات"""
        response = self.client.get("/api/v1/modules", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 12)
    
    def test_disk_orchestrator_status(self):
        """اختبار حالة Disk Orchestrator"""
        response = self.client.get(
            "/api/v1/modules/DiskSpaceOrchestrator/status",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("module_name", data)
    
    def test_network_monitor_status(self):
        """اختبار حالة Network Monitor"""
        response = self.client.get(
            "/api/v1/modules/NetworkMonitor/status",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)


@unittest.skipIf(not API_AVAILABLE, "FastAPI not available")
class TestAPIRBAC(unittest.TestCase):
    """اختبارات التحكم في الوصول"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.client = TestClient(app)
        
        # Get tokens for all roles
        self.admin_token = self.client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "admin123"
        }).json()["access_token"]
        
        self.analyst_token = self.client.post("/api/v1/auth/login", json={
            "username": "analyst", "password": "analyst123"
        }).json()["access_token"]
        
        self.viewer_token = self.client.post("/api/v1/auth/login", json={
            "username": "viewer", "password": "viewer123"
        }).json()["access_token"]
    
    def test_viewer_can_read(self):
        """اختبار قدرة المشاهد على القراءة"""
        response = self.client.get(
            "/api/v1/modules/DiskSpaceOrchestrator/status",
            headers={"Authorization": f"Bearer {self.viewer_token}"}
        )
        self.assertEqual(response.status_code, 200)
    
    def test_viewer_cannot_execute(self):
        """اختبار عدم قدرة المشاهد على التنفيذ"""
        response = self.client.post(
            "/api/v1/modules/DiskSpaceOrchestrator/execute",
            headers={"Authorization": f"Bearer {self.viewer_token}"},
            json={"run_mode": "immediate", "details": {}}
        )
        self.assertEqual(response.status_code, 403)
    
    def test_analyst_can_execute(self):
        """اختبار قدرة المحلل على التنفيذ"""
        response = self.client.post(
            "/api/v1/modules/NetworkMonitor/execute",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
            json={"run_mode": "immediate", "details": {}}
        )
        self.assertIn(response.status_code, [200, 202])
    
    def test_admin_full_access(self):
        """اختبار وصول المسؤول الكامل"""
        response = self.client.post(
            "/api/v1/modules/SecurityHardener/execute",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"run_mode": "immediate", "details": {}}
        )
        self.assertIn(response.status_code, [200, 202])


if __name__ == '__main__':
    unittest.main()
