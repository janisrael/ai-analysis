#!/usr/bin/env python3
"""
AI Avatar Assistant - System Monitor
Real-time monitoring of AI performance, resources, and system health
"""

import os
import time
import json
import psutil
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import requests

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_free_gb: float
    ai_models_loaded: int
    active_conversations: int
    total_requests: int
    avg_response_time: float
    error_rate: float
    uptime_hours: float

@dataclass
class AIModelStatus:
    """AI model status information"""
    model_name: str
    is_loaded: bool
    last_used: datetime
    total_requests: int
    avg_response_time: float
    success_rate: float
    memory_usage_mb: float
    status: str  # "healthy", "slow", "error", "offline"

@dataclass
class HealthAlert:
    """System health alert"""
    id: str
    timestamp: datetime
    severity: str  # "info", "warning", "error", "critical"
    category: str  # "performance", "ai", "system", "security"
    title: str
    description: str
    recommendation: str
    is_resolved: bool = False

class SystemMonitor:
    """Comprehensive system monitoring for AI Avatar Assistant"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.start_time = datetime.now()
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Metrics storage
        self.metrics_history: List[SystemMetrics] = []
        self.ai_models: Dict[str, AIModelStatus] = {}
        self.active_alerts: List[HealthAlert] = []
        self.resolved_alerts: List[HealthAlert] = []
        
        # Performance tracking
        self.total_requests = 0
        self.total_response_time = 0.0
        self.error_count = 0
        self.active_conversations = 0
        
        # Thresholds
        self.thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_warning": 85.0,
            "disk_critical": 95.0,
            "response_time_warning": 2.0,
            "response_time_critical": 5.0,
            "error_rate_warning": 5.0,
            "error_rate_critical": 15.0
        }
        
        self.initialize_ai_models()
    
    def initialize_ai_models(self):
        """Initialize AI model tracking"""
        models = ["mistral", "llama2", "neural-chat", "codellama", "phi"]
        for model in models:
            self.ai_models[model] = AIModelStatus(
                model_name=model,
                is_loaded=False,
                last_used=datetime.now(),
                total_requests=0,
                avg_response_time=0.0,
                success_rate=100.0,
                memory_usage_mb=0.0,
                status="offline"
            )
    
    def start_monitoring(self, interval: int = 30):
        """Start continuous system monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("System monitoring stopped")
    
    def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 24 hours of metrics
                cutoff = datetime.now() - timedelta(hours=24)
                self.metrics_history = [
                    m for m in self.metrics_history if m.timestamp > cutoff
                ]
                
                # Check for alerts
                self.check_health_alerts(metrics)
                
                # Update AI model status
                self.update_ai_model_status()
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(interval)
    
    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # AI performance
        ai_models_loaded = sum(1 for model in self.ai_models.values() if model.is_loaded)
        avg_response_time = (
            self.total_response_time / max(self.total_requests, 1)
        )
        error_rate = (self.error_count / max(self.total_requests, 1)) * 100
        
        # Uptime
        uptime = (datetime.now() - self.start_time).total_seconds() / 3600
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_available_gb=memory.available / (1024**3),
            disk_usage_percent=disk.percent,
            disk_free_gb=disk.free / (1024**3),
            ai_models_loaded=ai_models_loaded,
            active_conversations=self.active_conversations,
            total_requests=self.total_requests,
            avg_response_time=avg_response_time,
            error_rate=error_rate,
            uptime_hours=uptime
        )
    
    def update_ai_model_status(self):
        """Update AI model status by checking Ollama"""
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                loaded_models = {
                    model['name'].split(':')[0] 
                    for model in response.json().get('models', [])
                }
                
                for model_name, status in self.ai_models.items():
                    if model_name in loaded_models:
                        status.is_loaded = True
                        status.status = self.determine_model_health(model_name)
                    else:
                        status.is_loaded = False
                        status.status = "offline"
                        
        except Exception as e:
            self.logger.warning(f"Could not check AI model status: {e}")
            for status in self.ai_models.values():
                status.status = "unknown"
    
    def determine_model_health(self, model_name: str) -> str:
        """Determine health status of an AI model"""
        status = self.ai_models[model_name]
        
        if status.avg_response_time > 3.0:
            return "slow"
        elif status.success_rate < 90.0:
            return "error"
        elif not status.is_loaded:
            return "offline"
        else:
            return "healthy"
    
    def check_health_alerts(self, metrics: SystemMetrics):
        """Check system metrics and generate alerts"""
        current_time = datetime.now()
        
        # CPU alerts
        if metrics.cpu_percent > self.thresholds["cpu_critical"]:
            self.create_alert(
                "cpu_critical",
                "critical",
                "performance",
                "Critical CPU Usage",
                f"CPU usage is {metrics.cpu_percent:.1f}%",
                "Consider closing unnecessary applications or upgrading hardware"
            )
        elif metrics.cpu_percent > self.thresholds["cpu_warning"]:
            self.create_alert(
                "cpu_warning",
                "warning",
                "performance",
                "High CPU Usage",
                f"CPU usage is {metrics.cpu_percent:.1f}%",
                "Monitor CPU usage and consider optimizing AI model usage"
            )
        
        # Memory alerts
        if metrics.memory_percent > self.thresholds["memory_critical"]:
            self.create_alert(
                "memory_critical",
                "critical",
                "performance",
                "Critical Memory Usage",
                f"Memory usage is {metrics.memory_percent:.1f}%",
                "Close applications or restart system to free memory"
            )
        elif metrics.memory_percent > self.thresholds["memory_warning"]:
            self.create_alert(
                "memory_warning",
                "warning",
                "performance",
                "High Memory Usage",
                f"Memory usage is {metrics.memory_percent:.1f}%",
                "Consider using lighter AI models like PHI for quick tasks"
            )
        
        # Disk space alerts
        if metrics.disk_usage_percent > self.thresholds["disk_critical"]:
            self.create_alert(
                "disk_critical",
                "critical",
                "system",
                "Critical Disk Space",
                f"Disk usage is {metrics.disk_usage_percent:.1f}%",
                "Free up disk space immediately to prevent system issues"
            )
        
        # AI performance alerts
        if metrics.avg_response_time > self.thresholds["response_time_critical"]:
            self.create_alert(
                "ai_slow",
                "warning",
                "ai",
                "Slow AI Response",
                f"Average response time is {metrics.avg_response_time:.2f}s",
                "Switch to faster models like PHI or restart Ollama service"
            )
        
        if metrics.error_rate > self.thresholds["error_rate_warning"]:
            self.create_alert(
                "ai_errors",
                "warning",
                "ai",
                "High AI Error Rate",
                f"AI error rate is {metrics.error_rate:.1f}%",
                "Check Ollama service status and model availability"
            )
    
    def create_alert(self, alert_id: str, severity: str, category: str, 
                    title: str, description: str, recommendation: str):
        """Create a new health alert"""
        # Check if alert already exists and is recent
        existing = next(
            (alert for alert in self.active_alerts 
             if alert.id == alert_id and not alert.is_resolved),
            None
        )
        
        if existing:
            # Update existing alert
            existing.timestamp = datetime.now()
            existing.description = description
        else:
            # Create new alert
            alert = HealthAlert(
                id=alert_id,
                timestamp=datetime.now(),
                severity=severity,
                category=category,
                title=title,
                description=description,
                recommendation=recommendation
            )
            self.active_alerts.append(alert)
            self.logger.warning(f"Health Alert: {title} - {description}")
    
    def resolve_alert(self, alert_id: str):
        """Resolve a health alert"""
        for alert in self.active_alerts:
            if alert.id == alert_id and not alert.is_resolved:
                alert.is_resolved = True
                self.resolved_alerts.append(alert)
                break
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        if not self.metrics_history:
            return {"status": "No metrics available"}
        
        latest = self.metrics_history[-1]
        active_alerts = [alert for alert in self.active_alerts if not alert.is_resolved]
        
        # Determine overall health
        critical_alerts = [a for a in active_alerts if a.severity == "critical"]
        warning_alerts = [a for a in active_alerts if a.severity == "warning"]
        
        if critical_alerts:
            overall_health = "critical"
        elif warning_alerts:
            overall_health = "warning"
        else:
            overall_health = "healthy"
        
        return {
            "overall_health": overall_health,
            "timestamp": latest.timestamp.isoformat(),
            "uptime_hours": latest.uptime_hours,
            "system": {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "memory_available_gb": latest.memory_available_gb,
                "disk_usage_percent": latest.disk_usage_percent,
                "disk_free_gb": latest.disk_free_gb
            },
            "ai": {
                "models_loaded": latest.ai_models_loaded,
                "active_conversations": latest.active_conversations,
                "total_requests": latest.total_requests,
                "avg_response_time": latest.avg_response_time,
                "error_rate": latest.error_rate,
                "models": {name: asdict(status) for name, status in self.ai_models.items()}
            },
            "alerts": {
                "active": len(active_alerts),
                "critical": len(critical_alerts),
                "warnings": len(warning_alerts),
                "details": [asdict(alert) for alert in active_alerts[-10:]]  # Last 10 alerts
            }
        }
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, List]:
        """Get performance trends over specified time period"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff]
        
        if not recent_metrics:
            return {}
        
        return {
            "timestamps": [m.timestamp.isoformat() for m in recent_metrics],
            "cpu_percent": [m.cpu_percent for m in recent_metrics],
            "memory_percent": [m.memory_percent for m in recent_metrics],
            "response_times": [m.avg_response_time for m in recent_metrics],
            "request_counts": [m.total_requests for m in recent_metrics],
            "error_rates": [m.error_rate for m in recent_metrics]
        }
    
    def record_ai_request(self, model_name: str, response_time: float, success: bool):
        """Record an AI request for performance tracking"""
        self.total_requests += 1
        self.total_response_time += response_time
        
        if not success:
            self.error_count += 1
        
        # Update model-specific stats
        if model_name in self.ai_models:
            model_status = self.ai_models[model_name]
            model_status.total_requests += 1
            model_status.last_used = datetime.now()
            
            # Update average response time
            if model_status.total_requests == 1:
                model_status.avg_response_time = response_time
            else:
                model_status.avg_response_time = (
                    (model_status.avg_response_time * (model_status.total_requests - 1) + response_time)
                    / model_status.total_requests
                )
            
            # Update success rate
            if success:
                successful_requests = model_status.total_requests * (model_status.success_rate / 100)
                model_status.success_rate = (successful_requests / model_status.total_requests) * 100
            else:
                failed_requests = model_status.total_requests * (1 - model_status.success_rate / 100) + 1
                model_status.success_rate = (1 - failed_requests / model_status.total_requests) * 100
    
    def export_metrics(self, filepath: str = "logs/system_metrics.json"):
        """Export metrics to file"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "system_status": self.get_system_status(),
                "performance_trends": self.get_performance_trends(),
                "metrics_history": [asdict(m) for m in self.metrics_history[-100:]],  # Last 100 metrics
                "resolved_alerts": [asdict(a) for a in self.resolved_alerts[-50:]]  # Last 50 resolved alerts
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Metrics exported to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
            return False

# Global system monitor instance
system_monitor = SystemMonitor()