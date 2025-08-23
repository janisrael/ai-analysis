#!/usr/bin/env python3
"""
AI Avatar Assistant - Main Application

A smart AI assistant with floating avatar and dynamic tooltips for task management.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.avatar import AvatarWidget
from ui.tooltip import TooltipWidget
from ui.task_dialog import TaskDialog, QuickTaskDialog
from ui.focus_mode import FocusModeManager
from core.database import TaskDatabase
from core.ai_engine import AIEngine
from core.actions import ActionSystem
from core.scheduler import EventScheduler
from core.voice_system import VoiceNotificationSystem
from core.external_apis import ExternalAPIManager
from core.analytics_engine import LiveAnalyticsEngine
from core.report_generator import ReportGenerator
from ui.analytics_dashboard import AnalyticsDashboard
from ui.chat_interface import ChatInterface

class AIAvatarAssistant:
    """Main application class that coordinates all components"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in system tray
        
        # Initialize logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.init_components()
        
        # Setup system tray
        self.setup_system_tray()
        
        # Connect signals
        self.connect_signals()
        
        # Setup timers
        self.setup_timers()
        
        self.logger.info("AI Avatar Assistant initialized successfully")
    
    def setup_logging(self):
        """Setup application logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/assistant.log'),
                logging.StreamHandler()
            ]
        )
    
    def init_components(self):
        """Initialize all application components"""
        try:
            # Core components
            self.db = TaskDatabase()
            self.ai_engine = AIEngine()
            self.action_system = ActionSystem()
            self.scheduler = EventScheduler()
            self.voice_system = VoiceNotificationSystem()
            self.api_manager = ExternalAPIManager()
            self.analytics_engine = LiveAnalyticsEngine()
            self.report_generator = ReportGenerator("data/tasks.db", self.analytics_engine, self.voice_system)
            
            # UI components
            self.avatar = AvatarWidget()
            self.tooltip = TooltipWidget()
            self.focus_manager = FocusModeManager(self)
            self.analytics_dashboard = AnalyticsDashboard()
            self.chat_interface = ChatInterface(
                self.db, self.analytics_engine, self.action_system, 
                self.voice_system, self.report_generator
            )
            
            # State variables
            self.is_running = False
            self.current_notification = None
            
            self.logger.info("All components initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "System Tray", 
                               "System tray is not available on this system.")
            sys.exit(1)
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(self.create_tray_icon())
        
        # Create context menu
        tray_menu = QMenu()
        
        # Show/Hide Avatar
        self.toggle_action = QAction("Hide Avatar", None)
        self.toggle_action.triggered.connect(self.toggle_avatar_visibility)
        tray_menu.addAction(self.toggle_action)
        
        tray_menu.addSeparator()
        
        # Quick Add Task
        quick_add_action = QAction("➕ Quick Add Task", None)
        quick_add_action.triggered.connect(self.show_add_task_dialog)
        tray_menu.addAction(quick_add_action)
        
        # Create Full Task
        full_task_action = QAction("📝 Create Task...", None)
        full_task_action.triggered.connect(lambda: self.show_full_task_dialog())
        tray_menu.addAction(full_task_action)
        
        # Show Tasks
        show_tasks_action = QAction("📋 Show Tasks", None)
        show_tasks_action.triggered.connect(self.show_tasks_overview)
        tray_menu.addAction(show_tasks_action)
        
        tray_menu.addSeparator()
        
        # Focus Mode submenu
        focus_menu = tray_menu.addMenu("🎯 Focus Mode")
        
        start_focus_action = QAction("Start 25min Session", None)
        start_focus_action.triggered.connect(lambda: self.start_focus_mode())
        focus_menu.addAction(start_focus_action)
        
        custom_focus_action = QAction("Custom Duration...", None)
        custom_focus_action.triggered.connect(self.show_custom_focus_dialog)
        focus_menu.addAction(custom_focus_action)
        
        self.stop_focus_action = QAction("Stop Current Session", None)
        self.stop_focus_action.triggered.connect(self.stop_focus_session)
        self.stop_focus_action.setEnabled(False)
        focus_menu.addAction(self.stop_focus_action)
        
        tray_menu.addSeparator()
        
        # Voice Control submenu
        voice_menu = tray_menu.addMenu("🎙️ Voice")
        
        self.voice_enabled_action = QAction("Enable Voice Notifications", None)
        self.voice_enabled_action.setCheckable(True)
        self.voice_enabled_action.setChecked(self.voice_system.enabled)
        self.voice_enabled_action.triggered.connect(self.toggle_voice_notifications)
        voice_menu.addAction(self.voice_enabled_action)
        
        voice_test_action = QAction("Test Voice", None)
        voice_test_action.triggered.connect(self.test_voice_system)
        voice_menu.addAction(voice_test_action)
        
        voice_settings_action = QAction("Voice Settings...", None)
        voice_settings_action.triggered.connect(self.show_voice_settings)
        voice_menu.addAction(voice_settings_action)
        
        # Pause Notifications
        self.pause_action = QAction("⏸️ Pause Notifications", None)
        self.pause_action.triggered.connect(self.toggle_notifications)
        tray_menu.addAction(self.pause_action)
        
        # Statistics
        stats_action = QAction("📊 Show Statistics", None)
        stats_action.triggered.connect(self.show_statistics)
        tray_menu.addAction(stats_action)
        
        # Analytics Dashboard
        analytics_action = QAction("📈 Analytics Dashboard", None)
        analytics_action.triggered.connect(self.show_analytics_dashboard)
        tray_menu.addAction(analytics_action)
        
        # Settings
        settings_action = QAction("⚙️ Settings", None)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        
        tray_menu.addSeparator()
        
        # Exit
        exit_action = QAction("🚪 Exit", None)
        exit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Tray icon activation
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
    
    def create_tray_icon(self):
        """Create system tray icon"""
        # Create a simple icon programmatically
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw a simple AI icon
        painter.setBrush(QBrush(QColor(74, 144, 226)))
        painter.drawEllipse(4, 4, 24, 24)
        
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(8, 10, 4, 4)  # Left eye
        painter.drawEllipse(20, 10, 4, 4)  # Right eye
        painter.drawEllipse(12, 18, 8, 4)  # Mouth
        
        painter.end()
        
        return QIcon(pixmap)
    
    def connect_signals(self):
        """Connect signals between components"""
        # Avatar signals
        self.avatar.avatar_clicked.connect(self.on_avatar_clicked)
        self.avatar.avatar_hovered.connect(self.on_avatar_hovered)
        
        # Tooltip signals
        self.tooltip.action_triggered.connect(self.on_action_triggered)
        self.tooltip.tooltip_closed.connect(self.on_tooltip_closed)
        
        # Scheduler callbacks
        self.scheduler.register_default_callback(self.on_event_triggered)
        
        # Analytics dashboard signals
        self.analytics_dashboard.refresh_requested.connect(self.refresh_analytics_data)
        
        # Chat interface signals
        self.chat_interface.action_triggered.connect(self.on_action_triggered)
    
    def setup_timers(self):
        """Setup application timers"""
        # Periodic status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(60000)  # Every minute
        
        # Analytics update timer
        self.analytics_timer = QTimer()
        self.analytics_timer.timeout.connect(self.update_analytics_periodically)
        self.analytics_timer.start(600000)  # Every 10 minutes
    
    def start(self):
        """Start the application"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Show avatar
        self.avatar.show_avatar()
        
        # Start scheduler
        self.scheduler.start()
        
        # Show welcome message
        welcome_data = {
            "type": "welcome",
            "title": "🤖 AI Assistant Ready!",
            "message": "Your AI assistant is now active and monitoring your tasks. Click on me anytime for help!",
            "actions": ["show_tasks", "add_task", "dismiss"],
            "urgency": 0.3
        }
        
        # Show welcome after a short delay
        QTimer.singleShot(2000, lambda: self.show_notification(welcome_data))
        
        self.logger.info("AI Avatar Assistant started")
    
    def stop(self):
        """Stop the application"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Hide UI components
        self.avatar.hide_avatar()
        self.tooltip.hide_tooltip()
        
        # Stop scheduler
        self.scheduler.stop()
        
        self.logger.info("AI Avatar Assistant stopped")
    
    def quit_application(self):
        """Quit the entire application"""
        self.stop()
        self.app.quit()
    
    # Event Handlers
    @pyqtSlot()
    def on_avatar_clicked(self):
        """Handle avatar click - now opens chat interface"""
        self.logger.info("Avatar clicked - opening chat interface")
        
        # Open chat interface
        self.chat_interface.show_chat()
        
        # Voice greeting if enabled
        if self.voice_system.enabled:
            self.voice_system.speak_notification("Hello! I'm here to help. What would you like to know?", "friendly")
    
    @pyqtSlot()
    def on_avatar_hovered(self):
        """Handle avatar hover"""
        # Could show a brief status or do nothing
        pass
    
    @pyqtSlot(str, dict)
    def on_action_triggered(self, action_name, context):
        """Handle action triggered from tooltip"""
        self.logger.info(f"Action triggered: {action_name}")
        
        # Execute action through action system
        result = self.action_system.execute_action(action_name, context)
        
        # Handle special actions that need UI updates
        if result.get('action') == 'show_task_overview':
            self.show_tasks_overview()
        elif result.get('action') == 'hide_tooltip':
            self.tooltip.hide_tooltip()
        elif result.get('action') == 'show_task_dialog':
            task_data = result.get('data')
            if task_data:
                self.show_full_task_dialog(task_data)
        elif action_name == 'add_task':
            self.show_add_task_dialog()
        elif action_name == 'open_task':
            # Get task data and show edit dialog
            task_id = context.get('task_id')
            if task_id:
                tasks = self.db.get_tasks()
                task = next((t for t in tasks if t['id'] == task_id), None)
                if task:
                    self.show_full_task_dialog(task)
        elif action_name == 'start_focus_mode':
            self.start_focus_mode(context)
        elif action_name == 'open_analytics':
            self.show_analytics_dashboard()
        elif action_name == 'apply_suggestion':
            # Handle AI suggestion application
            self.tooltip.hide_tooltip()
            self.tray_icon.showMessage("AI Assistant", "AI suggestion noted. Check analytics for details.", 
                                     QSystemTrayIcon.Information, 2000)
        elif action_name in ['show_tasks', 'get_suggestions']:
            # Handle various tooltip actions
            if action_name == 'show_tasks':
                self.show_tasks_overview()
            elif action_name == 'get_suggestions':
                self.show_analytics_dashboard()
        elif action_name == 'dismiss':
            self.tooltip.hide_tooltip()
        elif action_name == 'open_report':
            self.open_report(context)
        elif action_name == 'download_report':
            self.download_report(context)
        elif action_name == 'list_projects':
            self.show_project_list()
        
        # Show result message if provided
        if result.get('success') and result.get('message'):
            # Update avatar mood based on action
            if action_name == "mark_done":
                self.avatar.set_mood("happy")
                self.avatar.notify_normal()
                # Voice feedback for task completion
                if self.voice_system.enabled and context.get('task_id'):
                    tasks = self.db.get_tasks()
                    task = next((t for t in tasks if t['id'] == context['task_id']), None)
                    if task:
                        self.voice_system.speak_task_notification(task['title'], "completed")
            elif action_name in ["snooze", "dismiss"]:
                self.avatar.set_mood("sleeping")
    
    @pyqtSlot()
    def on_tooltip_closed(self):
        """Handle tooltip closed"""
        self.current_notification = None
        # Reset avatar mood to default
        QTimer.singleShot(3000, lambda: self.avatar.set_mood("happy"))
    
    def on_event_triggered(self, event_data):
        """Handle events from scheduler"""
        self.logger.info(f"Event triggered: {event_data.get('type', 'unknown')}")
        
        # Show notification
        self.show_notification(event_data)
        
        # Voice notification
        if self.voice_system.enabled:
            urgency_level = "urgent" if event_data.get('urgency', 0.5) >= 0.8 else "normal"
            
            # Determine notification type for voice
            event_type = event_data.get('type', '')
            title = event_data.get('title', '')
            message = event_data.get('message', '')
            
            if 'deadline' in event_type or 'overdue' in event_type:
                # Extract task title from message if possible
                task_title = title.replace('⚠️', '').replace('🔥', '').strip()
                notification_type = "deadline_soon" if "soon" in message else "deadline_now"
                self.voice_system.speak_task_notification(task_title, notification_type)
            elif event_type == "daily_summary":
                self.voice_system.speak_notification(message, "normal")
            elif event_type == "productivity_tip":
                self.voice_system.speak_notification(f"Productivity tip: {message}", "friendly")
            else:
                # Generic notification
                voice_text = f"{title}. {message}" if title and message else title or message
                self.voice_system.speak_notification(voice_text, urgency_level)
        
        # Animate avatar based on urgency
        urgency = event_data.get('urgency', 0.5)
        if urgency >= 0.8:
            self.avatar.notify_urgent()
            self.avatar.set_mood("urgent")
        else:
            self.avatar.notify_normal()
            self.avatar.set_mood("thinking")
    
    def show_notification(self, notification_data):
        """Show a notification tooltip"""
        self.current_notification = notification_data
        
        # Position tooltip near avatar
        avatar_rect = self.avatar.geometry()
        self.tooltip.position_near_avatar(avatar_rect)
        
        # Show tooltip
        self.tooltip.show_notification(notification_data)
    
    # System Tray Actions
    def on_tray_icon_activated(self, reason):
        """Handle system tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_avatar_visibility()
        elif reason == QSystemTrayIcon.Trigger:
            # Single click - could show status or menu
            pass
    
    def toggle_avatar_visibility(self):
        """Toggle avatar visibility"""
        if self.avatar.isVisible():
            self.avatar.hide_avatar()
            self.tooltip.hide_tooltip()
            self.toggle_action.setText("Show Avatar")
        else:
            self.avatar.show_avatar()
            self.toggle_action.setText("Hide Avatar")
    
    def toggle_notifications(self):
        """Toggle notification pause state"""
        if self.scheduler.is_notifications_paused():
            self.scheduler.resume_notifications()
            self.pause_action.setText("Pause Notifications")
            self.tray_icon.showMessage("AI Assistant", "Notifications resumed", 
                                     QSystemTrayIcon.Information, 2000)
        else:
            self.scheduler.pause_notifications(60)  # Pause for 1 hour
            self.pause_action.setText("Resume Notifications")
            self.tray_icon.showMessage("AI Assistant", "Notifications paused for 1 hour", 
                                     QSystemTrayIcon.Information, 2000)
    
    def show_add_task_dialog(self):
        """Show add task dialog"""
        try:
            dialog = QuickTaskDialog(self)
            dialog.task_saved.connect(self.on_task_created)
            dialog.exec_()
        except Exception as e:
            self.logger.error(f"Failed to show add task dialog: {e}")
            # Fallback to quick task creation
            self.show_quick_task_input()
    
    def show_full_task_dialog(self, task_data=None):
        """Show full task creation/editing dialog"""
        try:
            dialog = TaskDialog(task_data, self)
            dialog.task_saved.connect(self.on_task_saved)
            dialog.task_deleted.connect(self.on_task_deleted)
            dialog.exec_()
        except Exception as e:
            self.logger.error(f"Failed to show task dialog: {e}")
    
    def show_quick_task_input(self):
        """Fallback quick task input"""
        sample_task_id = self.db.add_task(
            title="Sample Task",
            description="This is a sample task created from the system tray",
            deadline=datetime.now() + timedelta(hours=2),
            priority=3
        )
        
        self.tray_icon.showMessage("AI Assistant", "Sample task added!", 
                                 QSystemTrayIcon.Information, 2000)
        
        self.logger.info(f"Added sample task with ID: {sample_task_id}")
    
    def on_task_created(self, task_data):
        """Handle new task creation"""
        try:
            task_id = self.db.add_task(
                title=task_data['title'],
                description=task_data.get('description', ''),
                deadline=task_data.get('deadline'),
                priority=task_data.get('priority', 3),
                metadata=task_data.get('metadata', {})
            )
            
            self.tray_icon.showMessage("AI Assistant", 
                                     f"Task '{task_data['title']}' created!", 
                                     QSystemTrayIcon.Information, 2000)
            
            self.logger.info(f"Created new task: {task_data['title']} (ID: {task_id})")
            
            # Schedule reminders if deadline is set
            if task_data.get('deadline'):
                self.scheduler.schedule_task_reminders(task_id, task_data['deadline'])
                
        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            QMessageBox.warning(None, "Error", f"Failed to create task: {e}")
    
    def on_task_saved(self, task_data):
        """Handle task save (create or update)"""
        try:
            if 'id' in task_data:
                # Update existing task
                self.db.update_task_status(task_data['id'], task_data['status'])
                # Note: A full implementation would update all fields
                self.logger.info(f"Updated task: {task_data['title']}")
                message = f"Task '{task_data['title']}' updated!"
            else:
                # Create new task
                self.on_task_created(task_data)
                return
            
            self.tray_icon.showMessage("AI Assistant", message, 
                                     QSystemTrayIcon.Information, 2000)
                                     
        except Exception as e:
            self.logger.error(f"Failed to save task: {e}")
            QMessageBox.warning(None, "Error", f"Failed to save task: {e}")
    
    def on_task_deleted(self, task_id):
        """Handle task deletion"""
        try:
            # Mark as cancelled instead of deleting
            self.db.update_task_status(task_id, "cancelled")
            
            self.tray_icon.showMessage("AI Assistant", 
                                     "Task deleted successfully!", 
                                     QSystemTrayIcon.Information, 2000)
            
            self.logger.info(f"Deleted task ID: {task_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to delete task: {e}")
            QMessageBox.warning(None, "Error", f"Failed to delete task: {e}")
    
    def start_focus_mode(self, context=None):
        """Start focus mode session"""
        # Get task info from context if available
        task_title = "Focus Session"
        duration = 25  # Default Pomodoro duration
        
        if context and 'task_id' in context:
            task_id = context['task_id']
            tasks = self.db.get_tasks()
            task = next((t for t in tasks if t['id'] == task_id), None)
            if task:
                task_title = f"Focus: {task['title']}"
        elif context and 'metadata' in context:
            metadata = context['metadata']
            if isinstance(metadata, dict):
                task_title = metadata.get('task_title', task_title)
                duration = metadata.get('duration', duration)
        
        # Start focus session
        if self.focus_manager.start_focus_session(task_title, duration):
            self.avatar.set_mood("focused")
            self.stop_focus_action.setEnabled(True)
            self.tray_icon.showMessage(
                "AI Assistant", 
                f"Focus session started: {task_title}",
                QSystemTrayIcon.Information, 2000
            )
            
            # Voice notification for focus start
            if self.voice_system.enabled:
                self.voice_system.speak_task_notification(task_title, "focus_start")
            
            self.logger.info(f"Started focus session: {task_title}")
        else:
                         self.tray_icon.showMessage(
                 "AI Assistant", 
                 "A focus session is already active",
                 QSystemTrayIcon.Warning, 2000
             )
    
    def show_custom_focus_dialog(self):
        """Show custom focus duration dialog"""
        from PyQt5.QtWidgets import QInputDialog
        
        duration, ok = QInputDialog.getInt(
            None, 
            "Custom Focus Session", 
            "Enter duration in minutes:", 
            25, 1, 120
        )
        
        if ok:
            task_title, ok = QInputDialog.getText(
                None,
                "Focus Session",
                "Task name (optional):",
                text="Focus Session"
            )
            
            if ok:
                context = {
                    'metadata': {
                        'task_title': task_title,
                        'duration': duration
                    }
                }
                self.start_focus_mode(context)
    
    def stop_focus_session(self):
        """Stop the current focus session"""
        self.focus_manager.stop_current_session()
        self.stop_focus_action.setEnabled(False)
        self.avatar.set_mood("happy")
    
    def show_statistics(self):
        """Show productivity statistics"""
        stats = self.focus_manager.get_stats()
        pending_tasks = len(self.db.get_tasks(status="pending"))
        completed_today = len([t for t in self.db.get_tasks(status="completed") 
                              if t.get('updated_at') and 
                              datetime.fromisoformat(t['updated_at']).date() == datetime.now().date()])
        
        stats_data = {
            "type": "statistics",
            "title": "📊 Productivity Statistics",
            "message": f"Today's Progress:\n" +
                      f"• Focus sessions: {stats['sessions_today']}\n" +
                      f"• Tasks completed: {completed_today}\n" +
                      f"• Pending tasks: {pending_tasks}\n" +
                      f"• Currently active: {'Yes' if stats['current_active'] else 'No'}",
            "actions": ["start_focus_mode", "show_tasks", "dismiss"],
            "urgency": 0.3,
            "metadata": stats
        }
        
        self.show_notification(stats_data)
    
    def show_analytics_dashboard(self):
        """Show the analytics dashboard with live insights"""
        try:
            # Get fresh analytics data
            analytics_data = self.analytics_engine.get_visual_analytics_data()
            
            # Update dashboard
            self.analytics_dashboard.update_dashboard(analytics_data)
            
            # Show dashboard
            self.analytics_dashboard.show_dashboard()
            
            # Voice announcement if enabled
            if self.voice_system.enabled:
                self.voice_system.speak_notification("Analytics dashboard opened. Analyzing your productivity patterns.", "normal")
            
        except Exception as e:
            self.logger.error(f"Error showing analytics dashboard: {e}")
            self.tray_icon.showMessage(
                "AI Assistant", 
                f"Analytics dashboard error: {e}",
                QSystemTrayIcon.Warning, 3000
            )
    
    def update_analytics_periodically(self):
        """Periodically update analytics and provide insights"""
        try:
            # Get current situation analysis
            analysis = self.analytics_engine.analyze_current_situation()
            
            # Check for critical alerts
            alerts = analysis.get("alerts", [])
            critical_alerts = [alert for alert in alerts if alert.get("severity") == "critical"]
            
            if critical_alerts:
                # Show critical alert notification
                for alert in critical_alerts[:2]:  # Max 2 critical alerts
                    alert_data = {
                        "type": "critical_alert",
                        "title": f"🚨 {alert.get('title', 'Critical Alert')}",
                        "message": alert.get("message", ""),
                        "actions": ["open_analytics", "dismiss"],
                        "urgency": 1.0
                    }
                    self.show_notification(alert_data)
                    
                    # Voice alert if enabled
                    if self.voice_system.enabled:
                        self.voice_system.speak_notification(
                            f"Critical alert: {alert.get('message', '')}", 
                            "urgent", 
                            interrupt=True
                        )
            
            # Check for high-priority recommendations
            recommendations = analysis.get("recommendations", [])
            high_priority_recs = [rec for rec in recommendations if rec.get("priority") in ["urgent", "high"]]
            
            if high_priority_recs and len(critical_alerts) == 0:  # Don't spam if there are critical alerts
                # Show one high-priority recommendation
                rec = high_priority_recs[0]
                rec_data = {
                    "type": "ai_recommendation",
                    "title": f"💡 {rec.get('title', 'AI Suggestion')}",
                    "message": rec.get("description", ""),
                    "actions": ["open_analytics", "apply_suggestion", "dismiss"],
                    "urgency": 0.7
                }
                
                # Only show recommendation every 30 minutes to avoid spam
                current_time = datetime.now()
                if not hasattr(self, '_last_recommendation_time') or \
                   (current_time - self._last_recommendation_time).seconds > 1800:
                    
                    self.show_notification(rec_data)
                    self._last_recommendation_time = current_time
                    
                    # Voice recommendation if enabled
                    if self.voice_system.enabled:
                        self.voice_system.speak_notification(
                            f"AI recommendation: {rec.get('description', '')}", 
                            "friendly"
                        )
        
        except Exception as e:
            self.logger.error(f"Error in analytics update: {e}")
    
    def refresh_analytics_data(self):
        """Refresh analytics data for the dashboard"""
        try:
            analytics_data = self.analytics_engine.get_visual_analytics_data()
            self.analytics_dashboard.update_dashboard(analytics_data)
        except Exception as e:
            self.logger.error(f"Error refreshing analytics data: {e}")
    
    def open_report(self, context: Dict):
        """Open a generated report"""
        report_id = context.get("report_id")
        url = context.get("url")
        
        if not report_id:
            return
        
        try:
            # Get the report
            report = self.report_generator.get_report(report_id)
            if report and report.html_path and os.path.exists(report.html_path):
                # Open the HTML file in the default browser
                import webbrowser
                webbrowser.open(f"file://{os.path.abspath(report.html_path)}")
                
                # Voice announcement
                if self.voice_system.enabled:
                    self.voice_system.speak_notification(
                        "Opening your report. Click the play button in the report to hear my voice explanation.",
                        "normal"
                    )
                
                self.logger.info(f"Opened report {report_id}")
            else:
                self.tray_icon.showMessage(
                    "AI Assistant", 
                    "Report not found or expired.",
                    QSystemTrayIcon.Warning, 3000
                )
        except Exception as e:
            self.logger.error(f"Error opening report: {e}")
            self.tray_icon.showMessage(
                "AI Assistant", 
                f"Error opening report: {e}",
                QSystemTrayIcon.Critical, 3000
            )
    
    def download_report(self, context: Dict):
        """Download a report as PDF"""
        report_id = context.get("report_id")
        
        if not report_id:
            return
        
        try:
            report = self.report_generator.get_report(report_id)
            if report and report.pdf_path and os.path.exists(report.pdf_path):
                # Open file dialog to save PDF
                from PyQt5.QtWidgets import QFileDialog
                
                save_path, _ = QFileDialog.getSaveFileName(
                    None,
                    "Save Report",
                    f"{report.title.replace(':', '-')}.pdf",
                    "PDF Files (*.pdf)"
                )
                
                if save_path:
                    import shutil
                    shutil.copy2(report.pdf_path, save_path)
                    
                    self.tray_icon.showMessage(
                        "AI Assistant", 
                        f"Report saved to {save_path}",
                        QSystemTrayIcon.Information, 3000
                    )
                    
                    if self.voice_system.enabled:
                        self.voice_system.speak_notification("Report downloaded successfully.", "normal")
            else:
                self.tray_icon.showMessage(
                    "AI Assistant", 
                    "PDF version not available for this report.",
                    QSystemTrayIcon.Warning, 3000
                )
        except Exception as e:
            self.logger.error(f"Error downloading report: {e}")
    
    def show_project_list(self):
        """Show list of available projects"""
        try:
            # Get projects from tasks metadata
            projects = set()
            tasks = self.db.get_tasks()
            
            for task in tasks:
                metadata = task.get('metadata', '{}')
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                project = metadata.get('project') or metadata.get('category')
                if project:
                    projects.add(project)
            
            if projects:
                project_list = "\n".join([f"• {project}" for project in sorted(projects)])
                projects_data = {
                    "type": "project_list",
                    "title": "📋 Available Projects",
                    "message": f"Here are your projects:\n\n{project_list}\n\nAsk me to 'Generate report for [project name]'",
                    "actions": ["dismiss"],
                    "urgency": 0.3
                }
            else:
                projects_data = {
                    "type": "no_projects",
                    "title": "📋 No Projects Found",
                    "message": "I couldn't find any projects in your tasks. Try adding project names to your task metadata, or ask for a general productivity report instead.",
                    "actions": ["add_task", "dismiss"],
                    "urgency": 0.3
                }
            
            self.show_notification(projects_data)
            
        except Exception as e:
            self.logger.error(f"Error showing project list: {e}")
    
    def toggle_voice_notifications(self):
        """Toggle voice notifications on/off"""
        new_state = self.voice_enabled_action.isChecked()
        self.voice_system.set_enabled(new_state)
        
        status_message = "Voice notifications enabled" if new_state else "Voice notifications disabled"
        self.tray_icon.showMessage("AI Assistant", status_message, 
                                 QSystemTrayIcon.Information, 2000)
        
        # Test voice if enabling
        if new_state and self.voice_system.is_initialized:
            self.voice_system.speak_notification("Voice notifications are now enabled.")
    
    def test_voice_system(self):
        """Test the voice notification system"""
        if not self.voice_system.is_initialized:
            self.tray_icon.showMessage("AI Assistant", 
                                     "Voice system not available. Please check configuration.",
                                     QSystemTrayIcon.Warning, 3000)
            return
        
        test_message = "This is a test of the voice notification system. If you can hear this, voice notifications are working correctly."
        success = self.voice_system.test_voice(test_message)
        
        if not success:
            self.tray_icon.showMessage("AI Assistant", 
                                     "Voice test failed. Please check your audio settings.",
                                     QSystemTrayIcon.Warning, 3000)
    
    def show_voice_settings(self):
        """Show voice settings dialog"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox, QPushButton, QComboBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Voice Settings")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Voice enabled checkbox
        enabled_cb = QCheckBox("Enable Voice Notifications")
        enabled_cb.setChecked(self.voice_system.enabled)
        layout.addWidget(enabled_cb)
        
        # Voice rate slider
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Speech Rate:"))
        rate_slider = QSlider(Qt.Horizontal)
        rate_slider.setRange(50, 400)
        rate_slider.setValue(self.voice_system.voice_rate)
        rate_label = QLabel(f"{self.voice_system.voice_rate} WPM")
        rate_slider.valueChanged.connect(lambda v: rate_label.setText(f"{v} WPM"))
        rate_layout.addWidget(rate_slider)
        rate_layout.addWidget(rate_label)
        layout.addLayout(rate_layout)
        
        # Voice volume slider
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        volume_slider = QSlider(Qt.Horizontal)
        volume_slider.setRange(0, 100)
        volume_slider.setValue(int(self.voice_system.voice_volume * 100))
        volume_label = QLabel(f"{int(self.voice_system.voice_volume * 100)}%")
        volume_slider.valueChanged.connect(lambda v: volume_label.setText(f"{v}%"))
        volume_layout.addWidget(volume_slider)
        volume_layout.addWidget(volume_label)
        layout.addLayout(volume_layout)
        
        # Voice gender selection
        gender_layout = QHBoxLayout()
        gender_layout.addWidget(QLabel("Voice Gender:"))
        gender_combo = QComboBox()
        gender_combo.addItems(["Female", "Male"])
        gender_combo.setCurrentText(self.voice_system.voice_gender.title())
        gender_layout.addWidget(gender_combo)
        layout.addLayout(gender_layout)
        
        # Test button
        test_btn = QPushButton("Test Voice")
        test_btn.clicked.connect(lambda: self.voice_system.test_voice("This is a test of your voice settings."))
        layout.addWidget(test_btn)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        def save_settings():
            self.voice_system.set_enabled(enabled_cb.isChecked())
            self.voice_system.set_voice_rate(rate_slider.value())
            self.voice_system.set_voice_volume(volume_slider.value() / 100.0)
            self.voice_system.voice_gender = gender_combo.currentText().lower()
            self.voice_system.save_config()
            self.voice_enabled_action.setChecked(enabled_cb.isChecked())
            dialog.accept()
        
        save_btn.clicked.connect(save_settings)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def show_tasks_overview(self):
        """Show tasks overview"""
        tasks = self.db.get_tasks(status="pending")
        
        overview_data = {
            "type": "task_overview",
            "title": f"📋 Tasks Overview ({len(tasks)} pending)",
            "message": "Here are your current tasks:\n" + 
                      "\n".join([f"• {task['title']}" for task in tasks[:5]]),
            "actions": ["prioritize_tasks", "start_focus_mode", "dismiss"],
            "urgency": 0.4,
            "metadata": {"tasks": tasks}
        }
        
        self.show_notification(overview_data)
    
    def show_task_details(self, task_data):
        """Show detailed task information"""
        if not task_data:
            return
        
        details_data = {
            "type": "task_details",
            "title": f"📝 {task_data.get('title', 'Task Details')}",
            "message": task_data.get('description', 'No description available'),
            "actions": ["mark_done", "reschedule", "edit_task", "dismiss"],
            "urgency": 0.6,
            "task_id": task_data.get('id'),
            "metadata": task_data
        }
        
        self.show_notification(details_data)
    
    def show_settings(self):
        """Show settings dialog"""
        # For now, just show a simple message
        # In a full implementation, this would open a settings dialog
        
        settings_data = {
            "type": "settings",
            "title": "⚙️ Settings",
            "message": "Settings dialog would open here. For now, you can modify the config.json file.",
            "actions": ["open_config", "restart_app", "dismiss"],
            "urgency": 0.3
        }
        
        self.show_notification(settings_data)
    
    def update_status(self):
        """Update application status"""
        # This could update the tray icon, check for system changes, etc.
        status = self.scheduler.get_status()
        self.logger.debug(f"Scheduler status: {status}")
        
        # Update tray icon tooltip with status
        pending_events = len(self.scheduler.get_next_events())
        pending_tasks = len(self.db.get_tasks(status="pending"))
        
        tooltip_text = f"AI Assistant\nPending tasks: {pending_tasks}\nUpcoming events: {pending_events}"
        self.tray_icon.setToolTip(tooltip_text)
    
    def run(self):
        """Run the application"""
        try:
            # Start the assistant
            self.start()
            
            # Show system tray message
            self.tray_icon.showMessage("AI Assistant", "AI Avatar Assistant is now running!", 
                                     QSystemTrayIcon.Information, 3000)
            
            # Run the Qt event loop
            return self.app.exec_()
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            return 1
        finally:
            self.stop()

def main():
    """Main entry point"""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    try:
        assistant = AIAvatarAssistant()
        return assistant.run()
    except Exception as e:
        print(f"Failed to start AI Avatar Assistant: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())