import sys
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QLineEdit, QPushButton, QScrollArea, QFrame, 
                            QLabel, QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QTextCursor, QPixmap, QIcon
import logging

class ChatMessage:
    """Represents a single chat message"""
    
    def __init__(self, content: str, is_user: bool, timestamp: datetime = None, message_type: str = "text"):
        self.content = content
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now()
        self.message_type = message_type  # text, action, system, suggestion
        self.actions = []  # Available actions for this message

class MessageWidget(QFrame):
    """Widget for displaying a single chat message"""
    
    action_triggered = pyqtSignal(str, dict)
    
    def __init__(self, message: ChatMessage, parent=None):
        super().__init__(parent)
        self.message = message
        self.init_ui()
    
    def init_ui(self):
        """Initialize the message widget UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        
        # Message container
        if self.message.is_user:
            self.setStyleSheet("""
                QFrame {
                    background-color: #E3F2FD;
                    border: 1px solid #BBDEFB;
                    border-radius: 12px;
                    margin-left: 50px;
                    margin-right: 10px;
                }
            """)
            alignment = Qt.AlignRight
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F5F5F5;
                    border: 1px solid #E0E0E0;
                    border-radius: 12px;
                    margin-left: 10px;
                    margin-right: 50px;
                }
            """)
            alignment = Qt.AlignLeft
        
        # Sender label
        sender_layout = QHBoxLayout()
        sender_label = QLabel("You" if self.message.is_user else "🤖 AI Assistant")
        sender_label.setFont(QFont("Arial", 9, QFont.Bold))
        sender_label.setStyleSheet("color: #666; margin-bottom: 2px;")
        
        time_label = QLabel(self.message.timestamp.strftime("%H:%M"))
        time_label.setFont(QFont("Arial", 8))
        time_label.setStyleSheet("color: #999;")
        
        if self.message.is_user:
            sender_layout.addStretch()
            sender_layout.addWidget(sender_label)
            sender_layout.addWidget(time_label)
        else:
            sender_layout.addWidget(sender_label)
            sender_layout.addWidget(time_label)
            sender_layout.addStretch()
        
        layout.addLayout(sender_layout)
        
        # Message content
        content_label = QLabel(self.message.content)
        content_label.setWordWrap(True)
        content_label.setFont(QFont("Arial", 10))
        content_label.setAlignment(alignment)
        content_label.setStyleSheet("color: #333; line-height: 1.4;")
        layout.addWidget(content_label)
        
        # Action buttons
        if self.message.actions:
            self.add_action_buttons(layout)
        
        self.setLayout(layout)
    
    def add_action_buttons(self, layout):
        """Add action buttons to the message"""
        button_layout = QHBoxLayout()
        
        for action in self.message.actions:
            btn = QPushButton(action.get("label", "Action"))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4A90E2;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 9pt;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #357ABD;
                }
            """)
            btn.clicked.connect(lambda checked, a=action: self.action_triggered.emit(a.get("action", ""), a.get("context", {})))
            button_layout.addWidget(btn)
        
        if not self.message.is_user:
            button_layout.addStretch()
        else:
            button_layout.insertStretch(0)
        
        layout.addLayout(button_layout)

class ConversationalAI:
    """AI brain for handling natural language conversations"""
    
    def __init__(self, db, analytics_engine, action_system, report_generator=None):
        self.db = db
        self.analytics_engine = analytics_engine
        self.action_system = action_system
        self.report_generator = report_generator
        self.logger = logging.getLogger(__name__)
        
        # Conversation context
        self.conversation_history = []
        self.user_context = {}
        
        # AI personality settings
        self.personality_style = "friendly"  # friendly, professional, casual
        self.response_patterns = self.load_response_patterns()
        
    def load_response_patterns(self) -> Dict:
        """Load response patterns for different types of queries"""
        return {
            "greetings": [
                "Hello! I'm your AI assistant. How can I help you today?",
                "Hi there! What would you like to know or do?",
                "Hey! I'm here to help you stay productive. What's on your mind?"
            ],
            "task_queries": [
                "Let me check your tasks...",
                "I'll look into your task list for you.",
                "Analyzing your current tasks..."
            ],
            "productivity_queries": [
                "Let me analyze your productivity patterns...",
                "I'll check your recent performance data.",
                "Analyzing your work patterns..."
            ],
            "help_requests": [
                "I can help you with tasks, productivity analysis, focus sessions, and more!",
                "Here's what I can do for you: manage tasks, analyze productivity, start focus sessions, and provide insights.",
                "I'm here to help! I can manage your tasks, track productivity, suggest improvements, and much more."
            ]
        }
    
    def process_message(self, user_input: str) -> ChatMessage:
        """Process user input and generate AI response"""
        user_input = user_input.strip().lower()
        
        # Store user message in context
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Analyze intent and generate response
        intent = self.analyze_intent(user_input)
        response_content, actions = self.generate_response(intent, user_input)
        
        # Create response message
        response_message = ChatMessage(
            content=response_content,
            is_user=False,
            message_type="response"
        )
        response_message.actions = actions
        
        # Store AI response in context
        self.conversation_history.append({"role": "assistant", "content": response_content})
        
        return response_message
    
    def analyze_intent(self, user_input: str) -> Dict:
        """Analyze user intent from natural language input"""
        intents = {
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
            "task_query": ["tasks", "task", "todo", "to do", "what do i have", "what's pending", "deadline"],
            "add_task": ["add task", "create task", "new task", "remind me", "i need to"],
            "productivity": ["productivity", "how am i doing", "performance", "stats", "analytics"],
            "focus": ["focus", "concentrate", "start focus", "focus mode", "pomodoro"],
                         "help": ["help", "what can you do", "commands", "how to", "assist"],
             "status": ["status", "overview", "summary", "what's happening"],
             "schedule": ["schedule", "calendar", "when", "time", "availability"],
             "suggestions": ["suggest", "recommend", "advice", "what should", "ideas"],
             "report": ["report", "generate report", "create report", "show report", "analysis report"]
        }
        
        detected_intents = []
        confidence_scores = {}
        
        for intent_name, keywords in intents.items():
            score = 0
            for keyword in keywords:
                if keyword in user_input:
                    score += 1
            
            if score > 0:
                confidence_scores[intent_name] = score / len(keywords)
                detected_intents.append(intent_name)
        
        # Return the highest confidence intent
        if detected_intents:
            primary_intent = max(confidence_scores.keys(), key=lambda k: confidence_scores[k])
            return {
                "primary": primary_intent,
                "confidence": confidence_scores[primary_intent],
                "alternatives": detected_intents,
                "entities": self.extract_entities(user_input)
            }
        
        return {"primary": "unknown", "confidence": 0, "alternatives": [], "entities": {}}
    
    def extract_entities(self, user_input: str) -> Dict:
        """Extract entities like task names, dates, priorities from user input"""
        entities = {}
        
        # Extract time expressions
        time_patterns = [
            (r"tomorrow", "tomorrow"),
            (r"today", "today"),
            (r"next week", "next_week"),
            (r"(\d+)\s*hours?", "hours"),
            (r"(\d+)\s*minutes?", "minutes"),
            (r"at\s*(\d{1,2}):(\d{2})", "time"),
        ]
        
        for pattern, entity_type in time_patterns:
            match = re.search(pattern, user_input)
            if match:
                entities[entity_type] = match.group()
        
        # Extract priority indicators
        if any(word in user_input for word in ["urgent", "important", "high priority", "asap"]):
            entities["priority"] = "high"
        elif any(word in user_input for word in ["low priority", "when possible", "not urgent"]):
            entities["priority"] = "low"
        
        return entities
    
    def generate_response(self, intent: Dict, user_input: str) -> tuple:
        """Generate response content and actions based on intent"""
        primary_intent = intent.get("primary", "unknown")
        entities = intent.get("entities", {})
        
        if primary_intent == "greeting":
            return self.handle_greeting()
        elif primary_intent == "task_query":
            return self.handle_task_query()
        elif primary_intent == "add_task":
            return self.handle_add_task(user_input, entities)
        elif primary_intent == "productivity":
            return self.handle_productivity_query()
        elif primary_intent == "focus":
            return self.handle_focus_request(entities)
        elif primary_intent == "help":
            return self.handle_help_request()
        elif primary_intent == "status":
            return self.handle_status_request()
        elif primary_intent == "suggestions":
            return self.handle_suggestions_request()
        elif primary_intent == "report":
            return self.handle_report_request(user_input, entities)
        else:
            return self.handle_unknown_query(user_input)
    
    def handle_greeting(self) -> tuple:
        """Handle greeting messages"""
        import random
        greeting = random.choice(self.response_patterns["greetings"])
        
        actions = [
            {"label": "📋 Show Tasks", "action": "show_tasks", "context": {}},
            {"label": "📊 Analytics", "action": "open_analytics", "context": {}},
            {"label": "🎯 Start Focus", "action": "start_focus_mode", "context": {}}
        ]
        
        return greeting, actions
    
    def handle_task_query(self) -> tuple:
        """Handle task-related queries"""
        tasks = self.db.get_tasks(status="pending")
        overdue_tasks = [t for t in tasks if self.is_task_overdue(t)]
        today_tasks = [t for t in tasks if self.is_task_due_today(t)]
        
        if not tasks:
            response = "You don't have any pending tasks right now. Great job staying on top of things! 🎉"
            actions = [{"label": "➕ Add Task", "action": "add_task", "context": {}}]
        else:
            response = f"You have {len(tasks)} pending tasks. "
            
            if overdue_tasks:
                response += f"{len(overdue_tasks)} are overdue and need immediate attention. "
            
            if today_tasks:
                response += f"{len(today_tasks)} are due today. "
            
            if not overdue_tasks and not today_tasks:
                response += "You're on track with your deadlines! 👍"
            
            actions = [
                {"label": "📋 View All Tasks", "action": "show_tasks", "context": {}},
                {"label": "🎯 Start Focus Session", "action": "start_focus_mode", "context": {}}
            ]
            
            if overdue_tasks:
                actions.insert(0, {"label": "⚠️ Handle Overdue", "action": "show_overdue_tasks", "context": {}})
        
        return response, actions
    
    def handle_add_task(self, user_input: str, entities: Dict) -> tuple:
        """Handle task creation requests"""
        # Try to extract task title from user input
        task_patterns = [
            r"add task[:\s]+(.+)",
            r"create task[:\s]+(.+)",
            r"remind me to[:\s]+(.+)",
            r"i need to[:\s]+(.+)",
            r"task[:\s]+(.+)"
        ]
        
        task_title = None
        for pattern in task_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                task_title = match.group(1).strip()
                break
        
        if task_title:
            # Extract priority from entities
            priority = 3  # Default medium priority
            if entities.get("priority") == "high":
                priority = 1
            elif entities.get("priority") == "low":
                priority = 5
            
            # Create the task
            task_id = self.db.add_task(
                title=task_title,
                priority=priority,
                metadata={"created_via": "chat", "entities": entities}
            )
            
            response = f"✅ Created task: '{task_title}'"
            if entities.get("priority"):
                response += f" with {entities['priority']} priority"
            
            actions = [
                {"label": "📝 Edit Task", "action": "edit_task", "context": {"task_id": task_id}},
                {"label": "🎯 Start Focus", "action": "start_focus_mode", "context": {"task_title": task_title}}
            ]
        else:
            response = "I'd be happy to help you create a task! What would you like to be reminded about?"
            actions = [{"label": "📝 Open Task Creator", "action": "add_task", "context": {}}]
        
        return response, actions
    
    def handle_productivity_query(self) -> tuple:
        """Handle productivity analysis requests"""
        analysis = self.analytics_engine.analyze_current_situation()
        productivity = analysis.get("productivity_status", {})
        
        completion_rate = productivity.get("completion_rate", 0)
        score = productivity.get("score", 0)
        zone = productivity.get("productivity_zone", "unknown")
        
        response = f"📊 Your productivity is in the '{zone}' zone with a {completion_rate:.1%} completion rate and a score of {score}/100. "
        
        trend = productivity.get("trend", {})
        if trend.get("direction") == "improving":
            response += "Great news - your productivity is trending upward! 📈"
        elif trend.get("direction") == "declining":
            response += "I notice your productivity has been declining. Let's work on improving it! 📉"
        else:
            response += "Your productivity has been stable. 📊"
        
        actions = [
            {"label": "📈 Full Analytics", "action": "open_analytics", "context": {}},
            {"label": "💡 Get Suggestions", "action": "get_suggestions", "context": {}}
        ]
        
        # Add specific suggestions based on analysis
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            high_priority_rec = next((r for r in recommendations if r.get("priority") in ["urgent", "high"]), None)
            if high_priority_rec:
                actions.append({
                    "label": f"🎯 {high_priority_rec.get('title', 'Apply Suggestion')[:20]}...",
                    "action": "apply_suggestion",
                    "context": {"recommendation": high_priority_rec}
                })
        
        return response, actions
    
    def handle_focus_request(self, entities: Dict) -> tuple:
        """Handle focus session requests"""
        duration = 25  # Default Pomodoro
        
        # Extract duration from entities
        if "hours" in entities:
            duration = int(re.search(r"(\d+)", entities["hours"]).group(1)) * 60
        elif "minutes" in entities:
            duration = int(re.search(r"(\d+)", entities["minutes"]).group(1))
        
        response = f"🎯 I'll start a {duration}-minute focus session for you! What would you like to focus on?"
        
        # Get current pending tasks for suggestions
        tasks = self.db.get_tasks(status="pending")
        high_priority_tasks = [t for t in tasks if t.get("priority", 3) <= 2]
        
        actions = [
            {"label": f"▶️ Start {duration}min Focus", "action": "start_focus_mode", "context": {"duration": duration}}
        ]
        
        # Add task-specific focus options
        for task in high_priority_tasks[:2]:  # Show top 2 high-priority tasks
            actions.append({
                "label": f"🎯 Focus: {task['title'][:20]}...",
                "action": "start_focus_mode",
                "context": {"duration": duration, "task_title": task["title"], "task_id": task["id"]}
            })
        
        return response, actions
    
    def handle_help_request(self) -> tuple:
        """Handle help and capability requests"""
        response = """🤖 I'm your AI productivity assistant! Here's what I can help you with:

📋 **Task Management**: Create, view, and manage your tasks
📊 **Analytics**: Analyze your productivity patterns and trends  
🎯 **Focus Sessions**: Start Pomodoro-style focus sessions
💡 **Smart Suggestions**: Get AI-powered productivity recommendations
📈 **Live Monitoring**: Track your work patterns in real-time
🎙️ **Voice Commands**: Talk to me naturally (coming soon!)

Just ask me in natural language - for example:
• "Show me my tasks"
• "Add task: Buy groceries"  
• "How's my productivity?"
• "Start a 45-minute focus session"
• "What should I work on next?"
"""
        
        actions = [
            {"label": "📋 View Tasks", "action": "show_tasks", "context": {}},
            {"label": "📊 Analytics", "action": "open_analytics", "context": {}},
            {"label": "➕ Add Task", "action": "add_task", "context": {}}
        ]
        
        return response, actions
    
    def handle_status_request(self) -> tuple:
        """Handle status and overview requests"""
        tasks = self.db.get_tasks(status="pending")
        completed_today = len([t for t in self.db.get_tasks(status="completed") 
                              if self.is_task_completed_today(t)])
        
        analysis = self.analytics_engine.analyze_current_situation()
        productivity = analysis.get("productivity_status", {})
        
        response = f"""📊 **Your Status Overview:**

📋 Tasks: {len(tasks)} pending
✅ Completed today: {completed_today}
📈 Productivity score: {productivity.get('score', 0)}/100
🎯 Current zone: {productivity.get('productivity_zone', 'unknown').title()}

"""
        
        # Add alerts if any
        alerts = analysis.get("alerts", [])
        if alerts:
            response += f"⚠️ {len(alerts)} active alerts need your attention.\n"
        
        # Add top recommendation
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            top_rec = recommendations[0]
            response += f"💡 Top suggestion: {top_rec.get('title', 'Check analytics')}"
        
        actions = [
            {"label": "📋 View Tasks", "action": "show_tasks", "context": {}},
            {"label": "📊 Full Analytics", "action": "open_analytics", "context": {}}
        ]
        
        if alerts:
            actions.insert(0, {"label": "⚠️ View Alerts", "action": "open_analytics", "context": {"tab": "overview"}})
        
        return response, actions
    
    def handle_suggestions_request(self) -> tuple:
        """Handle requests for AI suggestions"""
        analysis = self.analytics_engine.analyze_current_situation()
        recommendations = analysis.get("recommendations", [])
        
        if not recommendations:
            response = "🎉 You're doing great! No urgent suggestions right now. Keep up the good work!"
            actions = [{"label": "📊 View Analytics", "action": "open_analytics", "context": {}}]
        else:
            top_recommendations = recommendations[:3]
            response = "💡 **Here are my top suggestions for you:**\n\n"
            
            for i, rec in enumerate(top_recommendations, 1):
                priority_emoji = {"urgent": "🚨", "high": "⚠️", "medium": "💡", "low": "ℹ️"}
                emoji = priority_emoji.get(rec.get("priority", "medium"), "💡")
                response += f"{emoji} **{rec.get('title', 'Suggestion')}**\n{rec.get('description', '')}\n\n"
            
            actions = []
            for rec in top_recommendations:
                actions.append({
                    "label": f"✅ {rec.get('title', 'Apply')[:15]}...",
                    "action": "apply_suggestion",
                    "context": {"recommendation": rec}
                })
            
            actions.append({"label": "📊 Full Analytics", "action": "open_analytics", "context": {}})
        
        return response, actions
    
    def handle_report_request(self, user_input: str, entities: Dict) -> tuple:
        """Handle report generation requests"""
        if not self.report_generator:
            response = "I'd love to generate reports for you, but the report generator isn't available right now. You can still view analytics through the dashboard!"
            actions = [{"label": "📊 Open Analytics", "action": "open_analytics", "context": {}}]
            return response, actions
        
        # Parse what kind of report they want
        query_lower = user_input.lower()
        
        # Check for project-specific report
        if any(word in query_lower for word in ["project", "for", "about"]):
            # Try to extract project name
            project_name = self.extract_project_name(user_input)
            if project_name:
                try:
                    report = self.report_generator.generate_project_report(project_name, user_input)
                    temp_link = self.report_generator.generate_temporary_link(report)
                    
                    response = f"📊 I've generated a comprehensive report for '{project_name}'!\n\n"
                    response += f"The report includes:\n"
                    response += f"• 📈 Visual charts and analytics\n"
                    response += f"• 💡 AI-powered insights\n"
                    response += f"• 🎯 Actionable recommendations\n"
                    response += f"• 🎙️ Voice narration (click 'Play Report')\n\n"
                    response += f"Click the link below to view your report. When you open it, I'll start explaining the findings!"
                    
                    actions = [
                        {"label": "📄 View Report", "action": "open_report", "context": {"report_id": report.report_id, "url": temp_link}},
                        {"label": "📊 Analytics Dashboard", "action": "open_analytics", "context": {}},
                        {"label": "💾 Download PDF", "action": "download_report", "context": {"report_id": report.report_id}}
                    ]
                    
                    return response, actions
                    
                except Exception as e:
                    response = f"I encountered an issue generating the report for '{project_name}'. Let me try a different approach."
                    actions = [{"label": "📊 View Analytics", "action": "open_analytics", "context": {}}]
                    return response, actions
            else:
                response = "I'd be happy to generate a project report! Which project would you like me to analyze? You can say something like 'Generate report for Website Redesign'."
                actions = [{"label": "📋 List Projects", "action": "list_projects", "context": {}}]
                return response, actions
        
        # Productivity report
        elif any(word in query_lower for word in ["productivity", "performance", "stats"]):
            try:
                time_period = "30days"
                if "week" in query_lower:
                    time_period = "7days"
                elif "quarter" in query_lower:
                    time_period = "90days"
                
                report = self.report_generator.generate_productivity_report(time_period)
                temp_link = self.report_generator.generate_temporary_link(report)
                
                response = f"📈 I've generated your productivity analysis report!\n\n"
                response += f"The report covers:\n"
                response += f"• 📊 Performance trends and metrics\n"
                response += f"• 🔍 Detailed pattern analysis\n"
                response += f"• 💡 Personalized recommendations\n"
                response += f"• 🎙️ Voice explanation of findings\n\n"
                response += f"Click below to view your report with voice narration!"
                
                actions = [
                    {"label": "📄 View Report", "action": "open_report", "context": {"report_id": report.report_id, "url": temp_link}},
                    {"label": "📊 Live Analytics", "action": "open_analytics", "context": {}}
                ]
                
                return response, actions
                
            except Exception as e:
                response = "I had trouble generating your productivity report. Let me show you the analytics dashboard instead."
                actions = [{"label": "📊 Open Analytics", "action": "open_analytics", "context": {}}]
                return response, actions
        
        # Custom report
        else:
            try:
                report = self.report_generator.generate_custom_report(user_input)
                temp_link = self.report_generator.generate_temporary_link(report)
                
                response = f"📋 I've created a custom report based on your request!\n\n"
                response += f"The report includes my analysis and findings related to: '{user_input}'\n\n"
                response += f"Click below to view the report with voice explanation!"
                
                actions = [
                    {"label": "📄 View Report", "action": "open_report", "context": {"report_id": report.report_id, "url": temp_link}},
                    {"label": "📊 Analytics", "action": "open_analytics", "context": {}}
                ]
                
                return response, actions
                
            except Exception as e:
                response = "I can help you generate various reports! Try asking for:\n• 'Generate report for [project name]'\n• 'Show me my productivity report'\n• 'Create analysis report for last week'"
                actions = [{"label": "📊 View Analytics", "action": "open_analytics", "context": {}}]
                return response, actions
    
    def extract_project_name(self, user_input: str) -> Optional[str]:
        """Extract project name from user input"""
        # Simple extraction - look for words after "for", "about", "on"
        indicators = ["for", "about", "on", "project"]
        words = user_input.split()
        
        for i, word in enumerate(words):
            if word.lower() in indicators and i + 1 < len(words):
                # Take the next 1-3 words as project name
                project_words = []
                for j in range(i + 1, min(i + 4, len(words))):
                    if words[j].lower() not in ["report", "analysis", "the", "my"]:
                        project_words.append(words[j].strip(".,!?"))
                    else:
                        break
                
                if project_words:
                    return " ".join(project_words)
        
        return None
    
    def handle_unknown_query(self, user_input: str) -> tuple:
        """Handle queries that don't match known intents"""
        response = f"I'm not quite sure how to help with '{user_input}', but I'm always learning! Here are some things I can definitely help you with:"
        
        actions = [
            {"label": "📋 Show Tasks", "action": "show_tasks", "context": {}},
            {"label": "📊 Analytics", "action": "open_analytics", "context": {}},
            {"label": "💡 Get Help", "action": "show_help", "context": {}},
            {"label": "➕ Add Task", "action": "add_task", "context": {}}
        ]
        
        return response, actions
    
    # Helper methods
    def is_task_overdue(self, task: Dict) -> bool:
        """Check if a task is overdue"""
        if not task.get('deadline'):
            return False
        try:
            deadline = datetime.fromisoformat(task['deadline'])
            return deadline < datetime.now() and task['status'] != 'completed'
        except:
            return False
    
    def is_task_due_today(self, task: Dict) -> bool:
        """Check if a task is due today"""
        if not task.get('deadline'):
            return False
        try:
            deadline = datetime.fromisoformat(task['deadline'])
            return deadline.date() == datetime.now().date()
        except:
            return False
    
    def is_task_completed_today(self, task: Dict) -> bool:
        """Check if a task was completed today"""
        if task['status'] != 'completed' or not task.get('updated_at'):
            return False
        try:
            updated = datetime.fromisoformat(task['updated_at'])
            return updated.date() == datetime.now().date()
        except:
            return False

class ChatInterface(QWidget):
    """Main chat interface widget"""
    
    action_triggered = pyqtSignal(str, dict)
    
    def __init__(self, db, analytics_engine, action_system, voice_system=None, report_generator=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.analytics_engine = analytics_engine
        self.action_system = action_system
        self.voice_system = voice_system
        self.report_generator = report_generator
        
        # Initialize conversational AI
        self.ai = ConversationalAI(db, analytics_engine, action_system, report_generator)
        
        # Chat state
        self.messages = []
        self.is_listening = False
        
        self.init_ui()
        self.show_welcome_message()
    
    def init_ui(self):
        """Initialize the chat interface UI"""
        self.setWindowTitle("🤖 Chat with AI Assistant")
        self.setGeometry(300, 300, 450, 600)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("🤖 AI Assistant Chat")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Voice button
        if self.voice_system:
            self.voice_btn = QPushButton("🎤")
            self.voice_btn.setFixedSize(40, 40)
            self.voice_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4A90E2;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #357ABD;
                }
                QPushButton:pressed {
                    background-color: #FF6B6B;
                }
            """)
            self.voice_btn.clicked.connect(self.toggle_voice_input)
            header_layout.addWidget(self.voice_btn)
        
        layout.addLayout(header_layout)
        
        # Chat area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 8px;
            }
        """)
        
        # Chat container
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_container.setLayout(self.chat_layout)
        self.chat_scroll.setWidget(self.chat_container)
        
        layout.addWidget(self.chat_scroll)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask me anything... (e.g., 'Show my tasks', 'How's my productivity?')")
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border-color: #4A90E2;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        send_btn = QPushButton("Send")
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        self.setLayout(layout)
        
        # Style the entire widget
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
        """)
    
    def show_welcome_message(self):
        """Show initial welcome message"""
        welcome_message = ChatMessage(
            content="👋 Hello! I'm your AI productivity assistant. I can help you manage tasks, analyze your productivity, start focus sessions, and much more!\n\nTry asking me:\n• 'Show me my tasks'\n• 'How's my productivity?'\n• 'Start a focus session'\n• 'Add task: Call the dentist'",
            is_user=False,
            message_type="welcome"
        )
        welcome_message.actions = [
            {"label": "📋 My Tasks", "action": "show_tasks", "context": {}},
            {"label": "📊 Analytics", "action": "open_analytics", "context": {}},
            {"label": "💡 Help", "action": "show_help", "context": {}}
        ]
        
        self.add_message(welcome_message)
    
    def add_message(self, message: ChatMessage):
        """Add a message to the chat"""
        self.messages.append(message)
        
        # Create message widget
        message_widget = MessageWidget(message)
        message_widget.action_triggered.connect(self.on_action_triggered)
        
        # Add to chat layout
        self.chat_layout.addWidget(message_widget)
        
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
        
        # Voice output for AI messages
        if not message.is_user and self.voice_system and self.voice_system.enabled:
            # Don't speak very long messages or welcome messages
            if len(message.content) < 200 and message.message_type != "welcome":
                self.voice_system.speak_notification(message.content, "friendly")
    
    def scroll_to_bottom(self):
        """Scroll chat to bottom"""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def send_message(self):
        """Send user message and get AI response"""
        user_text = self.input_field.text().strip()
        if not user_text:
            return
        
        # Clear input
        self.input_field.clear()
        
        # Add user message
        user_message = ChatMessage(content=user_text, is_user=True)
        self.add_message(user_message)
        
        # Get AI response
        try:
            ai_response = self.ai.process_message(user_text)
            
            # Add AI response after a short delay for natural feel
            QTimer.singleShot(500, lambda: self.add_message(ai_response))
            
        except Exception as e:
            error_message = ChatMessage(
                content=f"Sorry, I encountered an error: {str(e)}. Please try again!",
                is_user=False,
                message_type="error"
            )
            self.add_message(error_message)
            self.logger.error(f"Chat AI error: {e}")
    
    def toggle_voice_input(self):
        """Toggle voice input mode"""
        if not self.voice_system:
            return
        
        if self.is_listening:
            self.stop_voice_input()
        else:
            self.start_voice_input()
    
    def start_voice_input(self):
        """Start listening for voice input"""
        # This is a placeholder - would need speech recognition library
        self.is_listening = True
        self.voice_btn.setText("🔴")
        self.voice_btn.setStyleSheet(self.voice_btn.styleSheet().replace("#4A90E2", "#FF6B6B"))
        
        # Show listening indicator
        self.input_field.setPlaceholderText("🎤 Listening... (Click microphone to stop)")
        
        # TODO: Implement actual speech recognition
        # For now, just show a message
        QTimer.singleShot(3000, self.simulate_voice_input)
    
    def stop_voice_input(self):
        """Stop listening for voice input"""
        self.is_listening = False
        self.voice_btn.setText("🎤")
        self.voice_btn.setStyleSheet(self.voice_btn.styleSheet().replace("#FF6B6B", "#4A90E2"))
        self.input_field.setPlaceholderText("Ask me anything... (e.g., 'Show my tasks', 'How's my productivity?')")
    
    def simulate_voice_input(self):
        """Simulate voice input (placeholder)"""
        if self.is_listening:
            self.stop_voice_input()
            # Simulate recognized speech
            self.input_field.setText("Show me my tasks")
            QTimer.singleShot(500, self.send_message)
    
    @pyqtSlot(str, dict)
    def on_action_triggered(self, action: str, context: dict):
        """Handle action triggered from chat message"""
        self.action_triggered.emit(action, context)
    
    def show_chat(self):
        """Show the chat interface"""
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_field.setFocus()

# Test the chat interface
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    # Mock objects for testing
    class MockDB:
        def get_tasks(self, status=None):
            return [
                {"id": 1, "title": "Complete project report", "status": "pending", "priority": 1, "deadline": "2024-01-20T17:00:00"},
                {"id": 2, "title": "Buy groceries", "status": "pending", "priority": 3, "deadline": None}
            ]
        
        def add_task(self, title, priority=3, metadata=None):
            return 123
    
    class MockAnalytics:
        def analyze_current_situation(self):
            return {
                "productivity_status": {"completion_rate": 0.75, "score": 85, "productivity_zone": "high"},
                "recommendations": [{"title": "Take a break", "description": "You've been working for 3 hours", "priority": "medium"}],
                "alerts": []
            }
    
    class MockActions:
        pass
    
    app = QApplication(sys.argv)
    
    chat = ChatInterface(MockDB(), MockAnalytics(), MockActions())
    chat.show()
    
    sys.exit(app.exec_())