"""
Inter-Module Communication Bus
نظام الاتصال بين الموديولات
"""

import json
import queue
import threading
import logging
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List
from uuid import uuid4

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """أنواع الرسائل"""
    EVENT = "event"
    QUERY = "query"
    COMMAND = "command"
    RESPONSE = "response"


@dataclass
class Message:
    """رسالة بين الموديولات"""
    message_id: str
    type: MessageType
    source_module: str
    target_module: str
    payload: Dict
    timestamp: datetime
    correlation_id: str = None


class CommunicationBus:
    """
    ناقل الاتصال المركزي بين الموديولات
    Central message bus for inter-module communication
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.lock = threading.Lock()
        self.message_queue = queue.Queue()
        self.running = False
        self.processor_thread = None
        
        logger.info("Communication Bus initialized")
    
    def start(self):
        """بدء معالجة الرسائل"""
        if not self.running:
            self.running = True
            self.processor_thread = threading.Thread(
                target=self._process_messages,
                daemon=True
            )
            self.processor_thread.start()
            logger.info("Communication Bus started")
    
    def stop(self):
        """إيقاف معالجة الرسائل"""
        self.running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        logger.info("Communication Bus stopped")
    
    def subscribe(self, event_type: str, callback: Callable):
        """
        الاشتراك في نوع حدث معين
        
        Args:
            event_type: نوع الحدث (مثل: 'disk_space.low')
            callback: دالة يتم استدعاؤها عند حدوث الحدث
        """
        with self.lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            
            self.subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to {event_type}")
    
    def publish(self, event_type: str, source_module: str, payload: Dict):
        """
        نشر حدث على الناقل
        
        Args:
            event_type: نوع الحدث
            source_module: الموديول المصدر
            payload: البيانات المرفقة
        """
        message = Message(
            message_id=str(uuid4()),
            type=MessageType.EVENT,
            source_module=source_module,
            target_module='*',
            payload=payload,
            timestamp=datetime.now()
        )
        
        self.message_queue.put((event_type, message))
        logger.debug(f"Published event: {event_type} from {source_module}")
    
    def _process_messages(self):
        """معالجة الرسائل في الخلفية"""
        while self.running:
            try:
                event_type, message = self.message_queue.get(timeout=1)
                
                # Find subscribers
                with self.lock:
                    callbacks = self.subscribers.get(event_type, [])
                    wildcard_callbacks = self.subscribers.get('*', [])
                    callbacks.extend(wildcard_callbacks)
                
                # Call each subscriber
                for callback in callbacks:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error(f"Error in subscriber callback: {e}")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")


# Global bus instance
_bus_instance = None

def get_bus() -> CommunicationBus:
    """الحصول على instance الناقل العام"""
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = CommunicationBus()
        _bus_instance.start()
    return _bus_instance
