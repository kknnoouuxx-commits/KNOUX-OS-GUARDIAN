"""
Database Management
إدارة قاعدة البيانات SQLite
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from datetime import datetime
from src.core.serialization import safe_json_dumps

logger = logging.getLogger(__name__)


class DatabaseManager:
    """مدير قاعدة البيانات"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = Path.cwd() / 'database' / 'knoux_guardian.db'
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._initialize_database()
        logger.info(f"Database initialized: {self.db_path}")
    
    def _initialize_database(self):
        """إنشاء الجداول الأساسية"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # System snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id TEXT UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    snapshot_path TEXT,
                    can_rollback BOOLEAN DEFAULT 1
                )
            """)
            
            # Decision artifacts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decision_artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    rule_id TEXT,
                    rule_name TEXT,
                    explanation TEXT,
                    result_json TEXT
                )
            """)
            
            # System events log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    module_name TEXT,
                    severity TEXT,
                    message TEXT,
                    details_json TEXT
                )
            """)
            
            conn.commit()
            logger.info("Database tables initialized")
    
    @contextmanager
    def get_connection(self):
        """الحصول على اتصال بقاعدة البيانات"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def log_event(self, event_type: str, module_name: str, 
                  severity: str, message: str, details: dict = None):
        """تسجيل حدث في قاعدة البيانات"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_events 
                (event_type, module_name, severity, message, details_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event_type,
                module_name,
                severity,
                message,
                safe_json_dumps(details) if details else None
            ))
            conn.commit()

    def fetch_events(self,
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     event_type: Optional[str] = None,
                     module_name: Optional[str] = None,
                     severity: Optional[str] = None,
                     limit: int = 1000):
        """قراءة أحداث النظام من قاعدة البيانات"""
        query = """
            SELECT timestamp, event_type, module_name, severity, message, details_json
            FROM system_events
            WHERE 1=1
        """
        params = []

        if start_time is not None:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat(sep=' '))

        if end_time is not None:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat(sep=' '))

        if event_type is not None:
            query += " AND event_type = ?"
            params.append(event_type)

        if module_name is not None:
            query += " AND module_name = ?"
            params.append(module_name)

        if severity is not None:
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(int(limit))

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def count_events(self,
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     event_type: Optional[str] = None,
                     module_name: Optional[str] = None,
                     severity: Optional[str] = None) -> int:
        """حساب عدد الأحداث"""
        query = """
            SELECT COUNT(*) as cnt
            FROM system_events
            WHERE 1=1
        """
        params = []

        if start_time is not None:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat(sep=' '))

        if end_time is not None:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat(sep=' '))

        if event_type is not None:
            query += " AND event_type = ?"
            params.append(event_type)

        if module_name is not None:
            query += " AND module_name = ?"
            params.append(module_name)

        if severity is not None:
            query += " AND severity = ?"
            params.append(severity)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    def log_decision_artifact(self,
                             decision_id: str,
                             rule_id: str,
                             rule_name: str,
                             explanation: str,
                             result: dict):
        """تسجيل نتيجة قرار في جدول decision_artifacts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO decision_artifacts
                (decision_id, rule_id, rule_name, explanation, result_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                decision_id,
                rule_id,
                rule_name,
                explanation,
                safe_json_dumps(result, ensure_ascii=False)
            ))
            conn.commit()


# Global database instance
_db_instance = None

def get_database() -> DatabaseManager:
    """الحصول على instance قاعدة البيانات العامة"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
