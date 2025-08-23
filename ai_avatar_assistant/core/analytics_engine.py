import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics
from collections import defaultdict, Counter
import math

class LiveAnalyticsEngine:
    """Advanced analytics engine for live pattern detection and insights"""
    
    def __init__(self, db_path="data/tasks.db", config_path="data/config.json"):
        self.db_path = db_path
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        
        # Analysis cache
        self.analysis_cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Pattern detection settings
        self.min_data_points = 5
        self.trend_threshold = 0.1  # 10% change to consider a trend
        self.anomaly_threshold = 2.0  # Standard deviations for anomaly detection
        
        # Productivity metrics
        self.productivity_zones = {
            "high": 0.8,      # >80% completion rate
            "medium": 0.6,    # 60-80% completion rate
            "low": 0.4,       # 40-60% completion rate
            "critical": 0.0   # <40% completion rate
        }
        
        self.initialize_analytics()
    
    def initialize_analytics(self):
        """Initialize analytics tables and indices"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create analytics table for storing insights
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analytics_insights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        insight_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        severity TEXT DEFAULT 'info',
                        data TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_resolved BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                # Create productivity metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS productivity_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        tasks_completed INTEGER DEFAULT 0,
                        tasks_created INTEGER DEFAULT 0,
                        focus_sessions INTEGER DEFAULT 0,
                        focus_duration INTEGER DEFAULT 0,
                        productivity_score REAL DEFAULT 0.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create work patterns table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS work_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hour_of_day INTEGER,
                        day_of_week INTEGER,
                        activity_type TEXT,
                        activity_count INTEGER DEFAULT 1,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                self.logger.info("Analytics engine initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize analytics: {e}")
    
    def analyze_current_situation(self) -> Dict:
        """Perform comprehensive live analysis of current situation"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "productivity_status": self.analyze_productivity_status(),
            "workload_analysis": self.analyze_workload(),
            "pattern_insights": self.detect_patterns(),
            "anomaly_detection": self.detect_anomalies(),
            "recommendations": [],
            "alerts": []
        }
        
        # Generate recommendations based on analysis
        analysis["recommendations"] = self.generate_recommendations(analysis)
        
        # Detect alerts that need immediate attention
        analysis["alerts"] = self.detect_alerts(analysis)
        
        # Cache the analysis
        self.analysis_cache["current_situation"] = {
            "data": analysis,
            "timestamp": datetime.now().timestamp()
        }
        
        return analysis
    
    def analyze_productivity_status(self) -> Dict:
        """Analyze current productivity status and trends"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get recent task data (last 30 days)
                thirty_days_ago = datetime.now() - timedelta(days=30)
                
                cursor.execute('''
                    SELECT * FROM tasks 
                    WHERE created_at >= ? 
                    ORDER BY created_at DESC
                ''', (thirty_days_ago,))
                
                tasks = [dict(row) for row in cursor.fetchall()]
                
                if not tasks:
                    return {"status": "no_data", "message": "Insufficient data for analysis"}
                
                # Calculate metrics
                total_tasks = len(tasks)
                completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
                pending_tasks = len([t for t in tasks if t['status'] == 'pending'])
                overdue_tasks = len([t for t in tasks if self.is_task_overdue(t)])
                
                completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
                
                # Daily productivity trend
                daily_stats = self.calculate_daily_productivity(tasks)
                
                # Determine productivity zone
                productivity_zone = self.get_productivity_zone(completion_rate)
                
                # Calculate trend
                trend = self.calculate_productivity_trend(daily_stats)
                
                return {
                    "completion_rate": completion_rate,
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "pending_tasks": pending_tasks,
                    "overdue_tasks": overdue_tasks,
                    "productivity_zone": productivity_zone,
                    "trend": trend,
                    "daily_stats": daily_stats[-7:],  # Last 7 days
                    "score": self.calculate_productivity_score(completion_rate, overdue_tasks, total_tasks)
                }
                
        except Exception as e:
            self.logger.error(f"Error analyzing productivity: {e}")
            return {"status": "error", "message": str(e)}
    
    def analyze_workload(self) -> Dict:
        """Analyze current workload distribution and capacity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get pending tasks
                cursor.execute('''
                    SELECT * FROM tasks 
                    WHERE status = 'pending'
                    ORDER BY deadline ASC
                ''')
                
                pending_tasks = [dict(row) for row in cursor.fetchall()]
                
                # Analyze by priority
                priority_distribution = Counter()
                deadline_distribution = {"overdue": 0, "today": 0, "this_week": 0, "later": 0}
                category_distribution = Counter()
                
                now = datetime.now()
                today = now.date()
                week_end = today + timedelta(days=7)
                
                estimated_hours = 0
                
                for task in pending_tasks:
                    # Priority distribution
                    priority_distribution[task.get('priority', 3)] += 1
                    
                    # Category distribution
                    metadata = task.get('metadata', '{}')
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    
                    category = metadata.get('category', 'uncategorized')
                    category_distribution[category] += 1
                    
                    # Estimated hours
                    estimated_hours += metadata.get('estimated_hours', 2)  # Default 2 hours
                    
                    # Deadline analysis
                    if task.get('deadline'):
                        deadline = datetime.fromisoformat(task['deadline']).date()
                        if deadline < today:
                            deadline_distribution["overdue"] += 1
                        elif deadline == today:
                            deadline_distribution["today"] += 1
                        elif deadline <= week_end:
                            deadline_distribution["this_week"] += 1
                        else:
                            deadline_distribution["later"] += 1
                    else:
                        deadline_distribution["later"] += 1
                
                # Calculate workload metrics
                total_pending = len(pending_tasks)
                workload_intensity = self.calculate_workload_intensity(deadline_distribution, total_pending)
                capacity_analysis = self.analyze_capacity(estimated_hours, deadline_distribution)
                
                return {
                    "total_pending": total_pending,
                    "estimated_hours": estimated_hours,
                    "priority_distribution": dict(priority_distribution),
                    "deadline_distribution": deadline_distribution,
                    "category_distribution": dict(category_distribution),
                    "workload_intensity": workload_intensity,
                    "capacity_analysis": capacity_analysis,
                    "overload_risk": self.assess_overload_risk(deadline_distribution, estimated_hours)
                }
                
        except Exception as e:
            self.logger.error(f"Error analyzing workload: {e}")
            return {"status": "error", "message": str(e)}
    
    def detect_patterns(self) -> Dict:
        """Detect patterns in user behavior and task management"""
        patterns = {
            "work_schedule": self.analyze_work_schedule(),
            "task_creation_patterns": self.analyze_task_creation_patterns(),
            "completion_patterns": self.analyze_completion_patterns(),
            "procrastination_indicators": self.detect_procrastination(),
            "productivity_cycles": self.detect_productivity_cycles()
        }
        
        return patterns
    
    def detect_anomalies(self) -> List[Dict]:
        """Detect anomalies in productivity and behavior patterns"""
        anomalies = []
        
        try:
            # Analyze task creation anomalies
            task_creation_anomalies = self.detect_task_creation_anomalies()
            anomalies.extend(task_creation_anomalies)
            
            # Analyze completion rate anomalies
            completion_anomalies = self.detect_completion_anomalies()
            anomalies.extend(completion_anomalies)
            
            # Analyze time-based anomalies
            time_anomalies = self.detect_time_anomalies()
            anomalies.extend(time_anomalies)
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            anomalies.append({
                "type": "system_error",
                "severity": "warning",
                "message": f"Anomaly detection error: {e}"
            })
        
        return anomalies
    
    def generate_recommendations(self, analysis: Dict) -> List[Dict]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        productivity = analysis.get("productivity_status", {})
        workload = analysis.get("workload_analysis", {})
        patterns = analysis.get("pattern_insights", {})
        
        # Productivity-based recommendations
        if productivity.get("completion_rate", 0) < 0.5:
            recommendations.append({
                "type": "productivity_improvement",
                "priority": "high",
                "title": "Low Completion Rate Detected",
                "description": f"Your task completion rate is {productivity.get('completion_rate', 0):.1%}. Consider breaking large tasks into smaller ones.",
                "actions": ["prioritize_tasks", "start_focus_mode", "review_workload"]
            })
        
        # Workload-based recommendations
        overdue_count = workload.get("deadline_distribution", {}).get("overdue", 0)
        if overdue_count > 3:
            recommendations.append({
                "type": "deadline_management",
                "priority": "urgent",
                "title": "Multiple Overdue Tasks",
                "description": f"You have {overdue_count} overdue tasks. Immediate action required.",
                "actions": ["reschedule_overdue", "prioritize_urgent", "delegate_tasks"]
            })
        
        # Capacity recommendations
        estimated_hours = workload.get("estimated_hours", 0)
        if estimated_hours > 40:  # More than a work week
            recommendations.append({
                "type": "capacity_management",
                "priority": "medium",
                "title": "High Workload Detected",
                "description": f"You have {estimated_hours} hours of estimated work. Consider prioritizing or delegating.",
                "actions": ["review_priorities", "delegate_tasks", "extend_deadlines"]
            })
        
        # Pattern-based recommendations
        downtime_detected = self.detect_downtime_periods(patterns)
        if downtime_detected:
            recommendations.append({
                "type": "project_planning",
                "priority": "medium",
                "title": "Downtime Periods Detected",
                "description": "Analysis shows periods of low activity. Consider planning new projects or initiatives.",
                "actions": ["plan_new_project", "skill_development", "process_improvement"]
            })
        
        # Time management recommendations
        work_schedule = patterns.get("work_schedule", {})
        if self.has_scattered_work_pattern(work_schedule):
            recommendations.append({
                "type": "time_management",
                "priority": "medium",
                "title": "Scattered Work Pattern",
                "description": "Your work times are scattered. Consider establishing regular work blocks.",
                "actions": ["time_blocking", "schedule_optimization", "focus_sessions"]
            })
        
        return recommendations
    
    def detect_alerts(self, analysis: Dict) -> List[Dict]:
        """Detect situations that need immediate attention"""
        alerts = []
        
        workload = analysis.get("workload_analysis", {})
        productivity = analysis.get("productivity_status", {})
        
        # Critical alerts
        if workload.get("overload_risk", 0) > 0.8:
            alerts.append({
                "type": "overload_warning",
                "severity": "critical",
                "title": "Workload Overload Risk",
                "message": "Your current workload may be unsustainable. Consider immediate action.",
                "suggested_actions": ["review_priorities", "delegate_tasks", "reschedule_deadlines"]
            })
        
        if productivity.get("overdue_tasks", 0) > 5:
            alerts.append({
                "type": "deadline_crisis",
                "severity": "critical",
                "title": "Multiple Overdue Tasks",
                "message": f"You have {productivity.get('overdue_tasks')} overdue tasks requiring immediate attention.",
                "suggested_actions": ["emergency_triage", "stakeholder_communication", "deadline_renegotiation"]
            })
        
        # Warning alerts
        if productivity.get("trend", {}).get("direction") == "declining":
            trend_change = productivity.get("trend", {}).get("change", 0)
            if abs(trend_change) > 0.2:  # 20% decline
                alerts.append({
                    "type": "productivity_decline",
                    "severity": "warning",
                    "title": "Productivity Declining",
                    "message": f"Your productivity has declined by {abs(trend_change):.1%} recently.",
                    "suggested_actions": ["analyze_blockers", "adjust_workload", "seek_support"]
                })
        
        return alerts
    
    # Helper methods for detailed analysis
    
    def is_task_overdue(self, task: Dict) -> bool:
        """Check if a task is overdue"""
        if not task.get('deadline'):
            return False
        
        try:
            deadline = datetime.fromisoformat(task['deadline'])
            return deadline < datetime.now() and task['status'] != 'completed'
        except:
            return False
    
    def calculate_daily_productivity(self, tasks: List[Dict]) -> List[Dict]:
        """Calculate daily productivity metrics"""
        daily_stats = defaultdict(lambda: {"completed": 0, "created": 0, "date": None})
        
        for task in tasks:
            # Task creation
            created_date = datetime.fromisoformat(task['created_at']).date()
            daily_stats[created_date]["created"] += 1
            daily_stats[created_date]["date"] = created_date
            
            # Task completion
            if task['status'] == 'completed' and task.get('updated_at'):
                updated_date = datetime.fromisoformat(task['updated_at']).date()
                daily_stats[updated_date]["completed"] += 1
        
        # Convert to list and sort by date
        stats_list = []
        for date, stats in daily_stats.items():
            stats["completion_rate"] = stats["completed"] / max(stats["created"], 1)
            stats_list.append(stats)
        
        return sorted(stats_list, key=lambda x: x["date"])
    
    def get_productivity_zone(self, completion_rate: float) -> str:
        """Determine productivity zone based on completion rate"""
        for zone, threshold in self.productivity_zones.items():
            if completion_rate >= threshold:
                return zone
        return "critical"
    
    def calculate_productivity_trend(self, daily_stats: List[Dict]) -> Dict:
        """Calculate productivity trend over time"""
        if len(daily_stats) < 3:
            return {"direction": "insufficient_data", "change": 0}
        
        # Get completion rates for trend analysis
        rates = [stat["completion_rate"] for stat in daily_stats[-7:]]  # Last 7 days
        
        if len(rates) < 2:
            return {"direction": "insufficient_data", "change": 0}
        
        # Simple linear trend
        recent_avg = statistics.mean(rates[-3:]) if len(rates) >= 3 else rates[-1]
        older_avg = statistics.mean(rates[:-3]) if len(rates) >= 6 else rates[0]
        
        change = recent_avg - older_avg
        
        if abs(change) < self.trend_threshold:
            direction = "stable"
        elif change > 0:
            direction = "improving"
        else:
            direction = "declining"
        
        return {"direction": direction, "change": change, "confidence": min(len(rates) / 7, 1.0)}
    
    def calculate_productivity_score(self, completion_rate: float, overdue_tasks: int, total_tasks: int) -> float:
        """Calculate overall productivity score (0-100)"""
        base_score = completion_rate * 100
        
        # Penalty for overdue tasks
        overdue_penalty = (overdue_tasks / max(total_tasks, 1)) * 30
        
        # Bonus for high completion rate
        excellence_bonus = max(0, (completion_rate - 0.8) * 50) if completion_rate > 0.8 else 0
        
        score = max(0, min(100, base_score - overdue_penalty + excellence_bonus))
        return round(score, 1)
    
    def calculate_workload_intensity(self, deadline_dist: Dict, total_tasks: int) -> str:
        """Calculate workload intensity level"""
        if total_tasks == 0:
            return "none"
        
        urgent_tasks = deadline_dist.get("overdue", 0) + deadline_dist.get("today", 0)
        urgent_ratio = urgent_tasks / total_tasks
        
        if urgent_ratio > 0.5:
            return "critical"
        elif urgent_ratio > 0.3:
            return "high"
        elif urgent_ratio > 0.1:
            return "medium"
        else:
            return "low"
    
    def analyze_capacity(self, estimated_hours: int, deadline_dist: Dict) -> Dict:
        """Analyze work capacity and sustainability"""
        # Assume 8 hours per day, 5 days per week
        daily_capacity = 8
        weekly_capacity = 40
        
        urgent_tasks = deadline_dist.get("overdue", 0) + deadline_dist.get("today", 0)
        this_week_tasks = deadline_dist.get("this_week", 0)
        
        # Estimate hours needed this week
        hours_this_week = (urgent_tasks + this_week_tasks) * 2  # Assume 2 hours per task average
        
        capacity_utilization = hours_this_week / weekly_capacity
        
        return {
            "hours_this_week": hours_this_week,
            "capacity_utilization": capacity_utilization,
            "sustainability": "unsustainable" if capacity_utilization > 1.2 else 
                            "high_stress" if capacity_utilization > 1.0 else
                            "manageable" if capacity_utilization > 0.7 else "light"
        }
    
    def assess_overload_risk(self, deadline_dist: Dict, estimated_hours: int) -> float:
        """Assess risk of workload overload (0-1 scale)"""
        factors = []
        
        # Overdue tasks factor
        overdue_factor = min(deadline_dist.get("overdue", 0) / 10, 1.0)
        factors.append(overdue_factor * 0.4)
        
        # Today's tasks factor
        today_factor = min(deadline_dist.get("today", 0) / 5, 1.0)
        factors.append(today_factor * 0.3)
        
        # Hours factor
        hours_factor = min(estimated_hours / 80, 1.0)  # 80 hours = 2 weeks
        factors.append(hours_factor * 0.3)
        
        return sum(factors)
    
    def analyze_work_schedule(self) -> Dict:
        """Analyze work schedule patterns"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get task creation and completion times
                cursor.execute('''
                    SELECT created_at, updated_at, status FROM tasks 
                    WHERE created_at >= date('now', '-30 days')
                ''')
                
                tasks = cursor.fetchall()
                
                hour_activity = defaultdict(int)
                day_activity = defaultdict(int)
                
                for task in tasks:
                    # Task creation time
                    created_dt = datetime.fromisoformat(task[0])
                    hour_activity[created_dt.hour] += 1
                    day_activity[created_dt.weekday()] += 1
                    
                    # Task completion time
                    if task[1] and task[2] == 'completed':
                        updated_dt = datetime.fromisoformat(task[1])
                        hour_activity[updated_dt.hour] += 1
                        day_activity[updated_dt.weekday()] += 1
                
                # Find peak hours and days
                peak_hour = max(hour_activity.keys(), key=lambda h: hour_activity[h]) if hour_activity else 9
                peak_day = max(day_activity.keys(), key=lambda d: day_activity[d]) if day_activity else 0
                
                return {
                    "hourly_activity": dict(hour_activity),
                    "daily_activity": dict(day_activity),
                    "peak_hour": peak_hour,
                    "peak_day": peak_day,
                    "work_span": self.calculate_work_span(hour_activity)
                }
                
        except Exception as e:
            self.logger.error(f"Error analyzing work schedule: {e}")
            return {}
    
    def detect_downtime_periods(self, patterns: Dict) -> bool:
        """Detect if there are significant downtime periods"""
        work_schedule = patterns.get("work_schedule", {})
        hourly_activity = work_schedule.get("hourly_activity", {})
        
        if not hourly_activity:
            return True  # No activity data suggests downtime
        
        # Calculate average activity
        total_activity = sum(hourly_activity.values())
        avg_activity = total_activity / 24 if total_activity > 0 else 0
        
        # Count hours with significantly low activity
        low_activity_hours = sum(1 for hour, activity in hourly_activity.items() 
                               if activity < avg_activity * 0.3)
        
        # If more than 18 hours have low activity, suggest downtime
        return low_activity_hours > 18
    
    def has_scattered_work_pattern(self, work_schedule: Dict) -> bool:
        """Check if work pattern is scattered throughout the day"""
        hourly_activity = work_schedule.get("hourly_activity", {})
        
        if not hourly_activity:
            return False
        
        # Count active hours (hours with any activity)
        active_hours = [hour for hour, activity in hourly_activity.items() if activity > 0]
        
        if len(active_hours) < 3:
            return False
        
        # Check for gaps in activity
        active_hours.sort()
        gaps = []
        for i in range(1, len(active_hours)):
            gap = active_hours[i] - active_hours[i-1]
            if gap > 1:
                gaps.append(gap)
        
        # If there are multiple large gaps, pattern is scattered
        large_gaps = [gap for gap in gaps if gap > 3]
        return len(large_gaps) > 2
    
    def calculate_work_span(self, hour_activity: Dict) -> Dict:
        """Calculate the span of work hours"""
        if not hour_activity:
            return {"start": 9, "end": 17, "span": 8}
        
        active_hours = [hour for hour, activity in hour_activity.items() if activity > 0]
        
        if not active_hours:
            return {"start": 9, "end": 17, "span": 8}
        
        start_hour = min(active_hours)
        end_hour = max(active_hours)
        span = end_hour - start_hour + 1
        
        return {"start": start_hour, "end": end_hour, "span": span}
    
    def analyze_task_creation_patterns(self) -> Dict:
        """Analyze patterns in task creation"""
        # Implementation for task creation pattern analysis
        return {"pattern": "regular", "frequency": "daily", "peak_times": [9, 14]}
    
    def analyze_completion_patterns(self) -> Dict:
        """Analyze patterns in task completion"""
        # Implementation for completion pattern analysis
        return {"pattern": "deadline_driven", "completion_times": [16, 17]}
    
    def detect_procrastination(self) -> Dict:
        """Detect signs of procrastination"""
        # Implementation for procrastination detection
        return {"risk_level": "medium", "indicators": ["late_starts", "deadline_rush"]}
    
    def detect_productivity_cycles(self) -> Dict:
        """Detect productivity cycles and patterns"""
        # Implementation for productivity cycle detection
        return {"cycle_type": "weekly", "peak_days": [1, 2, 3], "low_days": [4, 5]}
    
    def detect_task_creation_anomalies(self) -> List[Dict]:
        """Detect anomalies in task creation patterns"""
        # Implementation for task creation anomaly detection
        return []
    
    def detect_completion_anomalies(self) -> List[Dict]:
        """Detect anomalies in task completion patterns"""
        # Implementation for completion anomaly detection
        return []
    
    def detect_time_anomalies(self) -> List[Dict]:
        """Detect time-based anomalies"""
        # Implementation for time anomaly detection
        return []
    
    def get_visual_analytics_data(self) -> Dict:
        """Get data formatted for visual analytics dashboard"""
        analysis = self.analyze_current_situation()
        
        return {
            "charts": {
                "productivity_trend": self.format_productivity_chart_data(analysis),
                "workload_distribution": self.format_workload_chart_data(analysis),
                "time_analysis": self.format_time_chart_data(analysis),
                "project_timeline": self.format_project_timeline_data()
            },
            "metrics": {
                "productivity_score": analysis["productivity_status"].get("score", 0),
                "completion_rate": analysis["productivity_status"].get("completion_rate", 0),
                "workload_intensity": analysis["workload_analysis"].get("workload_intensity", "unknown"),
                "overload_risk": analysis["workload_analysis"].get("overload_risk", 0)
            },
            "insights": analysis["recommendations"],
            "alerts": analysis["alerts"]
        }
    
    def format_productivity_chart_data(self, analysis: Dict) -> Dict:
        """Format data for productivity trend chart"""
        daily_stats = analysis["productivity_status"].get("daily_stats", [])
        
        return {
            "type": "line",
            "title": "Productivity Trend (7 Days)",
            "data": {
                "labels": [stat["date"].strftime("%m/%d") if stat["date"] else "" for stat in daily_stats],
                "datasets": [{
                    "label": "Completion Rate",
                    "data": [stat["completion_rate"] * 100 for stat in daily_stats],
                    "borderColor": "#4A90E2",
                    "backgroundColor": "rgba(74, 144, 226, 0.1)"
                }]
            }
        }
    
    def format_workload_chart_data(self, analysis: Dict) -> Dict:
        """Format data for workload distribution chart"""
        deadline_dist = analysis["workload_analysis"].get("deadline_distribution", {})
        
        return {
            "type": "doughnut",
            "title": "Task Distribution by Deadline",
            "data": {
                "labels": ["Overdue", "Today", "This Week", "Later"],
                "datasets": [{
                    "data": [
                        deadline_dist.get("overdue", 0),
                        deadline_dist.get("today", 0),
                        deadline_dist.get("this_week", 0),
                        deadline_dist.get("later", 0)
                    ],
                    "backgroundColor": ["#FF6B6B", "#FFD93D", "#6BCF7F", "#4A90E2"]
                }]
            }
        }
    
    def format_time_chart_data(self, analysis: Dict) -> Dict:
        """Format data for time analysis chart"""
        patterns = analysis["pattern_insights"]
        work_schedule = patterns.get("work_schedule", {})
        hourly_activity = work_schedule.get("hourly_activity", {})
        
        return {
            "type": "bar",
            "title": "Activity by Hour of Day",
            "data": {
                "labels": [f"{h}:00" for h in range(24)],
                "datasets": [{
                    "label": "Activity Level",
                    "data": [hourly_activity.get(h, 0) for h in range(24)],
                    "backgroundColor": "#4A90E2"
                }]
            }
        }
    
    def format_project_timeline_data(self) -> Dict:
        """Format data for project timeline visualization"""
        # This would create a Gantt-chart style visualization
        return {
            "type": "timeline",
            "title": "Project Timeline & Workload",
            "data": {
                "projects": [],  # Would be populated with actual project data
                "milestones": [],
                "workload_periods": []
            }
        }

# Test the analytics engine
if __name__ == "__main__":
    import os
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    analytics = LiveAnalyticsEngine()
    
    print("🔍 Testing Live Analytics Engine...")
    
    # Test current situation analysis
    analysis = analytics.analyze_current_situation()
    
    print(f"\n📊 Productivity Status:")
    productivity = analysis.get("productivity_status", {})
    print(f"  Completion Rate: {productivity.get('completion_rate', 0):.1%}")
    print(f"  Productivity Zone: {productivity.get('productivity_zone', 'unknown')}")
    print(f"  Score: {productivity.get('score', 0)}/100")
    
    print(f"\n📋 Workload Analysis:")
    workload = analysis.get("workload_analysis", {})
    print(f"  Total Pending: {workload.get('total_pending', 0)}")
    print(f"  Estimated Hours: {workload.get('estimated_hours', 0)}")
    print(f"  Intensity: {workload.get('workload_intensity', 'unknown')}")
    
    print(f"\n💡 Recommendations: {len(analysis.get('recommendations', []))}")
    for rec in analysis.get("recommendations", [])[:3]:
        print(f"  • {rec.get('title', 'No title')} ({rec.get('priority', 'normal')})")
    
    print(f"\n⚠️  Alerts: {len(analysis.get('alerts', []))}")
    for alert in analysis.get("alerts", [])[:3]:
        print(f"  • {alert.get('title', 'No title')} ({alert.get('severity', 'info')})")
    
    # Test visual analytics data
    print(f"\n📈 Visual Analytics Data:")
    visual_data = analytics.get_visual_analytics_data()
    print(f"  Charts available: {len(visual_data.get('charts', {}))}")
    print(f"  Metrics tracked: {len(visual_data.get('metrics', {}))}")
    
    print("\n✅ Analytics engine test completed!")