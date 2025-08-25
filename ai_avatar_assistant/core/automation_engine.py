#!/usr/bin/env python3
"""
AI Avatar Assistant - Automation Engine
Intelligent automation triggers and workflows for proactive assistance
"""

import os
import json
import time
import threading
import logging
from typing import Dict, List, Optional, Callable, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

class TriggerType(Enum):
    """Types of automation triggers"""
    TIME_BASED = "time_based"
    DATA_CHANGE = "data_change"
    PROJECT_STATUS = "project_status"
    TEAM_AVAILABILITY = "team_availability"
    PERFORMANCE_METRIC = "performance_metric"
    USER_INTERACTION = "user_interaction"
    EXTERNAL_EVENT = "external_event"

class ActionType(Enum):
    """Types of automation actions"""
    NOTIFY = "notify"
    ESTIMATE_PROJECT = "estimate_project"
    RECOMMEND_TEAM = "recommend_team"
    GENERATE_REPORT = "generate_report"
    UPDATE_DATA = "update_data"
    SEND_MESSAGE = "send_message"
    TRIGGER_WORKFLOW = "trigger_workflow"

@dataclass
class AutomationTrigger:
    """Definition of an automation trigger"""
    id: str
    name: str
    description: str
    trigger_type: TriggerType
    conditions: Dict[str, Any]
    is_active: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    cooldown_minutes: int = 0

@dataclass
class AutomationAction:
    """Definition of an automation action"""
    id: str
    name: str
    description: str
    action_type: ActionType
    parameters: Dict[str, Any]
    is_active: bool = True

@dataclass
class AutomationWorkflow:
    """Complete automation workflow"""
    id: str
    name: str
    description: str
    trigger: AutomationTrigger
    actions: List[AutomationAction]
    is_active: bool = True
    created_at: datetime
    last_executed: Optional[datetime] = None
    execution_count: int = 0

class AutomationEngine:
    """Intelligent automation engine for proactive assistance"""
    
    def __init__(self, ai_assistant, data_source_manager, analytics_engine):
        self.ai_assistant = ai_assistant
        self.data_source_manager = data_source_manager
        self.analytics_engine = analytics_engine
        self.logger = logging.getLogger(__name__)
        
        self.workflows: Dict[str, AutomationWorkflow] = {}
        self.is_running = False
        self.monitor_thread = None
        self.event_handlers = {}
        
        self.load_workflows()
        self.setup_default_workflows()
        self.register_event_handlers()
    
    def load_workflows(self):
        """Load automation workflows from configuration"""
        config_path = "data/automation_workflows.json"
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    
                for workflow_data in data.get("workflows", []):
                    workflow = self._deserialize_workflow(workflow_data)
                    self.workflows[workflow.id] = workflow
                    
                self.logger.info(f"Loaded {len(self.workflows)} automation workflows")
            else:
                self.logger.info("No existing automation workflows found")
                
        except Exception as e:
            self.logger.error(f"Error loading automation workflows: {e}")
    
    def save_workflows(self):
        """Save automation workflows to configuration"""
        config_path = "data/automation_workflows.json"
        
        try:
            os.makedirs("data", exist_ok=True)
            
            data = {
                "workflows": [self._serialize_workflow(workflow) for workflow in self.workflows.values()],
                "updated_at": datetime.now().isoformat()
            }
            
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=4, default=str)
                
            self.logger.info("Automation workflows saved")
            
        except Exception as e:
            self.logger.error(f"Error saving automation workflows: {e}")
    
    def setup_default_workflows(self):
        """Setup default automation workflows"""
        defaults = [
            {
                "id": "daily_analytics",
                "name": "Daily Analytics Report",
                "description": "Generate daily analytics report at 9 AM",
                "trigger": {
                    "id": "daily_9am",
                    "name": "Daily 9 AM Trigger",
                    "description": "Triggers every day at 9 AM",
                    "trigger_type": TriggerType.TIME_BASED,
                    "conditions": {"time": "09:00", "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]}
                },
                "actions": [
                    {
                        "id": "generate_daily_report",
                        "name": "Generate Daily Report",
                        "description": "Create analytics report for yesterday",
                        "action_type": ActionType.GENERATE_REPORT,
                        "parameters": {"report_type": "daily", "include_voice": True}
                    }
                ]
            },
            {
                "id": "project_deadline_alert",
                "name": "Project Deadline Alert",
                "description": "Alert when project deadline is approaching",
                "trigger": {
                    "id": "deadline_approaching",
                    "name": "Deadline Approaching",
                    "description": "Triggers when project deadline is within 2 days",
                    "trigger_type": TriggerType.PROJECT_STATUS,
                    "conditions": {"deadline_days": 2, "status": "active"}
                },
                "actions": [
                    {
                        "id": "deadline_notification",
                        "name": "Deadline Notification",
                        "description": "Send deadline reminder notification",
                        "action_type": ActionType.NOTIFY,
                        "parameters": {"type": "deadline_warning", "include_voice": True}
                    }
                ]
            },
            {
                "id": "auto_estimate_new_projects",
                "name": "Auto-Estimate New Projects",
                "description": "Automatically estimate new projects when detected",
                "trigger": {
                    "id": "new_project_detected",
                    "name": "New Project Detected",
                    "description": "Triggers when new project is added to data sources",
                    "trigger_type": TriggerType.DATA_CHANGE,
                    "conditions": {"entity_type": "project", "change_type": "created"}
                },
                "actions": [
                    {
                        "id": "auto_project_estimate",
                        "name": "Auto Project Estimate",
                        "description": "Generate automatic project estimate",
                        "action_type": ActionType.ESTIMATE_PROJECT,
                        "parameters": {"confidence_threshold": 0.7, "notify_result": True}
                    }
                ]
            },
            {
                "id": "team_recommendation_on_skill_match",
                "name": "Team Recommendation on Skill Match",
                "description": "Recommend team members when skills are needed",
                "trigger": {
                    "id": "skill_requirement_detected",
                    "name": "Skill Requirement Detected",
                    "description": "Triggers when project requires specific skills",
                    "trigger_type": TriggerType.PROJECT_STATUS,
                    "conditions": {"has_skill_requirements": True, "team_assigned": False}
                },
                "actions": [
                    {
                        "id": "team_skill_recommendation",
                        "name": "Team Skill Recommendation",
                        "description": "Recommend team members based on required skills",
                        "action_type": ActionType.RECOMMEND_TEAM,
                        "parameters": {"match_threshold": 0.8, "max_recommendations": 3}
                    }
                ]
            }
        ]
        
        for default in defaults:
            if default["id"] not in self.workflows:
                workflow = self._create_workflow_from_dict(default)
                self.workflows[workflow.id] = workflow
                self.logger.info(f"Created default workflow: {workflow.name}")
        
        self.save_workflows()
    
    def register_event_handlers(self):
        """Register event handlers for different trigger types"""
        self.event_handlers = {
            TriggerType.TIME_BASED: self._handle_time_trigger,
            TriggerType.DATA_CHANGE: self._handle_data_change_trigger,
            TriggerType.PROJECT_STATUS: self._handle_project_status_trigger,
            TriggerType.TEAM_AVAILABILITY: self._handle_team_availability_trigger,
            TriggerType.PERFORMANCE_METRIC: self._handle_performance_metric_trigger,
            TriggerType.USER_INTERACTION: self._handle_user_interaction_trigger,
            TriggerType.EXTERNAL_EVENT: self._handle_external_event_trigger
        }
    
    def start_automation(self):
        """Start the automation engine"""
        if self.is_running:
            self.logger.warning("Automation engine already running")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("Automation engine started")
    
    def stop_automation(self):
        """Stop the automation engine"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Automation engine stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop for automation triggers"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                for workflow in self.workflows.values():
                    if not workflow.is_active:
                        continue
                    
                    # Check cooldown
                    if self._is_in_cooldown(workflow, current_time):
                        continue
                    
                    # Check if trigger conditions are met
                    if self._evaluate_trigger(workflow.trigger, current_time):
                        self._execute_workflow(workflow, current_time)
                
                # Sleep for monitoring interval
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in automation monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _is_in_cooldown(self, workflow: AutomationWorkflow, current_time: datetime) -> bool:
        """Check if workflow is in cooldown period"""
        if workflow.last_executed is None:
            return False
        
        cooldown_delta = timedelta(minutes=workflow.trigger.cooldown_minutes)
        return (current_time - workflow.last_executed) < cooldown_delta
    
    def _evaluate_trigger(self, trigger: AutomationTrigger, current_time: datetime) -> bool:
        """Evaluate if trigger conditions are met"""
        if not trigger.is_active:
            return False
        
        handler = self.event_handlers.get(trigger.trigger_type)
        if not handler:
            self.logger.warning(f"No handler for trigger type: {trigger.trigger_type}")
            return False
        
        try:
            return handler(trigger, current_time)
        except Exception as e:
            self.logger.error(f"Error evaluating trigger {trigger.id}: {e}")
            return False
    
    def _handle_time_trigger(self, trigger: AutomationTrigger, current_time: datetime) -> bool:
        """Handle time-based triggers"""
        conditions = trigger.conditions
        target_time = conditions.get("time", "09:00")
        target_days = conditions.get("days", ["monday", "tuesday", "wednesday", "thursday", "friday"])
        
        # Check if current day matches
        current_day = current_time.strftime("%A").lower()
        if current_day not in target_days:
            return False
        
        # Check if current time matches (within 1 minute)
        target_hour, target_minute = map(int, target_time.split(":"))
        target_datetime = current_time.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        time_diff = abs((current_time - target_datetime).total_seconds())
        return time_diff < 60  # Within 1 minute
    
    def _handle_data_change_trigger(self, trigger: AutomationTrigger, current_time: datetime) -> bool:
        """Handle data change triggers"""
        conditions = trigger.conditions
        entity_type = conditions.get("entity_type", "project")
        change_type = conditions.get("change_type", "created")
        
        # This would check for recent data changes
        # For now, return False as we'd need change tracking
        return False
    
    def _handle_project_status_trigger(self, trigger: AutomationTrigger, current_time: datetime) -> bool:
        """Handle project status triggers"""
        conditions = trigger.conditions
        
        if "deadline_days" in conditions:
            # Check for approaching deadlines
            deadline_days = conditions["deadline_days"]
            projects = self.data_source_manager.get_all_projects()
            
            for project in projects:
                deadline_str = project.get("deadline")
                if deadline_str:
                    try:
                        deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                        days_until = (deadline - current_time).days
                        
                        if days_until <= deadline_days and days_until > 0:
                            return True
                    except:
                        continue
        
        return False
    
    def _handle_team_availability_trigger(self, trigger: AutomationTrigger, current_time: datetime) -> bool:
        """Handle team availability triggers"""
        # Check team member availability changes
        return False
    
    def _handle_performance_metric_trigger(self, trigger: AutomationTrigger, current_time: datetime) -> bool:
        """Handle performance metric triggers"""
        conditions = trigger.conditions
        metric = conditions.get("metric")
        threshold = conditions.get("threshold")
        
        if not metric or threshold is None:
            return False
        
        # Get current metrics from analytics engine
        analytics_data = self.analytics_engine.get_visual_analytics_data()
        metrics = analytics_data.get("metrics", {})
        
        current_value = metrics.get(metric)
        if current_value is None:
            return False
        
        # Check threshold condition
        condition_type = conditions.get("condition", "greater_than")
        if condition_type == "greater_than":
            return current_value > threshold
        elif condition_type == "less_than":
            return current_value < threshold
        elif condition_type == "equals":
            return current_value == threshold
        
        return False
    
    def _handle_user_interaction_trigger(self, trigger: AutomationTrigger, current_time: datetime) -> bool:
        """Handle user interaction triggers"""
        # This would be triggered by user actions
        return False
    
    def _handle_external_event_trigger(self, trigger: AutomationTrigger, current_time: datetime) -> bool:
        """Handle external event triggers"""
        # This would be triggered by external API events
        return False
    
    def _execute_workflow(self, workflow: AutomationWorkflow, current_time: datetime):
        """Execute an automation workflow"""
        self.logger.info(f"Executing workflow: {workflow.name}")
        
        try:
            # Update workflow execution tracking
            workflow.last_executed = current_time
            workflow.execution_count += 1
            workflow.trigger.last_triggered = current_time
            workflow.trigger.trigger_count += 1
            
            # Execute all actions
            for action in workflow.actions:
                if action.is_active:
                    self._execute_action(action, workflow)
            
            # Save updated workflow state
            self.save_workflows()
            
            self.logger.info(f"Workflow {workflow.name} executed successfully")
            
        except Exception as e:
            self.logger.error(f"Error executing workflow {workflow.name}: {e}")
    
    def _execute_action(self, action: AutomationAction, workflow: AutomationWorkflow):
        """Execute a single automation action"""
        self.logger.info(f"Executing action: {action.name}")
        
        try:
            if action.action_type == ActionType.NOTIFY:
                self._execute_notify_action(action, workflow)
            elif action.action_type == ActionType.ESTIMATE_PROJECT:
                self._execute_estimate_action(action, workflow)
            elif action.action_type == ActionType.RECOMMEND_TEAM:
                self._execute_team_recommendation_action(action, workflow)
            elif action.action_type == ActionType.GENERATE_REPORT:
                self._execute_report_action(action, workflow)
            elif action.action_type == ActionType.UPDATE_DATA:
                self._execute_update_data_action(action, workflow)
            elif action.action_type == ActionType.SEND_MESSAGE:
                self._execute_send_message_action(action, workflow)
            elif action.action_type == ActionType.TRIGGER_WORKFLOW:
                self._execute_trigger_workflow_action(action, workflow)
            else:
                self.logger.warning(f"Unknown action type: {action.action_type}")
                
        except Exception as e:
            self.logger.error(f"Error executing action {action.name}: {e}")
    
    def _execute_notify_action(self, action: AutomationAction, workflow: AutomationWorkflow):
        """Execute notification action"""
        params = action.parameters
        notification_type = params.get("type", "general")
        include_voice = params.get("include_voice", False)
        
        message = f"Automation alert: {workflow.name} triggered"
        
        if include_voice and hasattr(self.ai_assistant, 'voice_system'):
            self.ai_assistant.voice_system.speak(message)
        
        # Could also send to system tray, email, etc.
        self.logger.info(f"Notification sent: {message}")
    
    def _execute_estimate_action(self, action: AutomationAction, workflow: AutomationWorkflow):
        """Execute project estimation action"""
        params = action.parameters
        confidence_threshold = params.get("confidence_threshold", 0.7)
        notify_result = params.get("notify_result", True)
        
        # Get recent projects that need estimation
        projects = self.data_source_manager.get_all_projects()
        
        for project in projects:
            if not project.get("estimated", False):
                # Perform estimation
                if hasattr(self.ai_assistant, 'project_estimator'):
                    estimate = self.ai_assistant.project_estimator.estimate_project(
                        project.get("description", ""),
                        project.get("requirements", []),
                        project.get("technologies", [])
                    )
                    
                    if estimate.confidence_level >= confidence_threshold:
                        if notify_result:
                            message = f"Auto-estimated project '{project.get('name', 'Unknown')}': {estimate.total_hours} hours"
                            if hasattr(self.ai_assistant, 'voice_system'):
                                self.ai_assistant.voice_system.speak(message)
                        
                        # Mark as estimated
                        project["estimated"] = True
                        project["estimate_hours"] = estimate.total_hours
                        project["estimate_confidence"] = estimate.confidence_level
    
    def _execute_team_recommendation_action(self, action: AutomationAction, workflow: AutomationWorkflow):
        """Execute team recommendation action"""
        params = action.parameters
        match_threshold = params.get("match_threshold", 0.8)
        max_recommendations = params.get("max_recommendations", 3)
        
        # Find projects needing team recommendations
        projects = self.data_source_manager.get_all_projects()
        
        for project in projects:
            if not project.get("team_assigned", False):
                required_skills = project.get("technologies", [])
                if required_skills:
                    # Get team recommendations
                    team_members = self.data_source_manager.get_team_members()
                    recommendations = []
                    
                    for member in team_members:
                        member_skills = member.get("skills", [])
                        matches = sum(1 for skill in required_skills if skill in member_skills)
                        match_score = matches / len(required_skills) if required_skills else 0
                        
                        if match_score >= match_threshold:
                            recommendations.append({
                                "member": member,
                                "match_score": match_score
                            })
                    
                    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
                    top_recommendations = recommendations[:max_recommendations]
                    
                    if top_recommendations:
                        message = f"Team recommendations for '{project.get('name', 'Unknown')}': "
                        message += ", ".join([rec["member"]["name"] for rec in top_recommendations])
                        
                        if hasattr(self.ai_assistant, 'voice_system'):
                            self.ai_assistant.voice_system.speak(message)
    
    def _execute_report_action(self, action: AutomationAction, workflow: AutomationWorkflow):
        """Execute report generation action"""
        params = action.parameters
        report_type = params.get("report_type", "daily")
        include_voice = params.get("include_voice", True)
        
        if hasattr(self.ai_assistant, 'report_generator'):
            report = self.ai_assistant.report_generator.generate_analytics_report(
                report_type=report_type,
                include_voice_script=include_voice
            )
            
            if include_voice and hasattr(self.ai_assistant, 'voice_system'):
                message = f"Generated {report_type} analytics report"
                self.ai_assistant.voice_system.speak(message)
            
            self.logger.info(f"Generated {report_type} report via automation")
    
    def _execute_update_data_action(self, action: AutomationAction, workflow: AutomationWorkflow):
        """Execute data update action"""
        params = action.parameters
        # This would update data based on parameters
        self.logger.info("Data update action executed")
    
    def _execute_send_message_action(self, action: AutomationAction, workflow: AutomationWorkflow):
        """Execute send message action"""
        params = action.parameters
        message = params.get("message", "Automation message")
        
        if hasattr(self.ai_assistant, 'voice_system'):
            self.ai_assistant.voice_system.speak(message)
        
        self.logger.info(f"Message sent: {message}")
    
    def _execute_trigger_workflow_action(self, action: AutomationAction, workflow: AutomationWorkflow):
        """Execute trigger workflow action"""
        params = action.parameters
        target_workflow_id = params.get("workflow_id")
        
        if target_workflow_id and target_workflow_id in self.workflows:
            target_workflow = self.workflows[target_workflow_id]
            self._execute_workflow(target_workflow, datetime.now())
    
    def create_workflow(self, workflow_data: Dict[str, Any]) -> str:
        """Create a new automation workflow"""
        workflow = self._create_workflow_from_dict(workflow_data)
        self.workflows[workflow.id] = workflow
        self.save_workflows()
        
        self.logger.info(f"Created new workflow: {workflow.name}")
        return workflow.id
    
    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        # Update workflow properties
        if "name" in updates:
            workflow.name = updates["name"]
        if "description" in updates:
            workflow.description = updates["description"]
        if "is_active" in updates:
            workflow.is_active = updates["is_active"]
        
        self.save_workflows()
        self.logger.info(f"Updated workflow: {workflow.name}")
        return True
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete an automation workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow_name = self.workflows[workflow_id].name
        del self.workflows[workflow_id]
        self.save_workflows()
        
        self.logger.info(f"Deleted workflow: {workflow_name}")
        return True
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get automation engine status"""
        return {
            "is_running": self.is_running,
            "total_workflows": len(self.workflows),
            "active_workflows": sum(1 for w in self.workflows.values() if w.is_active),
            "workflows": [
                {
                    "id": w.id,
                    "name": w.name,
                    "is_active": w.is_active,
                    "execution_count": w.execution_count,
                    "last_executed": w.last_executed
                }
                for w in self.workflows.values()
            ]
        }
    
    def trigger_workflow_manually(self, workflow_id: str) -> bool:
        """Manually trigger a workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        self._execute_workflow(workflow, datetime.now())
        return True
    
    def _create_workflow_from_dict(self, data: Dict[str, Any]) -> AutomationWorkflow:
        """Create workflow object from dictionary"""
        trigger_data = data["trigger"]
        trigger = AutomationTrigger(
            id=trigger_data["id"],
            name=trigger_data["name"],
            description=trigger_data["description"],
            trigger_type=TriggerType(trigger_data["trigger_type"]),
            conditions=trigger_data["conditions"]
        )
        
        actions = []
        for action_data in data["actions"]:
            action = AutomationAction(
                id=action_data["id"],
                name=action_data["name"],
                description=action_data["description"],
                action_type=ActionType(action_data["action_type"]),
                parameters=action_data["parameters"]
            )
            actions.append(action)
        
        return AutomationWorkflow(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            trigger=trigger,
            actions=actions,
            created_at=datetime.now()
        )
    
    def _serialize_workflow(self, workflow: AutomationWorkflow) -> Dict[str, Any]:
        """Serialize workflow to dictionary"""
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "is_active": workflow.is_active,
            "created_at": workflow.created_at.isoformat(),
            "last_executed": workflow.last_executed.isoformat() if workflow.last_executed else None,
            "execution_count": workflow.execution_count,
            "trigger": asdict(workflow.trigger),
            "actions": [asdict(action) for action in workflow.actions]
        }
    
    def _deserialize_workflow(self, data: Dict[str, Any]) -> AutomationWorkflow:
        """Deserialize workflow from dictionary"""
        trigger_data = data["trigger"]
        trigger = AutomationTrigger(**trigger_data)
        
        actions = []
        for action_data in data["actions"]:
            action = AutomationAction(**action_data)
            actions.append(action)
        
        return AutomationWorkflow(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            trigger=trigger,
            actions=actions,
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_executed=datetime.fromisoformat(data["last_executed"]) if data.get("last_executed") else None,
            execution_count=data.get("execution_count", 0)
        )