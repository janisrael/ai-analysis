import sys
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QGraphicsDropShadowEffect, QApplication, QDesktopWidget, QScrollArea)
from PyQt5.QtCore import QTimer, QPropertyAnimation, QRect, QEasingCurve, pyqtSignal, Qt, QPoint
from PyQt5.QtGui import QFont, QColor, QPainter, QPainterPath, QRegion
import json

class TooltipWidget(QWidget):
    """Tooltip widget that appears near the avatar with actions"""
    
    # Signals
    action_triggered = pyqtSignal(str, dict)  # action_name, context
    tooltip_closed = pyqtSignal()
    
    def __init__(self, config_path="data/config.json"):
        super().__init__()
        self.config = self.load_config(config_path)
        self.notification_config = self.config.get("notifications", {})
        
        # Tooltip properties
        self.auto_hide_timeout = self.notification_config.get("auto_hide_timeout", 10) * 1000
        self.current_data = None
        self.is_visible = False
        
        # Timers
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_tooltip)
        
        self.init_ui()
        self.setup_animations()
        
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def init_ui(self):
        """Initialize the tooltip UI"""
        # Make window frameless and always on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set initial size (will be adjusted based on content)
        self.setFixedSize(350, 200)
        
        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)
        
        # Create the main container with rounded corners and shadow
        self.container = QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 240);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Container layout
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(12)
        
        # Title label
        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        self.title_label.setWordWrap(True)
        container_layout.addWidget(self.title_label)
        
        # Message label
        self.message_label = QLabel()
        self.message_label.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                font-size: 12px;
                background: transparent;
                border: none;
                line-height: 1.4;
            }
        """)
        self.message_label.setWordWrap(True)
        container_layout.addWidget(self.message_label)
        
        # Action buttons container
        self.buttons_container = QWidget()
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(8)
        self.buttons_container.setLayout(self.buttons_layout)
        container_layout.addWidget(self.buttons_container)
        
        # Close button (always present)
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.close_button.clicked.connect(self.hide_tooltip)
        
        # Position close button in top-right corner
        self.close_button.setParent(self.container)
        
        self.container.setLayout(container_layout)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 5)
        self.container.setGraphicsEffect(shadow)
        
        self.main_layout.addWidget(self.container)
        self.setLayout(self.main_layout)
        
        # Hide initially
        self.hide()
        
    def setup_animations(self):
        """Setup show/hide animations"""
        # Fade in animation
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)
        
        # Fade out animation
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(250)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out.finished.connect(self.hide)
        
        # Slide in animation
        self.slide_in = QPropertyAnimation(self, b"geometry")
        self.slide_in.setDuration(300)
        self.slide_in.setEasingCurve(QEasingCurve.OutCubic)
    
    def show_notification(self, notification_data):
        """Show notification with given data"""
        self.current_data = notification_data
        
        # Update content
        self.title_label.setText(notification_data.get("title", "Notification"))
        self.message_label.setText(notification_data.get("message", ""))
        
        # Clear existing action buttons
        self.clear_action_buttons()
        
        # Add action buttons
        actions = notification_data.get("actions", [])
        self.create_action_buttons(actions)
        
        # Adjust size based on content
        self.adjust_size()
        
        # Position tooltip
        self.position_tooltip()
        
        # Show with animation
        self.show_with_animation()
        
        # Set auto-hide timer if enabled
        if self.auto_hide_timeout > 0:
            self.hide_timer.start(self.auto_hide_timeout)
    
    def clear_action_buttons(self):
        """Clear all action buttons"""
        while self.buttons_layout.count():
            child = self.buttons_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def create_action_buttons(self, actions):
        """Create action buttons from action list"""
        action_labels = {
            "open_task": "📂 Open",
            "mark_done": "✅ Done",
            "snooze": "⏰ Snooze",
            "reschedule": "📅 Reschedule",
            "extend_deadline": "⏳ Extend",
            "show_tasks": "📋 Tasks",
            "prioritize_tasks": "⭐ Prioritize",
            "start_focus_mode": "🎯 Focus",
            "dismiss": "❌ Dismiss",
            "get_suggestions": "💡 Tips",
            "open_calendar": "📅 Calendar",
            "open_email": "📧 Email"
        }
        
        # Limit number of buttons to avoid overcrowding
        max_buttons = 4
        displayed_actions = actions[:max_buttons]
        
        for action in displayed_actions:
            button_text = action_labels.get(action, action.replace("_", " ").title())
            button = self.create_action_button(button_text, action)
            self.buttons_layout.addWidget(button)
        
        # Add "More" button if there are additional actions
        if len(actions) > max_buttons:
            more_button = self.create_action_button("⋯ More", "show_more_actions")
            self.buttons_layout.addWidget(more_button)
        
        # Add stretch to push buttons to the left
        self.buttons_layout.addStretch()
    
    def create_action_button(self, text, action):
        """Create a single action button"""
        button = QPushButton(text)
        button.setStyleSheet("""
            QPushButton {
                background-color: rgba(74, 144, 226, 200);
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: rgba(84, 154, 236, 220);
            }
            QPushButton:pressed {
                background-color: rgba(64, 134, 216, 240);
            }
        """)
        
        button.clicked.connect(lambda: self.on_action_clicked(action))
        return button
    
    def on_action_clicked(self, action):
        """Handle action button click"""
        context = self.current_data.copy() if self.current_data else {}
        self.action_triggered.emit(action, context)
        
        # Hide tooltip for most actions (except those that need to keep it open)
        persistent_actions = ["show_more_actions", "get_suggestions"]
        if action not in persistent_actions:
            self.hide_tooltip()
    
    def adjust_size(self):
        """Adjust tooltip size based on content"""
        # Calculate required height
        title_height = self.title_label.heightForWidth(320)
        message_height = self.message_label.heightForWidth(320)
        buttons_height = 40  # Approximate button height
        padding = 60  # Total padding and margins
        
        required_height = title_height + message_height + buttons_height + padding
        required_height = max(120, min(required_height, 300))  # Clamp between 120-300px
        
        self.setFixedSize(350, required_height)
    
    def position_tooltip(self):
        """Position tooltip relative to avatar or screen"""
        desktop = QDesktopWidget()
        screen_rect = desktop.screenGeometry()
        
        # Default position (we'll improve this when we integrate with avatar)
        margin = 20
        
        # Position in bottom-right area, leaving space for avatar
        x = screen_rect.width() - self.width() - margin
        y = screen_rect.height() - self.height() - 120  # Leave space for avatar
        
        # Ensure tooltip stays on screen
        x = max(margin, min(x, screen_rect.width() - self.width() - margin))
        y = max(margin, min(y, screen_rect.height() - self.height() - margin))
        
        self.move(x, y)
    
    def position_near_avatar(self, avatar_rect):
        """Position tooltip near the avatar"""
        desktop = QDesktopWidget()
        screen_rect = desktop.screenGeometry()
        margin = 15
        
        # Try to position tooltip to the left of avatar
        x = avatar_rect.x() - self.width() - margin
        y = avatar_rect.y()
        
        # If tooltip would go off-screen to the left, position to the right
        if x < margin:
            x = avatar_rect.right() + margin
        
        # If tooltip would go off-screen to the right, position above
        if x + self.width() > screen_rect.width() - margin:
            x = avatar_rect.x() - (self.width() - avatar_rect.width()) // 2
            y = avatar_rect.y() - self.height() - margin
        
        # If tooltip would go off-screen above, position below
        if y < margin:
            y = avatar_rect.bottom() + margin
        
        # Final bounds check
        x = max(margin, min(x, screen_rect.width() - self.width() - margin))
        y = max(margin, min(y, screen_rect.height() - self.height() - margin))
        
        self.move(x, y)
    
    def show_with_animation(self):
        """Show tooltip with animation"""
        if self.is_visible:
            return
        
        self.is_visible = True
        
        # Position close button
        self.close_button.move(self.container.width() - 25, 5)
        
        # Start from slightly offset position for slide effect
        final_rect = self.geometry()
        start_rect = QRect(final_rect.x(), final_rect.y() + 20, 
                          final_rect.width(), final_rect.height())
        
        self.setGeometry(start_rect)
        self.show()
        
        # Animate slide and fade in
        self.slide_in.setStartValue(start_rect)
        self.slide_in.setEndValue(final_rect)
        
        self.fade_in.start()
        self.slide_in.start()
    
    def hide_tooltip(self):
        """Hide tooltip with animation"""
        if not self.is_visible:
            return
        
        self.is_visible = False
        self.hide_timer.stop()
        
        # Start fade out animation
        self.fade_out.start()
        self.tooltip_closed.emit()
    
    def resizeEvent(self, event):
        """Handle resize event to reposition close button"""
        super().resizeEvent(event)
        if hasattr(self, 'close_button'):
            self.close_button.move(self.container.width() - 25, 5)
    
    def enterEvent(self, event):
        """Mouse entered tooltip - pause auto-hide"""
        self.hide_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse left tooltip - resume auto-hide"""
        if self.auto_hide_timeout > 0 and self.is_visible:
            self.hide_timer.start(self.auto_hide_timeout // 2)  # Shorter timeout after mouse leave
        super().leaveEvent(event)


# Test the tooltip widget
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    tooltip = TooltipWidget()
    
    # Test notification data
    test_notification = {
        "title": "⚠️ Project Report Due Soon!",
        "message": "Your project report is due in 2 hours. Would you like to open it or reschedule the deadline?",
        "actions": ["open_task", "reschedule", "snooze", "mark_done", "get_suggestions"],
        "urgency": 0.9,
        "task_id": 123
    }
    
    # Show test notification
    tooltip.show_notification(test_notification)
    
    # Connect signals for testing
    tooltip.action_triggered.connect(lambda action, context: print(f"Action: {action}, Context: {context}"))
    tooltip.tooltip_closed.connect(lambda: print("Tooltip closed"))
    
    sys.exit(app.exec_())