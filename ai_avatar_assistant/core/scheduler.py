from apscheduler.schedulers.qt import QtScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from typing import List, Dict, Callable
import json
import logging
from .database import TaskDatabase
from .ai_engine import AIEngine

class EventScheduler:
    """Background scheduler for monitoring and triggering events"""
    
    def __init__(self, config_path="data/config.json"):
        self.config = self.load_config(config_path)
        self.notification_config = self.config.get("notifications", {})
        
        # Initialize components
        self.db = TaskDatabase()
        self.ai_engine = AIEngine(config_path)
        
        # Initialize scheduler
        self.scheduler = QtScheduler()
        
        # Event callbacks
        self.event_callbacks = {}
        
        # Scheduler state
        self.is_running = False
        self.paused_until = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.setup_scheduled_jobs()
    
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def setup_scheduled_jobs(self):
        """Setup recurring scheduled jobs"""
        # Main event check interval
        check_interval = self.notification_config.get("check_interval", 300)  # 5 minutes
        
        self.scheduler.add_job(
            func=self.check_events,
            trigger=IntervalTrigger(seconds=check_interval),
            id='main_event_check',
            name='Main Event Check',
            max_instances=1,
            replace_existing=True
        )
        
        # AI analysis job (less frequent)
        self.scheduler.add_job(
            func=self.run_ai_analysis,
            trigger=IntervalTrigger(seconds=check_interval * 2),
            id='ai_analysis',
            name='AI Analysis',
            max_instances=1,
            replace_existing=True
        )
        
        # Daily summary (at 9 AM)
        self.scheduler.add_job(
            func=self.generate_daily_summary,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_summary',
            name='Daily Summary',
            replace_existing=True
        )
        
        # Productivity check (every 2 hours during work hours)
        self.scheduler.add_job(
            func=self.productivity_check,
            trigger=CronTrigger(hour='9-17/2'),
            id='productivity_check',
            name='Productivity Check',
            replace_existing=True
        )
        
        # Silent hours check
        self.scheduler.add_job(
            func=self.check_silent_hours,
            trigger=IntervalTrigger(minutes=30),
            id='silent_hours_check',
            name='Silent Hours Check',
            max_instances=1,
            replace_existing=True
        )
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            self.logger.info("Event scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            self.logger.info("Event scheduler stopped")
    
    def pause_notifications(self, minutes: int = 60):
        """Pause notifications for a specified time"""
        self.paused_until = datetime.now() + timedelta(minutes=minutes)
        self.logger.info(f"Notifications paused until {self.paused_until}")
    
    def resume_notifications(self):
        """Resume notifications"""
        self.paused_until = None
        self.logger.info("Notifications resumed")
    
    def is_notifications_paused(self) -> bool:
        """Check if notifications are currently paused"""
        if self.paused_until is None:
            return False
        
        if datetime.now() >= self.paused_until:
            self.paused_until = None
            return False
        
        return True
    
    def is_silent_hours(self) -> bool:
        """Check if current time is within silent hours"""
        if not self.notification_config.get("enabled", True):
            return True
        
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        silent_start = self.notification_config.get("silent_hours_start", "22:00")
        silent_end = self.notification_config.get("silent_hours_end", "08:00")
        
        # Handle overnight silent period (e.g., 22:00 to 08:00)
        if silent_start > silent_end:
            return current_time >= silent_start or current_time <= silent_end
        else:
            return silent_start <= current_time <= silent_end
    
    def should_show_notification(self) -> bool:
        """Determine if notifications should be shown"""
        return (not self.is_notifications_paused() and 
                not self.is_silent_hours())
    
    # Scheduled Job Functions
    def check_events(self):
        """Main event checking function"""
        try:
            if not self.should_show_notification():
                return
            
            # Check database for pending events
            pending_events = self.db.get_pending_events()
            
            for event in pending_events:
                self.trigger_event(event)
                # Mark event as triggered
                self.db.mark_event_triggered(event['id'])
            
        except Exception as e:
            self.logger.error(f"Error in check_events: {e}")
    
    def run_ai_analysis(self):
        """Run AI analysis for intelligent recommendations"""
        try:
            if not self.should_show_notification():
                return
            
            # Get AI recommendations
            recommendations = self.ai_engine.analyze_current_situation()
            
            # Only show the most urgent recommendation
            if recommendations:
                urgent_rec = recommendations[0]  # Already sorted by urgency
                if urgent_rec.get('urgency', 0) > 0.7:  # Only show high urgency items
                    self.trigger_ai_recommendation(urgent_rec)
            
        except Exception as e:
            self.logger.error(f"Error in run_ai_analysis: {e}")
    
    def generate_daily_summary(self):
        """Generate daily task summary"""
        try:
            if not self.should_show_notification():
                return
            
            # Get task statistics
            pending_tasks = self.db.get_tasks(status="pending")
            urgent_tasks = self.db.get_tasks(status="pending", upcoming_hours=24)
            
            summary_data = {
                "type": "daily_summary",
                "title": "🌅 Daily Summary",
                "message": f"Good morning! You have {len(pending_tasks)} pending tasks, with {len(urgent_tasks)} due today.",
                "actions": ["show_tasks", "prioritize_tasks", "start_focus_mode"],
                "urgency": 0.5,
                "metadata": {
                    "total_tasks": len(pending_tasks),
                    "urgent_tasks": len(urgent_tasks)
                }
            }
            
            self.trigger_event(summary_data)
            
        except Exception as e:
            self.logger.error(f"Error in generate_daily_summary: {e}")
    
    def productivity_check(self):
        """Periodic productivity check"""
        try:
            if not self.should_show_notification():
                return
            
            # Check if user has been productive
            current_hour = datetime.now().hour
            
            # Only during work hours
            if 9 <= current_hour <= 17:
                pending_tasks = self.db.get_tasks(status="pending")
                urgent_tasks = [t for t in pending_tasks if t.get('deadline') and 
                              datetime.fromisoformat(t['deadline']) <= datetime.now() + timedelta(hours=4)]
                
                if urgent_tasks:
                    productivity_data = {
                        "type": "productivity_reminder",
                        "title": "⏰ Productivity Check",
                        "message": f"You have {len(urgent_tasks)} urgent tasks. How's your progress?",
                        "actions": ["show_tasks", "start_focus_mode", "snooze"],
                        "urgency": 0.6,
                        "metadata": {"urgent_count": len(urgent_tasks)}
                    }
                    
                    self.trigger_event(productivity_data)
            
        except Exception as e:
            self.logger.error(f"Error in productivity_check: {e}")
    
    def check_silent_hours(self):
        """Check and update silent hours status"""
        # This is mainly for logging and status updates
        if self.is_silent_hours():
            self.logger.debug("Currently in silent hours")
        else:
            self.logger.debug("Active notification period")
    
    # Event Triggering
    def trigger_event(self, event_data: Dict):
        """Trigger an event by calling registered callbacks"""
        event_type = event_data.get('type', 'general')
        
        # Call appropriate callback
        if event_type in self.event_callbacks:
            callback = self.event_callbacks[event_type]
            callback(event_data)
        elif 'default' in self.event_callbacks:
            callback = self.event_callbacks['default']
            callback(event_data)
        else:
            self.logger.warning(f"No callback registered for event type: {event_type}")
    
    def trigger_ai_recommendation(self, recommendation: Dict):
        """Trigger an AI recommendation"""
        # Add some additional context
        recommendation['source'] = 'ai_analysis'
        recommendation['timestamp'] = datetime.now().isoformat()
        
        self.trigger_event(recommendation)
    
    # Callback Management
    def register_event_callback(self, event_type: str, callback: Callable):
        """Register a callback for specific event types"""
        self.event_callbacks[event_type] = callback
        self.logger.info(f"Registered callback for event type: {event_type}")
    
    def register_default_callback(self, callback: Callable):
        """Register a default callback for all events"""
        self.event_callbacks['default'] = callback
        self.logger.info("Registered default event callback")
    
    # Manual Event Creation
    def add_one_time_event(self, event_data: Dict, trigger_time: datetime):
        """Add a one-time scheduled event"""
        job_id = f"one_time_{trigger_time.timestamp()}"
        
        self.scheduler.add_job(
            func=lambda: self.trigger_event(event_data),
            trigger='date',
            run_date=trigger_time,
            id=job_id,
            name=f"One-time event: {event_data.get('title', 'Unknown')}"
        )
        
        self.logger.info(f"Added one-time event scheduled for {trigger_time}")
        return job_id
    
    def add_recurring_event(self, event_data: Dict, interval_seconds: int):
        """Add a recurring event"""
        job_id = f"recurring_{datetime.now().timestamp()}"
        
        self.scheduler.add_job(
            func=lambda: self.trigger_event(event_data),
            trigger=IntervalTrigger(seconds=interval_seconds),
            id=job_id,
            name=f"Recurring event: {event_data.get('title', 'Unknown')}"
        )
        
        self.logger.info(f"Added recurring event with {interval_seconds}s interval")
        return job_id
    
    def remove_scheduled_event(self, job_id: str):
        """Remove a scheduled event"""
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed scheduled event: {job_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove job {job_id}: {e}")
            return False
    
    # Task Integration
    def schedule_task_reminders(self, task_id: int, deadline: datetime):
        """Schedule reminders for a specific task"""
        # 2 hours before deadline
        if deadline > datetime.now() + timedelta(hours=2):
            reminder_time = deadline - timedelta(hours=2)
            reminder_data = {
                "type": "deadline_reminder",
                "title": "⚠️ Task Due Soon",
                "message": "Your task is due in 2 hours",
                "task_id": task_id,
                "actions": ["open_task", "reschedule", "snooze"],
                "urgency": 0.8
            }
            self.add_one_time_event(reminder_data, reminder_time)
        
        # At deadline
        deadline_data = {
            "type": "deadline_warning",
            "title": "🔥 Task Due Now!",
            "message": "Your task deadline has arrived",
            "task_id": task_id,
            "actions": ["open_task", "extend_deadline", "mark_done"],
            "urgency": 1.0
        }
        self.add_one_time_event(deadline_data, deadline)
    
    # Status and Info
    def get_status(self) -> Dict:
        """Get scheduler status information"""
        jobs = self.scheduler.get_jobs()
        
        return {
            "running": self.is_running,
            "paused_until": self.paused_until.isoformat() if self.paused_until else None,
            "silent_hours": self.is_silent_hours(),
            "notifications_enabled": self.should_show_notification(),
            "active_jobs": len(jobs),
            "job_details": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in jobs
            ]
        }
    
    def get_next_events(self, count: int = 5) -> List[Dict]:
        """Get upcoming events"""
        pending_events = self.db.get_pending_events()
        return sorted(pending_events, key=lambda x: x.get('trigger_time', ''))[:count]