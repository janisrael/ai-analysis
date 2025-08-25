import os
import subprocess
import webbrowser
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, List
import json
from .database import TaskDatabase

class ActionSystem:
    """Handles all user actions triggered from tooltips and UI"""
    
    def __init__(self, config_path: str = "data/config.json"):
        self.db = TaskDatabase()
        self.config = self.load_config(config_path)
        self.action_handlers = self.register_action_handlers()
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def register_action_handlers(self) -> Dict[str, Callable]:
        """Register all available action handlers"""
        return {
            # Task management actions
            "open_task": self.open_task,
            "mark_done": self.mark_task_done,
            "snooze": self.snooze_task,
            "reschedule": self.reschedule_task,
            "extend_deadline": self.extend_deadline,
            
            # Productivity actions
            "show_tasks": self.show_task_overview,
            "prioritize_tasks": self.prioritize_tasks,
            "bulk_reschedule": self.bulk_reschedule,
            "task_overview": self.show_task_overview,
            "start_focus_mode": self.start_focus_mode,
            
            # System actions
            "dismiss": self.dismiss_notification,
            "pause_notifications": self.pause_notifications,
            "settings": self.open_settings,
            
            # External integrations
            "open_calendar": self.open_calendar,
            "open_email": self.open_email,
            "open_file": self.open_file,
            "open_url": self.open_url,
            
            # AI actions
            "ask_ai": self.ask_ai_assistant,
            "get_suggestions": self.get_task_suggestions
        }
    
    def execute_action(self, action_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an action and return the result"""
        context = context or {}
        
        if action_name not in self.action_handlers:
            return {
                "success": False,
                "error": f"Unknown action: {action_name}",
                "message": "Action not found"
            }
        
        try:
            result = self.action_handlers[action_name](context)
            
            # Log the action for learning
            self.db.log_user_action(
                action_type=action_name,
                context=json.dumps(context),
                task_id=context.get('task_id')
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to execute action: {action_name}"
            }
    
    # Task Management Actions
    def open_task(self, context: Dict) -> Dict:
        """Open a task for editing/viewing"""
        task_id = context.get('task_id')
        if not task_id:
            return {"success": False, "message": "No task ID provided"}
        
        # For now, we'll just return the task data
        # In a full implementation, this would open a task editor dialog
        tasks = self.db.get_tasks()
        task = next((t for t in tasks if t['id'] == task_id), None)
        
        if task:
            return {
                "success": True,
                "message": f"Opened task: {task['title']}",
                "data": task,
                "action": "show_task_dialog"
            }
        else:
            return {"success": False, "message": "Task not found"}
    
    def mark_task_done(self, context: Dict) -> Dict:
        """Mark a task as completed"""
        task_id = context.get('task_id')
        if not task_id:
            return {"success": False, "message": "No task ID provided"}
        
        success = self.db.update_task_status(task_id, "completed")
        if success:
            return {
                "success": True,
                "message": "Task marked as completed! 🎉",
                "action": "hide_tooltip"
            }
        else:
            return {"success": False, "message": "Failed to update task"}
    
    def snooze_task(self, context: Dict) -> Dict:
        """Snooze a task notification"""
        task_id = context.get('task_id')
        snooze_minutes = context.get('snooze_minutes', 30)
        
        # Create a new event to remind later
        if task_id:
            tasks = self.db.get_tasks()
            task = next((t for t in tasks if t['id'] == task_id), None)
            if task:
                snooze_time = datetime.now() + timedelta(minutes=snooze_minutes)
                self.db.add_event(
                    event_type="snooze_reminder",
                    title=f"Snoozed: {task['title']}",
                    trigger_time=snooze_time,
                    task_id=task_id
                )
        
        return {
            "success": True,
            "message": f"Snoozed for {snooze_minutes} minutes ⏰",
            "action": "hide_tooltip"
        }
    
    def reschedule_task(self, context: Dict) -> Dict:
        """Reschedule a task deadline"""
        task_id = context.get('task_id')
        new_deadline = context.get('new_deadline')  # Should be a datetime string
        
        if not task_id:
            return {"success": False, "message": "No task ID provided"}
        
        # For now, just extend by 1 day if no specific deadline provided
        if not new_deadline:
            # This would open a datetime picker in the full implementation
            return {
                "success": True,
                "message": "Reschedule dialog would open here",
                "action": "show_reschedule_dialog",
                "data": {"task_id": task_id}
            }
        
        return {"success": True, "message": "Task rescheduled"}
    
    def extend_deadline(self, context: Dict) -> Dict:
        """Extend task deadline by a default amount"""
        task_id = context.get('task_id')
        extend_hours = context.get('extend_hours', 24)
        
        if not task_id:
            return {"success": False, "message": "No task ID provided"}
        
        # This would update the deadline in the database
        return {
            "success": True,
            "message": f"Deadline extended by {extend_hours} hours",
            "action": "hide_tooltip"
        }
    
    # Productivity Actions
    def show_task_overview(self, context: Dict) -> Dict:
        """Show an overview of all tasks"""
        tasks = self.db.get_tasks(status="pending")
        return {
            "success": True,
            "message": f"Found {len(tasks)} pending tasks",
            "action": "show_task_overview",
            "data": {"tasks": tasks}
        }
    
    def prioritize_tasks(self, context: Dict) -> Dict:
        """Help user prioritize their tasks"""
        return {
            "success": True,
            "message": "Task prioritization wizard would open",
            "action": "show_prioritization_dialog"
        }
    
    def bulk_reschedule(self, context: Dict) -> Dict:
        """Bulk reschedule multiple tasks"""
        return {
            "success": True,
            "message": "Bulk reschedule dialog would open",
            "action": "show_bulk_reschedule_dialog"
        }
    
    def start_focus_mode(self, context: Dict) -> Dict:
        """Start focus mode for concentrated work"""
        return {
            "success": True,
            "message": "Focus mode activated! 🎯",
            "action": "start_focus_mode"
        }
    
    # System Actions
    def dismiss_notification(self, context: Dict) -> Dict:
        """Dismiss the current notification"""
        return {
            "success": True,
            "message": "Notification dismissed",
            "action": "hide_tooltip"
        }
    
    def pause_notifications(self, context: Dict) -> Dict:
        """Pause notifications for a period"""
        pause_minutes = context.get('pause_minutes', 60)
        return {
            "success": True,
            "message": f"Notifications paused for {pause_minutes} minutes",
            "action": "pause_notifications",
            "data": {"pause_until": datetime.now() + timedelta(minutes=pause_minutes)}
        }
    
    def open_settings(self, context: Dict) -> Dict:
        """Open application settings"""
        return {
            "success": True,
            "message": "Settings dialog would open",
            "action": "show_settings_dialog"
        }
    
    # External Integration Actions
    def open_calendar(self, context: Dict) -> Dict:
        """Open default calendar application"""
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['start', 'outlookcal:'], shell=True)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open', '-a', 'Calendar'])
            
            return {"success": True, "message": "Calendar opened"}
        except Exception as e:
            return {"success": False, "message": f"Failed to open calendar: {str(e)}"}
    
    def open_email(self, context: Dict) -> Dict:
        """Open default email application"""
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['start', 'mailto:'], shell=True)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open', '-a', 'Mail'])
            
            return {"success": True, "message": "Email opened"}
        except Exception as e:
            return {"success": False, "message": f"Failed to open email: {str(e)}"}
    
    def open_file(self, context: Dict) -> Dict:
        """Open a specific file"""
        file_path = context.get('file_path')
        if not file_path:
            return {"success": False, "message": "No file path provided"}
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open', file_path])
            
            return {"success": True, "message": f"Opened file: {file_path}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to open file: {str(e)}"}
    
    def open_url(self, context: Dict) -> Dict:
        """Open a URL in the default browser"""
        url = context.get('url')
        if not url:
            return {"success": False, "message": "No URL provided"}
        
        try:
            webbrowser.open(url)
            return {"success": True, "message": f"Opened URL: {url}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to open URL: {str(e)}"}
    
    # AI Actions
    def ask_ai_assistant(self, context: Dict) -> Dict:
        """Ask the AI assistant a question"""
        question = context.get('question', '')
        return {
            "success": True,
            "message": "AI chat dialog would open",
            "action": "show_ai_chat",
            "data": {"question": question}
        }
    
    def get_task_suggestions(self, context: Dict) -> Dict:
        """Get AI suggestions for task management"""
        task_id = context.get('task_id')
        
        suggestions = [
            "Break this task into smaller subtasks",
            "Set up a focused work environment",
            "Use the Pomodoro technique",
            "Schedule specific time blocks for this task"
        ]
        
        return {
            "success": True,
            "message": "Here are some suggestions:",
            "action": "show_suggestions",
            "data": {"suggestions": suggestions}
        }
    
    def get_available_actions(self, context_type: str = None) -> List[str]:
        """Get list of available actions, optionally filtered by context"""
        if context_type == "task":
            return ["open_task", "mark_done", "snooze", "reschedule", "extend_deadline"]
        elif context_type == "productivity":
            return ["show_tasks", "prioritize_tasks", "start_focus_mode"]
        else:
            return list(self.action_handlers.keys())