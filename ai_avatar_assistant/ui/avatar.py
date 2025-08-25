import sys
from PyQt5.QtWidgets import (QWidget, QLabel, QApplication, QGraphicsDropShadowEffect, 
                             QDesktopWidget, QVBoxLayout, QHBoxLayout)
from PyQt5.QtCore import QTimer, QPropertyAnimation, QRect, QEasingCurve, pyqtSignal, Qt, QSize
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor, QPen, QFont, QMovie
import json

class AvatarWidget(QWidget):
    """Floating avatar widget that displays AI assistant"""
    
    # Signals
    avatar_clicked = pyqtSignal()
    avatar_hovered = pyqtSignal()
    
    def __init__(self, config_path="data/config.json"):
        super().__init__()
        self.config = self.load_config(config_path)
        self.avatar_config = self.config.get("avatar", {})
        
        # Avatar properties
        self.size = self.avatar_config.get("size", 64)
        self.position = self.avatar_config.get("position", "bottom_right")
        self.animation_speed = self.avatar_config.get("animation_speed", 1.0)
        
        # Animation states
        self.is_animating = False
        self.current_animation = None
        self.idle_animation_timer = QTimer()
        
        self.init_ui()
        self.setup_animations()
        self.position_avatar()
        
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def init_ui(self):
        """Initialize the avatar UI"""
        # Make window frameless and always on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.size + 20, self.size + 20)  # Extra space for shadow
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Avatar label
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(self.size, self.size)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("""
            QLabel {
                border-radius: %dpx;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4A90E2, stop:1 #357ABD);
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            QLabel:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5BA0F2, stop:1 #4A8ACF);
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """ % (self.size // 2))
        
        # Try to load avatar image, fallback to text
        self.load_avatar_image()
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 3)
        self.avatar_label.setGraphicsEffect(shadow)
        
        layout.addWidget(self.avatar_label)
        self.setLayout(layout)
        
        # Mouse events
        self.avatar_label.mousePressEvent = self.on_avatar_click
        self.avatar_label.enterEvent = self.on_avatar_hover
        self.avatar_label.leaveEvent = self.on_avatar_leave
        
        # Make draggable
        self.mousePressEvent = self.mouse_press_event
        self.mouseMoveEvent = self.mouse_move_event
        self.drag_position = None
    
    def load_avatar_image(self):
        """Load avatar image or create default avatar"""
        # Try to load a GIF animation first
        try:
            movie = QMovie("assets/avatar.gif")
            if movie.isValid():
                self.avatar_label.setMovie(movie)
                movie.start()
                return
        except:
            pass
        
        # Try to load static image
        try:
            pixmap = QPixmap("assets/avatar.png")
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(self.size - 10, self.size - 10, 
                                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.avatar_label.setPixmap(scaled_pixmap)
                return
        except:
            pass
        
        # Default text avatar
        self.create_text_avatar()
    
    def create_text_avatar(self):
        """Create a default text-based avatar"""
        self.avatar_label.setText("🤖")
        font = QFont()
        font.setPointSize(self.size // 3)
        self.avatar_label.setFont(font)
        self.avatar_label.setAlignment(Qt.AlignCenter)
    
    def setup_animations(self):
        """Setup animation timers and properties"""
        # Idle animation (subtle pulse)
        self.idle_animation_timer.timeout.connect(self.idle_pulse)
        self.idle_animation_timer.start(3000)  # Every 3 seconds
        
        # Bounce animation for notifications
        self.bounce_animation = QPropertyAnimation(self, b"geometry")
        self.bounce_animation.setDuration(int(500 / self.animation_speed))
        self.bounce_animation.setEasingCurve(QEasingCurve.OutBounce)
        
        # Glow animation for urgent notifications
        self.glow_animation = QPropertyAnimation(self.avatar_label, b"styleSheet")
        self.glow_animation.setDuration(int(1000 / self.animation_speed))
    
    def position_avatar(self):
        """Position avatar according to configuration"""
        desktop = QDesktopWidget()
        screen_rect = desktop.screenGeometry()
        
        margin = 20
        
        if self.position == "bottom_right":
            x = screen_rect.width() - self.width() - margin
            y = screen_rect.height() - self.height() - margin
        elif self.position == "bottom_left":
            x = margin
            y = screen_rect.height() - self.height() - margin
        elif self.position == "top_right":
            x = screen_rect.width() - self.width() - margin
            y = margin
        elif self.position == "top_left":
            x = margin
            y = margin
        else:  # center
            x = (screen_rect.width() - self.width()) // 2
            y = (screen_rect.height() - self.height()) // 2
        
        self.move(x, y)
    
    # Animation Methods
    def idle_pulse(self):
        """Subtle pulse animation during idle"""
        if self.is_animating:
            return
        
        # Simple scale animation
        original_size = self.size
        self.animate_scale(original_size, original_size + 2, 200)
    
    def animate_scale(self, from_size, to_size, duration):
        """Animate avatar scaling"""
        if self.is_animating:
            return
        
        self.is_animating = True
        
        # Create temporary animation effect
        timer = QTimer()
        steps = 20
        current_step = 0
        size_diff = to_size - from_size
        
        def update_size():
            nonlocal current_step
            if current_step < steps:
                progress = current_step / steps
                new_size = int(from_size + size_diff * progress)
                self.avatar_label.setFixedSize(new_size, new_size)
                current_step += 1
            else:
                # Return to original size
                timer.stop()
                QTimer.singleShot(100, lambda: self.animate_scale(to_size, from_size, duration // 2))
                
        timer.timeout.connect(update_size)
        timer.start(duration // steps)
        
        # Reset animation state after completion
        QTimer.singleShot(duration * 2, lambda: setattr(self, 'is_animating', False))
    
    def bounce_notification(self):
        """Bounce animation for notifications"""
        if self.is_animating:
            return
        
        self.is_animating = True
        original_rect = self.geometry()
        bounce_rect = QRect(original_rect.x(), original_rect.y() - 10, 
                          original_rect.width(), original_rect.height())
        
        self.bounce_animation.setStartValue(original_rect)
        self.bounce_animation.setKeyValueAt(0.5, bounce_rect)
        self.bounce_animation.setEndValue(original_rect)
        
        self.bounce_animation.finished.connect(lambda: setattr(self, 'is_animating', False))
        self.bounce_animation.start()
    
    def glow_urgent(self):
        """Glow animation for urgent notifications"""
        # Animate background color to create glow effect
        normal_style = self.avatar_label.styleSheet()
        glow_style = normal_style.replace(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4A90E2, stop:1 #357ABD)",
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF6B6B, stop:1 #FF5252)"
        )
        
        # Simple glow effect by changing styles
        self.avatar_label.setStyleSheet(glow_style)
        QTimer.singleShot(500, lambda: self.avatar_label.setStyleSheet(normal_style))
        QTimer.singleShot(1000, lambda: self.avatar_label.setStyleSheet(glow_style))
        QTimer.singleShot(1500, lambda: self.avatar_label.setStyleSheet(normal_style))
    
    def wave_animation(self):
        """Wave animation for greetings"""
        # Simple rotation animation
        if hasattr(self, 'rotation_animation'):
            return
        
        # This would be a more complex animation in a full implementation
        self.bounce_notification()
    
    # Event Handlers
    def on_avatar_click(self, event):
        """Handle avatar click"""
        self.avatar_clicked.emit()
        self.bounce_notification()
    
    def on_avatar_hover(self, event):
        """Handle avatar hover"""
        self.avatar_hovered.emit()
        # Change cursor to pointer
        self.setCursor(Qt.PointingHandCursor)
    
    def on_avatar_leave(self, event):
        """Handle mouse leave"""
        self.setCursor(Qt.ArrowCursor)
    
    # Drag functionality
    def mouse_press_event(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouse_move_event(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    # Public Animation Interface
    def notify_urgent(self):
        """Trigger urgent notification animation"""
        self.glow_urgent()
        self.bounce_notification()
    
    def notify_normal(self):
        """Trigger normal notification animation"""
        self.bounce_notification()
    
    def greet_user(self):
        """Trigger greeting animation"""
        self.wave_animation()
    
    def set_mood(self, mood):
        """Change avatar appearance based on mood"""
        mood_styles = {
            "happy": "🤖",
            "focused": "🎯",
            "urgent": "⚠️",
            "sleeping": "😴",
            "thinking": "🤔"
        }
        
        if mood in mood_styles and hasattr(self.avatar_label, 'setText'):
            self.avatar_label.setText(mood_styles[mood])
    
    def show_avatar(self):
        """Show the avatar widget"""
        self.show()
        self.activateWindow()
        self.raise_()
    
    def hide_avatar(self):
        """Hide the avatar widget"""
        self.hide()

# Test the avatar widget
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    avatar = AvatarWidget()
    avatar.show_avatar()
    
    # Test animations
    QTimer.singleShot(2000, avatar.notify_normal)
    QTimer.singleShot(4000, avatar.notify_urgent)
    QTimer.singleShot(6000, avatar.greet_user)
    
    sys.exit(app.exec_())