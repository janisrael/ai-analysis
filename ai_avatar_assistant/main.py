#!/usr/bin/env python3
"""
AI Avatar Assistant - Main Application
A comprehensive AI-powered assistant with dynamic tooltips, project estimation,
team recommendations, analytics, voice notifications, and widget-based orchestration.
"""

import sys
import os
import logging
import json
from datetime import datetime
from typing import Dict, Any

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Import core components
from core.ai_engine import AIEngine
from core.action_system import ActionSystem
from core.database import TaskDatabase
from core.scheduler import EventScheduler
from core.voice_system import VoiceNotificationSystem
from core.analytics_engine import LiveAnalyticsEngine
from core.report_generator import ReportGenerator
from core.data_source_manager import DataSourceManager
from core.project_estimator import ProjectEstimator
from core.widget_api import WidgetIntegrationManager

# Import UI components
from ui.avatar import Avatar
from ui.tooltip import DynamicTooltip
from ui.task_dialog import TaskDialog
from ui.focus_mode import FocusMode
from ui.analytics_dashboard import AnalyticsDashboard
from ui.chat_interface import ChatInterface
from ui.settings_dashboard import SettingsDashboard
from ui.widget_integration_dialog import WidgetIntegrationDialog

class AIAvatarAssistant(QMainWindow):
    """Main AI Avatar Assistant Application with Universal Orchestration"""
    
    def __init__(self):
        super().__init__()
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize core systems
        self.init_core_systems()
        
        # Initialize UI components
        self.init_ui_components()
        
        # Setup system tray
        self.setup_system_tray()
        
        # Start background services
        self.start_background_services()
        
        # Setup timers and signals
        self.setup_timers_and_signals()
        
        self.logger.info("🚀 AI Avatar Assistant initialized successfully")
    
    def setup_logging(self):
        """Setup logging configuration"""
        os.makedirs("logs", exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"logs/ai_avatar_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler()
            ]
        )
    
    def init_core_systems(self):
        """Initialize core system components"""
        self.logger.info("Initializing core systems...")
        
        # Database
        self.db = TaskDatabase()
        
        # Data source management
        self.data_source_manager = DataSourceManager()
        
        # AI Engine
        self.ai_engine = AIEngine()
        
        # Project estimation engine
        self.project_estimator = ProjectEstimator(self.data_source_manager)
        
        # Analytics engine
        self.analytics_engine = LiveAnalyticsEngine()
        
        # Report generator
        self.report_generator = ReportGenerator(
            self.db.db_path, 
            self.analytics_engine,
            None  # Voice system will be set later
        )
        
        # Action system
        self.action_system = ActionSystem(self.db)
        
        # Event scheduler
        self.scheduler = EventScheduler(self.db, self.ai_engine)
        
        # Voice notification system
        self.voice_system = VoiceNotificationSystem()
        self.report_generator.voice_system = self.voice_system
        
        # Widget integration manager
        self.widget_integration_manager = WidgetIntegrationManager(
            self, self.data_source_manager, self.project_estimator
        )
        
        self.logger.info("✅ Core systems initialized")
    
    def init_ui_components(self):
        """Initialize UI components"""
        self.logger.info("Initializing UI components...")
        
        # Main window setup
        self.setWindowTitle("AI Avatar Assistant - Universal Orchestration")
        self.setFixedSize(400, 300)
        
        # Avatar
        self.avatar = Avatar()
        self.avatar.clicked.connect(self.on_avatar_clicked)
        
        # Dynamic tooltip
        self.tooltip = DynamicTooltip(self.ai_engine, self.action_system)
        
        # Analytics dashboard
        self.analytics_dashboard = AnalyticsDashboard()
        
        # Chat interface
        self.chat_interface = ChatInterface(
            self.db, 
            self.analytics_engine, 
            self.action_system,
            self.voice_system,
            self.report_generator
        )
        
        # Settings dashboard
        self.settings_dashboard = SettingsDashboard(self.data_source_manager)
        
        # Widget integration dialog
        self.widget_integration_dialog = WidgetIntegrationDialog(
            self.widget_integration_manager
        )
        
        # Task dialog
        self.task_dialog = TaskDialog(self.db)
        
        # Focus mode
        self.focus_mode = FocusMode()
        
        # Central widget with avatar
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Welcome message
        welcome_label = QLabel("🤖 AI Avatar Assistant")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin: 20px;
            }
        """)
        layout.addWidget(welcome_label)
        
        # Status label
        self.status_label = QLabel("Universal Orchestration Agent Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #27ae60;
                margin: 10px;
                font-style: italic;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Avatar container
        avatar_container = QWidget()
        avatar_layout = QHBoxLayout()
        avatar_layout.addStretch()
        avatar_layout.addWidget(self.avatar)
        avatar_layout.addStretch()
        avatar_container.setLayout(avatar_layout)
        layout.addWidget(avatar_container)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()
        
        # Action buttons
        button_layout = QGridLayout()
        
        chat_btn = QPushButton("💬 Chat Assistant")
        chat_btn.clicked.connect(self.show_chat_interface)
        button_layout.addWidget(chat_btn, 0, 0)
        
        estimate_btn = QPushButton("📊 Estimate Project")
        estimate_btn.clicked.connect(self.show_project_estimation)
        button_layout.addWidget(estimate_btn, 0, 1)
        
        analytics_btn = QPushButton("📈 Analytics")
        analytics_btn.clicked.connect(self.show_analytics_dashboard)
        button_layout.addWidget(analytics_btn, 1, 0)
        
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.clicked.connect(self.show_settings_dashboard)
        button_layout.addWidget(settings_btn, 1, 1)
        
        widget_btn = QPushButton("🔗 Widget Manager")
        widget_btn.clicked.connect(self.show_widget_integration)
        button_layout.addWidget(widget_btn, 2, 0)
        
        focus_btn = QPushButton("🎯 Focus Mode")
        focus_btn.clicked.connect(self.start_focus_mode)
        button_layout.addWidget(focus_btn, 2, 1)
        
        actions_layout.addLayout(button_layout)
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        layout.addStretch()
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Apply styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
        """)
        
        self.logger.info("✅ UI components initialized")
    
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        self.logger.info("Setting up system tray...")
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("assets/avatar.png"))  # You'll need to add this icon
        self.tray_icon.setToolTip("AI Avatar Assistant - Universal Orchestration")
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Main sections
        show_action = QAction("🏠 Show Assistant", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # Quick actions
        chat_action = QAction("💬 Open Chat", self)
        chat_action.triggered.connect(self.show_chat_interface)
        tray_menu.addAction(chat_action)
        
        estimate_action = QAction("📊 Project Estimation", self)
        estimate_action.triggered.connect(self.show_project_estimation)
        tray_menu.addAction(estimate_action)
        
        analytics_action = QAction("📈 Analytics Dashboard", self)
        analytics_action.triggered.connect(self.show_analytics_dashboard)
        tray_menu.addAction(analytics_action)
        
        tray_menu.addSeparator()
        
        # Widget management
        widget_menu = QMenu("🔗 Widget Integration", self)
        
        widget_manager_action = QAction("📱 Widget Manager", self)
        widget_manager_action.triggered.connect(self.show_widget_integration)
        widget_menu.addAction(widget_manager_action)
        
        start_api_action = QAction("▶️ Start Widget API", self)
        start_api_action.triggered.connect(self.start_widget_api)
        widget_menu.addAction(start_api_action)
        
        stop_api_action = QAction("⏹️ Stop Widget API", self)
        stop_api_action.triggered.connect(self.stop_widget_api)
        widget_menu.addAction(stop_api_action)
        
        tray_menu.addMenu(widget_menu)
        
        # Voice menu
        voice_menu = QMenu("🎙️ Voice", self)
        
        toggle_voice_action = QAction("🔊 Toggle Voice Notifications", self)
        toggle_voice_action.triggered.connect(self.toggle_voice_notifications)
        voice_menu.addAction(toggle_voice_action)
        
        test_voice_action = QAction("🧪 Test Voice", self)
        test_voice_action.triggered.connect(self.test_voice_system)
        voice_menu.addAction(test_voice_action)
        
        voice_settings_action = QAction("⚙️ Voice Settings", self)
        voice_settings_action.triggered.connect(self.show_voice_settings)
        voice_menu.addAction(voice_settings_action)
        
        tray_menu.addMenu(voice_menu)
        
        # Settings and tools
        tray_menu.addSeparator()
        
        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.show_settings_dashboard)
        tray_menu.addAction(settings_action)
        
        focus_action = QAction("🎯 Focus Mode", self)
        focus_action.triggered.connect(self.start_focus_mode)
        tray_menu.addAction(focus_action)
        
        # System actions
        tray_menu.addSeparator()
        
        status_action = QAction("⚡ System Status", self)
        status_action.triggered.connect(self.show_system_status)
        tray_menu.addAction(status_action)
        
        quit_action = QAction("❌ Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Connect tray icon activation
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        self.logger.info("✅ System tray setup complete")
    
    def start_background_services(self):
        """Start background services"""
        self.logger.info("Starting background services...")
        
        # Start event scheduler
        self.scheduler.start()
        
        # Start data source synchronization
        self.data_source_manager.start_monitoring()
        
        # Initialize widget API (optional - can be started manually)
        # self.widget_integration_manager.initialize_widget_api()
        
        self.logger.info("✅ Background services started")
    
    def setup_timers_and_signals(self):
        """Setup timers and signal connections"""
        self.logger.info("Setting up timers and signals...")
        
        # Analytics update timer
        self.analytics_timer = QTimer()
        self.analytics_timer.timeout.connect(self.update_analytics_periodically)
        self.analytics_timer.start(600000)  # 10 minutes
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_system_status)
        self.status_timer.start(30000)  # 30 seconds
        
        # Connect signals
        self.scheduler.event_triggered.connect(self.on_event_triggered)
        self.action_system.action_executed.connect(self.on_action_triggered)
        self.analytics_dashboard.refresh_requested.connect(self.refresh_analytics_data)
        self.chat_interface.action_triggered.connect(self.on_action_triggered)
        self.widget_integration_dialog.integration_created.connect(self.on_widget_integration_created)
        self.settings_dashboard.settings_changed.connect(self.on_settings_changed)
        
        self.logger.info("✅ Timers and signals configured")
    
    def on_avatar_clicked(self):
        """Handle avatar click - show chat interface"""
        self.show_chat_interface()
        
        if self.voice_system.enabled:
            self.voice_system.speak_greeting()
    
    def show_chat_interface(self):
        """Show the chat interface"""
        self.chat_interface.show_chat()
        self.logger.info("Chat interface opened")
    
    def show_project_estimation(self):
        """Show project estimation interface"""
        # Use chat interface for project estimation
        self.chat_interface.show_chat()
        self.chat_interface.add_message(
            "Hi! I can help you estimate your project. Please describe your project requirements, "
            "technologies you'd like to use, and any specific deadlines or constraints.", 
            False
        )
        self.logger.info("Project estimation interface opened")
    
    def show_analytics_dashboard(self):
        """Show analytics dashboard"""
        # Fetch and update analytics data
        analytics_data = self.analytics_engine.get_visual_analytics_data()
        self.analytics_dashboard.update_dashboard(analytics_data)
        self.analytics_dashboard.show_dashboard()
        
        if self.voice_system.enabled:
            self.voice_system.speak_notification(
                "Analytics dashboard opened. Your productivity insights are ready for review.",
                "normal"
            )
        
        self.logger.info("Analytics dashboard opened")
    
    def show_settings_dashboard(self):
        """Show settings dashboard"""
        self.settings_dashboard.show()
        self.logger.info("Settings dashboard opened")
    
    def show_widget_integration(self):
        """Show widget integration dialog"""
        self.widget_integration_dialog.show()
        self.logger.info("Widget integration dialog opened")
    
    def start_focus_mode(self):
        """Start focus mode"""
        self.focus_mode.show()
        
        if self.voice_system.enabled:
            self.voice_system.speak_notification(
                "Focus mode activated. Minimizing distractions for optimal productivity.",
                "calm"
            )
        
        self.logger.info("Focus mode started")
    
    def start_widget_api(self):
        """Start the widget API server"""
        try:
            if self.widget_integration_manager.initialize_widget_api():
                self.tray_icon.showMessage(
                    "Widget API Started",
                    "Widget API server is now running on port 5555",
                    QSystemTrayIcon.Information,
                    3000
                )
                self.logger.info("Widget API server started from tray")
            else:
                self.tray_icon.showMessage(
                    "Widget API Error",
                    "Failed to start widget API server",
                    QSystemTrayIcon.Critical,
                    3000
                )
        except Exception as e:
            self.logger.error(f"Error starting widget API: {e}")
    
    def stop_widget_api(self):
        """Stop the widget API server"""
        try:
            self.widget_integration_manager.shutdown()
            self.tray_icon.showMessage(
                "Widget API Stopped",
                "Widget API server has been stopped",
                QSystemTrayIcon.Information,
                3000
            )
            self.logger.info("Widget API server stopped from tray")
        except Exception as e:
            self.logger.error(f"Error stopping widget API: {e}")
    
    def show_system_status(self):
        """Show comprehensive system status"""
        # Get status from all components
        data_status = self.data_source_manager.get_data_source_status()
        widget_status = self.widget_integration_manager.get_widget_status() if self.widget_integration_manager.widget_server else {"server_running": False}
        
        status_message = f"""
AI Avatar Assistant - System Status

🗄️ Data Sources: {data_status['active_sources']}/{data_status['total_sources']} active
📊 Analytics Engine: Running
🎙️ Voice System: {'Enabled' if self.voice_system.enabled else 'Disabled'}
🔗 Widget API: {'Running on port ' + str(widget_status.get('port', 'N/A')) if widget_status['server_running'] else 'Stopped'}
📱 Active Widgets: {widget_status.get('active_widgets', 0)}
🔑 API Keys: {widget_status.get('active_api_keys', 0)}

Last Sync: {data_status.get('last_sync', 'Never')}
        """
        
        QMessageBox.information(self, "System Status", status_message.strip())
    
    def on_event_triggered(self, event_type: str, event_data: Dict):
        """Handle triggered events"""
        self.logger.info(f"Event triggered: {event_type}")
        
        # Voice notifications for events
        if self.voice_system.enabled:
            if event_type == "task_reminder":
                self.voice_system.speak_task_notification(event_data.get("task_name", "Task"))
            elif event_type == "deadline_approaching":
                self.voice_system.speak_notification(
                    f"Deadline approaching for {event_data.get('task_name', 'task')}",
                    "urgent"
                )
            elif event_type == "productivity_alert":
                self.voice_system.speak_notification(
                    "Your productivity seems lower than usual. Consider taking a break or switching tasks.",
                    "friendly"
                )
        
        # Show tooltip for important events
        if event_type in ["deadline_approaching", "task_overdue"]:
            self.tooltip.show_tooltip(
                self.avatar,
                f"⚠️ {event_data.get('message', 'Important notification')}",
                "warning"
            )
    
    def on_action_triggered(self, action: str, context: Dict = None):
        """Handle action execution"""
        self.logger.info(f"Action triggered: {action}")
        
        if action == "mark_done":
            if self.voice_system.enabled:
                self.voice_system.speak_notification("Task completed! Great work!", "friendly")
        
        elif action == "open_analytics":
            self.show_analytics_dashboard()
        
        elif action == "apply_suggestion":
            suggestion = context.get("suggestion", "")
            self.tray_icon.showMessage(
                "Suggestion Applied",
                f"Applied suggestion: {suggestion}",
                QSystemTrayIcon.Information,
                3000
            )
        
        elif action == "open_report":
            self.open_report(context)
        
        elif action == "download_report":
            self.download_report(context)
        
        elif action == "list_projects":
            self.show_project_list()
        
        elif action == "estimate_project":
            self.show_project_estimation()
        
        elif action == "show_team_recommendations":
            self.show_team_recommendations(context)
    
    def on_widget_integration_created(self, integration_data: Dict):
        """Handle new widget integration creation"""
        self.logger.info(f"New widget integration created: {integration_data['widget_id']}")
        
        self.tray_icon.showMessage(
            "Widget Integration Created",
            f"New widget created with ID: {integration_data['widget_id'][:12]}...",
            QSystemTrayIcon.Information,
            5000
        )
        
        if self.voice_system.enabled:
            self.voice_system.speak_notification(
                "New widget integration created successfully. Your AI assistant is now available for embedding.",
                "friendly"
            )
    
    def on_settings_changed(self, settings: Dict):
        """Handle settings changes"""
        self.logger.info("Settings changed")
        
        # Apply relevant settings
        if "voice" in settings:
            voice_settings = settings["voice"]
            if "enabled" in voice_settings:
                self.voice_system.set_enabled(voice_settings["enabled"])
        
        # Update data source manager settings
        if "data" in settings:
            data_settings = settings["data"]
            if "auto_sync_interval" in data_settings:
                self.data_source_manager.watch_interval = data_settings["auto_sync_interval"] * 60
    
    def update_analytics_periodically(self):
        """Periodic analytics update and notification"""
        try:
            # Run analytics analysis
            situation = self.analytics_engine.analyze_current_situation()
            
            # Check for critical alerts
            if situation.get("alerts"):
                critical_alerts = [alert for alert in situation["alerts"] if alert.get("priority") == "high"]
                
                for alert in critical_alerts:
                    self.tray_icon.showMessage(
                        "Analytics Alert",
                        alert.get("message", "Important productivity alert"),
                        QSystemTrayIcon.Warning,
                        5000
                    )
                    
                    if self.voice_system.enabled:
                        self.voice_system.speak_notification(alert.get("message", "Alert"), "urgent")
            
            # Check for high-priority recommendations
            if situation.get("recommendations"):
                high_priority_recs = [rec for rec in situation["recommendations"] if rec.get("priority") == "high"]
                
                for rec in high_priority_recs[:1]:  # Show only the top recommendation
                    self.tray_icon.showMessage(
                        "AI Recommendation",
                        rec.get("action", "I have a productivity suggestion for you"),
                        QSystemTrayIcon.Information,
                        4000
                    )
            
            self.logger.info("Analytics updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating analytics: {e}")
    
    def update_system_status(self):
        """Update system status display"""
        try:
            # Update status label
            active_sources = self.data_source_manager.get_data_source_status()["active_sources"]
            widget_running = bool(self.widget_integration_manager.widget_server and 
                                self.widget_integration_manager.widget_server.is_running)
            
            status_text = f"🟢 Active Sources: {active_sources} | Widget API: {'🟢' if widget_running else '🔴'}"
            self.status_label.setText(status_text)
            
        except Exception as e:
            self.logger.error(f"Error updating system status: {e}")
    
    def refresh_analytics_data(self):
        """Refresh analytics data for dashboard"""
        try:
            analytics_data = self.analytics_engine.get_visual_analytics_data()
            self.analytics_dashboard.update_dashboard(analytics_data)
            self.logger.info("Analytics data refreshed")
        except Exception as e:
            self.logger.error(f"Error refreshing analytics: {e}")
    
    def open_report(self, context: Dict):
        """Open generated report in browser"""
        try:
            report_id = context.get("report_id")
            if report_id:
                import webbrowser
                report_url = f"file://{os.path.abspath('data/reports')}/{report_id}.html"
                webbrowser.open(report_url)
                
                if self.voice_system.enabled:
                    self.voice_system.speak_notification("Report opened in your browser", "normal")
                
                self.logger.info(f"Opened report: {report_id}")
        except Exception as e:
            self.logger.error(f"Error opening report: {e}")
    
    def download_report(self, context: Dict):
        """Download report as PDF"""
        try:
            report_id = context.get("report_id")
            if report_id:
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Save Report", f"report_{report_id}.pdf", "PDF Files (*.pdf)"
                )
                
                if file_path:
                    # Copy the generated PDF to selected location
                    import shutil
                    source_path = f"data/reports/{report_id}.pdf"
                    if os.path.exists(source_path):
                        shutil.copy(source_path, file_path)
                        
                        QMessageBox.information(self, "Success", f"Report saved to {file_path}")
                        self.logger.info(f"Report downloaded: {file_path}")
        except Exception as e:
            self.logger.error(f"Error downloading report: {e}")
    
    def show_project_list(self):
        """Show list of projects"""
        try:
            projects = self.data_source_manager.get_all_projects()
            
            if projects:
                project_list = "\n".join([
                    f"• {proj.get('name', proj.get('project_name', 'Unnamed Project'))}"
                    for proj in projects[:10]  # Show top 10
                ])
                
                if len(projects) > 10:
                    project_list += f"\n... and {len(projects) - 10} more projects"
                
                self.tooltip.show_tooltip(
                    self.avatar,
                    f"📋 Current Projects ({len(projects)} total):\n{project_list}",
                    "info"
                )
            else:
                self.tooltip.show_tooltip(
                    self.avatar,
                    "📋 No projects found. Connect your data sources to see projects.",
                    "info"
                )
            
            self.logger.info("Project list displayed")
        except Exception as e:
            self.logger.error(f"Error showing project list: {e}")
    
    def show_team_recommendations(self, context: Dict):
        """Show team member recommendations"""
        try:
            skills = context.get("skills", [])
            team_members = self.data_source_manager.get_team_members()
            
            if team_members:
                # Simple skill matching
                recommendations = []
                for member in team_members:
                    member_skills = member.get("skills", [])
                    if isinstance(member_skills, str):
                        member_skills = [member_skills]
                    
                    # Check for skill matches
                    matches = sum(1 for skill in skills if 
                                any(skill.lower() in ms.lower() for ms in member_skills))
                    
                    if matches > 0:
                        recommendations.append({
                            "name": member.get("name", "Unknown"),
                            "matches": matches,
                            "skills": member_skills
                        })
                
                # Sort by matches
                recommendations.sort(key=lambda x: x["matches"], reverse=True)
                
                if recommendations:
                    rec_text = "\n".join([
                        f"• {rec['name']} ({rec['matches']} matches)"
                        for rec in recommendations[:5]
                    ])
                    
                    self.tooltip.show_tooltip(
                        self.avatar,
                        f"👥 Recommended Team Members:\n{rec_text}",
                        "info"
                    )
                else:
                    self.tooltip.show_tooltip(
                        self.avatar,
                        "👥 No team members found with matching skills.",
                        "warning"
                    )
            else:
                self.tooltip.show_tooltip(
                    self.avatar,
                    "👥 No team member data available. Please configure your data sources.",
                    "warning"
                )
            
            self.logger.info("Team recommendations displayed")
        except Exception as e:
            self.logger.error(f"Error showing team recommendations: {e}")
    
    def toggle_voice_notifications(self):
        """Toggle voice notification system"""
        try:
            current_state = self.voice_system.enabled
            self.voice_system.set_enabled(not current_state)
            
            state_text = "enabled" if not current_state else "disabled"
            self.tray_icon.showMessage(
                "Voice Notifications",
                f"Voice notifications {state_text}",
                QSystemTrayIcon.Information,
                2000
            )
            
            if not current_state:  # If we just enabled voice
                self.voice_system.speak_notification("Voice notifications enabled", "friendly")
            
            self.logger.info(f"Voice notifications {state_text}")
        except Exception as e:
            self.logger.error(f"Error toggling voice notifications: {e}")
    
    def test_voice_system(self):
        """Test voice notification system"""
        try:
            if self.voice_system.enabled:
                self.voice_system.test_voice()
                self.tray_icon.showMessage(
                    "Voice Test",
                    "Voice test completed",
                    QSystemTrayIcon.Information,
                    2000
                )
            else:
                self.tray_icon.showMessage(
                    "Voice Test",
                    "Voice notifications are disabled",
                    QSystemTrayIcon.Warning,
                    2000
                )
            
            self.logger.info("Voice system tested")
        except Exception as e:
            self.logger.error(f"Error testing voice system: {e}")
    
    def show_voice_settings(self):
        """Show voice settings dialog"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Voice Settings")
            dialog.setFixedSize(300, 200)
            
            layout = QVBoxLayout()
            
            # Enable voice checkbox
            enable_checkbox = QCheckBox("Enable Voice Notifications")
            enable_checkbox.setChecked(self.voice_system.enabled)
            layout.addWidget(enable_checkbox)
            
            # Voice rate slider
            rate_label = QLabel(f"Voice Rate: {self.voice_system.voice_rate}")
            layout.addWidget(rate_label)
            
            rate_slider = QSlider(Qt.Horizontal)
            rate_slider.setRange(100, 300)
            rate_slider.setValue(self.voice_system.voice_rate)
            rate_slider.valueChanged.connect(lambda v: rate_label.setText(f"Voice Rate: {v}"))
            layout.addWidget(rate_slider)
            
            # Voice volume slider
            volume_label = QLabel(f"Voice Volume: {int(self.voice_system.voice_volume * 100)}%")
            layout.addWidget(volume_label)
            
            volume_slider = QSlider(Qt.Horizontal)
            volume_slider.setRange(0, 100)
            volume_slider.setValue(int(self.voice_system.voice_volume * 100))
            volume_slider.valueChanged.connect(lambda v: volume_label.setText(f"Voice Volume: {v}%"))
            layout.addWidget(volume_slider)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            test_btn = QPushButton("Test")
            test_btn.clicked.connect(lambda: self.voice_system.test_voice())
            button_layout.addWidget(test_btn)
            
            save_btn = QPushButton("Save")
            def save_settings():
                self.voice_system.set_enabled(enable_checkbox.isChecked())
                self.voice_system.set_voice_rate(rate_slider.value())
                self.voice_system.set_voice_volume(volume_slider.value() / 100)
                self.voice_system.save_config()
                dialog.accept()
            
            save_btn.clicked.connect(save_settings)
            button_layout.addWidget(save_btn)
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            self.logger.error(f"Error showing voice settings: {e}")
    
    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def closeEvent(self, event):
        """Handle close event - minimize to tray instead of quitting"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                "AI Avatar Assistant",
                "Application minimized to tray. Right-click the tray icon for options.",
                QSystemTrayIcon.Information,
                2000
            )
            self.hide()
            event.ignore()
        else:
            event.accept()
    
    def quit_application(self):
        """Properly quit the application"""
        self.logger.info("Shutting down AI Avatar Assistant...")
        
        try:
            # Stop background services
            if self.scheduler:
                self.scheduler.stop()
            
            if self.voice_system:
                self.voice_system.shutdown()
            
            if self.widget_integration_manager:
                self.widget_integration_manager.shutdown()
            
            # Close database connections
            if self.db:
                self.db.close()
            
            self.logger.info("✅ AI Avatar Assistant shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        QApplication.quit()

def main():
    """Main application entry point"""
    # Create QApplication
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray
    
    # Set application properties
    app.setApplicationName("AI Avatar Assistant")
    app.setApplicationVersion("1.0.0")
    app.setApplicationDisplayName("AI Avatar Assistant - Universal Orchestration")
    
    # Create and show main window
    assistant = AIAvatarAssistant()
    assistant.show()
    
    # Start application
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        assistant.quit_application()

if __name__ == "__main__":
    main()