"""
Decision Orchestrator Engine
محرك اتخاذ القرارات المركزي
"""

import logging
import time
from datetime import datetime
from typing import Dict, List
from enum import Enum
from dataclasses import dataclass
from uuid import uuid4

from src.core.database import get_database

logger = logging.getLogger(__name__)


class RulePriority(Enum):
    """أولوية القواعد"""
    CRITICAL = 1  # استقرار النظام/الأمان
    HIGH = 2      # الأداء/البطارية
    MEDIUM = 3    # التحسين
    LOW = 4       # تجميلي


@dataclass
class DecisionRule:
    """قاعدة قرار"""
    rule_id: str
    name: str
    description: str
    priority: RulePriority
    enabled: bool = True


class RuleEngine:
    """
    محرك القواعد
    Evaluates rules and determines actions
    """
    
    def __init__(self):
        self.rules: List[DecisionRule] = []
        self.execution_history: Dict[str, List[datetime]] = {}
        logger.info("Rule Engine initialized")
    
    def register_rule(self, rule: DecisionRule):
        """تسجيل قاعدة جديدة"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority.value)
        logger.info(f"Registered rule: {rule.rule_id}")
    
    def evaluate_all_rules(self, system_state: Dict) -> List[Dict]:
        """
        تقييم جميع القواعد
        
        Args:
            system_state: حالة النظام الحالية
            
        Returns:
            قائمة الإجراءات المقترحة
        """
        proposed_actions = []

        cpu_usage = float(system_state.get('cpu_usage', 0.0) or 0.0)
        memory_usage = float(system_state.get('memory_usage', 0.0) or 0.0)
        disk_free_percent = float(system_state.get('disk_free_percent', 100.0) or 100.0)
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            if rule.rule_id == 'cpu.high_usage' and cpu_usage >= 85:
                proposed_actions.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.name,
                    'priority': rule.priority.name,
                    'action_type': 'notify',
                    'risk_level': 'low',
                    'summary': 'High CPU usage detected',
                    'details': {
                        'cpu_usage': cpu_usage,
                        'threshold': 85
                    }
                })

            elif rule.rule_id == 'memory.high_usage' and memory_usage >= 90:
                proposed_actions.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.name,
                    'priority': rule.priority.name,
                    'action_type': 'notify',
                    'risk_level': 'low',
                    'summary': 'High memory usage detected',
                    'details': {
                        'memory_usage': memory_usage,
                        'threshold': 90
                    }
                })

            elif rule.rule_id == 'disk.low_space' and disk_free_percent <= 10:
                proposed_actions.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.name,
                    'priority': rule.priority.name,
                    'action_type': 'notify',
                    'risk_level': 'low',
                    'summary': 'Low disk free space detected',
                    'details': {
                        'disk_free_percent': disk_free_percent,
                        'threshold': 10
                    }
                })
        
        return proposed_actions


class DecisionOrchestrator:
    """
    المنسق الرئيسي للقرارات
    Main orchestrator that coordinates all decision-making
    """
    
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.db = get_database()
        self.running = False

        self._register_default_rules()
        
        logger.info("Decision Orchestrator initialized")

    def _register_default_rules(self):
        self.rule_engine.register_rule(DecisionRule(
            rule_id='cpu.high_usage',
            name='High CPU Usage',
            description='Detect sustained high CPU usage and notify user/modules',
            priority=RulePriority.HIGH
        ))

        self.rule_engine.register_rule(DecisionRule(
            rule_id='memory.high_usage',
            name='High Memory Usage',
            description='Detect low available memory and notify user/modules',
            priority=RulePriority.HIGH
        ))

        self.rule_engine.register_rule(DecisionRule(
            rule_id='disk.low_space',
            name='Low Disk Space',
            description='Detect low disk free percentage and notify user/modules',
            priority=RulePriority.CRITICAL
        ))
    
    def main_loop(self):
        """الحلقة الرئيسية لاتخاذ القرارات"""
        self.running = True
        logger.info("Decision Orchestrator main loop started")
        
        try:
            while self.running:
                # Step 1: Collect system state
                system_state = self._collect_system_state()
                
                # Step 2: Evaluate rules
                proposed_actions = self.rule_engine.evaluate_all_rules(system_state)
                
                # Step 3: Execute actions (if any)
                if proposed_actions:
                    logger.info(f"Proposed {len(proposed_actions)} actions")

                    for action in proposed_actions:
                        decision_id = str(uuid4())
                        explanation = action.get('summary', '')

                        try:
                            self.db.log_decision_artifact(
                                decision_id=decision_id,
                                rule_id=action.get('rule_id', ''),
                                rule_name=action.get('rule_name', ''),
                                explanation=explanation,
                                result=action
                            )
                        except Exception as e:
                            logger.error(f"Failed to persist decision artifact: {e}")
                
                # Sleep for 30 seconds
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("Decision loop interrupted")
            self.running = False
    
    def _collect_system_state(self) -> Dict:
        """جمع حالة النظام الحالية"""
        import psutil
        
        state = {
            'timestamp': datetime.now(),
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
        }
        
        # Add disk usage
        try:
            disk = psutil.disk_usage('/')
            state['disk_free_percent'] = (disk.free / disk.total) * 100
        except:
            state['disk_free_percent'] = 100
        
        return state
