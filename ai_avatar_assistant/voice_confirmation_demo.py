#!/usr/bin/env python3
"""
AI Avatar Assistant - Voice Confirmation Demo
Demonstrates the enhanced voice command system with confirmation
"""

import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QFont

# Add current directory to path
sys.path.append('.')

try:
    from core.voice_confirmation_system import VoiceConfirmationSystem, VoiceCommand
except ImportError:
    print("⚠️ Voice confirmation system not available - running simulation")
    VoiceConfirmationSystem = None

class VoiceConfirmationDemo(QMainWindow):
    """Demo application for voice confirmation system"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎤 ARIA Voice Confirmation Demo")
        self.setGeometry(100, 100, 600, 500)
        
        # Initialize voice confirmation system
        if VoiceConfirmationSystem:
            self.voice_confirm = VoiceConfirmationSystem()
        else:
            self.voice_confirm = None
        
        self.init_ui()
        self.setup_demo_commands()
    
    def init_ui(self):
        """Initialize the demo UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("🎤 ARIA Voice Confirmation System Demo")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Description
        description = QLabel("""
✨ Enhanced Voice Command Flow:
1. Say "Hey ARIA, [command]" 
2. ARIA shows confirmation tooltip
3. Say "SUBMIT" to execute or "CANCEL" to abort
4. If you take too long, ARIA asks again
5. Click buttons or use voice - your choice!
        """)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Demo buttons
        demo_label = QLabel("🧪 Try These Demo Commands:")
        demo_font = QFont()
        demo_font.setBold(True)
        demo_label.setFont(demo_font)
        layout.addWidget(demo_label)
        
        # Command buttons
        self.create_demo_button(layout, "🚀 Project Estimation", 
                               "estimate my React e-commerce project")
        
        self.create_demo_button(layout, "👥 Team Recommendation", 
                               "who should work on frontend development")
        
        self.create_demo_button(layout, "📊 Analytics Report", 
                               "generate analytics report for this week")
        
        self.create_demo_button(layout, "🔗 Widget Integration", 
                               "create widget integration for ClickUp")
        
        # Log area
        log_label = QLabel("📋 Command Log:")
        log_label.setFont(demo_font)
        layout.addWidget(log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(150)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.log_area)
        
        central_widget.setLayout(layout)
        
        # Style the window
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
                padding: 5px;
            }
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2A5A8F;
            }
        """)
    
    def create_demo_button(self, layout, text, command):
        """Create a demo button for testing commands"""
        button = QPushButton(text)
        button.clicked.connect(lambda: self.simulate_voice_command(command))
        layout.addWidget(button)
    
    def setup_demo_commands(self):
        """Setup demo command handlers"""
        self.command_handlers = {
            "estimate": self.handle_estimation,
            "team": self.handle_team_recommendation,
            "analytics": self.handle_analytics,
            "widget": self.handle_widget_integration
        }
    
    def simulate_voice_command(self, command_text):
        """Simulate a voice command for demo purposes"""
        self.log(f"🎤 Voice Input: '{command_text}'")
        
        # Determine intent and parameters
        intent, parameters, preview = self.parse_command(command_text)
        
        if not self.voice_confirm:
            # Fallback demo without actual voice confirmation
            self.log("⚠️ Voice confirmation system not available")
            self.log(f"🔄 Would show confirmation for: {preview}")
            QTimer.singleShot(2000, lambda: self.execute_demo_command(intent, parameters))
            return
        
        # Process with voice confirmation system
        command_id = self.voice_confirm.process_voice_command(
            command_text=command_text,
            intent=intent,
            parameters=parameters,
            confidence=0.95,
            callback=self.execute_demo_command,
            preview_text=preview
        )
        
        self.log(f"🔄 Command queued for confirmation: {command_id}")
        self.log("💡 Say 'SUBMIT' or click Submit button to execute")
        self.log("❌ Say 'CANCEL' or click Cancel button to abort")
    
    def parse_command(self, command_text):
        """Parse command text to extract intent and parameters"""
        command_lower = command_text.lower()
        
        if "estimate" in command_lower or "project" in command_lower:
            return "estimate", {"project_type": "react_ecommerce"}, "Estimate React e-commerce project"
        
        elif "team" in command_lower or "who should" in command_lower:
            return "team", {"role": "frontend", "technology": "react"}, "Find frontend developer for React"
        
        elif "analytics" in command_lower or "report" in command_lower:
            return "analytics", {"period": "week", "type": "summary"}, "Generate weekly analytics report"
        
        elif "widget" in command_lower or "integration" in command_lower:
            return "widget", {"platform": "clickup", "type": "dashboard"}, "Create ClickUp widget integration"
        
        else:
            return "general", {"query": command_text}, f"Process: {command_text}"
    
    def execute_demo_command(self, intent, parameters):
        """Execute a demo command after confirmation"""
        self.log(f"✅ Executing command: {intent}")
        
        # Simulate processing time
        self.log("⏳ Processing...")
        
        # Use QTimer to simulate async processing
        QTimer.singleShot(1500, lambda: self.complete_demo_command(intent, parameters))
    
    def complete_demo_command(self, intent, parameters):
        """Complete demo command execution"""
        if intent in self.command_handlers:
            result = self.command_handlers[intent](parameters)
            self.log(f"🎯 Result: {result}")
        else:
            self.log(f"🤖 ARIA: I've processed your {intent} request")
        
        self.log("=" * 50)
    
    def handle_estimation(self, parameters):
        """Handle project estimation demo"""
        project_type = parameters.get("project_type", "unknown")
        return f"""
Project Estimation Complete:
• Type: {project_type.replace('_', ' ').title()}
• Duration: 12-16 weeks
• Team: 4 developers
• Cost: $75,000 - $120,000
• Risk Level: Medium
• Recommended start: Next sprint
        """.strip()
    
    def handle_team_recommendation(self, parameters):
        """Handle team recommendation demo"""
        role = parameters.get("role", "developer")
        technology = parameters.get("technology", "general")
        return f"""
Team Recommendation:
• Role: {role.title()} Developer
• Technology: {technology.title()}
• Recommended: Sarah Chen (85% match)
• Availability: 60% capacity
• Skills: React, TypeScript, Redux
• Experience: 5+ years
        """.strip()
    
    def handle_analytics(self, parameters):
        """Handle analytics demo"""
        period = parameters.get("period", "week")
        return f"""
Analytics Report ({period}):
• Projects Active: 3
• Completion Rate: 87%
• Team Velocity: +15%
• Budget Status: On track
• Risk Alerts: 1 (minor)
• Productivity Score: 94/100
        """.strip()
    
    def handle_widget_integration(self, parameters):
        """Handle widget integration demo"""
        platform = parameters.get("platform", "generic")
        return f"""
Widget Integration Created:
• Platform: {platform.title()}
• API Key: aria_widget_demo_123
• Widget ID: aw_demo_456
• Status: ✅ Ready to embed
• Code generated and copied to clipboard
        """.strip()
    
    def log(self, message):
        """Add message to log area"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        cursor = self.log_area.textCursor()
        cursor.movePosition(cursor.End)
        self.log_area.setTextCursor(cursor)

def main():
    """Run the voice confirmation demo"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("ARIA Voice Confirmation Demo")
    app.setApplicationVersion("1.0")
    
    # Create and show demo window
    demo = VoiceConfirmationDemo()
    demo.show()
    
    print("🎤 ARIA Voice Confirmation Demo")
    print("=" * 40)
    print("✨ Features demonstrated:")
    print("  • Voice command confirmation with 'submit' keyword")
    print("  • Visual confirmation tooltip with buttons")
    print("  • Timeout handling with re-prompting")
    print("  • Voice and UI confirmation options")
    print("  • Command preview before execution")
    print()
    print("🎯 Try the demo buttons to see confirmation in action!")
    print("💡 In real usage, you'd say 'Hey ARIA' first, then your command")
    print()
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()