import os
import json
import uuid
import hashlib
import hmac
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import jwt
import threading
import requests
from urllib.parse import urlparse

class WidgetAPIServer:
    """API server for embedding AI Avatar Assistant as a widget in external dashboards"""
    
    def __init__(self, ai_assistant, data_source_manager, project_estimator, port=5555):
        self.ai_assistant = ai_assistant
        self.data_source_manager = data_source_manager
        self.project_estimator = project_estimator
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for cross-origin requests
        
        # Widget management
        self.authorized_widgets = {}  # widget_id -> widget_config
        self.api_keys = {}  # api_key -> client_config
        self.active_sessions = {}  # session_id -> session_data
        
        # Load configuration
        self.config_file = "data/widget_api_config.json"
        self.load_configuration()
        
        # Setup routes
        self.setup_routes()
        
        # Start server thread
        self.server_thread = None
        self.is_running = False
    
    def load_configuration(self):
        """Load widget API configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                self.authorized_widgets = config.get("authorized_widgets", {})
                self.api_keys = config.get("api_keys", {})
                
                self.logger.info(f"Loaded {len(self.authorized_widgets)} authorized widgets")
                
            except Exception as e:
                self.logger.error(f"Failed to load widget configuration: {e}")
                self.create_default_configuration()
        else:
            self.create_default_configuration()
    
    def create_default_configuration(self):
        """Create default widget API configuration"""
        default_config = {
            "authorized_widgets": {},
            "api_keys": {},
            "settings": {
                "max_widgets_per_domain": 5,
                "session_timeout": 3600,
                "rate_limit": 100,
                "allowed_origins": ["*"],
                "require_https": False
            }
        }
        
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        self.logger.info("Created default widget API configuration")
    
    def save_configuration(self):
        """Save current configuration"""
        try:
            config = {
                "authorized_widgets": self.authorized_widgets,
                "api_keys": self.api_keys,
                "settings": {
                    "max_widgets_per_domain": 5,
                    "session_timeout": 3600,
                    "rate_limit": 100,
                    "allowed_origins": ["*"],
                    "require_https": False
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save widget configuration: {e}")
    
    def generate_api_key(self, client_name: str, domain: str, permissions: List[str] = None) -> str:
        """Generate a new API key for a client"""
        api_key = f"ak_{uuid.uuid4().hex[:16]}"
        
        client_config = {
            "client_name": client_name,
            "domain": domain,
            "permissions": permissions or ["read", "estimate", "chat"],
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "usage_count": 0,
            "active": True
        }
        
        self.api_keys[api_key] = client_config
        self.save_configuration()
        
        self.logger.info(f"Generated API key for {client_name} ({domain})")
        return api_key
    
    def authorize_widget(self, api_key: str, widget_url: str, widget_config: Dict) -> str:
        """Authorize a widget for a specific URL"""
        if api_key not in self.api_keys:
            raise ValueError("Invalid API key")
        
        client_config = self.api_keys[api_key]
        if not client_config["active"]:
            raise ValueError("API key is disabled")
        
        # Parse and validate URL
        parsed_url = urlparse(widget_url)
        domain = parsed_url.netloc
        
        if client_config["domain"] != "*" and domain != client_config["domain"]:
            raise ValueError("Domain not authorized for this API key")
        
        # Generate widget ID
        widget_id = f"widget_{uuid.uuid4().hex[:12]}"
        
        # Store widget configuration
        widget_data = {
            "widget_id": widget_id,
            "api_key": api_key,
            "widget_url": widget_url,
            "domain": domain,
            "config": widget_config,
            "created_at": datetime.now().isoformat(),
            "last_accessed": None,
            "access_count": 0,
            "active": True
        }
        
        self.authorized_widgets[widget_id] = widget_data
        self.save_configuration()
        
        self.logger.info(f"Authorized widget {widget_id} for {widget_url}")
        return widget_id
    
    def validate_request(self, widget_id: str, api_key: str) -> bool:
        """Validate widget request"""
        if widget_id not in self.authorized_widgets:
            return False
        
        widget_data = self.authorized_widgets[widget_id]
        
        if not widget_data["active"]:
            return False
        
        if widget_data["api_key"] != api_key:
            return False
        
        # Update usage statistics
        widget_data["last_accessed"] = datetime.now().isoformat()
        widget_data["access_count"] += 1
        
        self.api_keys[api_key]["last_used"] = datetime.now().isoformat()
        self.api_keys[api_key]["usage_count"] += 1
        
        return True
    
    def setup_routes(self):
        """Setup Flask routes for the widget API"""
        
        @self.app.route('/widget/register', methods=['POST'])
        def register_widget():
            """Register a new widget"""
            try:
                data = request.get_json()
                
                client_name = data.get('client_name')
                domain = data.get('domain')
                widget_url = data.get('widget_url')
                widget_config = data.get('widget_config', {})
                
                if not all([client_name, domain, widget_url]):
                    return jsonify({"error": "Missing required fields"}), 400
                
                # Generate API key
                api_key = self.generate_api_key(client_name, domain)
                
                # Authorize widget
                widget_id = self.authorize_widget(api_key, widget_url, widget_config)
                
                return jsonify({
                    "success": True,
                    "api_key": api_key,
                    "widget_id": widget_id,
                    "widget_url": f"/widget/embed/{widget_id}"
                })
                
            except Exception as e:
                self.logger.error(f"Widget registration error: {e}")
                return jsonify({"error": str(e)}), 400
        
        @self.app.route('/widget/embed/<widget_id>')
        def embed_widget(widget_id):
            """Serve the embeddable widget"""
            if widget_id not in self.authorized_widgets:
                return "Widget not found", 404
            
            widget_data = self.authorized_widgets[widget_id]
            if not widget_data["active"]:
                return "Widget disabled", 403
            
            # Generate widget HTML
            widget_html = self.generate_widget_html(widget_id, widget_data)
            return widget_html
        
        @self.app.route('/api/chat', methods=['POST'])
        def chat_endpoint():
            """Handle chat requests from widgets"""
            try:
                data = request.get_json()
                widget_id = data.get('widget_id')
                api_key = data.get('api_key')
                message = data.get('message')
                context = data.get('context', {})
                
                if not self.validate_request(widget_id, api_key):
                    return jsonify({"error": "Unauthorized"}), 401
                
                # Process chat message through AI assistant
                response = self.process_chat_message(message, context, widget_id)
                
                return jsonify({
                    "success": True,
                    "response": response
                })
                
            except Exception as e:
                self.logger.error(f"Chat endpoint error: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/estimate', methods=['POST'])
        def estimate_endpoint():
            """Handle project estimation requests"""
            try:
                data = request.get_json()
                widget_id = data.get('widget_id')
                api_key = data.get('api_key')
                
                if not self.validate_request(widget_id, api_key):
                    return jsonify({"error": "Unauthorized"}), 401
                
                project_description = data.get('project_description')
                requirements = data.get('requirements', [])
                technologies = data.get('technologies', [])
                deadline = data.get('deadline')
                
                # Generate project estimate
                estimate = self.project_estimator.estimate_project(
                    project_description, requirements, technologies, deadline
                )
                
                # Convert estimate to JSON-serializable format
                estimate_data = {
                    "project_name": estimate.project_name,
                    "total_hours": estimate.total_hours,
                    "optimistic_hours": estimate.optimistic_hours,
                    "realistic_hours": estimate.realistic_hours,
                    "pessimistic_hours": estimate.pessimistic_hours,
                    "complexity_score": estimate.complexity_score,
                    "difficulty_level": estimate.difficulty_level,
                    "confidence_level": estimate.confidence_level,
                    "risk_score": estimate.risk_score,
                    "risk_factors": estimate.risk_factors,
                    "technologies": estimate.technologies,
                    "recommended_team_size": estimate.recommended_team_size,
                    "recommended_roles": estimate.recommended_roles,
                    "team_members": estimate.team_members,
                    "phase_breakdown": estimate.phase_breakdown,
                    "similar_projects": estimate.similar_projects
                }
                
                return jsonify({
                    "success": True,
                    "estimate": estimate_data
                })
                
            except Exception as e:
                self.logger.error(f"Estimate endpoint error: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/data/projects', methods=['GET'])
        def get_projects():
            """Get all projects data"""
            try:
                widget_id = request.args.get('widget_id')
                api_key = request.args.get('api_key')
                
                if not self.validate_request(widget_id, api_key):
                    return jsonify({"error": "Unauthorized"}), 401
                
                projects = self.data_source_manager.get_all_projects()
                
                return jsonify({
                    "success": True,
                    "projects": projects,
                    "count": len(projects)
                })
                
            except Exception as e:
                self.logger.error(f"Projects endpoint error: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/data/team', methods=['GET'])
        def get_team_members():
            """Get team members data"""
            try:
                widget_id = request.args.get('widget_id')
                api_key = request.args.get('api_key')
                
                if not self.validate_request(widget_id, api_key):
                    return jsonify({"error": "Unauthorized"}), 401
                
                team_members = self.data_source_manager.get_team_members()
                
                return jsonify({
                    "success": True,
                    "team_members": team_members,
                    "count": len(team_members)
                })
                
            except Exception as e:
                self.logger.error(f"Team endpoint error: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/analytics', methods=['GET'])
        def get_analytics():
            """Get analytics data"""
            try:
                widget_id = request.args.get('widget_id')
                api_key = request.args.get('api_key')
                
                if not self.validate_request(widget_id, api_key):
                    return jsonify({"error": "Unauthorized"}), 401
                
                # Get analytics from the main AI assistant
                analytics_data = self.ai_assistant.analytics_engine.get_visual_analytics_data()
                
                return jsonify({
                    "success": True,
                    "analytics": analytics_data
                })
                
            except Exception as e:
                self.logger.error(f"Analytics endpoint error: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/actions', methods=['POST'])
        def execute_action():
            """Execute actions through the widget"""
            try:
                data = request.get_json()
                widget_id = data.get('widget_id')
                api_key = data.get('api_key')
                
                if not self.validate_request(widget_id, api_key):
                    return jsonify({"error": "Unauthorized"}), 401
                
                action = data.get('action')
                parameters = data.get('parameters', {})
                
                # Execute action through AI assistant's action system
                result = self.execute_widget_action(action, parameters, widget_id)
                
                return jsonify({
                    "success": True,
                    "result": result
                })
                
            except Exception as e:
                self.logger.error(f"Action endpoint error: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get widget and system status"""
            try:
                widget_id = request.args.get('widget_id')
                api_key = request.args.get('api_key')
                
                if widget_id and api_key:
                    if not self.validate_request(widget_id, api_key):
                        return jsonify({"error": "Unauthorized"}), 401
                
                status = {
                    "server_status": "running",
                    "data_sources": self.data_source_manager.get_data_source_status(),
                    "widget_count": len(self.authorized_widgets),
                    "active_sessions": len(self.active_sessions),
                    "last_sync": datetime.now().isoformat()
                }
                
                return jsonify({
                    "success": True,
                    "status": status
                })
                
            except Exception as e:
                self.logger.error(f"Status endpoint error: {e}")
                return jsonify({"error": str(e)}), 500
    
    def generate_widget_html(self, widget_id: str, widget_data: Dict) -> str:
        """Generate HTML for embeddable widget"""
        widget_config = widget_data.get("config", {})
        
        # Get the base URL for API calls
        base_url = request.host_url.rstrip('/')
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Avatar Assistant Widget</title>
    <style>
        .ai-avatar-widget {
            width: {{ width }};
            height: {{ height }};
            border: 1px solid #ddd;
            border-radius: 8px;
            background: white;
            display: flex;
            flex-direction: column;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            position: relative;
            overflow: hidden;
        }
        
        .widget-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            justify-content: between;
        }
        
        .avatar-icon {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: rgba(255,255,255,0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            font-size: 16px;
        }
        
        .widget-title {
            flex: 1;
            font-weight: 600;
            font-size: 14px;
        }
        
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4CAF50;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .widget-content {
            flex: 1;
            padding: 16px;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }
        
        .chat-area {
            flex: 1;
            min-height: 200px;
            border: 1px solid #eee;
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 12px;
            overflow-y: auto;
            background: #fafafa;
        }
        
        .message {
            margin-bottom: 12px;
            padding: 8px 12px;
            border-radius: 12px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .message.user {
            background: #667eea;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .message.assistant {
            background: white;
            border: 1px solid #e0e0e0;
            margin-right: auto;
        }
        
        .input-area {
            display: flex;
            gap: 8px;
        }
        
        .message-input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 20px;
            outline: none;
            font-size: 14px;
        }
        
        .send-button {
            padding: 8px 16px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
        }
        
        .send-button:hover {
            background: #5a67d8;
        }
        
        .send-button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .quick-actions {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }
        
        .quick-action {
            padding: 4px 8px;
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 12px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .quick-action:hover {
            background: #667eea;
            color: white;
        }
        
        .loading {
            display: none;
            text-align: center;
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="ai-avatar-widget">
        <div class="widget-header">
            <div class="avatar-icon">🤖</div>
            <div class="widget-title">AI Assistant</div>
            <div class="status-indicator"></div>
        </div>
        
        <div class="widget-content">
            <div class="quick-actions">
                <div class="quick-action" onclick="quickAction('estimate')">📊 Estimate Project</div>
                <div class="quick-action" onclick="quickAction('team')">👥 Find Team</div>
                <div class="quick-action" onclick="quickAction('analytics')">📈 Analytics</div>
                <div class="quick-action" onclick="quickAction('status')">⚡ Status</div>
            </div>
            
            <div class="chat-area" id="chatArea">
                <div class="message assistant">
                    Hello! I'm your AI Assistant. I can help you with project estimation, team recommendations, analytics, and more. What would you like to know?
                </div>
            </div>
            
            <div class="loading" id="loading">AI is thinking...</div>
            
            <div class="input-area">
                <input type="text" 
                       class="message-input" 
                       id="messageInput" 
                       placeholder="Type your message..."
                       onkeypress="handleKeyPress(event)">
                <button class="send-button" onclick="sendMessage()" id="sendButton">Send</button>
            </div>
        </div>
    </div>

    <script>
        const WIDGET_ID = '{{ widget_id }}';
        const API_KEY = '{{ api_key }}';
        const BASE_URL = '{{ base_url }}';
        
        let isLoading = false;
        
        function addMessage(content, isUser = false) {
            const chatArea = document.getElementById('chatArea');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
            messageDiv.textContent = content;
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        function setLoading(loading) {
            isLoading = loading;
            document.getElementById('loading').style.display = loading ? 'block' : 'none';
            document.getElementById('sendButton').disabled = loading;
            document.getElementById('messageInput').disabled = loading;
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || isLoading) return;
            
            addMessage(message, true);
            input.value = '';
            setLoading(true);
            
            try {
                const response = await fetch(`${BASE_URL}/api/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        widget_id: WIDGET_ID,
                        api_key: API_KEY,
                        message: message,
                        context: {
                            domain: window.location.hostname,
                            timestamp: new Date().toISOString()
                        }
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage(data.response.message || data.response);
                } else {
                    addMessage('Sorry, I encountered an error. Please try again.');
                }
                
            } catch (error) {
                console.error('Chat error:', error);
                addMessage('Sorry, I couldn\\'t connect to the server. Please try again.');
            } finally {
                setLoading(false);
            }
        }
        
        async function quickAction(action) {
            if (isLoading) return;
            
            setLoading(true);
            
            try {
                let response;
                
                switch (action) {
                    case 'estimate':
                        addMessage('📊 I can help you estimate a project. Please describe your project requirements.', false);
                        break;
                        
                    case 'team':
                        response = await fetch(`${BASE_URL}/api/data/team?widget_id=${WIDGET_ID}&api_key=${API_KEY}`);
                        const teamData = await response.json();
                        if (teamData.success) {
                            addMessage(`👥 Found ${teamData.count} team members available. What kind of skills are you looking for?`, false);
                        }
                        break;
                        
                    case 'analytics':
                        response = await fetch(`${BASE_URL}/api/analytics?widget_id=${WIDGET_ID}&api_key=${API_KEY}`);
                        const analyticsData = await response.json();
                        if (analyticsData.success) {
                            addMessage('📈 Here\\'s your current analytics overview. Your productivity is looking good!', false);
                        }
                        break;
                        
                    case 'status':
                        response = await fetch(`${BASE_URL}/api/status?widget_id=${WIDGET_ID}&api_key=${API_KEY}`);
                        const statusData = await response.json();
                        if (statusData.success) {
                            const status = statusData.status;
                            addMessage(`⚡ System Status: ${status.data_sources.active_sources}/${status.data_sources.total_sources} data sources active, ${status.widget_count} widgets deployed.`, false);
                        }
                        break;
                }
                
            } catch (error) {
                console.error('Quick action error:', error);
                addMessage('Sorry, I couldn\\'t complete that action. Please try again.');
            } finally {
                setLoading(false);
            }
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        // Initialize widget
        document.addEventListener('DOMContentLoaded', function() {
            console.log('AI Avatar Widget initialized');
            
            // Send initial status check
            quickAction('status');
        });
    </script>
</body>
</html>
        """
        
        from jinja2 import Template
        template = Template(html_template)
        
        return template.render(
            widget_id=widget_id,
            api_key=widget_data["api_key"],
            base_url=request.host_url.rstrip('/'),
            width=widget_config.get("width", "400px"),
            height=widget_config.get("height", "500px")
        )
    
    def process_chat_message(self, message: str, context: Dict, widget_id: str) -> Dict:
        """Process chat message through the AI assistant"""
        try:
            # Get widget configuration for context
            widget_data = self.authorized_widgets[widget_id]
            
            # Add widget context to the message context
            enhanced_context = {
                **context,
                "widget_id": widget_id,
                "domain": widget_data["domain"],
                "widget_url": widget_data["widget_url"]
            }
            
            # Process through conversational AI
            if hasattr(self.ai_assistant, 'chat_interface') and hasattr(self.ai_assistant.chat_interface, 'ai'):
                response = self.ai_assistant.chat_interface.ai.process_message(message, enhanced_context)
            else:
                # Fallback: simple responses
                response = self.generate_fallback_response(message, enhanced_context)
            
            return {
                "message": response.get("message", response),
                "actions": response.get("actions", []),
                "context": enhanced_context
            }
            
        except Exception as e:
            self.logger.error(f"Chat processing error: {e}")
            return {
                "message": "I apologize, but I encountered an error processing your request. Please try again.",
                "actions": [],
                "context": context
            }
    
    def generate_fallback_response(self, message: str, context: Dict) -> Dict:
        """Generate fallback responses when AI system is not available"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['estimate', 'project', 'cost', 'time']):
            return {
                "message": "I can help you estimate your project! Please provide more details about your project requirements, technologies, and timeline.",
                "actions": ["show_estimation_form"]
            }
        
        elif any(word in message_lower for word in ['team', 'member', 'skill', 'developer']):
            return {
                "message": "I can recommend team members based on your project needs. What skills or roles are you looking for?",
                "actions": ["show_team_search"]
            }
        
        elif any(word in message_lower for word in ['analytics', 'report', 'data', 'insight']):
            return {
                "message": "I can provide analytics and insights about your projects and team performance. What specific metrics would you like to see?",
                "actions": ["show_analytics"]
            }
        
        elif any(word in message_lower for word in ['status', 'health', 'system']):
            status = self.data_source_manager.get_data_source_status()
            return {
                "message": f"System is running well! {status['active_sources']} data sources are active out of {status['total_sources']} total sources.",
                "actions": ["show_detailed_status"]
            }
        
        else:
            return {
                "message": "I'm here to help with project estimation, team recommendations, analytics, and system management. How can I assist you today?",
                "actions": ["show_help_menu"]
            }
    
    def execute_widget_action(self, action: str, parameters: Dict, widget_id: str) -> Dict:
        """Execute actions requested through the widget"""
        try:
            widget_data = self.authorized_widgets[widget_id]
            
            if action == "estimate_project":
                # Generate project estimate
                estimate = self.project_estimator.estimate_project(
                    parameters.get("description", ""),
                    parameters.get("requirements", []),
                    parameters.get("technologies", []),
                    parameters.get("deadline")
                )
                
                return {
                    "action": action,
                    "result": {
                        "project_name": estimate.project_name,
                        "total_hours": estimate.total_hours,
                        "difficulty": estimate.difficulty_level,
                        "confidence": estimate.confidence_level,
                        "team_size": estimate.recommended_team_size
                    }
                }
            
            elif action == "search_team":
                # Search for team members
                team_members = self.data_source_manager.get_team_members()
                skills = parameters.get("skills", [])
                
                # Filter team members by skills
                filtered_members = []
                for member in team_members:
                    member_skills = member.get("skills", [])
                    if any(skill.lower() in [s.lower() for s in member_skills] for skill in skills):
                        filtered_members.append(member)
                
                return {
                    "action": action,
                    "result": {
                        "members": filtered_members[:5],  # Top 5 matches
                        "total_found": len(filtered_members)
                    }
                }
            
            elif action == "get_analytics":
                # Get analytics data
                analytics_data = self.ai_assistant.analytics_engine.get_visual_analytics_data()
                
                return {
                    "action": action,
                    "result": analytics_data
                }
            
            else:
                return {
                    "action": action,
                    "result": {"error": f"Unknown action: {action}"}
                }
                
        except Exception as e:
            self.logger.error(f"Action execution error: {e}")
            return {
                "action": action,
                "result": {"error": str(e)}
            }
    
    def start_server(self):
        """Start the widget API server"""
        if self.is_running:
            return
        
        def run_server():
            try:
                self.app.run(
                    host='0.0.0.0',
                    port=self.port,
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
            except Exception as e:
                self.logger.error(f"Server error: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.is_running = True
        
        self.logger.info(f"Widget API server started on port {self.port}")
    
    def stop_server(self):
        """Stop the widget API server"""
        self.is_running = False
        if self.server_thread:
            self.server_thread.join(timeout=1.0)
        
        self.logger.info("Widget API server stopped")
    
    def get_widget_status(self) -> Dict:
        """Get current widget status"""
        return {
            "server_running": self.is_running,
            "port": self.port,
            "total_widgets": len(self.authorized_widgets),
            "active_widgets": sum(1 for w in self.authorized_widgets.values() if w["active"]),
            "total_api_keys": len(self.api_keys),
            "active_api_keys": sum(1 for k in self.api_keys.values() if k["active"]),
            "active_sessions": len(self.active_sessions)
        }

# Widget integration manager for the main application
class WidgetIntegrationManager:
    """Manages widget integration for the AI Avatar Assistant"""
    
    def __init__(self, ai_assistant, data_source_manager, project_estimator):
        self.ai_assistant = ai_assistant
        self.data_source_manager = data_source_manager
        self.project_estimator = project_estimator
        self.widget_server = None
        self.logger = logging.getLogger(__name__)
    
    def initialize_widget_api(self, port: int = 5555):
        """Initialize the widget API server"""
        try:
            self.widget_server = WidgetAPIServer(
                self.ai_assistant,
                self.data_source_manager,
                self.project_estimator,
                port
            )
            
            self.widget_server.start_server()
            self.logger.info(f"Widget API initialized on port {port}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize widget API: {e}")
            return False
    
    def generate_integration_code(self, client_name: str, domain: str, widget_url: str) -> Dict:
        """Generate integration code for embedding the widget"""
        if not self.widget_server:
            raise ValueError("Widget API not initialized")
        
        try:
            # Generate API key and authorize widget
            api_key = self.widget_server.generate_api_key(client_name, domain)
            widget_id = self.widget_server.authorize_widget(api_key, widget_url, {})
            
            # Generate integration code
            integration_code = f"""
<!-- AI Avatar Assistant Widget Integration -->
<div id="ai-avatar-widget-container"></div>

<script>
(function() {{
    const widgetContainer = document.getElementById('ai-avatar-widget-container');
    const iframe = document.createElement('iframe');
    
    iframe.src = 'http://localhost:{self.widget_server.port}/widget/embed/{widget_id}';
    iframe.style.width = '400px';
    iframe.style.height = '500px';
    iframe.style.border = '1px solid #ddd';
    iframe.style.borderRadius = '8px';
    iframe.frameBorder = '0';
    iframe.allowTransparency = 'true';
    
    widgetContainer.appendChild(iframe);
    
    // Widget API for custom interactions
    window.AIAvatar = {{
        widgetId: '{widget_id}',
        apiKey: '{api_key}',
        baseUrl: 'http://localhost:{self.widget_server.port}',
        
        async chat(message) {{
            const response = await fetch(this.baseUrl + '/api/chat', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    widget_id: this.widgetId,
                    api_key: this.apiKey,
                    message: message
                }})
            }});
            return await response.json();
        }},
        
        async estimate(projectData) {{
            const response = await fetch(this.baseUrl + '/api/estimate', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    widget_id: this.widgetId,
                    api_key: this.apiKey,
                    ...projectData
                }})
            }});
            return await response.json();
        }},
        
        async getAnalytics() {{
            const response = await fetch(
                `${{this.baseUrl}}/api/analytics?widget_id=${{this.widgetId}}&api_key=${{this.apiKey}}`
            );
            return await response.json();
        }}
    }};
}})();
</script>
            """
            
            return {
                "success": True,
                "api_key": api_key,
                "widget_id": widget_id,
                "integration_code": integration_code.strip(),
                "widget_url": f"http://localhost:{self.widget_server.port}/widget/embed/{widget_id}",
                "api_endpoint": f"http://localhost:{self.widget_server.port}/api"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate integration code: {e}")
            raise
    
    def get_widget_dashboard_url(self) -> str:
        """Get the URL for the widget management dashboard"""
        if not self.widget_server:
            return None
        
        return f"http://localhost:{self.widget_server.port}/dashboard"
    
    def shutdown(self):
        """Shutdown the widget integration"""
        if self.widget_server:
            self.widget_server.stop_server()
            self.widget_server = None

# Test the widget API
if __name__ == "__main__":
    import sys
    import tempfile
    
    # Create mock components for testing
    class MockAIAssistant:
        def __init__(self):
            self.analytics_engine = self
        
        def get_visual_analytics_data(self):
            return {"productivity": 0.85, "projects": 5, "tasks_completed": 23}
    
    class MockDataSourceManager:
        def get_data_source_status(self):
            return {"active_sources": 2, "total_sources": 3}
        
        def get_all_projects(self):
            return [{"name": "Test Project", "status": "active"}]
        
        def get_team_members(self):
            return [{"name": "John Doe", "skills": ["python", "react"]}]
    
    class MockProjectEstimator:
        def estimate_project(self, desc, req, tech, deadline):
            from types import SimpleNamespace
            return SimpleNamespace(
                project_name="Test Project",
                total_hours=120,
                optimistic_hours=100,
                realistic_hours=120,
                pessimistic_hours=150,
                complexity_score=0.6,
                difficulty_level="Medium",
                confidence_level=0.8,
                risk_score=0.3,
                risk_factors=[],
                technologies=tech or [],
                recommended_team_size=3,
                recommended_roles=["developer", "designer"],
                team_members=[],
                phase_breakdown={},
                similar_projects=[]
            )
    
    print("🧪 Testing Widget API Server...")
    
    # Create mock components
    ai_assistant = MockAIAssistant()
    data_manager = MockDataSourceManager()
    estimator = MockProjectEstimator()
    
    # Create integration manager
    integration_manager = WidgetIntegrationManager(ai_assistant, data_manager, estimator)
    
    # Initialize widget API
    if integration_manager.initialize_widget_api(5556):
        print("✅ Widget API server started on port 5556")
        
        # Generate integration code
        try:
            integration_data = integration_manager.generate_integration_code(
                "Test Client",
                "localhost",
                "http://localhost:3000/dashboard"
            )
            
            print(f"✅ Generated API key: {integration_data['api_key'][:16]}...")
            print(f"✅ Widget ID: {integration_data['widget_id']}")
            print(f"✅ Widget URL: {integration_data['widget_url']}")
            print("✅ Integration code generated successfully")
            
        except Exception as e:
            print(f"❌ Failed to generate integration code: {e}")
        
        print("\n🌐 Widget API server is running...")
        print("Access the widget at: http://localhost:5556/widget/embed/{widget_id}")
        print("API endpoint: http://localhost:5556/api")
        
        # Keep server running for testing
        try:
            input("Press Enter to stop the server...")
        except KeyboardInterrupt:
            pass
        
        integration_manager.shutdown()
        print("✅ Widget API server stopped")
    else:
        print("❌ Failed to start widget API server")