import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QApplication,
                             QDesktopWidget, QGraphicsDropShadowEffect)
from PyQt5.QtCore import QTimer, QTime, pyqtSignal, Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush
from datetime import datetime, timedelta

class FocusModeOverlay(QWidget):
    """Focus mode overlay that appears on screen during focused work sessions"""
    
    focus_completed = pyqtSignal()
    focus_cancelled = pyqtSignal()
    break_requested = pyqtSignal()
    
    def __init__(self, duration_minutes=25, task_title="Focus Session"):
        super().__init__()
        self.duration_minutes = duration_minutes
        self.task_title = task_title
        self.start_time = None
        self.is_active = False
        self.is_break = False
        
        # Timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        
        self.completion_timer = QTimer()
        self.completion_timer.setSingleShot(True)
        self.completion_timer.timeout.connect(self.on_focus_completed)
        
        self.init_ui()
        self.setup_animations()
    
    def init_ui(self):
        """Initialize the focus mode UI"""
        # Window setup
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Position in top-right corner
        self.setFixedSize(300, 120)
        self.position_overlay()
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Container with rounded background
        self.container = QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(76, 175, 80, 200), stop:1 rgba(67, 160, 71, 200));
                border-radius: 15px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)
        
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(15, 10, 15, 10)
        container_layout.setSpacing(8)
        
        # Title
        self.title_label = QLabel("🎯 Focus Mode")
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.title_label)
        
        # Task name
        self.task_label = QLabel(self.task_title)
        self.task_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 200);
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)
        self.task_label.setAlignment(Qt.AlignCenter)
        self.task_label.setWordWrap(True)
        container_layout.addWidget(self.task_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 0.2);
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.8), stop:1 rgba(255, 255, 255, 0.6));
                border-radius: 7px;
            }
        """)
        container_layout.addWidget(self.progress_bar)
        
        # Time display
        self.time_label = QLabel("25:00")
        self.time_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        self.time_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.time_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        self.pause_btn = QPushButton("⏸️")
        self.pause_btn.setFixedSize(30, 25)
        self.pause_btn.setStyleSheet(self.get_button_style())
        self.pause_btn.clicked.connect(self.toggle_pause)
        button_layout.addWidget(self.pause_btn)
        
        self.break_btn = QPushButton("☕")
        self.break_btn.setFixedSize(30, 25)
        self.break_btn.setStyleSheet(self.get_button_style())
        self.break_btn.clicked.connect(self.request_break)
        button_layout.addWidget(self.break_btn)
        
        self.stop_btn = QPushButton("⏹️")
        self.stop_btn.setFixedSize(30, 25)
        self.stop_btn.setStyleSheet(self.get_button_style())
        self.stop_btn.clicked.connect(self.stop_focus)
        button_layout.addWidget(self.stop_btn)
        
        container_layout.addLayout(button_layout)
        
        self.container.setLayout(container_layout)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.container.setGraphicsEffect(shadow)
        
        layout.addWidget(self.container)
        self.setLayout(layout)
        
        # Hide initially
        self.hide()
    
    def get_button_style(self):
        """Get button stylesheet"""
        return """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.4);
            }
        """
    
    def setup_animations(self):
        """Setup animations for showing/hiding"""
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(0.95)
        
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(200)
        self.fade_out.setStartValue(0.95)
        self.fade_out.setEndValue(0.0)
        self.fade_out.finished.connect(self.hide)
    
    def position_overlay(self):
        """Position overlay in top-right corner"""
        desktop = QDesktopWidget()
        screen_rect = desktop.screenGeometry()
        
        x = screen_rect.width() - self.width() - 20
        y = 20
        
        self.move(x, y)
    
    def start_focus_session(self, duration_minutes=None, task_title=None):
        """Start a focus session"""
        if duration_minutes:
            self.duration_minutes = duration_minutes
        
        if task_title:
            self.task_title = task_title
            self.task_label.setText(task_title)
        
        self.start_time = datetime.now()
        self.is_active = True
        self.is_break = False
        
        # Update UI
        self.title_label.setText("🎯 Focus Mode")
        self.container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(76, 175, 80, 200), stop:1 rgba(67, 160, 71, 200));
                border-radius: 15px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)
        
        # Start timers
        self.update_timer.start(1000)  # Update every second
        self.completion_timer.start(self.duration_minutes * 60 * 1000)  # Total duration
        
        # Show with animation
        self.show()
        self.fade_in.start()
    
    def start_break_session(self, duration_minutes=5):
        """Start a break session"""
        self.duration_minutes = duration_minutes
        self.start_time = datetime.now()
        self.is_active = True
        self.is_break = True
        
        # Update UI for break
        self.title_label.setText("☕ Break Time")
        self.task_label.setText("Take a break, you've earned it!")
        self.container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(33, 150, 243, 200), stop:1 rgba(30, 136, 229, 200));
                border-radius: 15px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)
        
        # Start timers
        self.update_timer.start(1000)
        self.completion_timer.start(self.duration_minutes * 60 * 1000)
        
        # Show with animation
        self.show()
        self.fade_in.start()
    
    def update_display(self):
        """Update the time display and progress"""
        if not self.is_active or not self.start_time:
            return
        
        # Calculate elapsed time
        elapsed = datetime.now() - self.start_time
        elapsed_seconds = int(elapsed.total_seconds())
        total_seconds = self.duration_minutes * 60
        
        remaining_seconds = max(0, total_seconds - elapsed_seconds)
        
        # Update progress bar
        progress = min(100, (elapsed_seconds / total_seconds) * 100)
        self.progress_bar.setValue(int(progress))
        
        # Update time display
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        # Change color when time is running low
        if remaining_seconds <= 60 and not self.is_break:  # Last minute
            self.time_label.setStyleSheet("""
                QLabel {
                    color: #FFD54F;
                    font-size: 16px;
                    font-weight: bold;
                    background: transparent;
                    border: none;
                }
            """)
        elif remaining_seconds <= 300 and not self.is_break:  # Last 5 minutes
            self.time_label.setStyleSheet("""
                QLabel {
                    color: #FFB74D;
                    font-size: 16px;
                    font-weight: bold;
                    background: transparent;
                    border: none;
                }
            """)
        else:
            self.time_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    background: transparent;
                    border: none;
                }
            """)
    
    def toggle_pause(self):
        """Toggle pause/resume"""
        if self.update_timer.isActive():
            # Pause
            self.update_timer.stop()
            self.completion_timer.stop()
            self.pause_btn.setText("▶️")
            self.title_label.setText("⏸️ Paused")
        else:
            # Resume
            self.update_timer.start(1000)
            # Recalculate remaining time for completion timer
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                elapsed_seconds = int(elapsed.total_seconds())
                total_seconds = self.duration_minutes * 60
                remaining_seconds = max(0, total_seconds - elapsed_seconds)
                
                if remaining_seconds > 0:
                    self.completion_timer.start(remaining_seconds * 1000)
            
            self.pause_btn.setText("⏸️")
            self.title_label.setText("🎯 Focus Mode" if not self.is_break else "☕ Break Time")
    
    def request_break(self):
        """Request a break"""
        if not self.is_break:
            self.break_requested.emit()
    
    def stop_focus(self):
        """Stop the focus session"""
        self.is_active = False
        self.update_timer.stop()
        self.completion_timer.stop()
        
        self.focus_cancelled.emit()
        self.hide_overlay()
    
    def on_focus_completed(self):
        """Handle focus session completion"""
        self.is_active = False
        self.update_timer.stop()
        
        # Flash completion
        self.flash_completion()
        
        # Emit completion signal after flash
        QTimer.singleShot(1500, self.emit_completion)
    
    def flash_completion(self):
        """Flash overlay to indicate completion"""
        # Change to completion color
        completion_style = """
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 193, 7, 220), stop:1 rgba(255, 179, 0, 220));
                border-radius: 15px;
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """
        
        if self.is_break:
            self.title_label.setText("✅ Break Complete!")
            self.task_label.setText("Ready to get back to work?")
        else:
            self.title_label.setText("🎉 Session Complete!")
            self.task_label.setText("Great job! Time for a break.")
        
        self.container.setStyleSheet(completion_style)
        self.progress_bar.setValue(100)
        self.time_label.setText("00:00")
    
    def emit_completion(self):
        """Emit completion signal and hide"""
        self.focus_completed.emit()
        self.hide_overlay()
    
    def hide_overlay(self):
        """Hide the overlay with animation"""
        self.fade_out.start()
    
    def show_overlay(self):
        """Show the overlay with animation"""
        self.show()
        self.fade_in.start()
    
    def is_session_active(self):
        """Check if a session is currently active"""
        return self.is_active

class FocusModeManager:
    """Manages focus mode sessions and breaks"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.overlay = FocusModeOverlay()
        self.current_task = None
        self.sessions_completed = 0
        
        # Connect signals
        self.overlay.focus_completed.connect(self.on_session_completed)
        self.overlay.focus_cancelled.connect(self.on_session_cancelled)
        self.overlay.break_requested.connect(self.start_break)
    
    def start_focus_session(self, task_title="Focus Session", duration=25):
        """Start a focus session"""
        if self.overlay.is_session_active():
            return False
        
        self.current_task = task_title
        self.overlay.start_focus_session(duration, task_title)
        return True
    
    def start_break(self, duration=5):
        """Start a break session"""
        if self.overlay.is_session_active():
            self.overlay.stop_focus()
        
        self.overlay.start_break_session(duration)
    
    def stop_current_session(self):
        """Stop the current session"""
        if self.overlay.is_session_active():
            self.overlay.stop_focus()
    
    def on_session_completed(self):
        """Handle session completion"""
        if self.overlay.is_break:
            # Break completed, ready for work
            self.sessions_completed += 1
            if self.parent:
                self.parent.tray_icon.showMessage(
                    "AI Assistant", 
                    "Break time over! Ready to focus?",
                    self.parent.tray_icon.Information, 3000
                )
        else:
            # Work session completed
            self.sessions_completed += 1
            if self.parent:
                self.parent.tray_icon.showMessage(
                    "AI Assistant", 
                    f"Focus session completed! Sessions today: {self.sessions_completed}",
                    self.parent.tray_icon.Information, 3000
                )
            
            # Auto-start break after work session
            QTimer.singleShot(2000, lambda: self.start_break(5))
    
    def on_session_cancelled(self):
        """Handle session cancellation"""
        if self.parent:
            self.parent.tray_icon.showMessage(
                "AI Assistant", 
                "Focus session cancelled",
                self.parent.tray_icon.Information, 2000
            )
    
    def get_stats(self):
        """Get focus session statistics"""
        return {
            "sessions_today": self.sessions_completed,
            "current_active": self.overlay.is_session_active(),
            "current_task": self.current_task
        }

# Test the focus mode
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Test focus mode overlay
    focus = FocusModeOverlay(1, "Test Focus Session")  # 1 minute for testing
    focus.focus_completed.connect(lambda: print("Focus session completed!"))
    focus.focus_cancelled.connect(lambda: print("Focus session cancelled!"))
    
    focus.start_focus_session()
    
    sys.exit(app.exec_())