#!/usr/bin/env python3
"""
AI Avatar Assistant - Smart Notification System
Intelligent notifications with priority filtering and multiple delivery channels
"""

import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import queue

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class NotificationChannel(Enum):
    """Notification delivery channels"""
    SYSTEM = "system"           # System tray notifications
    VOICE = "voice"             # Text-to-speech
    VISUAL = "visual"           # In-app notifications
    LOG = "log"                 # Log file only
    EMAIL = "email"             # Email notifications (future)
    WEBHOOK = "webhook"         # Webhook/API notifications

class NotificationCategory(Enum):
    """Notification categories"""
    SYSTEM = "system"           # System status, health alerts
    AI = "ai"                   # AI model status, responses
    PROJECT = "project"         # Project updates, deadlines
    TASK = "task"               # Task completions, reminders
    PERFORMANCE = "performance" # Performance alerts, optimization
    SECURITY = "security"       # Security alerts, access issues
    USER = "user"               # User interactions, feedback

@dataclass
class NotificationRule:
    """Rules for notification filtering and routing"""
    id: str
    name: str
    description: str
    category: NotificationCategory
    min_priority: NotificationPriority
    channels: List[NotificationChannel]
    conditions: Dict[str, Any]
    quiet_hours: Optional[Dict[str, str]] = None  # {"start": "22:00", "end": "08:00"}
    is_active: bool = True

@dataclass
class Notification:
    """Individual notification"""
    id: str
    timestamp: datetime
    title: str
    message: str
    category: NotificationCategory
    priority: NotificationPriority
    source: str
    data: Dict[str, Any]
    channels: List[NotificationChannel]
    is_delivered: bool = False
    delivery_attempts: int = 0
    delivered_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None

class SmartNotificationSystem:
    """Intelligent notification system with priority filtering and smart delivery"""
    
    def __init__(self, voice_system=None):
        self.logger = logging.getLogger(__name__)
        self.voice_system = voice_system
        
        # Notification storage
        self.pending_notifications: queue.PriorityQueue = queue.PriorityQueue()
        self.delivered_notifications: List[Notification] = []
        self.notification_rules: Dict[str, NotificationRule] = {}
        
        # Processing thread
        self.is_running = False
        self.processor_thread = None
        
        # Statistics
        self.stats = {
            "total_sent": 0,
            "total_acknowledged": 0,
            "delivery_failures": 0,
            "last_reset": datetime.now()
        }
        
        # Configuration
        self.config_file = "data/notification_config.json"
        self.max_history = 1000
        self.delivery_retry_delay = 30  # seconds
        
        # Callbacks for different channels
        self.channel_handlers: Dict[NotificationChannel, Callable] = {}
        
        self.load_configuration()
        self.setup_default_rules()
    
    def load_configuration(self):
        """Load notification configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Load rules
                for rule_data in config.get('rules', []):
                    rule = NotificationRule(**rule_data)
                    self.notification_rules[rule.id] = rule
                
                # Load settings
                settings = config.get('settings', {})
                self.max_history = settings.get('max_history', 1000)
                self.delivery_retry_delay = settings.get('delivery_retry_delay', 30)
                
                self.logger.info("Notification configuration loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to load notification config: {e}")
    
    def save_configuration(self):
        """Save notification configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            config = {
                "rules": [asdict(rule) for rule in self.notification_rules.values()],
                "settings": {
                    "max_history": self.max_history,
                    "delivery_retry_delay": self.delivery_retry_delay
                },
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save notification config: {e}")
    
    def setup_default_rules(self):
        """Setup default notification rules"""
        if not self.notification_rules:
            default_rules = [
                NotificationRule(
                    id="critical_system",
                    name="Critical System Alerts",
                    description="Critical system health alerts require immediate attention",
                    category=NotificationCategory.SYSTEM,
                    min_priority=NotificationPriority.CRITICAL,
                    channels=[NotificationChannel.SYSTEM, NotificationChannel.VOICE, NotificationChannel.VISUAL],
                    conditions={"severity": "critical"}
                ),
                NotificationRule(
                    id="ai_performance",
                    name="AI Performance Issues",
                    description="AI model performance and availability alerts",
                    category=NotificationCategory.AI,
                    min_priority=NotificationPriority.HIGH,
                    channels=[NotificationChannel.VISUAL, NotificationChannel.LOG],
                    conditions={}
                ),
                NotificationRule(
                    id="project_deadlines",
                    name="Project Deadlines",
                    description="Project deadline reminders and alerts",
                    category=NotificationCategory.PROJECT,
                    min_priority=NotificationPriority.NORMAL,
                    channels=[NotificationChannel.SYSTEM, NotificationChannel.VISUAL],
                    conditions={},
                    quiet_hours={"start": "22:00", "end": "08:00"}
                ),
                NotificationRule(
                    id="task_completions",
                    name="Task Completions",
                    description="Task completion notifications",
                    category=NotificationCategory.TASK,
                    min_priority=NotificationPriority.LOW,
                    channels=[NotificationChannel.VISUAL],
                    conditions={}
                ),
                NotificationRule(
                    id="security_alerts",
                    name="Security Alerts",
                    description="Security-related notifications",
                    category=NotificationCategory.SECURITY,
                    min_priority=NotificationPriority.HIGH,
                    channels=[NotificationChannel.SYSTEM, NotificationChannel.VISUAL, NotificationChannel.LOG],
                    conditions={}
                )
            ]
            
            for rule in default_rules:
                self.notification_rules[rule.id] = rule
            
            self.save_configuration()
    
    def start(self):
        """Start the notification processing system"""
        if self.is_running:
            return
        
        self.is_running = True
        self.processor_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.processor_thread.start()
        self.logger.info("Smart notification system started")
    
    def stop(self):
        """Stop the notification processing system"""
        self.is_running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        self.logger.info("Smart notification system stopped")
    
    def _processing_loop(self):
        """Main notification processing loop"""
        while self.is_running:
            try:
                # Get notification with timeout
                try:
                    priority, notification = self.pending_notifications.get(timeout=1.0)
                    self._process_notification(notification)
                    self.pending_notifications.task_done()
                except queue.Empty:
                    continue
                
            except Exception as e:
                self.logger.error(f"Notification processing error: {e}")
                time.sleep(1)
    
    def _process_notification(self, notification: Notification):
        """Process a single notification"""
        try:
            # Check if in quiet hours
            if self._is_quiet_hours(notification):
                # Reschedule for later
                self._reschedule_notification(notification)
                return
            
            # Deliver via specified channels
            success = False
            for channel in notification.channels:
                if self._deliver_via_channel(notification, channel):
                    success = True
            
            if success:
                notification.is_delivered = True
                notification.delivered_at = datetime.now()
                self.delivered_notifications.append(notification)
                self.stats["total_sent"] += 1
                
                # Keep history manageable
                if len(self.delivered_notifications) > self.max_history:
                    self.delivered_notifications = self.delivered_notifications[-self.max_history:]
                
                self.logger.debug(f"Notification delivered: {notification.title}")
            else:
                # Retry later if critical
                if notification.priority in [NotificationPriority.URGENT, NotificationPriority.CRITICAL]:
                    notification.delivery_attempts += 1
                    if notification.delivery_attempts < 3:
                        threading.Timer(
                            self.delivery_retry_delay,
                            lambda: self.pending_notifications.put((self._get_priority_value(notification.priority), notification))
                        ).start()
                
                self.stats["delivery_failures"] += 1
                
        except Exception as e:
            self.logger.error(f"Failed to process notification: {e}")
    
    def _deliver_via_channel(self, notification: Notification, channel: NotificationChannel) -> bool:
        """Deliver notification via specific channel"""
        try:
            if channel in self.channel_handlers:
                return self.channel_handlers[channel](notification)
            
            # Built-in channel handlers
            if channel == NotificationChannel.LOG:
                return self._deliver_log(notification)
            elif channel == NotificationChannel.VOICE and self.voice_system:
                return self._deliver_voice(notification)
            elif channel == NotificationChannel.VISUAL:
                return self._deliver_visual(notification)
            elif channel == NotificationChannel.SYSTEM:
                return self._deliver_system(notification)
            else:
                self.logger.warning(f"No handler for channel: {channel}")
                return False
                
        except Exception as e:
            self.logger.error(f"Channel delivery error ({channel}): {e}")
            return False
    
    def _deliver_log(self, notification: Notification) -> bool:
        """Deliver notification to log"""
        log_level = {
            NotificationPriority.LOW: logging.INFO,
            NotificationPriority.NORMAL: logging.INFO,
            NotificationPriority.HIGH: logging.WARNING,
            NotificationPriority.URGENT: logging.ERROR,
            NotificationPriority.CRITICAL: logging.CRITICAL
        }.get(notification.priority, logging.INFO)
        
        self.logger.log(log_level, f"[{notification.category.value.upper()}] {notification.title}: {notification.message}")
        return True
    
    def _deliver_voice(self, notification: Notification) -> bool:
        """Deliver notification via voice"""
        if not self.voice_system:
            return False
        
        # Create voice-friendly message
        voice_message = f"{notification.title}. {notification.message}"
        
        # Only speak high priority notifications
        if notification.priority.value in ['high', 'urgent', 'critical']:
            return self.voice_system.speak_async(voice_message)
        
        return True
    
    def _deliver_visual(self, notification: Notification) -> bool:
        """Deliver notification via visual UI"""
        # This would integrate with the main UI to show notifications
        # For now, just log the visual delivery
        self.logger.info(f"Visual notification: {notification.title}")
        return True
    
    def _deliver_system(self, notification: Notification) -> bool:
        """Deliver notification via system tray"""
        # System tray notification (platform-specific implementation needed)
        self.logger.info(f"System notification: {notification.title}")
        return True
    
    def _is_quiet_hours(self, notification: Notification) -> bool:
        """Check if current time is in quiet hours for this notification"""
        # Find applicable rule
        applicable_rule = None
        for rule in self.notification_rules.values():
            if (rule.category == notification.category and 
                rule.min_priority.value <= notification.priority.value and
                rule.is_active):
                applicable_rule = rule
                break
        
        if not applicable_rule or not applicable_rule.quiet_hours:
            return False
        
        # Check if in quiet hours
        now = datetime.now().time()
        quiet_start = datetime.strptime(applicable_rule.quiet_hours["start"], "%H:%M").time()
        quiet_end = datetime.strptime(applicable_rule.quiet_hours["end"], "%H:%M").time()
        
        if quiet_start <= quiet_end:
            return quiet_start <= now <= quiet_end
        else:  # Overnight quiet hours
            return now >= quiet_start or now <= quiet_end
    
    def _reschedule_notification(self, notification: Notification):
        """Reschedule notification for after quiet hours"""
        # Find next available time after quiet hours
        now = datetime.now()
        next_time = now + timedelta(hours=1)  # Try again in 1 hour
        
        threading.Timer(
            (next_time - now).total_seconds(),
            lambda: self.pending_notifications.put((self._get_priority_value(notification.priority), notification))
        ).start()
    
    def _get_priority_value(self, priority: NotificationPriority) -> int:
        """Get numeric value for priority (lower = higher priority)"""
        priority_values = {
            NotificationPriority.CRITICAL: 0,
            NotificationPriority.URGENT: 1,
            NotificationPriority.HIGH: 2,
            NotificationPriority.NORMAL: 3,
            NotificationPriority.LOW: 4
        }
        return priority_values.get(priority, 5)
    
    def send_notification(self, title: str, message: str, 
                         category: NotificationCategory = NotificationCategory.SYSTEM,
                         priority: NotificationPriority = NotificationPriority.NORMAL,
                         source: str = "system",
                         data: Optional[Dict[str, Any]] = None) -> str:
        """Send a notification"""
        notification_id = f"{category.value}_{int(time.time() * 1000)}"
        
        # Determine channels based on rules
        channels = self._get_channels_for_notification(category, priority)
        
        notification = Notification(
            id=notification_id,
            timestamp=datetime.now(),
            title=title,
            message=message,
            category=category,
            priority=priority,
            source=source,
            data=data or {},
            channels=channels
        )
        
        # Add to processing queue with priority
        self.pending_notifications.put((self._get_priority_value(priority), notification))
        
        return notification_id
    
    def _get_channels_for_notification(self, category: NotificationCategory, 
                                     priority: NotificationPriority) -> List[NotificationChannel]:
        """Get delivery channels for notification based on rules"""
        channels = [NotificationChannel.LOG]  # Always log
        
        for rule in self.notification_rules.values():
            if (rule.category == category and 
                self._get_priority_value(priority) <= self._get_priority_value(rule.min_priority) and
                rule.is_active):
                channels.extend(rule.channels)
                break
        
        return list(set(channels))  # Remove duplicates
    
    def acknowledge_notification(self, notification_id: str) -> bool:
        """Acknowledge a notification"""
        for notification in self.delivered_notifications:
            if notification.id == notification_id and not notification.acknowledged:
                notification.acknowledged = True
                notification.acknowledged_at = datetime.now()
                self.stats["total_acknowledged"] += 1
                return True
        
        return False
    
    def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Get list of pending notifications"""
        # Note: This is a simplified version as PriorityQueue doesn't easily support iteration
        return [{"status": "pending", "count": self.pending_notifications.qsize()}]
    
    def get_recent_notifications(self, hours: int = 24, 
                               category: Optional[NotificationCategory] = None) -> List[Dict[str, Any]]:
        """Get recent notifications"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [
            n for n in self.delivered_notifications 
            if n.timestamp > cutoff and (not category or n.category == category)
        ]
        
        return [asdict(n) for n in sorted(recent, key=lambda x: x.timestamp, reverse=True)]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification system statistics"""
        acknowledged_rate = (
            (self.stats["total_acknowledged"] / max(self.stats["total_sent"], 1)) * 100
        )
        
        failure_rate = (
            (self.stats["delivery_failures"] / max(self.stats["total_sent"] + self.stats["delivery_failures"], 1)) * 100
        )
        
        return {
            "total_sent": self.stats["total_sent"],
            "total_acknowledged": self.stats["total_acknowledged"],
            "delivery_failures": self.stats["delivery_failures"],
            "acknowledged_rate": acknowledged_rate,
            "failure_rate": failure_rate,
            "pending_count": self.pending_notifications.qsize(),
            "rules_active": sum(1 for rule in self.notification_rules.values() if rule.is_active),
            "last_reset": self.stats["last_reset"].isoformat()
        }
    
    def add_rule(self, rule: NotificationRule):
        """Add a notification rule"""
        self.notification_rules[rule.id] = rule
        self.save_configuration()
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a notification rule"""
        if rule_id in self.notification_rules:
            del self.notification_rules[rule_id]
            self.save_configuration()
            return True
        return False
    
    def update_rule(self, rule_id: str, **kwargs) -> bool:
        """Update a notification rule"""
        if rule_id in self.notification_rules:
            rule = self.notification_rules[rule_id]
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            self.save_configuration()
            return True
        return False
    
    def register_channel_handler(self, channel: NotificationChannel, handler: Callable):
        """Register a custom handler for a notification channel"""
        self.channel_handlers[channel] = handler
    
    def test_notification(self, channel: NotificationChannel = NotificationChannel.VISUAL):
        """Send a test notification"""
        return self.send_notification(
            title="Test Notification",
            message="This is a test notification from the AI Avatar Assistant",
            category=NotificationCategory.SYSTEM,
            priority=NotificationPriority.NORMAL,
            source="test_system"
        )

# Global notification system instance
notification_system = SmartNotificationSystem()