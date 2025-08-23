from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import os
from .database import TaskDatabase

class AIEngine:
    """AI Engine for intelligent event detection and recommendations"""
    
    def __init__(self, config_path: str = "data/config.json"):
        self.config = self.load_config(config_path)
        self.db = TaskDatabase()
        self.personality = self.config.get("ai", {}).get("personality", "friendly")
        self.confidence_threshold = self.config.get("ai", {}).get("confidence_threshold", 0.7)
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Return default configuration"""
        return {
            "ai": {
                "personality": "friendly",
                "confidence_threshold": 0.7,
                "learning_enabled": True
            }
        }
    
    def analyze_current_situation(self) -> List[Dict]:
        """Analyze current tasks and events to generate recommendations"""
        recommendations = []
        
        # Check for urgent deadlines
        urgent_tasks = self.db.get_tasks(status="pending", upcoming_hours=24)
        for task in urgent_tasks:
            if task['deadline']:
                time_until_deadline = datetime.fromisoformat(task['deadline']) - datetime.now()
                urgency_level = self.calculate_urgency(time_until_deadline, task['priority'])
                
                if urgency_level > 0.8:
                    recommendations.append({
                        "type": "urgent_deadline",
                        "task_id": task['id'],
                        "title": f"⚠️ {task['title']} is due soon!",
                        "message": f"Task '{task['title']}' is due in {self.format_time_delta(time_until_deadline)}",
                        "urgency": urgency_level,
                        "actions": ["open_task", "snooze", "mark_done", "reschedule"],
                        "metadata": task
                    })
        
        # Check for overdue tasks
        overdue_tasks = self.get_overdue_tasks()
        for task in overdue_tasks:
            recommendations.append({
                "type": "overdue_task",
                "task_id": task['id'],
                "title": f"🔥 Overdue: {task['title']}",
                "message": f"Task '{task['title']}' was due {self.format_time_delta(datetime.now() - datetime.fromisoformat(task['deadline']))} ago",
                "urgency": 1.0,
                "actions": ["open_task", "reschedule", "mark_done", "extend_deadline"],
                "metadata": task
            })
        
        # Check for productivity patterns
        productivity_rec = self.analyze_productivity_patterns()
        if productivity_rec:
            recommendations.append(productivity_rec)
        
        # Check for idle time
        idle_rec = self.check_idle_time()
        if idle_rec:
            recommendations.append(idle_rec)
        
        # Sort by urgency
        recommendations.sort(key=lambda x: x.get('urgency', 0), reverse=True)
        
        return recommendations
    
    def calculate_urgency(self, time_until_deadline: timedelta, priority: int) -> float:
        """Calculate urgency score based on deadline and priority"""
        if time_until_deadline.total_seconds() <= 0:
            return 1.0  # Overdue
        
        hours_until = time_until_deadline.total_seconds() / 3600
        
        # Base urgency on time remaining
        if hours_until <= 2:
            time_urgency = 0.9
        elif hours_until <= 6:
            time_urgency = 0.7
        elif hours_until <= 24:
            time_urgency = 0.5
        elif hours_until <= 72:
            time_urgency = 0.3
        else:
            time_urgency = 0.1
        
        # Adjust by priority (1-5 scale)
        priority_multiplier = min(priority / 3.0, 1.5)
        
        return min(time_urgency * priority_multiplier, 1.0)
    
    def get_overdue_tasks(self) -> List[Dict]:
        """Get all overdue tasks"""
        tasks = self.db.get_tasks(status="pending")
        overdue = []
        now = datetime.now()
        
        for task in tasks:
            if task['deadline']:
                deadline = datetime.fromisoformat(task['deadline'])
                if deadline < now:
                    overdue.append(task)
        
        return overdue
    
    def analyze_productivity_patterns(self) -> Optional[Dict]:
        """Analyze user behavior to suggest productivity improvements"""
        # Simple rule-based analysis for now
        # In a full implementation, this would use ML to analyze patterns
        
        pending_tasks = self.db.get_tasks(status="pending")
        if len(pending_tasks) > 10:
            return {
                "type": "productivity_suggestion",
                "title": "📈 Productivity Tip",
                "message": f"You have {len(pending_tasks)} pending tasks. Consider prioritizing the most important ones.",
                "urgency": 0.4,
                "actions": ["prioritize_tasks", "bulk_reschedule", "task_overview"],
                "metadata": {"task_count": len(pending_tasks)}
            }
        
        return None
    
    def check_idle_time(self) -> Optional[Dict]:
        """Check if user has been idle and suggest actions"""
        # This would integrate with system monitoring
        # For now, just check if there are pending tasks during work hours
        
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Work hours
            urgent_tasks = self.db.get_tasks(status="pending", upcoming_hours=4)
            if urgent_tasks:
                return {
                    "type": "idle_reminder",
                    "title": "⏰ Gentle Reminder",
                    "message": f"You have {len(urgent_tasks)} tasks due soon. Ready to tackle them?",
                    "urgency": 0.3,
                    "actions": ["show_tasks", "start_focus_mode", "snooze"],
                    "metadata": {"task_count": len(urgent_tasks)}
                }
        
        return None
    
    def generate_smart_suggestions(self, task_context: Dict) -> List[str]:
        """Generate contextual suggestions based on task and user behavior"""
        suggestions = []
        
        task_type = task_context.get('type', 'general')
        
        if task_type == "urgent_deadline":
            suggestions.extend([
                "Break this task into smaller chunks",
                "Set a timer for focused work",
                "Clear your calendar for the next 2 hours",
                "Ask for help if needed"
            ])
        elif task_type == "overdue_task":
            suggestions.extend([
                "Assess if this task is still relevant",
                "Consider delegating this task",
                "Update the deadline if circumstances changed",
                "Complete the most critical parts first"
            ])
        
        return suggestions
    
    def format_time_delta(self, delta: timedelta) -> str:
        """Format time delta in human-readable format"""
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''}"
        
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        elif minutes > 0:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            return "less than a minute"
    
    def get_personality_message(self, message_type: str, context: Dict = None) -> str:
        """Generate personality-appropriate messages"""
        personality_messages = {
            "friendly": {
                "greeting": "Hi there! 👋",
                "urgent": "Hey! This needs your attention! 🚨",
                "reminder": "Just a friendly reminder! 😊",
                "completion": "Great job! 🎉",
                "encouragement": "You've got this! 💪"
            },
            "professional": {
                "greeting": "Good day.",
                "urgent": "Urgent attention required.",
                "reminder": "Reminder:",
                "completion": "Task completed successfully.",
                "encouragement": "Proceeding as planned."
            },
            "casual": {
                "greeting": "Hey! 😎",
                "urgent": "Yo! This is important! 🔥",
                "reminder": "Heads up! 👀",
                "completion": "Nice! ✨",
                "encouragement": "Keep going! 🚀"
            }
        }
        
        return personality_messages.get(self.personality, personality_messages["friendly"]).get(message_type, "")
    
    def learn_from_action(self, action_type: str, context: Dict, outcome: str):
        """Learn from user actions to improve future recommendations"""
        # Log the action for future analysis
        self.db.log_user_action(action_type, json.dumps(context))
        
        # Simple learning: adjust confidence based on user responses
        # In a full implementation, this would use machine learning
        pass