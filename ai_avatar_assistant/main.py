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
from core.database import TaskDatabase
from core.ai_engine import AIEngine
from core.actions import ActionSystem
from core.scheduler import EventScheduler

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
            
            # UI components
            self.avatar = AvatarWidget()
            self.tooltip = TooltipWidget()
            
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
        
        # Add Task
        add_task_action = QAction("Add Task", None)
        add_task_action.triggered.connect(self.show_add_task_dialog)
        tray_menu.addAction(add_task_action)
        
        # Show Tasks
        show_tasks_action = QAction("Show Tasks", None)
        show_tasks_action.triggered.connect(self.show_tasks_overview)
        tray_menu.addAction(show_tasks_action)
        
        tray_menu.addSeparator()
        
        # Pause Notifications
        self.pause_action = QAction("Pause Notifications", None)
        self.pause_action.triggered.connect(self.toggle_notifications)
        tray_menu.addAction(self.pause_action)
        
        # Settings
        settings_action = QAction("Settings", None)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        
        tray_menu.addSeparator()
        
        # Exit
        exit_action = QAction("Exit", None)
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
    
    def setup_timers(self):
        """Setup application timers"""
        # Periodic status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(60000)  # Every minute
    
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
        """Handle avatar click"""
        self.logger.info("Avatar clicked")
        
        # Show main menu tooltip
        menu_data = {
            "type": "main_menu",
            "title": "🤖 AI Assistant",
            "message": "How can I help you today?",
            "actions": ["show_tasks", "add_task", "start_focus_mode", "get_suggestions"],
            "urgency": 0.5
        }
        
        self.show_notification(menu_data)
    
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
            self.show_task_details(result.get('data'))
        
        # Show result message if provided
        if result.get('success') and result.get('message'):
            # Update avatar mood based on action
            if action_name == "mark_done":
                self.avatar.set_mood("happy")
                self.avatar.notify_normal()
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
        # For now, just add a sample task
        # In a full implementation, this would open a proper dialog
        
        sample_task_id = self.db.add_task(
            title="Sample Task",
            description="This is a sample task created from the system tray",
            deadline=datetime.now() + timedelta(hours=2),
            priority=3
        )
        
        self.tray_icon.showMessage("AI Assistant", "Sample task added!", 
                                 QSystemTrayIcon.Information, 2000)
        
        self.logger.info(f"Added sample task with ID: {sample_task_id}")
    
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