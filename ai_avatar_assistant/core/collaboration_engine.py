#!/usr/bin/env python3
"""
AI Avatar Assistant - Collaboration Engine
Real-time collaboration features for team widgets and shared workspaces
"""

import os
import json
import time
import threading
import logging
import uuid
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import queue
import websocket

class CollaborationEventType(Enum):
    """Types of collaboration events"""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    MESSAGE_SENT = "message_sent"
    PROJECT_UPDATED = "project_updated"
    ESTIMATION_SHARED = "estimation_shared"
    TEAM_RECOMMENDATION = "team_recommendation"
    ANALYTICS_UPDATED = "analytics_updated"
    CURSOR_MOVED = "cursor_moved"
    WIDGET_INTERACTION = "widget_interaction"

@dataclass
class CollaborationUser:
    """User in collaboration session"""
    user_id: str
    name: str
    avatar_url: Optional[str]
    role: str
    widget_id: str
    session_id: str
    joined_at: datetime
    last_activity: datetime
    is_active: bool = True

@dataclass
class CollaborationMessage:
    """Message in collaboration session"""
    message_id: str
    session_id: str
    user_id: str
    content: str
    message_type: str  # text, system, ai_response, estimation, recommendation
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class CollaborationSession:
    """Collaboration session for a project or workspace"""
    session_id: str
    name: str
    description: str
    project_id: Optional[str]
    created_by: str
    created_at: datetime
    users: Dict[str, CollaborationUser]
    messages: List[CollaborationMessage]
    shared_data: Dict[str, Any]
    is_active: bool = True

class CollaborationEngine:
    """Real-time collaboration engine for team widgets"""
    
    def __init__(self, ai_assistant, widget_api_server):
        self.ai_assistant = ai_assistant
        self.widget_api_server = widget_api_server
        self.logger = logging.getLogger(__name__)
        
        self.sessions: Dict[str, CollaborationSession] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.widget_sessions: Dict[str, str] = {}  # widget_id -> session_id
        
        self.event_handlers: Dict[CollaborationEventType, List[Callable]] = {}
        self.message_queue = queue.Queue()
        self.is_running = False
        self.broadcast_thread = None
        
        self.setup_event_handlers()
        self.load_sessions()
    
    def setup_event_handlers(self):
        """Setup default event handlers"""
        for event_type in CollaborationEventType:
            self.event_handlers[event_type] = []
        
        # Register default handlers
        self.register_event_handler(CollaborationEventType.USER_JOINED, self._handle_user_joined)
        self.register_event_handler(CollaborationEventType.USER_LEFT, self._handle_user_left)
        self.register_event_handler(CollaborationEventType.MESSAGE_SENT, self._handle_message_sent)
        self.register_event_handler(CollaborationEventType.PROJECT_UPDATED, self._handle_project_updated)
    
    def load_sessions(self):
        """Load collaboration sessions from storage"""
        sessions_path = "data/collaboration_sessions.json"
        
        try:
            if os.path.exists(sessions_path):
                with open(sessions_path, 'r') as f:
                    data = json.load(f)
                
                for session_data in data.get("sessions", []):
                    session = self._deserialize_session(session_data)
                    self.sessions[session.session_id] = session
                
                self.logger.info(f"Loaded {len(self.sessions)} collaboration sessions")
            else:
                self.logger.info("No existing collaboration sessions found")
                
        except Exception as e:
            self.logger.error(f"Error loading collaboration sessions: {e}")
    
    def save_sessions(self):
        """Save collaboration sessions to storage"""
        sessions_path = "data/collaboration_sessions.json"
        
        try:
            os.makedirs("data", exist_ok=True)
            
            data = {
                "sessions": [self._serialize_session(session) for session in self.sessions.values()],
                "updated_at": datetime.now().isoformat()
            }
            
            with open(sessions_path, 'w') as f:
                json.dump(data, f, indent=4, default=str)
            
            self.logger.info("Collaboration sessions saved")
            
        except Exception as e:
            self.logger.error(f"Error saving collaboration sessions: {e}")
    
    def start_collaboration(self):
        """Start the collaboration engine"""
        if self.is_running:
            self.logger.warning("Collaboration engine already running")
            return
        
        self.is_running = True
        self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.broadcast_thread.start()
        
        self.logger.info("Collaboration engine started")
    
    def stop_collaboration(self):
        """Stop the collaboration engine"""
        self.is_running = False
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=5)
        
        self.logger.info("Collaboration engine stopped")
    
    def create_session(self, name: str, description: str, created_by: str, 
                      project_id: Optional[str] = None) -> str:
        """Create a new collaboration session"""
        session_id = f"collab_{uuid.uuid4().hex[:12]}"
        
        session = CollaborationSession(
            session_id=session_id,
            name=name,
            description=description,
            project_id=project_id,
            created_by=created_by,
            created_at=datetime.now(),
            users={},
            messages=[],
            shared_data={}
        )
        
        self.sessions[session_id] = session
        self.save_sessions()
        
        self.logger.info(f"Created collaboration session: {name} ({session_id})")
        return session_id
    
    def join_session(self, session_id: str, user_id: str, name: str, 
                    widget_id: str, role: str = "member", 
                    avatar_url: Optional[str] = None) -> bool:
        """Join a collaboration session"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        # Create user object
        user = CollaborationUser(
            user_id=user_id,
            name=name,
            avatar_url=avatar_url,
            role=role,
            widget_id=widget_id,
            session_id=session_id,
            joined_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        # Add user to session
        session.users[user_id] = user
        self.user_sessions[user_id] = session_id
        self.widget_sessions[widget_id] = session_id
        
        # Broadcast user joined event
        self.broadcast_event(CollaborationEventType.USER_JOINED, {
            "session_id": session_id,
            "user": asdict(user)
        })
        
        self.logger.info(f"User {name} joined session {session.name}")
        return True
    
    def leave_session(self, user_id: str) -> bool:
        """Leave a collaboration session"""
        if user_id not in self.user_sessions:
            return False
        
        session_id = self.user_sessions[user_id]
        session = self.sessions[session_id]
        
        if user_id in session.users:
            user = session.users[user_id]
            widget_id = user.widget_id
            
            # Remove user from session
            del session.users[user_id]
            del self.user_sessions[user_id]
            if widget_id in self.widget_sessions:
                del self.widget_sessions[widget_id]
            
            # Broadcast user left event
            self.broadcast_event(CollaborationEventType.USER_LEFT, {
                "session_id": session_id,
                "user_id": user_id,
                "user_name": user.name
            })
            
            self.logger.info(f"User {user.name} left session {session.name}")
            return True
        
        return False
    
    def send_message(self, user_id: str, content: str, message_type: str = "text", 
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Send a message in the collaboration session"""
        if user_id not in self.user_sessions:
            return None
        
        session_id = self.user_sessions[user_id]
        session = self.sessions[session_id]
        
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        message = CollaborationMessage(
            message_id=message_id,
            session_id=session_id,
            user_id=user_id,
            content=content,
            message_type=message_type,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        session.messages.append(message)
        
        # Update user activity
        if user_id in session.users:
            session.users[user_id].last_activity = datetime.now()
        
        # Broadcast message
        self.broadcast_event(CollaborationEventType.MESSAGE_SENT, {
            "session_id": session_id,
            "message": asdict(message)
        })
        
        return message_id
    
    def share_estimation(self, user_id: str, estimation_data: Dict[str, Any]) -> bool:
        """Share project estimation with session"""
        if user_id not in self.user_sessions:
            return False
        
        session_id = self.user_sessions[user_id]
        session = self.sessions[session_id]
        
        # Add estimation to shared data
        if "estimations" not in session.shared_data:
            session.shared_data["estimations"] = []
        
        estimation_data["shared_by"] = user_id
        estimation_data["shared_at"] = datetime.now().isoformat()
        session.shared_data["estimations"].append(estimation_data)
        
        # Broadcast estimation shared event
        self.broadcast_event(CollaborationEventType.ESTIMATION_SHARED, {
            "session_id": session_id,
            "user_id": user_id,
            "estimation": estimation_data
        })
        
        self.logger.info(f"User {user_id} shared estimation in session {session.name}")
        return True
    
    def share_team_recommendation(self, user_id: str, recommendation_data: Dict[str, Any]) -> bool:
        """Share team recommendation with session"""
        if user_id not in self.user_sessions:
            return False
        
        session_id = self.user_sessions[user_id]
        session = self.sessions[session_id]
        
        # Add recommendation to shared data
        if "recommendations" not in session.shared_data:
            session.shared_data["recommendations"] = []
        
        recommendation_data["shared_by"] = user_id
        recommendation_data["shared_at"] = datetime.now().isoformat()
        session.shared_data["recommendations"].append(recommendation_data)
        
        # Broadcast recommendation shared event
        self.broadcast_event(CollaborationEventType.TEAM_RECOMMENDATION, {
            "session_id": session_id,
            "user_id": user_id,
            "recommendation": recommendation_data
        })
        
        self.logger.info(f"User {user_id} shared team recommendation in session {session.name}")
        return True
    
    def update_shared_analytics(self, session_id: str, analytics_data: Dict[str, Any]) -> bool:
        """Update shared analytics data"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.shared_data["analytics"] = analytics_data
        session.shared_data["analytics_updated_at"] = datetime.now().isoformat()
        
        # Broadcast analytics update
        self.broadcast_event(CollaborationEventType.ANALYTICS_UPDATED, {
            "session_id": session_id,
            "analytics": analytics_data
        })
        
        return True
    
    def track_widget_interaction(self, user_id: str, interaction_data: Dict[str, Any]) -> bool:
        """Track widget interaction for collaboration awareness"""
        if user_id not in self.user_sessions:
            return False
        
        session_id = self.user_sessions[user_id]
        
        # Update user activity
        session = self.sessions[session_id]
        if user_id in session.users:
            session.users[user_id].last_activity = datetime.now()
        
        # Broadcast widget interaction
        self.broadcast_event(CollaborationEventType.WIDGET_INTERACTION, {
            "session_id": session_id,
            "user_id": user_id,
            "interaction": interaction_data
        })
        
        return True
    
    def register_event_handler(self, event_type: CollaborationEventType, handler: Callable):
        """Register event handler for collaboration events"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        self.logger.info(f"Registered handler for {event_type}")
    
    def broadcast_event(self, event_type: CollaborationEventType, data: Dict[str, Any]):
        """Broadcast event to all relevant users"""
        event = {
            "type": event_type.value,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.message_queue.put(event)
        
        # Trigger event handlers
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_type}: {e}")
    
    def _broadcast_loop(self):
        """Main broadcast loop for real-time events"""
        while self.is_running:
            try:
                # Get event from queue (with timeout)
                try:
                    event = self.message_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process and broadcast event
                self._process_broadcast_event(event)
                
            except Exception as e:
                self.logger.error(f"Error in broadcast loop: {e}")
                time.sleep(1)
    
    def _process_broadcast_event(self, event: Dict[str, Any]):
        """Process and broadcast event to relevant widgets"""
        event_type = event["type"]
        data = event["data"]
        session_id = data.get("session_id")
        
        if not session_id or session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        # Send event to all users in the session
        for user in session.users.values():
            if user.is_active:
                self._send_event_to_widget(user.widget_id, event)
    
    def _send_event_to_widget(self, widget_id: str, event: Dict[str, Any]):
        """Send event to specific widget"""
        try:
            # This would integrate with the widget API server
            # to send real-time events to the widget
            if hasattr(self.widget_api_server, 'send_event_to_widget'):
                self.widget_api_server.send_event_to_widget(widget_id, event)
            else:
                self.logger.debug(f"Would send event to widget {widget_id}: {event['type']}")
                
        except Exception as e:
            self.logger.error(f"Error sending event to widget {widget_id}: {e}")
    
    def _handle_user_joined(self, data: Dict[str, Any]):
        """Handle user joined event"""
        session_id = data["session_id"]
        user = data["user"]
        
        session = self.sessions[session_id]
        
        # Send welcome message
        welcome_message = f"{user['name']} joined the collaboration session"
        self.send_system_message(session_id, welcome_message)
        
        # Share current project data with new user
        if session.project_id:
            self._share_project_context(session_id, user["user_id"])
    
    def _handle_user_left(self, data: Dict[str, Any]):
        """Handle user left event"""
        session_id = data["session_id"]
        user_name = data["user_name"]
        
        # Send goodbye message
        goodbye_message = f"{user_name} left the collaboration session"
        self.send_system_message(session_id, goodbye_message)
    
    def _handle_message_sent(self, data: Dict[str, Any]):
        """Handle message sent event"""
        session_id = data["session_id"]
        message = data["message"]
        
        # Check if message needs AI response
        if message["message_type"] == "text" and self._should_ai_respond(message["content"]):
            self._generate_ai_response(session_id, message)
    
    def _handle_project_updated(self, data: Dict[str, Any]):
        """Handle project updated event"""
        session_id = data["session_id"]
        
        # Update shared project data
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if session.project_id:
                self._refresh_project_data(session_id)
    
    def send_system_message(self, session_id: str, content: str, 
                           metadata: Optional[Dict[str, Any]] = None):
        """Send a system message to the session"""
        if session_id not in self.sessions:
            return
        
        message_id = f"sys_{uuid.uuid4().hex[:12]}"
        message = CollaborationMessage(
            message_id=message_id,
            session_id=session_id,
            user_id="system",
            content=content,
            message_type="system",
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        session = self.sessions[session_id]
        session.messages.append(message)
        
        # Broadcast system message
        self.broadcast_event(CollaborationEventType.MESSAGE_SENT, {
            "session_id": session_id,
            "message": asdict(message)
        })
    
    def _should_ai_respond(self, message_content: str) -> bool:
        """Check if AI should respond to message"""
        ai_triggers = [
            "ai avatar", "assistant", "estimate", "recommend", "analyze",
            "help", "what do you think", "opinion", "suggest"
        ]
        
        content_lower = message_content.lower()
        return any(trigger in content_lower for trigger in ai_triggers)
    
    def _generate_ai_response(self, session_id: str, original_message: Dict[str, Any]):
        """Generate AI response to user message"""
        try:
            # Use the AI assistant to generate response
            if hasattr(self.ai_assistant, 'chat_interface'):
                # This would generate a contextual AI response
                ai_response = f"I understand you're discussing: {original_message['content'][:50]}..."
                
                # Send AI response
                ai_message_id = f"ai_{uuid.uuid4().hex[:12]}"
                ai_message = CollaborationMessage(
                    message_id=ai_message_id,
                    session_id=session_id,
                    user_id="ai_assistant",
                    content=ai_response,
                    message_type="ai_response",
                    timestamp=datetime.now(),
                    metadata={"responding_to": original_message["message_id"]}
                )
                
                session = self.sessions[session_id]
                session.messages.append(ai_message)
                
                # Broadcast AI response
                self.broadcast_event(CollaborationEventType.MESSAGE_SENT, {
                    "session_id": session_id,
                    "message": asdict(ai_message)
                })
                
        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
    
    def _share_project_context(self, session_id: str, user_id: str):
        """Share project context with new user"""
        session = self.sessions[session_id]
        
        if session.project_id:
            # Get project data
            projects = self.ai_assistant.data_source_manager.get_all_projects()
            project = next((p for p in projects if p.get("id") == session.project_id), None)
            
            if project:
                context_message = f"Project context: {project.get('name', 'Unknown')} - {project.get('description', '')[:100]}..."
                self.send_system_message(session_id, context_message, {
                    "type": "project_context",
                    "project_data": project
                })
    
    def _refresh_project_data(self, session_id: str):
        """Refresh project data for session"""
        session = self.sessions[session_id]
        
        if session.project_id:
            # Get updated project data
            projects = self.ai_assistant.data_source_manager.get_all_projects()
            project = next((p for p in projects if p.get("id") == session.project_id), None)
            
            if project:
                session.shared_data["project"] = project
                session.shared_data["project_updated_at"] = datetime.now().isoformat()
                
                # Broadcast project update
                self.broadcast_event(CollaborationEventType.PROJECT_UPDATED, {
                    "session_id": session_id,
                    "project": project
                })
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session.session_id,
            "name": session.name,
            "description": session.description,
            "project_id": session.project_id,
            "created_by": session.created_by,
            "created_at": session.created_at.isoformat(),
            "is_active": session.is_active,
            "user_count": len(session.users),
            "users": [
                {
                    "user_id": user.user_id,
                    "name": user.name,
                    "role": user.role,
                    "joined_at": user.joined_at.isoformat(),
                    "last_activity": user.last_activity.isoformat(),
                    "is_active": user.is_active
                }
                for user in session.users.values()
            ],
            "message_count": len(session.messages),
            "shared_data_keys": list(session.shared_data.keys())
        }
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get sessions for a specific user"""
        user_session_ids = [
            session_id for session_id, session in self.sessions.items()
            if user_id in session.users
        ]
        
        return [self.get_session_info(session_id) for session_id in user_session_ids]
    
    def get_collaboration_status(self) -> Dict[str, Any]:
        """Get collaboration engine status"""
        active_sessions = sum(1 for s in self.sessions.values() if s.is_active)
        total_users = sum(len(s.users) for s in self.sessions.values() if s.is_active)
        
        return {
            "is_running": self.is_running,
            "total_sessions": len(self.sessions),
            "active_sessions": active_sessions,
            "total_users": total_users,
            "recent_sessions": [
                self.get_session_info(s.session_id)
                for s in sorted(self.sessions.values(), 
                              key=lambda x: x.created_at, reverse=True)[:5]
            ]
        }
    
    def cleanup_inactive_sessions(self, hours_inactive: int = 24):
        """Clean up inactive sessions"""
        cutoff_time = datetime.now() - timedelta(hours=hours_inactive)
        
        inactive_sessions = []
        for session in self.sessions.values():
            # Check if session has any recent activity
            last_activity = max([user.last_activity for user in session.users.values()] + 
                              [session.created_at])
            
            if last_activity < cutoff_time:
                inactive_sessions.append(session.session_id)
        
        # Remove inactive sessions
        for session_id in inactive_sessions:
            del self.sessions[session_id]
            self.logger.info(f"Cleaned up inactive session: {session_id}")
        
        if inactive_sessions:
            self.save_sessions()
        
        return len(inactive_sessions)
    
    def _serialize_session(self, session: CollaborationSession) -> Dict[str, Any]:
        """Serialize session to dictionary"""
        return {
            "session_id": session.session_id,
            "name": session.name,
            "description": session.description,
            "project_id": session.project_id,
            "created_by": session.created_by,
            "created_at": session.created_at.isoformat(),
            "is_active": session.is_active,
            "users": [asdict(user) for user in session.users.values()],
            "messages": [asdict(msg) for msg in session.messages[-50:]],  # Keep last 50 messages
            "shared_data": session.shared_data
        }
    
    def _deserialize_session(self, data: Dict[str, Any]) -> CollaborationSession:
        """Deserialize session from dictionary"""
        users = {}
        for user_data in data.get("users", []):
            user = CollaborationUser(**user_data)
            users[user.user_id] = user
        
        messages = []
        for msg_data in data.get("messages", []):
            message = CollaborationMessage(**msg_data)
            messages.append(message)
        
        return CollaborationSession(
            session_id=data["session_id"],
            name=data["name"],
            description=data["description"],
            project_id=data.get("project_id"),
            created_by=data["created_by"],
            created_at=datetime.fromisoformat(data["created_at"]),
            users=users,
            messages=messages,
            shared_data=data.get("shared_data", {}),
            is_active=data.get("is_active", True)
        )