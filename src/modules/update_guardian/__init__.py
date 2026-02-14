"""
Predictive Update Guardian
إدارة ذكية لتحديثات نظام التشغيل والتطبيقات
"""

import logging
import threading
import time
import subprocess
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from src.core.communication_bus import get_bus
from src.core.safe_execution import safe_execute
from src.core.database import get_database
from src.core.config import get_config

logger = logging.getLogger(__name__)


class UpdateType(Enum):
    """نوع التحديث"""
    SECURITY = "Security"
    FEATURE = "Feature Update"
    DRIVER = "Driver"
    DEFINITION = "Definition"
    CUMULATIVE = "Cumulative Update"


class RiskLevel(Enum):
    """مستوى المخاطرة"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class WindowsUpdate:
    """تحديث Windows"""
    kb_number: str
    title: str
    description: str
    type: UpdateType
    size_mb: float
    release_date: datetime
    is_installed: bool
    is_hidden: bool
    categories: List[str]


@dataclass
class InstallationPlan:
    """خطة التثبيت"""
    update: WindowsUpdate
    risk_score: float
    risk_level: RiskLevel
    scheduled_time: datetime
    restore_point_required: bool
    estimated_duration_minutes: int
    explanation: str


class UpdateGuardian:
    """
    حارس التحديثات التنبؤي
    Predictive Update Guardian
    """
    
    def __init__(self):
        self.bus = get_bus()
        self.db = get_database()
        self.config = get_config()
        self.running = False
        self.monitor_thread = None
        
        # Blacklisted updates
        self.blacklist = self._load_blacklist()
        
        # Update history
        self.update_history = {}
        
        logger.info("Update Guardian initialized")
    
    def start(self):
        """بدء المراقبة"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitor_thread.start()
            
            logger.info("Update Guardian started")
    
    def stop(self):
        """إيقاف المراقبة"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Update Guardian stopped")
    
    def _monitoring_loop(self):
        """حلقة المراقبة الرئيسية"""
        check_interval_hours = self.config.get('modules.update_guardian.check_interval_hours', 6)
        check_interval_seconds = max(300, float(check_interval_hours) * 3600)
        
        while self.running:
            try:
                # Check for updates
                self._check_for_updates()
                
                # Wait for next check
                time.sleep(check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _check_for_updates(self):
        """التحقق من وجود تحديثات جديدة"""
        logger.info("Checking for Windows updates...")
        
        try:
            # Get available updates
            updates = self._enumerate_pending_updates()
            
            if updates:
                logger.info(f"Found {len(updates)} pending updates")
                
                # Assess risk for each update
                for update in updates:
                    risk_assessment = self._assess_update_risk(update)
                    
                    # Log assessment
                    self.db.log_event(
                        event_type='update_assessment',
                        module_name='update_guardian',
                        severity='info',
                        message=f"Update {update.kb_number}: {risk_assessment['risk_level']} risk",
                        details={
                            'update': update.__dict__,
                            'risk_assessment': risk_assessment
                        }
                    )
                    
                    # Take action based on risk
                    self._handle_update_based_on_risk(update, risk_assessment)
            else:
                logger.info("No pending updates found")
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
    
    def _enumerate_pending_updates(self) -> List[WindowsUpdate]:
        """تعداد التحديثات المعلقة"""
        updates = []
        
        try:
            # Use PowerShell to get updates
            ps_command = """
            $Session = New-Object -ComObject Microsoft.Update.Session
            $Searcher = $Session.CreateUpdateSearcher()
            $SearchResult = $Searcher.Search("IsInstalled=0 and IsHidden=0")
            
            $updates = @()
            foreach ($Update in $SearchResult.Updates) {
                $updateObj = @{
                    Title = $Update.Title
                    Description = $Update.Description
                    KB = ""
                    Size = [math]::Round($Update.MaxDownloadSize / 1MB, 2)
                    ReleaseDate = $Update.LastDeploymentChangeTime
                    Categories = @($Update.Categories | % { $_.Name })
                }
                
                # Extract KB number
                if ($Update.Title -match "KB\\d+") {
                    $updateObj.KB = $Matches[0]
                }
                
                $updates += $updateObj
            }
            
            $updates | ConvertTo-Json
            """
            
            timeout_seconds = int(self.config.get('modules.update_guardian.powershell_timeout_seconds', 120))
            timeout_seconds = max(30, timeout_seconds)

            try:
                result = subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds
                )
            except subprocess.TimeoutExpired:
                logger.warning(f"Windows Update query timed out after {timeout_seconds}s")
                return updates
            
            if result.returncode == 0 and result.stdout:
                updates_data = json.loads(result.stdout.strip() or "[]")
                if isinstance(updates_data, dict):
                    updates_data = [updates_data]
                
                for update_data in updates_data:
                    categories = update_data.get('Categories') or []
                    if isinstance(categories, str):
                        categories = [categories]

                    # Determine update type
                    update_type = self._determine_update_type(
                        update_data.get('Title', ''),
                        categories
                    )
                    
                    # Create WindowsUpdate object
                    update = WindowsUpdate(
                        kb_number=update_data.get('KB', ''),
                        title=update_data.get('Title', ''),
                        description=update_data.get('Description', ''),
                        type=update_type,
                        size_mb=float(update_data.get('Size') or 0.0),
                        release_date=self._parse_release_date(update_data.get('ReleaseDate')),
                        is_installed=False,
                        is_hidden=False,
                        categories=categories
                    )
                    
                    # Check if in blacklist
                    if update.kb_number not in self.blacklist:
                        updates.append(update)
        
        except Exception as e:
            logger.error(f"Error enumerating updates: {e}")
        
        return updates

    def _parse_release_date(self, raw_value: Optional[str]) -> datetime:
        """Parse PowerShell datetime outputs safely."""
        if isinstance(raw_value, datetime):
            return raw_value.replace(tzinfo=None)

        if raw_value is None:
            return datetime.now() - timedelta(days=30)

        value = str(raw_value).strip()
        if not value:
            return datetime.now() - timedelta(days=30)

        match = re.search(r"/Date\((\d+)\)/", value)
        if match:
            try:
                return datetime.fromtimestamp(int(match.group(1)) / 1000.0)
            except Exception:
                return datetime.now() - timedelta(days=30)

        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if dt.tzinfo is not None:
                dt = dt.astimezone().replace(tzinfo=None)
            return dt
        except Exception:
            pass

        for fmt in ("%m/%d/%Y %I:%M:%S %p", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except Exception:
                continue

        return datetime.now() - timedelta(days=30)
    
    def _determine_update_type(self, title: str, categories: List[str]) -> UpdateType:
        """تحديد نوع التحديث"""
        title_lower = title.lower()
        
        if any(cat.lower() == 'security updates' for cat in categories):
            return UpdateType.SECURITY
        elif 'feature update' in title_lower:
            return UpdateType.FEATURE
        elif 'driver' in title_lower:
            return UpdateType.DRIVER
        elif 'definition' in title_lower:
            return UpdateType.DEFINITION
        elif 'cumulative' in title_lower:
            return UpdateType.CUMULATIVE
        else:
            return UpdateType.SECURITY  # Default to security
    
    def _assess_update_risk(self, update: WindowsUpdate) -> Dict:
        """تقييم مخاطر التحديث"""
        risk_score = 0.0
        
        # Component 1: Update Type (40% weight)
        type_weights = {
            UpdateType.SECURITY: 20,
            UpdateType.DEFINITION: 10,
            UpdateType.CUMULATIVE: 40,
            UpdateType.DRIVER: 60,
            UpdateType.FEATURE: 50
        }
        risk_score += type_weights.get(update.type, 50) * 0.4
        
        # Component 2: Days since release (30% weight)
        if update.release_date:
            days_since_release = (datetime.now() - update.release_date).days
            
            if days_since_release < 3:
                recency_penalty = 80
            elif days_since_release < 7:
                recency_penalty = 50
            elif days_since_release < 14:
                recency_penalty = 30
            else:
                recency_penalty = 10
            
            risk_score += recency_penalty * 0.3
        else:
            risk_score += 50 * 0.3  # Unknown release date
        
        # Component 3: Size (20% weight)
        if update.size_mb > 1000:  # >1GB
            size_risk = 60
        elif update.size_mb > 500:
            size_risk = 40
        elif update.size_mb > 100:
            size_risk = 20
        else:
            size_risk = 10
        
        risk_score += size_risk * 0.2
        
        # Component 4: Community reputation (10% weight - would be from cloud)
        community_risk = 50  # Default
        risk_score += community_risk * 0.1
        
        # Determine risk level
        if risk_score < 30:
            risk_level = RiskLevel.LOW
        elif risk_score < 60:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH
        
        return {
            'risk_score': min(risk_score, 100),
            'risk_level': risk_level,
            'explanation': self._generate_risk_explanation(update, risk_score, risk_level)
        }
    
    def _generate_risk_explanation(self, update: WindowsUpdate, risk_score: float, risk_level: RiskLevel) -> str:
        """توليد تفسير للمخاطر"""
        explanations = {
            UpdateType.SECURITY: "تحديث أمان مهم، مخاطره منخفضة عادةً",
            UpdateType.FEATURE: "تحديث ميزات قد يسبب مشاكل توافق",
            UpdateType.DRIVER: "تحديثات التعريفات خطيرة وقد تسبب أعطالاً",
            UpdateType.DEFINITION: "تحديثات التعريفات آمنة جداً",
            UpdateType.CUMULATIVE: "تحديثات تراكمية، مخاطر متوسطة"
        }
        
        base_explanation = explanations.get(update.type, "تحديث غير معروف")
        
        if update.release_date:
            days_ago = (datetime.now() - update.release_date).days
            if days_ago < 7:
                base_explanation += f" (صدر منذ {days_ago} أيام فقط)"
        
        if risk_level == RiskLevel.HIGH:
            base_explanation += " - ⚠️ مخاطر عالية، يوصى بالتأجيل"
        elif risk_level == RiskLevel.MEDIUM:
            base_explanation += " - ⚠️ مخاطر متوسطة، يوصى بالانتظار 7 أيام"
        else:
            base_explanation += " - ✅ مخاطر منخفضة، آمن للتثبيت"
        
        return base_explanation
    
    def _handle_update_based_on_risk(self, update: WindowsUpdate, risk_assessment: Dict):
        """معالجة التحديث بناءً على مستوى المخاطرة"""
        risk_level = risk_assessment['risk_level']
        
        if risk_level == RiskLevel.LOW:
            # Auto-install low risk updates
            self._schedule_update_installation(update, risk_assessment)
            
        elif risk_level == RiskLevel.MEDIUM:
            # Defer medium risk updates
            self._defer_update(update, risk_assessment, days=7)
            
        elif risk_level == RiskLevel.HIGH:
            # Block high risk updates
            self._block_update(update, risk_assessment)
    
    def _schedule_update_installation(self, update: WindowsUpdate, risk_assessment: Dict):
        """جدولة تثبيت التحديث"""
        # Find optimal installation time
        optimal_time = self._find_optimal_install_time()
        
        # Create installation plan
        plan = InstallationPlan(
            update=update,
            risk_score=risk_assessment['risk_score'],
            risk_level=risk_assessment['risk_level'],
            scheduled_time=optimal_time,
            restore_point_required=True,
            estimated_duration_minutes=int(update.size_mb / 10),  # Estimate 10MB/min
            explanation=risk_assessment['explanation']
        )
        
        # Log plan
        self.db.log_event(
            event_type='update_scheduled',
            module_name='update_guardian',
            severity='info',
            message=f"Scheduled update {update.kb_number} for {optimal_time}",
            details={'plan': plan.__dict__}
        )
        
        # Publish event for scheduler
        self.bus.publish(
            'update.scheduled',
            source_module='update_guardian',
            payload={
                'update': update.__dict__,
                'plan': plan.__dict__
            }
        )
    
    def _find_optimal_install_time(self) -> datetime:
        """إيجاد الوقت الأمثل للتثبيت"""
        # Default: 3 AM tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        optimal_time = tomorrow.replace(hour=3, minute=0, second=0, microsecond=0)
        
        return optimal_time
    
    def _defer_update(self, update: WindowsUpdate, risk_assessment: Dict, days: int):
        """تأجيل التحديث"""
        defer_until = datetime.now() + timedelta(days=days)
        
        logger.info(f"Deferring update {update.kb_number} until {defer_until}")
        
        # Log deferral
        self.db.log_event(
            event_type='update_deferred',
            module_name='update_guardian',
            severity='warning',
            message=f"Deferred update {update.kb_number} for {days} days",
            details={
                'update': update.__dict__,
                'risk_assessment': risk_assessment,
                'defer_until': defer_until.isoformat()
            }
        )
        
        # Publish event
        self.bus.publish(
            'update.deferred',
            source_module='update_guardian',
            payload={
                'update': update.__dict__,
                'risk_assessment': risk_assessment,
                'defer_until': defer_until.isoformat(),
                'reason': 'Medium risk - waiting for community feedback'
            }
        )
    
    def _block_update(self, update: WindowsUpdate, risk_assessment: Dict):
        """حظر التحديث"""
        logger.warning(f"Blocking update {update.kb_number} due to high risk")
        
        # Add to blacklist
        self.blacklist[update.kb_number] = {
            'blocked_at': datetime.now().isoformat(),
            'reason': 'High risk assessment',
            'risk_score': risk_assessment['risk_score']
        }
        
        # Save blacklist
        self._save_blacklist()
        
        # Log block
        self.db.log_event(
            event_type='update_blocked',
            module_name='update_guardian',
            severity='warning',
            message=f"Blocked update {update.kb_number}",
            details={
                'update': update.__dict__,
                'risk_assessment': risk_assessment,
                'blacklist_entry': self.blacklist[update.kb_number]
            }
        )
        
        # Publish event
        self.bus.publish(
            'update.blocked',
            source_module='update_guardian',
            payload={
                'update': update.__dict__,
                'risk_assessment': risk_assessment,
                'reason': 'High risk - potentially problematic update'
            }
        )
    
    def _load_blacklist(self) -> Dict:
        """تحميل قائمة التحديثات المحظورة"""
        blacklist_file = Path(__file__).parent / 'update_blacklist.json'
        
        if blacklist_file.exists():
            try:
                with open(blacklist_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        else:
            return {}
    
    def _save_blacklist(self):
        """حفظ قائمة التحديثات المحظورة"""
        blacklist_file = Path(__file__).parent / 'update_blacklist.json'
        
        try:
            with open(blacklist_file, 'w', encoding='utf-8') as f:
                json.dump(self.blacklist, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving blacklist: {e}")


# Global instance
_update_guardian_instance = None

def get_update_guardian() -> UpdateGuardian:
    """الحصول على instance الموديول"""
    global _update_guardian_instance
    if _update_guardian_instance is None:
        _update_guardian_instance = UpdateGuardian()
    return _update_guardian_instance
