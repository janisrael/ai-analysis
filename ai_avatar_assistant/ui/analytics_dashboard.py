import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QFrame, QGridLayout,
                            QProgressBar, QTabWidget, QListWidget, QListWidgetItem,
                            QTextEdit, QSplitter, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor, QPainter, QPen, QBrush
import logging

try:
    # Try to import matplotlib for charts
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  Matplotlib not available. Charts will show simplified visualizations.")

class SimpleChartWidget(QWidget):
    """Simple chart widget for when matplotlib is not available"""
    
    def __init__(self, chart_data: Dict, parent=None):
        super().__init__(parent)
        self.chart_data = chart_data
        self.setMinimumSize(300, 200)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 8px;
            }
        """)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        margin = 20
        chart_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        # Draw title
        title = self.chart_data.get("title", "Chart")
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(rect.x() + 10, rect.y() + 15, title)
        
        chart_type = self.chart_data.get("type", "bar")
        data = self.chart_data.get("data", {})
        
        if chart_type == "line":
            self.draw_line_chart(painter, chart_rect, data)
        elif chart_type == "doughnut":
            self.draw_doughnut_chart(painter, chart_rect, data)
        elif chart_type == "bar":
            self.draw_bar_chart(painter, chart_rect, data)
        else:
            # Default text display
            painter.setFont(QFont("Arial", 10))
            painter.drawText(chart_rect, Qt.AlignCenter, f"Chart Type: {chart_type}")
    
    def draw_line_chart(self, painter, rect, data):
        """Draw a simple line chart"""
        datasets = data.get("datasets", [])
        if not datasets:
            return
        
        dataset = datasets[0]
        values = dataset.get("data", [])
        labels = data.get("labels", [])
        
        if not values:
            return
        
        # Calculate scaling
        max_val = max(values) if values else 100
        min_val = min(values) if values else 0
        val_range = max_val - min_val if max_val != min_val else 1
        
        # Draw axes
        painter.setPen(QPen(QColor("#666"), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())  # X-axis
        painter.drawLine(rect.bottomLeft(), rect.topLeft())      # Y-axis
        
        # Draw line
        if len(values) > 1:
            painter.setPen(QPen(QColor("#4A90E2"), 2))
            points = []
            for i, val in enumerate(values):
                x = rect.left() + (i * rect.width() / (len(values) - 1))
                y = rect.bottom() - ((val - min_val) / val_range * rect.height())
                points.append((x, y))
            
            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
    
    def draw_doughnut_chart(self, painter, rect, data):
        """Draw a simple doughnut chart"""
        datasets = data.get("datasets", [])
        if not datasets:
            return
        
        values = datasets[0].get("data", [])
        labels = data.get("labels", [])
        colors = datasets[0].get("backgroundColor", ["#FF6B6B", "#FFD93D", "#6BCF7F", "#4A90E2"])
        
        if not values or sum(values) == 0:
            return
        
        # Calculate center and radius
        center_x = rect.center().x()
        center_y = rect.center().y()
        radius = min(rect.width(), rect.height()) // 3
        inner_radius = radius // 2
        
        # Draw segments
        start_angle = 0
        total = sum(values)
        
        for i, (value, label) in enumerate(zip(values, labels)):
            if value == 0:
                continue
            
            span_angle = int(360 * value / total)
            color = QColor(colors[i % len(colors)])
            
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 1))
            
            # This is a simplified version - just draw colored rectangles as legend
            legend_y = rect.top() + 30 + i * 20
            painter.drawRect(rect.right() - 100, legend_y, 15, 15)
            painter.setPen(QPen(QColor("#333"), 1))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(rect.right() - 80, legend_y + 12, f"{label}: {value}")
            
            start_angle += span_angle
    
    def draw_bar_chart(self, painter, rect, data):
        """Draw a simple bar chart"""
        datasets = data.get("datasets", [])
        labels = data.get("labels", [])
        
        if not datasets or not labels:
            return
        
        values = datasets[0].get("data", [])
        
        if not values:
            return
        
        # Calculate scaling
        max_val = max(values) if values else 1
        bar_width = rect.width() // len(values) if values else 1
        
        # Draw bars
        painter.setBrush(QBrush(QColor("#4A90E2")))
        painter.setPen(QPen(QColor("#4A90E2"), 1))
        
        for i, val in enumerate(values):
            bar_height = int((val / max_val) * rect.height() * 0.8) if max_val > 0 else 0
            x = rect.left() + i * bar_width + bar_width * 0.1
            y = rect.bottom() - bar_height
            painter.drawRect(x, y, bar_width * 0.8, bar_height)

class MatplotlibChartWidget(QWidget):
    """Matplotlib-based chart widget"""
    
    def __init__(self, chart_data: Dict, parent=None):
        super().__init__(parent)
        self.chart_data = chart_data
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(6, 4), dpi=80)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        self.update_chart()
    
    def update_chart(self):
        """Update the chart with current data"""
        self.figure.clear()
        
        chart_type = self.chart_data.get("type", "bar")
        title = self.chart_data.get("title", "Chart")
        data = self.chart_data.get("data", {})
        
        ax = self.figure.add_subplot(111)
        ax.set_title(title, fontsize=12, fontweight='bold')
        
        if chart_type == "line":
            self.draw_matplotlib_line(ax, data)
        elif chart_type == "doughnut":
            self.draw_matplotlib_doughnut(ax, data)
        elif chart_type == "bar":
            self.draw_matplotlib_bar(ax, data)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def draw_matplotlib_line(self, ax, data):
        """Draw line chart with matplotlib"""
        datasets = data.get("datasets", [])
        labels = data.get("labels", [])
        
        for dataset in datasets:
            values = dataset.get("data", [])
            label = dataset.get("label", "Data")
            color = dataset.get("borderColor", "#4A90E2")
            
            ax.plot(labels, values, label=label, color=color, marker='o')
        
        ax.set_xlabel("Time")
        ax.set_ylabel("Value (%)")
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def draw_matplotlib_doughnut(self, ax, data):
        """Draw doughnut chart with matplotlib"""
        datasets = data.get("datasets", [])
        labels = data.get("labels", [])
        
        if datasets:
            values = datasets[0].get("data", [])
            colors = datasets[0].get("backgroundColor", [])
            
            # Filter out zero values
            filtered_data = [(v, l, c) for v, l, c in zip(values, labels, colors) if v > 0]
            if filtered_data:
                values, labels, colors = zip(*filtered_data)
                
                wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors, 
                                                autopct='%1.1f%%', startangle=90)
                
                # Create donut by adding a white circle in the center
                centre_circle = plt.Circle((0,0), 0.4, fc='white')
                ax.add_artist(centre_circle)
    
    def draw_matplotlib_bar(self, ax, data):
        """Draw bar chart with matplotlib"""
        datasets = data.get("datasets", [])
        labels = data.get("labels", [])
        
        if datasets:
            values = datasets[0].get("data", [])
            color = datasets[0].get("backgroundColor", "#4A90E2")
            
            bars = ax.bar(labels, values, color=color)
            ax.set_xlabel("Hour of Day")
            ax.set_ylabel("Activity Count")
            
            # Rotate x-axis labels if they're crowded
            if len(labels) > 10:
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

class MetricWidget(QWidget):
    """Widget for displaying a single metric"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", color: str = "#4A90E2", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.color = color
        self.init_ui()
    
    def init_ui(self):
        self.setFixedSize(150, 100)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                border-left: 4px solid {self.color};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 9))
        title_label.setStyleSheet("color: #666; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(self.value)
        value_label.setFont(QFont("Arial", 18, QFont.Bold))
        value_label.setStyleSheet(f"color: {self.color};")
        layout.addWidget(value_label)
        
        # Subtitle
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setFont(QFont("Arial", 8))
            subtitle_label.setStyleSheet("color: #999;")
            layout.addWidget(subtitle_label)
        
        self.setLayout(layout)

class InsightWidget(QWidget):
    """Widget for displaying insights and recommendations"""
    
    def __init__(self, insights: List[Dict], parent=None):
        super().__init__(parent)
        self.insights = insights
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("💡 AI Insights & Recommendations")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # Insights list
        for insight in self.insights[:5]:  # Show top 5 insights
            insight_frame = self.create_insight_frame(insight)
            layout.addWidget(insight_frame)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def create_insight_frame(self, insight: Dict) -> QFrame:
        """Create a frame for a single insight"""
        frame = QFrame()
        
        priority = insight.get("priority", "normal")
        priority_colors = {
            "urgent": "#FF6B6B",
            "high": "#FF9F40", 
            "medium": "#FFD93D",
            "low": "#6BCF7F"
        }
        
        color = priority_colors.get(priority, "#4A90E2")
        
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #ddd;
                border-left: 4px solid {color};
                border-radius: 4px;
                margin: 2px;
                padding: 8px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        
        # Title and priority
        header_layout = QHBoxLayout()
        
        title_label = QLabel(insight.get("title", "Insight"))
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(title_label)
        
        priority_label = QLabel(priority.upper())
        priority_label.setFont(QFont("Arial", 8, QFont.Bold))
        priority_label.setStyleSheet(f"color: {color}; background-color: {color}20; padding: 2px 6px; border-radius: 3px;")
        header_layout.addWidget(priority_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel(insight.get("description", ""))
        desc_label.setFont(QFont("Arial", 9))
        desc_label.setStyleSheet("color: #555;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Actions
        actions = insight.get("actions", [])
        if actions:
            actions_text = "Suggested actions: " + ", ".join(actions[:3])
            actions_label = QLabel(actions_text)
            actions_label.setFont(QFont("Arial", 8))
            actions_label.setStyleSheet("color: #777; font-style: italic;")
            actions_label.setWordWrap(True)
            layout.addWidget(actions_label)
        
        frame.setLayout(layout)
        return frame

class AlertWidget(QWidget):
    """Widget for displaying alerts"""
    
    def __init__(self, alerts: List[Dict], parent=None):
        super().__init__(parent)
        self.alerts = alerts
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("⚠️ Active Alerts")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        if not self.alerts:
            no_alerts_label = QLabel("✅ No active alerts")
            no_alerts_label.setFont(QFont("Arial", 10))
            no_alerts_label.setStyleSheet("color: #6BCF7F; font-style: italic;")
            layout.addWidget(no_alerts_label)
        else:
            # Alerts list
            for alert in self.alerts:
                alert_frame = self.create_alert_frame(alert)
                layout.addWidget(alert_frame)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def create_alert_frame(self, alert: Dict) -> QFrame:
        """Create a frame for a single alert"""
        frame = QFrame()
        
        severity = alert.get("severity", "info")
        severity_colors = {
            "critical": "#FF4444",
            "warning": "#FF9F40",
            "info": "#4A90E2"
        }
        
        color = severity_colors.get(severity, "#4A90E2")
        
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color}15;
                border: 1px solid {color};
                border-radius: 4px;
                margin: 2px;
                padding: 8px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        
        # Title and severity
        header_layout = QHBoxLayout()
        
        title_label = QLabel(alert.get("title", "Alert"))
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setStyleSheet(f"color: {color};")
        header_layout.addWidget(title_label)
        
        severity_label = QLabel(severity.upper())
        severity_label.setFont(QFont("Arial", 8, QFont.Bold))
        severity_label.setStyleSheet(f"color: white; background-color: {color}; padding: 2px 6px; border-radius: 3px;")
        header_layout.addWidget(severity_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Message
        message_label = QLabel(alert.get("message", ""))
        message_label.setFont(QFont("Arial", 9))
        message_label.setStyleSheet("color: #333;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        frame.setLayout(layout)
        return frame

class AnalyticsDashboard(QWidget):
    """Main analytics dashboard widget"""
    
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analytics_data = {}
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.refresh_data)
        self.init_ui()
        
        # Start auto-refresh every 5 minutes
        self.auto_refresh_timer.start(300000)  # 5 minutes
    
    def init_ui(self):
        """Initialize the dashboard UI"""
        self.setWindowTitle("AI Analytics Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 AI Analytics Dashboard")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        """)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        
        # Overview tab
        self.overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "📈 Overview")
        
        # Charts tab
        self.charts_tab = self.create_charts_tab()
        self.tab_widget.addTab(self.charts_tab, "📊 Charts")
        
        # Insights tab
        self.insights_tab = self.create_insights_tab()
        self.tab_widget.addTab(self.insights_tab, "💡 Insights")
        
        main_layout.addWidget(self.tab_widget)
        
        self.setLayout(main_layout)
        
        # Apply dark theme
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #4A90E2;
            }
        """)
    
    def create_overview_tab(self) -> QWidget:
        """Create the overview tab with key metrics"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Metrics section
        metrics_group = QGroupBox("Key Metrics")
        metrics_layout = QHBoxLayout()
        
        # Placeholder metrics - will be updated when data is loaded
        self.productivity_metric = MetricWidget("Productivity", "85%", "This week", "#6BCF7F")
        self.completion_metric = MetricWidget("Completion Rate", "72%", "Last 30 days", "#4A90E2")
        self.workload_metric = MetricWidget("Workload", "Medium", "Current intensity", "#FFD93D")
        self.overload_metric = MetricWidget("Overload Risk", "Low", "Risk level", "#6BCF7F")
        
        metrics_layout.addWidget(self.productivity_metric)
        metrics_layout.addWidget(self.completion_metric)
        metrics_layout.addWidget(self.workload_metric)
        metrics_layout.addWidget(self.overload_metric)
        metrics_layout.addStretch()
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # Split view for insights and alerts
        splitter = QSplitter(Qt.Horizontal)
        
        # Insights panel
        self.insights_panel = InsightWidget([])
        splitter.addWidget(self.insights_panel)
        
        # Alerts panel
        self.alerts_panel = AlertWidget([])
        splitter.addWidget(self.alerts_panel)
        
        splitter.setSizes([400, 300])
        layout.addWidget(splitter)
        
        widget.setLayout(layout)
        return widget
    
    def create_charts_tab(self) -> QWidget:
        """Create the charts tab with visualizations"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Charts grid
        charts_layout = QGridLayout()
        
        # Placeholder chart widgets - will be populated when data is loaded
        self.productivity_chart = None
        self.workload_chart = None
        self.time_chart = None
        
        layout.addLayout(charts_layout)
        widget.setLayout(layout)
        return widget
    
    def create_insights_tab(self) -> QWidget:
        """Create the insights tab with detailed analysis"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Detailed insights
        self.detailed_insights = QTextEdit()
        self.detailed_insights.setReadOnly(True)
        self.detailed_insights.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
            }
        """)
        
        layout.addWidget(QLabel("🔍 Detailed Analysis"))
        layout.addWidget(self.detailed_insights)
        
        widget.setLayout(layout)
        return widget
    
    def update_dashboard(self, analytics_data: Dict):
        """Update the dashboard with new analytics data"""
        self.analytics_data = analytics_data
        
        # Update metrics
        self.update_metrics(analytics_data.get("metrics", {}))
        
        # Update charts
        self.update_charts(analytics_data.get("charts", {}))
        
        # Update insights and alerts
        insights = analytics_data.get("insights", [])
        alerts = analytics_data.get("alerts", [])
        
        # Recreate insights and alerts panels
        self.insights_panel.insights = insights
        self.insights_panel.init_ui()
        
        self.alerts_panel.alerts = alerts
        self.alerts_panel.init_ui()
        
        # Update detailed insights
        self.update_detailed_insights(analytics_data)
    
    def update_metrics(self, metrics: Dict):
        """Update the metrics widgets"""
        productivity_score = metrics.get("productivity_score", 0)
        completion_rate = metrics.get("completion_rate", 0)
        workload_intensity = metrics.get("workload_intensity", "unknown")
        overload_risk = metrics.get("overload_risk", 0)
        
        # Update metric widgets
        self.productivity_metric.value = f"{productivity_score:.1f}%"
        self.completion_metric.value = f"{completion_rate:.1%}"
        self.workload_metric.value = workload_intensity.title()
        
        # Update overload risk
        risk_level = "Low" if overload_risk < 0.3 else "Medium" if overload_risk < 0.7 else "High"
        risk_color = "#6BCF7F" if overload_risk < 0.3 else "#FFD93D" if overload_risk < 0.7 else "#FF6B6B"
        self.overload_metric.value = risk_level
        self.overload_metric.color = risk_color
        
        # Force UI update
        for metric in [self.productivity_metric, self.completion_metric, self.workload_metric, self.overload_metric]:
            metric.init_ui()
    
    def update_charts(self, charts: Dict):
        """Update the charts"""
        # Clear existing charts
        charts_layout = self.charts_tab.layout().itemAt(0).layout()
        
        # Clear layout
        while charts_layout.count():
            child = charts_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add new charts
        row, col = 0, 0
        for chart_name, chart_data in charts.items():
            if chart_data:
                if MATPLOTLIB_AVAILABLE:
                    chart_widget = MatplotlibChartWidget(chart_data)
                else:
                    chart_widget = SimpleChartWidget(chart_data)
                
                charts_layout.addWidget(chart_widget, row, col)
                
                col += 1
                if col >= 2:  # 2 charts per row
                    col = 0
                    row += 1
    
    def update_detailed_insights(self, analytics_data: Dict):
        """Update the detailed insights text"""
        insights_text = "🔍 DETAILED ANALYTICS REPORT\n"
        insights_text += "=" * 50 + "\n\n"
        
        # Timestamp
        timestamp = analytics_data.get("timestamp", datetime.now().isoformat())
        insights_text += f"Generated: {timestamp}\n\n"
        
        # Productivity Status
        productivity = analytics_data.get("productivity_status", {})
        if productivity:
            insights_text += "📊 PRODUCTIVITY STATUS\n"
            insights_text += "-" * 25 + "\n"
            insights_text += f"Completion Rate: {productivity.get('completion_rate', 0):.1%}\n"
            insights_text += f"Total Tasks: {productivity.get('total_tasks', 0)}\n"
            insights_text += f"Completed: {productivity.get('completed_tasks', 0)}\n"
            insights_text += f"Pending: {productivity.get('pending_tasks', 0)}\n"
            insights_text += f"Overdue: {productivity.get('overdue_tasks', 0)}\n"
            insights_text += f"Productivity Zone: {productivity.get('productivity_zone', 'unknown').title()}\n"
            insights_text += f"Score: {productivity.get('score', 0)}/100\n\n"
        
        # Workload Analysis
        workload = analytics_data.get("workload_analysis", {})
        if workload:
            insights_text += "📋 WORKLOAD ANALYSIS\n"
            insights_text += "-" * 20 + "\n"
            insights_text += f"Total Pending: {workload.get('total_pending', 0)}\n"
            insights_text += f"Estimated Hours: {workload.get('estimated_hours', 0)}\n"
            insights_text += f"Intensity: {workload.get('workload_intensity', 'unknown').title()}\n"
            
            deadline_dist = workload.get('deadline_distribution', {})
            insights_text += f"Overdue: {deadline_dist.get('overdue', 0)}\n"
            insights_text += f"Due Today: {deadline_dist.get('today', 0)}\n"
            insights_text += f"Due This Week: {deadline_dist.get('this_week', 0)}\n"
            insights_text += f"Due Later: {deadline_dist.get('later', 0)}\n\n"
        
        # Recommendations
        recommendations = analytics_data.get("recommendations", [])
        if recommendations:
            insights_text += "💡 RECOMMENDATIONS\n"
            insights_text += "-" * 17 + "\n"
            for i, rec in enumerate(recommendations, 1):
                priority = rec.get('priority', 'normal').upper()
                title = rec.get('title', 'No title')
                description = rec.get('description', 'No description')
                insights_text += f"{i}. [{priority}] {title}\n"
                insights_text += f"   {description}\n\n"
        
        # Alerts
        alerts = analytics_data.get("alerts", [])
        if alerts:
            insights_text += "⚠️ ACTIVE ALERTS\n"
            insights_text += "-" * 15 + "\n"
            for i, alert in enumerate(alerts, 1):
                severity = alert.get('severity', 'info').upper()
                title = alert.get('title', 'No title')
                message = alert.get('message', 'No message')
                insights_text += f"{i}. [{severity}] {title}\n"
                insights_text += f"   {message}\n\n"
        
        self.detailed_insights.setText(insights_text)
    
    @pyqtSlot()
    def refresh_data(self):
        """Request fresh analytics data"""
        self.refresh_requested.emit()
    
    def show_dashboard(self):
        """Show the dashboard window"""
        self.show()
        self.raise_()
        self.activateWindow()

# Test the dashboard
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Sample analytics data for testing
    sample_data = {
        "charts": {
            "productivity_trend": {
                "type": "line",
                "title": "Productivity Trend (7 Days)",
                "data": {
                    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    "datasets": [{
                        "label": "Completion Rate",
                        "data": [85, 72, 90, 68, 82, 45, 30],
                        "borderColor": "#4A90E2"
                    }]
                }
            },
            "workload_distribution": {
                "type": "doughnut",
                "title": "Task Distribution",
                "data": {
                    "labels": ["Overdue", "Today", "This Week", "Later"],
                    "datasets": [{
                        "data": [3, 5, 8, 12],
                        "backgroundColor": ["#FF6B6B", "#FFD93D", "#6BCF7F", "#4A90E2"]
                    }]
                }
            }
        },
        "metrics": {
            "productivity_score": 78.5,
            "completion_rate": 0.72,
            "workload_intensity": "medium",
            "overload_risk": 0.35
        },
        "insights": [
            {
                "type": "productivity_improvement",
                "priority": "high",
                "title": "Focus Sessions Recommended",
                "description": "Your completion rate has dropped. Consider using focus mode.",
                "actions": ["start_focus_mode", "break_large_tasks"]
            }
        ],
        "alerts": [
            {
                "type": "deadline_warning",
                "severity": "warning",
                "title": "Approaching Deadlines",
                "message": "You have 5 tasks due today that need attention."
            }
        ]
    }
    
    dashboard = AnalyticsDashboard()
    dashboard.update_dashboard(sample_data)
    dashboard.show()
    
    sys.exit(app.exec_())