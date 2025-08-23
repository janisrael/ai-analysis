import os
import json
import uuid
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from urllib.parse import quote
import base64
import hashlib

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class ReportData:
    """Container for report data and metadata"""
    
    def __init__(self, report_id: str, report_type: str, title: str, project_name: str = None):
        self.report_id = report_id
        self.report_type = report_type  # project, productivity, task_analysis, timeline
        self.title = title
        self.project_name = project_name
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=24)  # Reports expire after 24 hours
        
        # Report content
        self.summary = ""
        self.insights = []
        self.recommendations = []
        self.charts = []
        self.data_tables = []
        self.voice_script = ""
        
        # File paths
        self.html_path = ""
        self.pdf_path = ""
        self.assets_path = ""

class ReportGenerator:
    """Dynamic report generator with visual charts and voice narration"""
    
    def __init__(self, db_path: str, analytics_engine, voice_system=None):
        self.db_path = db_path
        self.analytics_engine = analytics_engine
        self.voice_system = voice_system
        self.logger = logging.getLogger(__name__)
        
        # Report storage
        self.reports_dir = "data/reports"
        self.temp_reports = {}  # In-memory storage for active reports
        
        # Initialize directories
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(f"{self.reports_dir}/assets", exist_ok=True)
        os.makedirs(f"{self.reports_dir}/charts", exist_ok=True)
        
        # Initialize report database
        self.init_report_db()
    
    def init_report_db(self):
        """Initialize reports database table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS generated_reports (
                        report_id TEXT PRIMARY KEY,
                        report_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        project_name TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME,
                        html_path TEXT,
                        pdf_path TEXT,
                        voice_script TEXT,
                        access_count INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to initialize report database: {e}")
    
    def generate_project_report(self, project_name: str, user_query: str = "") -> ReportData:
        """Generate a comprehensive project report"""
        report_id = self.generate_report_id()
        report = ReportData(report_id, "project", f"Project Report: {project_name}", project_name)
        
        # Gather project data
        project_data = self.get_project_data(project_name)
        
        # Generate report content
        report.summary = self.generate_project_summary(project_data, project_name)
        report.insights = self.generate_project_insights(project_data)
        report.recommendations = self.generate_project_recommendations(project_data)
        
        # Create charts
        if MATPLOTLIB_AVAILABLE:
            report.charts = self.create_project_charts(project_data, report_id)
        
        # Generate voice script
        report.voice_script = self.generate_project_voice_script(report, project_data)
        
        # Create HTML report
        report.html_path = self.create_html_report(report)
        
        # Create PDF report if available
        if REPORTLAB_AVAILABLE:
            report.pdf_path = self.create_pdf_report(report)
        
        # Store report
        self.store_report(report)
        
        return report
    
    def generate_productivity_report(self, time_period: str = "30days") -> ReportData:
        """Generate a productivity analysis report"""
        report_id = self.generate_report_id()
        report = ReportData(report_id, "productivity", f"Productivity Report - Last {time_period}")
        
        # Get analytics data
        analysis_data = self.analytics_engine.analyze_current_situation()
        historical_data = self.get_historical_productivity_data(time_period)
        
        # Generate content
        report.summary = self.generate_productivity_summary(analysis_data, historical_data)
        report.insights = self.generate_productivity_insights(analysis_data)
        report.recommendations = analysis_data.get("recommendations", [])
        
        # Create charts
        if MATPLOTLIB_AVAILABLE:
            report.charts = self.create_productivity_charts(historical_data, report_id)
        
        # Generate voice script
        report.voice_script = self.generate_productivity_voice_script(report, analysis_data)
        
        # Create files
        report.html_path = self.create_html_report(report)
        if REPORTLAB_AVAILABLE:
            report.pdf_path = self.create_pdf_report(report)
        
        self.store_report(report)
        return report
    
    def generate_custom_report(self, query: str, report_type: str = "custom") -> ReportData:
        """Generate a custom report based on user query"""
        report_id = self.generate_report_id()
        
        # Parse query to understand what user wants
        report_focus = self.parse_report_query(query)
        
        report = ReportData(report_id, report_type, f"Custom Report: {report_focus['title']}")
        
        # Generate content based on query focus
        if "project" in report_focus["keywords"]:
            project_name = report_focus.get("project_name", "All Projects")
            return self.generate_project_report(project_name, query)
        elif "productivity" in report_focus["keywords"]:
            return self.generate_productivity_report()
        else:
            # General data report
            report.summary = self.generate_custom_summary(query, report_focus)
            report.insights = self.generate_custom_insights(query, report_focus)
            report.voice_script = self.generate_custom_voice_script(report, query)
            
            report.html_path = self.create_html_report(report)
            self.store_report(report)
            
        return report
    
    # Data gathering methods
    
    def get_project_data(self, project_name: str) -> Dict:
        """Get all data related to a specific project"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get tasks for this project
                cursor.execute('''
                    SELECT * FROM tasks 
                    WHERE json_extract(metadata, '$.project') = ? OR 
                          json_extract(metadata, '$.category') = ? OR
                          title LIKE ?
                    ORDER BY created_at DESC
                ''', (project_name, project_name, f"%{project_name}%"))
                
                tasks = [dict(row) for row in cursor.fetchall()]
                
                # Get related events
                cursor.execute('''
                    SELECT * FROM events 
                    WHERE title LIKE ? OR message LIKE ?
                    ORDER BY created_at DESC
                ''', (f"%{project_name}%", f"%{project_name}%"))
                
                events = [dict(row) for row in cursor.fetchall()]
                
                # Calculate project metrics
                total_tasks = len(tasks)
                completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
                pending_tasks = len([t for t in tasks if t['status'] == 'pending'])
                overdue_tasks = len([t for t in tasks if self.is_task_overdue(t)])
                
                completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
                
                # Get time spent (from focus sessions)
                cursor.execute('''
                    SELECT SUM(json_extract(metadata, '$.duration')) as total_duration
                    FROM user_actions 
                    WHERE action_type = 'focus_session_completed' 
                    AND context LIKE ?
                ''', (f"%{project_name}%",))
                
                time_result = cursor.fetchone()
                total_time_minutes = time_result[0] if time_result[0] else 0
                
                return {
                    "project_name": project_name,
                    "tasks": tasks,
                    "events": events,
                    "metrics": {
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                        "pending_tasks": pending_tasks,
                        "overdue_tasks": overdue_tasks,
                        "completion_rate": completion_rate,
                        "total_time_hours": total_time_minutes / 60,
                        "avg_task_completion_time": self.calculate_avg_completion_time(tasks)
                    },
                    "timeline": self.create_project_timeline(tasks, events)
                }
                
        except Exception as e:
            self.logger.error(f"Error getting project data: {e}")
            return {"project_name": project_name, "tasks": [], "events": [], "metrics": {}}
    
    def get_historical_productivity_data(self, period: str) -> Dict:
        """Get historical productivity data for analysis"""
        try:
            days = {"7days": 7, "30days": 30, "90days": 90}.get(period, 30)
            start_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get tasks created and completed in period
                cursor.execute('''
                    SELECT * FROM tasks 
                    WHERE created_at >= ?
                    ORDER BY created_at DESC
                ''', (start_date,))
                
                tasks = [dict(row) for row in cursor.fetchall()]
                
                # Get daily productivity metrics
                daily_metrics = self.calculate_daily_metrics(tasks, days)
                
                return {
                    "period": period,
                    "tasks": tasks,
                    "daily_metrics": daily_metrics,
                    "summary": self.calculate_period_summary(tasks, daily_metrics)
                }
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return {"period": period, "tasks": [], "daily_metrics": []}
    
    # Content generation methods
    
    def generate_project_summary(self, project_data: Dict, project_name: str) -> str:
        """Generate project summary text"""
        metrics = project_data.get("metrics", {})
        
        summary = f"""
# Project Summary: {project_name}

## Overview
This project currently has **{metrics.get('total_tasks', 0)} total tasks** with a **{metrics.get('completion_rate', 0):.1%} completion rate**.

## Current Status
- ✅ **Completed Tasks**: {metrics.get('completed_tasks', 0)}
- 📋 **Pending Tasks**: {metrics.get('pending_tasks', 0)}
- ⚠️ **Overdue Tasks**: {metrics.get('overdue_tasks', 0)}
- ⏱️ **Total Time Invested**: {metrics.get('total_time_hours', 0):.1f} hours

## Performance Indicators
- **Completion Rate**: {metrics.get('completion_rate', 0):.1%}
- **Average Task Completion Time**: {metrics.get('avg_task_completion_time', 0):.1f} days
- **Project Health**: {"🟢 Good" if metrics.get('completion_rate', 0) > 0.7 else "🟡 Needs Attention" if metrics.get('completion_rate', 0) > 0.4 else "🔴 Critical"}
"""
        
        return summary
    
    def generate_project_insights(self, project_data: Dict) -> List[Dict]:
        """Generate insights about the project"""
        insights = []
        metrics = project_data.get("metrics", {})
        tasks = project_data.get("tasks", [])
        
        # Completion rate insight
        completion_rate = metrics.get("completion_rate", 0)
        if completion_rate > 0.8:
            insights.append({
                "type": "positive",
                "title": "Excellent Progress",
                "description": f"Your project has an {completion_rate:.1%} completion rate, which is outstanding!"
            })
        elif completion_rate < 0.5:
            insights.append({
                "type": "warning",
                "title": "Progress Needs Attention",
                "description": f"The project completion rate is {completion_rate:.1%}. Consider reviewing task priorities and removing blockers."
            })
        
        # Overdue tasks insight
        overdue_count = metrics.get("overdue_tasks", 0)
        if overdue_count > 0:
            insights.append({
                "type": "alert",
                "title": "Overdue Tasks",
                "description": f"There are {overdue_count} overdue tasks that need immediate attention."
            })
        
        # Time investment insight
        total_hours = metrics.get("total_time_hours", 0)
        if total_hours > 0:
            insights.append({
                "type": "info",
                "title": "Time Investment",
                "description": f"You've invested {total_hours:.1f} hours in this project. That's dedication!"
            })
        
        # Task patterns insight
        high_priority_pending = len([t for t in tasks if t.get('priority', 3) <= 2 and t['status'] == 'pending'])
        if high_priority_pending > 0:
            insights.append({
                "type": "action",
                "title": "High Priority Tasks",
                "description": f"You have {high_priority_pending} high-priority tasks pending. Consider tackling these first."
            })
        
        return insights
    
    def generate_project_recommendations(self, project_data: Dict) -> List[Dict]:
        """Generate actionable recommendations for the project"""
        recommendations = []
        metrics = project_data.get("metrics", {})
        
        # Based on completion rate
        completion_rate = metrics.get("completion_rate", 0)
        if completion_rate < 0.6:
            recommendations.append({
                "priority": "high",
                "title": "Improve Task Completion",
                "description": "Consider breaking down large tasks into smaller, manageable chunks.",
                "actions": ["Review task complexity", "Set shorter deadlines", "Use focus sessions"]
            })
        
        # Based on overdue tasks
        if metrics.get("overdue_tasks", 0) > 2:
            recommendations.append({
                "priority": "urgent",
                "title": "Address Overdue Items",
                "description": "Multiple overdue tasks can impact project momentum.",
                "actions": ["Reschedule realistic deadlines", "Identify blockers", "Consider delegation"]
            })
        
        # Time management
        if metrics.get("total_time_hours", 0) == 0:
            recommendations.append({
                "priority": "medium",
                "title": "Track Time Investment",
                "description": "Start using focus sessions to track time spent on this project.",
                "actions": ["Use Pomodoro technique", "Log focus sessions", "Measure productivity"]
            })
        
        return recommendations
    
    # Voice script generation
    
    def generate_project_voice_script(self, report: ReportData, project_data: Dict) -> str:
        """Generate voice narration script for project report"""
        metrics = project_data.get("metrics", {})
        project_name = project_data.get("project_name", "your project")
        
        script = f"""
Welcome to your comprehensive project report for {project_name}. 

Let me walk you through the key findings and insights.

First, let's look at the overall status. Your project currently has {metrics.get('total_tasks', 0)} total tasks, 
with {metrics.get('completed_tasks', 0)} completed and {metrics.get('pending_tasks', 0)} still pending. 

This gives you a completion rate of {metrics.get('completion_rate', 0):.0%}. 
"""
        
        # Add performance commentary
        completion_rate = metrics.get('completion_rate', 0)
        if completion_rate > 0.8:
            script += "This is excellent progress! You're really staying on top of your project tasks. "
        elif completion_rate > 0.6:
            script += "You're making good progress. Keep up the momentum! "
        else:
            script += "There's room for improvement here. Let's look at some recommendations to help you get back on track. "
        
        # Add insights
        if metrics.get('overdue_tasks', 0) > 0:
            script += f"I notice you have {metrics.get('overdue_tasks')} overdue tasks. These need immediate attention to keep your project on schedule. "
        
        if metrics.get('total_time_hours', 0) > 0:
            script += f"You've invested {metrics.get('total_time_hours', 0):.1f} hours in this project so far. "
        
        # Add recommendations section
        script += """
Now, let me share some recommendations to help you improve your project performance.
"""
        
        recommendations = report.recommendations
        for i, rec in enumerate(recommendations[:3], 1):
            script += f"Recommendation {i}: {rec.get('title', 'Improvement')}. {rec.get('description', '')} "
        
        script += """
You can see all the detailed charts and data in the visual report below. 
Use the action buttons to implement the suggestions I've shared.

Thank you for letting me analyze your project. I'm here to help you succeed!
"""
        
        return script.strip()
    
    def generate_productivity_voice_script(self, report: ReportData, analysis_data: Dict) -> str:
        """Generate voice script for productivity report"""
        productivity = analysis_data.get("productivity_status", {})
        
        script = f"""
Welcome to your productivity analysis report.

Let me break down your performance metrics for you.

Your current productivity score is {productivity.get('score', 0)} out of 100, which puts you in the {productivity.get('productivity_zone', 'unknown')} productivity zone.

You have a {productivity.get('completion_rate', 0):.0%} task completion rate, with {productivity.get('completed_tasks', 0)} tasks completed and {productivity.get('pending_tasks', 0)} still pending.
"""
        
        # Add trend analysis
        trend = productivity.get("trend", {})
        if trend.get("direction") == "improving":
            script += "Great news! Your productivity trend is improving. You're building good momentum. "
        elif trend.get("direction") == "declining":
            script += "I notice your productivity has been declining recently. Don't worry, this happens to everyone. Let's work on getting you back on track. "
        else:
            script += "Your productivity has been stable. "
        
        # Add alerts
        alerts = analysis_data.get("alerts", [])
        if alerts:
            script += f"I have {len(alerts)} important alerts for you. "
            for alert in alerts[:2]:
                script += f"{alert.get('message', '')} "
        
        script += """
The visual charts below show your detailed patterns and trends. 
I've also included personalized recommendations to help you optimize your workflow.

Remember, productivity isn't about being perfect - it's about consistent progress. You're doing great!
"""
        
        return script.strip()
    
    # Chart creation methods
    
    def create_project_charts(self, project_data: Dict, report_id: str) -> List[str]:
        """Create charts for project report"""
        chart_paths = []
        
        try:
            # Task completion chart
            chart_path = self.create_task_completion_chart(project_data, report_id)
            if chart_path:
                chart_paths.append(chart_path)
            
            # Timeline chart
            timeline_path = self.create_project_timeline_chart(project_data, report_id)
            if timeline_path:
                chart_paths.append(timeline_path)
            
            # Priority distribution chart
            priority_path = self.create_priority_distribution_chart(project_data, report_id)
            if priority_path:
                chart_paths.append(priority_path)
                
        except Exception as e:
            self.logger.error(f"Error creating project charts: {e}")
        
        return chart_paths
    
    def create_task_completion_chart(self, project_data: Dict, report_id: str) -> str:
        """Create task completion status chart"""
        try:
            metrics = project_data.get("metrics", {})
            
            # Data for pie chart
            labels = ['Completed', 'Pending', 'Overdue']
            sizes = [
                metrics.get('completed_tasks', 0),
                metrics.get('pending_tasks', 0) - metrics.get('overdue_tasks', 0),
                metrics.get('overdue_tasks', 0)
            ]
            colors = ['#4CAF50', '#2196F3', '#F44336']
            
            # Remove zero values
            labels_filtered = []
            sizes_filtered = []
            colors_filtered = []
            
            for label, size, color in zip(labels, sizes, colors):
                if size > 0:
                    labels_filtered.append(f'{label}\n({size})')
                    sizes_filtered.append(size)
                    colors_filtered.append(color)
            
            if not sizes_filtered:
                return None
            
            # Create chart
            fig, ax = plt.subplots(figsize=(8, 6))
            wedges, texts, autotexts = ax.pie(sizes_filtered, labels=labels_filtered, colors=colors_filtered,
                                            autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10})
            
            ax.set_title(f'Task Completion Status\n{project_data.get("project_name", "Project")}', 
                        fontsize=14, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            # Save chart
            chart_path = f"{self.reports_dir}/charts/completion_{report_id}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return chart_path
            
        except Exception as e:
            self.logger.error(f"Error creating completion chart: {e}")
            return None
    
    def create_project_timeline_chart(self, project_data: Dict, report_id: str) -> str:
        """Create project timeline chart"""
        try:
            tasks = project_data.get("tasks", [])
            if not tasks:
                return None
            
            # Prepare timeline data
            dates = []
            completed_cumulative = []
            created_cumulative = []
            
            # Sort tasks by date
            sorted_tasks = sorted(tasks, key=lambda x: x['created_at'])
            
            current_date = datetime.fromisoformat(sorted_tasks[0]['created_at']).date()
            end_date = datetime.now().date()
            
            completed_count = 0
            created_count = 0
            
            while current_date <= end_date:
                # Count tasks created on this date
                created_today = len([t for t in sorted_tasks 
                                   if datetime.fromisoformat(t['created_at']).date() == current_date])
                created_count += created_today
                
                # Count tasks completed on this date
                completed_today = len([t for t in sorted_tasks 
                                     if t['status'] == 'completed' and t.get('updated_at') and
                                     datetime.fromisoformat(t['updated_at']).date() == current_date])
                completed_count += completed_today
                
                dates.append(current_date)
                created_cumulative.append(created_count)
                completed_cumulative.append(completed_count)
                
                current_date += timedelta(days=1)
            
            # Create chart
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot(dates, created_cumulative, label='Tasks Created', color='#2196F3', linewidth=2)
            ax.plot(dates, completed_cumulative, label='Tasks Completed', color='#4CAF50', linewidth=2)
            
            ax.set_title(f'Project Timeline\n{project_data.get("project_name", "Project")}', 
                        fontsize=14, fontweight='bold')
            ax.set_xlabel('Date')
            ax.set_ylabel('Cumulative Tasks')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Format dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Save chart
            chart_path = f"{self.reports_dir}/charts/timeline_{report_id}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return chart_path
            
        except Exception as e:
            self.logger.error(f"Error creating timeline chart: {e}")
            return None
    
    def create_priority_distribution_chart(self, project_data: Dict, report_id: str) -> str:
        """Create priority distribution chart"""
        try:
            tasks = project_data.get("tasks", [])
            if not tasks:
                return None
            
            # Count tasks by priority
            priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for task in tasks:
                priority = task.get('priority', 3)
                priority_counts[priority] += 1
            
            # Prepare data
            labels = ['High (1)', 'High-Med (2)', 'Medium (3)', 'Med-Low (4)', 'Low (5)']
            sizes = [priority_counts[i] for i in range(1, 6)]
            colors = ['#F44336', '#FF9800', '#2196F3', '#4CAF50', '#9E9E9E']
            
            # Remove zero values
            labels_filtered = []
            sizes_filtered = []
            colors_filtered = []
            
            for label, size, color in zip(labels, sizes, colors):
                if size > 0:
                    labels_filtered.append(f'{label}\n({size})')
                    sizes_filtered.append(size)
                    colors_filtered.append(color)
            
            if not sizes_filtered:
                return None
            
            # Create chart
            fig, ax = plt.subplots(figsize=(8, 6))
            bars = ax.bar(range(len(sizes_filtered)), sizes_filtered, color=colors_filtered)
            
            ax.set_title(f'Task Priority Distribution\n{project_data.get("project_name", "Project")}', 
                        fontsize=14, fontweight='bold')
            ax.set_xlabel('Priority Level')
            ax.set_ylabel('Number of Tasks')
            ax.set_xticks(range(len(labels_filtered)))
            ax.set_xticklabels([label.split('\n')[0] for label in labels_filtered])
            
            # Add value labels on bars
            for bar, size in zip(bars, sizes_filtered):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       str(size), ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            
            # Save chart
            chart_path = f"{self.reports_dir}/charts/priority_{report_id}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return chart_path
            
        except Exception as e:
            self.logger.error(f"Error creating priority chart: {e}")
            return None
    
    # HTML report creation
    
    def create_html_report(self, report: ReportData) -> str:
        """Create interactive HTML report with voice narration"""
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .voice-controls {{
            position: absolute;
            top: 20px;
            right: 20px;
        }}
        .voice-btn {{
            background: rgba(255,255,255,0.2);
            border: 2px solid white;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            margin: 0 5px;
            transition: all 0.3s ease;
        }}
        .voice-btn:hover {{
            background: white;
            color: #4A90E2;
        }}
        .voice-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        .content {{
            padding: 40px;
        }}
        .section {{
            margin-bottom: 40px;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }}
        .summary {{
            background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        }}
        .insights {{
            background: linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%);
        }}
        .recommendations {{
            background: linear-gradient(135deg, #E8F5E8 0%, #C8E6C9 100%);
        }}
        .charts {{
            background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        }}
        .section h2 {{
            color: #333;
            border-bottom: 3px solid #4A90E2;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .insight-card, .recommendation-card {{
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            border-left: 5px solid #4A90E2;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }}
        .insight-card.warning {{
            border-left-color: #FF9800;
        }}
        .insight-card.alert {{
            border-left-color: #F44336;
        }}
        .insight-card.positive {{
            border-left-color: #4CAF50;
        }}
        .recommendation-card.urgent {{
            border-left-color: #F44336;
        }}
        .recommendation-card.high {{
            border-left-color: #FF9800;
        }}
        .chart-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .action-buttons {{
            margin-top: 20px;
            text-align: center;
        }}
        .action-btn {{
            background: #4A90E2;
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            margin: 0 10px;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }}
        .action-btn:hover {{
            background: #357ABD;
            transform: translateY(-2px);
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
        }}
        .speaking-indicator {{
            display: none;
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #4A90E2;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            z-index: 1000;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0% {{ opacity: 0.6; }}
            50% {{ opacity: 1; }}
            100% {{ opacity: 0.6; }}
        }}
        .markdown {{
            white-space: pre-line;
        }}
    </style>
</head>
<body>
    <div class="speaking-indicator" id="speakingIndicator">
        🔊 AI Assistant is speaking...
    </div>
    
    <div class="container">
        <div class="header">
            <div class="voice-controls">
                <button class="voice-btn" onclick="startNarration()" id="playBtn">🔊 Play Report</button>
                <button class="voice-btn" onclick="stopNarration()" id="stopBtn" disabled>⏹️ Stop</button>
                <button class="voice-btn" onclick="downloadPDF()" id="downloadBtn">📄 Download PDF</button>
            </div>
            <h1>{report.title}</h1>
            <div class="subtitle">Generated on {report.created_at.strftime('%B %d, %Y at %I:%M %p')}</div>
        </div>
        
        <div class="content">
            <div class="section summary">
                <h2>📊 Executive Summary</h2>
                <div class="markdown">{report.summary}</div>
            </div>
            
            <div class="section insights">
                <h2>💡 Key Insights</h2>
"""
            
            # Add insights
            for insight in report.insights:
                insight_type = insight.get('type', 'info')
                html_content += f"""
                <div class="insight-card {insight_type}">
                    <h3>{insight.get('title', 'Insight')}</h3>
                    <p>{insight.get('description', '')}</p>
                </div>
"""
            
            # Add recommendations
            html_content += """
            </div>
            
            <div class="section recommendations">
                <h2>🎯 Recommendations</h2>
"""
            
            for rec in report.recommendations:
                priority = rec.get('priority', 'medium')
                html_content += f"""
                <div class="recommendation-card {priority}">
                    <h3>{rec.get('title', 'Recommendation')}</h3>
                    <p>{rec.get('description', '')}</p>
"""
                if rec.get('actions'):
                    html_content += "<p><strong>Suggested Actions:</strong> " + ", ".join(rec['actions']) + "</p>"
                
                html_content += "</div>"
            
            # Add charts
            if report.charts:
                html_content += """
            </div>
            
            <div class="section charts">
                <h2>📈 Visual Analysis</h2>
"""
                for chart_path in report.charts:
                    if os.path.exists(chart_path):
                        chart_filename = os.path.basename(chart_path)
                        # Copy chart to assets folder for the report
                        chart_url = f"charts/{chart_filename}"
                        html_content += f"""
                <div class="chart-container">
                    <img src="{chart_url}" alt="Analysis Chart" />
                </div>
"""
            
            # Add action buttons and footer
            html_content += f"""
            </div>
            
            <div class="action-buttons">
                <a href="#" class="action-btn" onclick="openTaskManager()">📋 Open Task Manager</a>
                <a href="#" class="action-btn" onclick="startFocusSession()">🎯 Start Focus Session</a>
                <a href="#" class="action-btn" onclick="openAnalytics()">📊 View Analytics</a>
            </div>
        </div>
        
        <div class="footer">
            <p>Report ID: {report.report_id} | Expires: {report.expires_at.strftime('%B %d, %Y')} | 
            Generated by AI Avatar Assistant</p>
        </div>
    </div>
    
    <script>
        // Voice narration script embedded directly
        const voiceScript = `{report.voice_script}`;
        let speechSynthesis = window.speechSynthesis;
        let currentUtterance = null;
        
        function startNarration() {{
            if (speechSynthesis.speaking) {{
                speechSynthesis.cancel();
            }}
            
            currentUtterance = new SpeechSynthesisUtterance(voiceScript);
            currentUtterance.rate = 0.9;
            currentUtterance.pitch = 1;
            currentUtterance.volume = 0.8;
            
            // Try to use a pleasant voice
            const voices = speechSynthesis.getVoices();
            const preferredVoice = voices.find(voice => 
                voice.name.includes('Female') || 
                voice.name.includes('Zira') || 
                voice.name.includes('Samantha')
            );
            
            if (preferredVoice) {{
                currentUtterance.voice = preferredVoice;
            }}
            
            currentUtterance.onstart = function() {{
                document.getElementById('speakingIndicator').style.display = 'block';
                document.getElementById('playBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
            }};
            
            currentUtterance.onend = function() {{
                document.getElementById('speakingIndicator').style.display = 'none';
                document.getElementById('playBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            }};
            
            speechSynthesis.speak(currentUtterance);
        }}
        
        function stopNarration() {{
            if (speechSynthesis.speaking) {{
                speechSynthesis.cancel();
                document.getElementById('speakingIndicator').style.display = 'none';
                document.getElementById('playBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            }}
        }}
        
        function downloadPDF() {{
            window.location.href = 'pdf/{os.path.basename(report.pdf_path or "")}';
        }}
        
        function openTaskManager() {{
            // This would integrate with the main application
            alert('Opening task manager...');
        }}
        
        function startFocusSession() {{
            // This would integrate with the main application
            alert('Starting focus session...');
        }}
        
        function openAnalytics() {{
            // This would integrate with the main application  
            alert('Opening analytics dashboard...');
        }}
        
        // Auto-start narration when page loads (optional)
        window.addEventListener('load', function() {{
            // Uncomment to auto-start narration
            // setTimeout(startNarration, 1000);
        }});
    </script>
</body>
</html>
"""
            
            # Save HTML file
            html_path = f"{self.reports_dir}/report_{report.report_id}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return html_path
            
        except Exception as e:
            self.logger.error(f"Error creating HTML report: {e}")
            return ""
    
    # Utility methods
    
    def generate_report_id(self) -> str:
        """Generate unique report ID"""
        return str(uuid.uuid4())[:8]
    
    def generate_temporary_link(self, report: ReportData) -> str:
        """Generate temporary link for accessing the report"""
        # Create a secure token
        token = hashlib.sha256(f"{report.report_id}{report.created_at}".encode()).hexdigest()[:16]
        
        # In a real implementation, this would be a proper URL
        return f"http://localhost:8080/reports/{report.report_id}?token={token}"
    
    def store_report(self, report: ReportData):
        """Store report in database and memory"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO generated_reports 
                    (report_id, report_type, title, project_name, created_at, expires_at, 
                     html_path, pdf_path, voice_script)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report.report_id, report.report_type, report.title, report.project_name,
                    report.created_at, report.expires_at, report.html_path, report.pdf_path,
                    report.voice_script
                ))
                conn.commit()
            
            # Store in memory for quick access
            self.temp_reports[report.report_id] = report
            
        except Exception as e:
            self.logger.error(f"Error storing report: {e}")
    
    def get_report(self, report_id: str) -> Optional[ReportData]:
        """Get report by ID"""
        # Check memory first
        if report_id in self.temp_reports:
            return self.temp_reports[report_id]
        
        # Check database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM generated_reports 
                    WHERE report_id = ? AND is_active = 1 AND expires_at > ?
                ''', (report_id, datetime.now()))
                
                row = cursor.fetchone()
                if row:
                    # Reconstruct report object
                    report = ReportData(row['report_id'], row['report_type'], row['title'], row['project_name'])
                    report.created_at = datetime.fromisoformat(row['created_at'])
                    report.expires_at = datetime.fromisoformat(row['expires_at'])
                    report.html_path = row['html_path']
                    report.pdf_path = row['pdf_path']
                    report.voice_script = row['voice_script']
                    
                    self.temp_reports[report_id] = report
                    return report
        except Exception as e:
            self.logger.error(f"Error getting report: {e}")
        
        return None
    
    def parse_report_query(self, query: str) -> Dict:
        """Parse user query to understand what kind of report they want"""
        query_lower = query.lower()
        
        focus = {
            "title": "Custom Report",
            "keywords": [],
            "project_name": None,
            "time_period": "30days"
        }
        
        # Check for project-specific requests
        project_indicators = ["project", "for", "about", "on"]
        for indicator in project_indicators:
            if indicator in query_lower:
                focus["keywords"].append("project")
                # Try to extract project name
                words = query.split()
                for i, word in enumerate(words):
                    if word.lower() in project_indicators and i + 1 < len(words):
                        focus["project_name"] = words[i + 1].strip(".,!?")
                        focus["title"] = f"Report for {focus['project_name']}"
                        break
        
        # Check for productivity requests
        if any(word in query_lower for word in ["productivity", "performance", "stats", "analytics"]):
            focus["keywords"].append("productivity")
            focus["title"] = "Productivity Analysis Report"
        
        # Check for time period
        if "week" in query_lower:
            focus["time_period"] = "7days"
        elif "month" in query_lower:
            focus["time_period"] = "30days"
        elif "quarter" in query_lower:
            focus["time_period"] = "90days"
        
        return focus
    
    # Helper methods for data processing
    
    def is_task_overdue(self, task: Dict) -> bool:
        """Check if task is overdue"""
        if not task.get('deadline') or task['status'] == 'completed':
            return False
        try:
            deadline = datetime.fromisoformat(task['deadline'])
            return deadline < datetime.now()
        except:
            return False
    
    def calculate_avg_completion_time(self, tasks: List[Dict]) -> float:
        """Calculate average task completion time in days"""
        completed_tasks = [t for t in tasks if t['status'] == 'completed' and t.get('updated_at')]
        
        if not completed_tasks:
            return 0
        
        total_days = 0
        for task in completed_tasks:
            try:
                created = datetime.fromisoformat(task['created_at'])
                completed = datetime.fromisoformat(task['updated_at'])
                days = (completed - created).days
                total_days += max(days, 0)  # Ensure non-negative
            except:
                continue
        
        return total_days / len(completed_tasks) if completed_tasks else 0
    
    def create_project_timeline(self, tasks: List[Dict], events: List[Dict]) -> List[Dict]:
        """Create timeline of project events"""
        timeline = []
        
        # Add task events
        for task in tasks:
            timeline.append({
                "date": task['created_at'],
                "type": "task_created",
                "description": f"Task created: {task['title']}"
            })
            
            if task['status'] == 'completed' and task.get('updated_at'):
                timeline.append({
                    "date": task['updated_at'],
                    "type": "task_completed",
                    "description": f"Task completed: {task['title']}"
                })
        
        # Add other events
        for event in events:
            timeline.append({
                "date": event['created_at'],
                "type": "event",
                "description": event.get('title', 'Event')
            })
        
        # Sort by date
        timeline.sort(key=lambda x: x['date'])
        
        return timeline
    
    def calculate_daily_metrics(self, tasks: List[Dict], days: int) -> List[Dict]:
        """Calculate daily productivity metrics"""
        daily_metrics = []
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            
            # Tasks created on this day
            created = len([t for t in tasks 
                          if datetime.fromisoformat(t['created_at']).date() == current_date.date()])
            
            # Tasks completed on this day
            completed = len([t for t in tasks 
                           if t['status'] == 'completed' and t.get('updated_at') and
                           datetime.fromisoformat(t['updated_at']).date() == current_date.date()])
            
            daily_metrics.append({
                "date": current_date.date(),
                "tasks_created": created,
                "tasks_completed": completed,
                "completion_rate": completed / max(created, 1)
            })
        
        return daily_metrics
    
    def calculate_period_summary(self, tasks: List[Dict], daily_metrics: List[Dict]) -> Dict:
        """Calculate summary for the time period"""
        total_created = len(tasks)
        total_completed = len([t for t in tasks if t['status'] == 'completed'])
        
        avg_daily_created = sum(d['tasks_created'] for d in daily_metrics) / len(daily_metrics)
        avg_daily_completed = sum(d['tasks_completed'] for d in daily_metrics) / len(daily_metrics)
        
        return {
            "total_created": total_created,
            "total_completed": total_completed,
            "completion_rate": total_completed / max(total_created, 1),
            "avg_daily_created": avg_daily_created,
            "avg_daily_completed": avg_daily_completed,
            "most_productive_day": max(daily_metrics, key=lambda x: x['tasks_completed'])['date'] if daily_metrics else None
        }
    
    def generate_custom_summary(self, query: str, report_focus: Dict) -> str:
        """Generate summary for custom reports"""
        return f"""
# Custom Analysis Report

Based on your request: "{query}"

This report provides insights and analysis relevant to your specific inquiry. 
I've analyzed your data to provide the most relevant information.

Please review the insights and recommendations below.
"""
    
    def generate_custom_insights(self, query: str, report_focus: Dict) -> List[Dict]:
        """Generate insights for custom reports"""
        return [
            {
                "type": "info",
                "title": "Custom Analysis",
                "description": f"Analysis based on your request: {query}"
            }
        ]
    
    def generate_custom_voice_script(self, report: ReportData, query: str) -> str:
        """Generate voice script for custom reports"""
        return f"""
Here is your custom report based on your request about {query}.

I've analyzed your data and prepared insights specifically for your inquiry.

Please review the visual report below for detailed findings and recommendations.
"""
    
    def create_pdf_report(self, report: ReportData) -> str:
        """Create PDF version of the report (placeholder)"""
        # This would use ReportLab to create a PDF
        # For now, just return a placeholder path
        pdf_path = f"{self.reports_dir}/pdf_{report.report_id}.pdf"
        
        try:
            if REPORTLAB_AVAILABLE:
                # Create simple PDF with basic content
                doc = SimpleDocTemplate(pdf_path, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []
                
                # Title
                title = Paragraph(report.title, styles['Title'])
                story.append(title)
                story.append(Spacer(1, 12))
                
                # Summary
                summary = Paragraph(report.summary.replace('\n', '<br/>'), styles['Normal'])
                story.append(summary)
                
                doc.build(story)
                
        except Exception as e:
            self.logger.error(f"Error creating PDF: {e}")
        
        return pdf_path

# Test the report generator
if __name__ == "__main__":
    import tempfile
    import os
    
    # Create temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        test_db = f.name
    
    # Mock analytics engine
    class MockAnalytics:
        def analyze_current_situation(self):
            return {
                "productivity_status": {
                    "completion_rate": 0.75,
                    "score": 85,
                    "productivity_zone": "high",
                    "trend": {"direction": "improving"}
                },
                "recommendations": [
                    {
                        "title": "Take Regular Breaks",
                        "description": "You've been working intensely. Consider taking breaks.",
                        "priority": "medium"
                    }
                ],
                "alerts": []
            }
    
    # Test report generation
    generator = ReportGenerator(test_db, MockAnalytics())
    
    print("🧪 Testing Report Generator...")
    
    # Test project report
    report = generator.generate_project_report("Test Project")
    print(f"✅ Generated project report: {report.report_id}")
    print(f"📄 HTML file: {report.html_path}")
    print(f"🎙️ Voice script length: {len(report.voice_script)} characters")
    
    # Test temporary link
    link = generator.generate_temporary_link(report)
    print(f"🔗 Temporary link: {link}")
    
    # Cleanup
    os.unlink(test_db)
    print("✅ Report generator test completed!")