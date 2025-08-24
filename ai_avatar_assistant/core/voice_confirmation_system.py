#!/usr/bin/env python3
"""
AI Avatar Assistant - Voice Confirmation System
Enhanced voice command system with confirmation and timeout handling
"""

import os
import time
import threading
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPixmap

class ConfirmationState(Enum):
    """States for voice confirmation process"""
    IDLE = "idle"
    LISTENING = "listening"
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class VoiceCommand:
    """Voice command with confirmation requirements"""
    id: str
    command_text: str
    intent: str
    parameters: Dict[str, Any]
    timestamp: datetime
    confidence: float
    requires_confirmation: bool = True
    timeout_seconds: int = 10
    preview_text: str = ""

class VoiceConfirmationTooltip(QWidget):
    """Floating tooltip for voice command confirmation"""
    
    # Signals
    command_confirmed = pyqtSignal(str)  # command_id
    command_cancelled = pyqtSignal(str)  # command_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_command = None
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the confirmation tooltip UI"""
        # Window properties
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(350, 120)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Background with rounded corners
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 240);
                border-radius: 12px;
                border: 2px solid rgba(74, 144, 226, 180);
            }
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
            QPushButton {
                background-color: rgba(74, 144, 226, 200);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(74, 144, 226, 255);
            }
            QPushButton:pressed {
                background-color: rgba(53, 122, 189, 255);
            }
            #cancelButton {
                background-color: rgba(220, 53, 69, 200);
            }
            #cancelButton:hover {
                background-color: rgba(220, 53, 69, 255);
            }
        """)
        
        # Header
        self.header_label = QLabel("🎤 Voice Command Detected")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(11)
        self.header_label.setFont(header_font)
        self.header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.header_label)
        
        # Command preview
        self.command_label = QLabel("")
        command_font = QFont()
        command_font.setPointSize(10)
        self.command_label.setFont(command_font)
        self.command_label.setAlignment(Qt.AlignCenter)
        self.command_label.setWordWrap(True)
        layout.addWidget(self.command_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Submit button
        self.submit_button = QPushButton("✓ Submit")
        self.submit_button.clicked.connect(self.confirm_command)
        self.submit_button.setShortcut("Return")
        button_layout.addWidget(self.submit_button)
        
        # Cancel button
        self.cancel_button = QPushButton("✗ Cancel")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.cancel_command)
        self.cancel_button.setShortcut("Escape")
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Initially hidden
        self.hide()
    
    def show_confirmation(self, command: VoiceCommand):
        """Show confirmation tooltip for a voice command"""
        self.current_command = command
        
        # Update UI
        self.command_label.setText(f"'{command.command_text}'\n{command.preview_text}")
        
        # Position tooltip (center of screen)
        from PyQt5.QtWidgets import QDesktopWidget
        desktop = QDesktopWidget()
        screen_rect = desktop.screenGeometry()
        x = (screen_rect.width() - self.width()) // 2
        y = (screen_rect.height() - self.height()) // 2
        self.move(x, y)
        
        # Show tooltip
        self.show()
        self.raise_()
        self.activateWindow()
        self.submit_button.setFocus()
        
        # Start timeout timer
        self.timeout_timer.start(command.timeout_seconds * 1000)
        
        # Update header with countdown
        self.update_countdown()
    
    def update_countdown(self):
        """Update header with countdown timer"""
        if self.timeout_timer.isActive():
            remaining = self.timeout_timer.remainingTime() // 1000
            self.header_label.setText(f"🎤 Voice Command Detected ({remaining}s)")
            
            # Schedule next update
            if remaining > 0:
                QTimer.singleShot(1000, self.update_countdown)
    
    def confirm_command(self):
        """Confirm the current command"""
        if self.current_command:
            self.timeout_timer.stop()
            self.command_confirmed.emit(self.current_command.id)
            self.hide()
            self.current_command = None
    
    def cancel_command(self):
        """Cancel the current command"""
        if self.current_command:
            self.timeout_timer.stop()
            self.command_cancelled.emit(self.current_command.id)
            self.hide()
            self.current_command = None
    
    def on_timeout(self):
        """Handle timeout - ask user for decision"""
        self.timeout_timer.stop()
        
        # Change appearance to highlight timeout
        self.header_label.setText("⏰ Command Timeout - Submit or Cancel?")
        self.setStyleSheet(self.styleSheet().replace(
            "border: 2px solid rgba(74, 144, 226, 180);",
            "border: 2px solid rgba(255, 193, 7, 200);"
        ))
        
        # Flash effect
        self.flash_tooltip()
    
    def flash_tooltip(self):
        """Flash the tooltip to get attention"""
        original_style = self.styleSheet()
        flash_style = original_style.replace(
            "background-color: rgba(45, 45, 45, 240);",
            "background-color: rgba(255, 193, 7, 240);"
        )
        
        self.setStyleSheet(flash_style)
        QTimer.singleShot(200, lambda: self.setStyleSheet(original_style))

class VoiceConfirmationSystem:
    """Enhanced voice command system with confirmation"""
    
    def __init__(self, voice_system=None, speech_recognition=None):
        self.logger = logging.getLogger(__name__)
        self.voice_system = voice_system
        self.speech_recognition = speech_recognition
        
        # State management
        self.state = ConfirmationState.IDLE
        self.pending_commands: Dict[str, VoiceCommand] = {}
        self.confirmation_callbacks: Dict[str, Callable] = {}
        
        # UI components
        self.confirmation_tooltip = VoiceConfirmationTooltip()
        self.confirmation_tooltip.command_confirmed.connect(self.on_command_confirmed)
        self.confirmation_tooltip.command_cancelled.connect(self.on_command_cancelled)
        
        # Configuration
        self.config = self.load_configuration()
        
        # Voice confirmation listening
        self.listening_for_submit = False
        self.submit_keywords = ["submit", "execute", "confirm", "yes", "do it"]
        self.cancel_keywords = ["cancel", "stop", "no", "abort", "nevermind"]
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load voice confirmation configuration"""
        config_path = "data/voice_confirmation_config.json"
        default_config = {
            "confirmation_required": True,
            "timeout_seconds": 10,
            "auto_submit_after_silence": False,
            "silence_duration": 3,
            "show_visual_confirmation": True,
            "voice_confirmation_enabled": True,
            "submit_keywords": ["submit", "execute", "confirm", "yes", "do it"],
            "cancel_keywords": ["cancel", "stop", "no", "abort", "nevermind"],
            "confirmation_prompt": "Say 'submit' to execute or 'cancel' to abort",
            "timeout_prompt": "Command timeout. Say 'submit' or 'cancel'?"
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            else:
                os.makedirs("data", exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error loading voice confirmation config: {e}")
        
        return default_config
    
    def process_voice_command(self, command_text: str, intent: str, 
                            parameters: Dict[str, Any], confidence: float,
                            callback: Callable, preview_text: str = "") -> str:
        """Process a voice command with confirmation"""
        
        # Generate unique command ID
        command_id = f"cmd_{int(time.time() * 1000)}"
        
        # Create command object
        command = VoiceCommand(
            id=command_id,
            command_text=command_text,
            intent=intent,
            parameters=parameters,
            timestamp=datetime.now(),
            confidence=confidence,
            requires_confirmation=self.config.get("confirmation_required", True),
            timeout_seconds=self.config.get("timeout_seconds", 10),
            preview_text=preview_text or f"Execute: {intent}"
        )
        
        # Store command and callback
        self.pending_commands[command_id] = command
        self.confirmation_callbacks[command_id] = callback
        
        # If confirmation not required, execute immediately
        if not command.requires_confirmation:
            self.execute_command(command_id)
            return command_id
        
        # Show confirmation
        self.show_confirmation(command)
        
        # Start listening for voice confirmation
        if self.config.get("voice_confirmation_enabled", True):
            self.start_voice_confirmation_listening(command_id)
        
        # Speak confirmation prompt
        if self.voice_system:
            prompt = self.config.get("confirmation_prompt", 
                                   "Say 'submit' to execute or 'cancel' to abort")
            self.voice_system.speak_async(prompt)
        
        return command_id
    
    def show_confirmation(self, command: VoiceCommand):
        """Show visual confirmation for command"""
        if self.config.get("show_visual_confirmation", True):
            self.confirmation_tooltip.show_confirmation(command)
        
        self.state = ConfirmationState.PENDING_CONFIRMATION
        self.logger.info(f"Showing confirmation for command: {command.command_text}")
    
    def start_voice_confirmation_listening(self, command_id: str):
        """Start listening for voice confirmation keywords"""
        self.listening_for_submit = True
        
        # Start a separate thread to listen for confirmation
        threading.Thread(
            target=self._voice_confirmation_listener,
            args=(command_id,),
            daemon=True
        ).start()
    
    def _voice_confirmation_listener(self, command_id: str):
        """Listen for voice confirmation in separate thread"""
        if not self.speech_recognition or not self.speech_recognition.is_enabled:
            return
        
        timeout = self.config.get("timeout_seconds", 10)
        start_time = time.time()
        
        while (self.listening_for_submit and 
               command_id in self.pending_commands and
               time.time() - start_time < timeout):
            
            try:
                # Listen for speech
                text = self.speech_recognition.listen_once(timeout=2)
                if text:
                    text_lower = text.lower()
                    
                    # Check for submit keywords
                    if any(keyword in text_lower for keyword in self.submit_keywords):
                        self.listening_for_submit = False
                        self.on_voice_confirmed(command_id)
                        return
                    
                    # Check for cancel keywords
                    elif any(keyword in text_lower for keyword in self.cancel_keywords):
                        self.listening_for_submit = False
                        self.on_voice_cancelled(command_id)
                        return
                
            except Exception as e:
                self.logger.debug(f"Voice confirmation listening error: {e}")
                time.sleep(0.5)
        
        # Timeout reached
        self.listening_for_submit = False
        if command_id in self.pending_commands:
            self.on_confirmation_timeout(command_id)
    
    def on_voice_confirmed(self, command_id: str):
        """Handle voice confirmation"""
        self.logger.info(f"Voice confirmation received for command: {command_id}")
        
        if self.voice_system:
            self.voice_system.speak_async("Command confirmed, executing now")
        
        self.execute_command(command_id)
        self.confirmation_tooltip.hide()
    
    def on_voice_cancelled(self, command_id: str):
        """Handle voice cancellation"""
        self.logger.info(f"Voice cancellation received for command: {command_id}")
        
        if self.voice_system:
            self.voice_system.speak_async("Command cancelled")
        
        self.cancel_command(command_id)
        self.confirmation_tooltip.hide()
    
    def on_command_confirmed(self, command_id: str):
        """Handle UI confirmation button click"""
        self.listening_for_submit = False
        self.execute_command(command_id)
    
    def on_command_cancelled(self, command_id: str):
        """Handle UI cancellation button click"""
        self.listening_for_submit = False
        self.cancel_command(command_id)
    
    def on_confirmation_timeout(self, command_id: str):
        """Handle confirmation timeout"""
        self.logger.info(f"Confirmation timeout for command: {command_id}")
        
        if self.voice_system:
            timeout_prompt = self.config.get("timeout_prompt", 
                                           "Command timeout. Say 'submit' or 'cancel'?")
            self.voice_system.speak_async(timeout_prompt)
        
        # Keep the tooltip visible but update it
        if command_id in self.pending_commands:
            self.confirmation_tooltip.on_timeout()
            
            # Extended listening for final decision
            self.start_voice_confirmation_listening(command_id)
    
    def execute_command(self, command_id: str):
        """Execute a confirmed command"""
        if command_id in self.pending_commands and command_id in self.confirmation_callbacks:
            command = self.pending_commands[command_id]
            callback = self.confirmation_callbacks[command_id]
            
            self.logger.info(f"Executing confirmed command: {command.command_text}")
            
            try:
                # Execute the callback
                callback(command.intent, command.parameters)
                self.state = ConfirmationState.CONFIRMED
                
            except Exception as e:
                self.logger.error(f"Error executing command: {e}")
                if self.voice_system:
                    self.voice_system.speak_async("Sorry, there was an error executing the command")
            
            # Cleanup
            self.cleanup_command(command_id)
    
    def cancel_command(self, command_id: str):
        """Cancel a pending command"""
        if command_id in self.pending_commands:
            command = self.pending_commands[command_id]
            self.logger.info(f"Cancelling command: {command.command_text}")
            self.state = ConfirmationState.CANCELLED
            self.cleanup_command(command_id)
    
    def cleanup_command(self, command_id: str):
        """Clean up command resources"""
        self.pending_commands.pop(command_id, None)
        self.confirmation_callbacks.pop(command_id, None)
        self.state = ConfirmationState.IDLE
    
    def get_pending_commands(self) -> List[VoiceCommand]:
        """Get list of pending commands"""
        return list(self.pending_commands.values())
    
    def cancel_all_pending(self):
        """Cancel all pending commands"""
        for command_id in list(self.pending_commands.keys()):
            self.cancel_command(command_id)
        
        self.confirmation_tooltip.hide()
        self.listening_for_submit = False
    
    def is_waiting_for_confirmation(self) -> bool:
        """Check if system is waiting for confirmation"""
        return self.state == ConfirmationState.PENDING_CONFIRMATION
    
    def configure_confirmation(self, **kwargs):
        """Update confirmation configuration"""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
        
        # Save updated configuration
        config_path = "data/voice_confirmation_config.json"
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving voice confirmation config: {e}")

# Global voice confirmation system instance
voice_confirmation_system = VoiceConfirmationSystem()