import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class DataSourceWidget(QWidget):
    """Widget for managing a single data source"""
    
    source_changed = pyqtSignal(str, dict)  # source_id, config
    source_removed = pyqtSignal(str)  # source_id
    test_requested = pyqtSignal(str)  # source_id
    
    def __init__(self, source_id: str, source_data: Dict, parent=None):
        super().__init__(parent)
        self.source_id = source_id
        self.source_data = source_data
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header with name and status
        header_layout = QHBoxLayout()
        
        # Source name and type
        name_label = QLabel(f"<b>{self.source_data.get('name', 'Unknown')}</b>")
        name_label.setStyleSheet("font-size: 14px; color: #2c3e50;")
        header_layout.addWidget(name_label)
        
        # Source type badge
        type_badge = QLabel(self.source_data.get('type', 'unknown'))
        type_badge.setStyleSheet("""
            background-color: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
        """)
        type_badge.setFixedHeight(20)
        header_layout.addWidget(type_badge)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_indicator = QLabel("●")
        if self.source_data.get('active', True):
            self.status_indicator.setStyleSheet("color: #27ae60; font-size: 16px;")
            self.status_indicator.setToolTip("Active")
        else:
            self.status_indicator.setStyleSheet("color: #e74c3c; font-size: 16px;")
            self.status_indicator.setToolTip("Inactive")
        header_layout.addWidget(self.status_indicator)
        
        layout.addLayout(header_layout)
        
        # Configuration form
        self.config_widget = self.create_config_widget()
        layout.addWidget(self.config_widget)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(self.source_data.get('active', True))
        self.active_checkbox.stateChanged.connect(self.on_active_changed)
        button_layout.addWidget(self.active_checkbox)
        
        button_layout.addStretch()
        
        test_btn = QPushButton("Test Connection")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        test_btn.clicked.connect(lambda: self.test_requested.emit(self.source_id))
        button_layout.addWidget(test_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        remove_btn.clicked.connect(lambda: self.source_removed.emit(self.source_id))
        button_layout.addWidget(remove_btn)
        
        layout.addLayout(button_layout)
        
        # Main widget styling
        self.setLayout(layout)
        self.setStyleSheet("""
            DataSourceWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        self.setFixedHeight(200)
    
    def create_config_widget(self) -> QWidget:
        """Create configuration widget based on source type"""
        widget = QWidget()
        layout = QFormLayout()
        
        source_type = self.source_data.get('type', '')
        config = self.source_data.get('config', {})
        
        self.config_fields = {}
        
        if source_type == 'json_folder':
            # Folder path
            folder_layout = QHBoxLayout()
            self.config_fields['folder_path'] = QLineEdit(config.get('folder_path', ''))
            folder_layout.addWidget(self.config_fields['folder_path'])
            
            browse_btn = QPushButton("Browse")
            browse_btn.clicked.connect(self.browse_folder)
            folder_layout.addWidget(browse_btn)
            
            layout.addRow("Folder Path:", folder_layout)
            
            # File pattern
            self.config_fields['file_pattern'] = QLineEdit(config.get('file_pattern', '*.json'))
            layout.addRow("File Pattern:", self.config_fields['file_pattern'])
            
            # Recursive checkbox
            self.config_fields['recursive'] = QCheckBox()
            self.config_fields['recursive'].setChecked(config.get('recursive', False))
            layout.addRow("Recursive:", self.config_fields['recursive'])
            
        elif source_type == 'sqlite':
            # Database path
            db_layout = QHBoxLayout()
            self.config_fields['database_path'] = QLineEdit(config.get('database_path', ''))
            db_layout.addWidget(self.config_fields['database_path'])
            
            browse_btn = QPushButton("Browse")
            browse_btn.clicked.connect(self.browse_file)
            db_layout.addWidget(browse_btn)
            
            layout.addRow("Database Path:", db_layout)
            
        elif source_type in ['mysql', 'postgresql']:
            # Host
            self.config_fields['host'] = QLineEdit(config.get('host', 'localhost'))
            layout.addRow("Host:", self.config_fields['host'])
            
            # Port
            port_value = str(config.get('port', 3306 if source_type == 'mysql' else 5432))
            self.config_fields['port'] = QLineEdit(port_value)
            layout.addRow("Port:", self.config_fields['port'])
            
            # Database
            self.config_fields['database'] = QLineEdit(config.get('database', ''))
            layout.addRow("Database:", self.config_fields['database'])
            
            # Username
            self.config_fields['username'] = QLineEdit(config.get('username', ''))
            layout.addRow("Username:", self.config_fields['username'])
            
            # Password
            self.config_fields['password'] = QLineEdit(config.get('password', ''))
            self.config_fields['password'].setEchoMode(QLineEdit.Password)
            layout.addRow("Password:", self.config_fields['password'])
            
        elif source_type == 'mongodb':
            # Host
            self.config_fields['host'] = QLineEdit(config.get('host', 'localhost'))
            layout.addRow("Host:", self.config_fields['host'])
            
            # Port
            self.config_fields['port'] = QLineEdit(str(config.get('port', 27017)))
            layout.addRow("Port:", self.config_fields['port'])
            
            # Database
            self.config_fields['database'] = QLineEdit(config.get('database', ''))
            layout.addRow("Database:", self.config_fields['database'])
            
            # Username (optional)
            self.config_fields['username'] = QLineEdit(config.get('username', ''))
            layout.addRow("Username:", self.config_fields['username'])
            
            # Password (optional)
            self.config_fields['password'] = QLineEdit(config.get('password', ''))
            self.config_fields['password'].setEchoMode(QLineEdit.Password)
            layout.addRow("Password:", self.config_fields['password'])
            
        elif source_type == 'clickup_api':
            # API Key
            self.config_fields['api_key'] = QLineEdit(config.get('api_key', ''))
            self.config_fields['api_key'].setEchoMode(QLineEdit.Password)
            layout.addRow("API Key:", self.config_fields['api_key'])
            
            # Team ID (optional)
            self.config_fields['team_id'] = QLineEdit(config.get('team_id', ''))
            layout.addRow("Team ID:", self.config_fields['team_id'])
        
        # Connect all fields to change handler
        for field in self.config_fields.values():
            if isinstance(field, QLineEdit):
                field.textChanged.connect(self.on_config_changed)
            elif isinstance(field, QCheckBox):
                field.stateChanged.connect(self.on_config_changed)
        
        widget.setLayout(layout)
        return widget
    
    def browse_folder(self):
        """Browse for folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.config_fields['folder_path'].setText(folder)
    
    def browse_file(self):
        """Browse for file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Database File", "", "SQLite Files (*.db *.sqlite)")
        if file_path:
            self.config_fields['database_path'].setText(file_path)
    
    def on_active_changed(self):
        """Handle active state change"""
        self.source_data['active'] = self.active_checkbox.isChecked()
        
        if self.source_data['active']:
            self.status_indicator.setStyleSheet("color: #27ae60; font-size: 16px;")
            self.status_indicator.setToolTip("Active")
        else:
            self.status_indicator.setStyleSheet("color: #e74c3c; font-size: 16px;")
            self.status_indicator.setToolTip("Inactive")
        
        self.on_config_changed()
    
    def on_config_changed(self):
        """Handle configuration change"""
        config = {}
        
        for key, field in self.config_fields.items():
            if isinstance(field, QLineEdit):
                value = field.text()
                # Convert port to int if it's a port field
                if key == 'port' and value.isdigit():
                    value = int(value)
                config[key] = value
            elif isinstance(field, QCheckBox):
                config[key] = field.isChecked()
        
        self.source_data['config'] = config
        self.source_changed.emit(self.source_id, self.source_data)
    
    def get_config(self) -> Dict:
        """Get current configuration"""
        return self.source_data

class AddDataSourceDialog(QDialog):
    """Dialog for adding new data sources"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Data Source")
        self.setModal(True)
        self.setFixedSize(500, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Source type selection
        type_layout = QFormLayout()
        self.source_type = QComboBox()
        self.source_type.addItems([
            "json_folder",
            "sqlite", 
            "mysql",
            "postgresql",
            "mongodb",
            "clickup_api"
        ])
        self.source_type.currentTextChanged.connect(self.on_type_changed)
        type_layout.addRow("Source Type:", self.source_type)
        
        # Source name
        self.source_name = QLineEdit()
        self.source_name.setPlaceholderText("Enter a descriptive name")
        type_layout.addRow("Name:", self.source_name)
        
        layout.addLayout(type_layout)
        
        # Configuration area
        self.config_area = QScrollArea()
        self.config_widget = QWidget()
        self.config_layout = QFormLayout()
        self.config_widget.setLayout(self.config_layout)
        self.config_area.setWidget(self.config_widget)
        self.config_area.setWidgetResizable(True)
        layout.addWidget(self.config_area)
        
        # Initialize with first type
        self.on_type_changed("json_folder")
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(test_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("Add Source")
        add_btn.clicked.connect(self.accept)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def on_type_changed(self, source_type: str):
        """Handle source type change"""
        # Clear existing configuration
        for i in reversed(range(self.config_layout.count())):
            self.config_layout.itemAt(i).widget().setParent(None)
        
        self.config_fields = {}
        
        if source_type == 'json_folder':
            # Folder path
            folder_layout = QHBoxLayout()
            self.config_fields['folder_path'] = QLineEdit()
            self.config_fields['folder_path'].setPlaceholderText("/path/to/json/files")
            folder_layout.addWidget(self.config_fields['folder_path'])
            
            browse_btn = QPushButton("Browse")
            browse_btn.clicked.connect(self.browse_folder)
            folder_layout.addWidget(browse_btn)
            
            folder_widget = QWidget()
            folder_widget.setLayout(folder_layout)
            self.config_layout.addRow("Folder Path:", folder_widget)
            
            # File pattern
            self.config_fields['file_pattern'] = QLineEdit("*.json")
            self.config_layout.addRow("File Pattern:", self.config_fields['file_pattern'])
            
            # Recursive
            self.config_fields['recursive'] = QCheckBox()
            self.config_layout.addRow("Scan Subfolders:", self.config_fields['recursive'])
            
        elif source_type == 'sqlite':
            # Database path
            db_layout = QHBoxLayout()
            self.config_fields['database_path'] = QLineEdit()
            self.config_fields['database_path'].setPlaceholderText("/path/to/database.db")
            db_layout.addWidget(self.config_fields['database_path'])
            
            browse_btn = QPushButton("Browse")
            browse_btn.clicked.connect(self.browse_file)
            db_layout.addWidget(browse_btn)
            
            db_widget = QWidget()
            db_widget.setLayout(db_layout)
            self.config_layout.addRow("Database Path:", db_widget)
            
        elif source_type in ['mysql', 'postgresql']:
            # Host
            self.config_fields['host'] = QLineEdit("localhost")
            self.config_layout.addRow("Host:", self.config_fields['host'])
            
            # Port
            default_port = "3306" if source_type == 'mysql' else "5432"
            self.config_fields['port'] = QLineEdit(default_port)
            self.config_layout.addRow("Port:", self.config_fields['port'])
            
            # Database
            self.config_fields['database'] = QLineEdit()
            self.config_fields['database'].setPlaceholderText("database_name")
            self.config_layout.addRow("Database:", self.config_fields['database'])
            
            # Username
            self.config_fields['username'] = QLineEdit()
            self.config_fields['username'].setPlaceholderText("username")
            self.config_layout.addRow("Username:", self.config_fields['username'])
            
            # Password
            self.config_fields['password'] = QLineEdit()
            self.config_fields['password'].setEchoMode(QLineEdit.Password)
            self.config_fields['password'].setPlaceholderText("password")
            self.config_layout.addRow("Password:", self.config_fields['password'])
            
        elif source_type == 'mongodb':
            # Host
            self.config_fields['host'] = QLineEdit("localhost")
            self.config_layout.addRow("Host:", self.config_fields['host'])
            
            # Port
            self.config_fields['port'] = QLineEdit("27017")
            self.config_layout.addRow("Port:", self.config_fields['port'])
            
            # Database
            self.config_fields['database'] = QLineEdit()
            self.config_fields['database'].setPlaceholderText("database_name")
            self.config_layout.addRow("Database:", self.config_fields['database'])
            
            # Username (optional)
            self.config_fields['username'] = QLineEdit()
            self.config_fields['username'].setPlaceholderText("username (optional)")
            self.config_layout.addRow("Username:", self.config_fields['username'])
            
            # Password (optional)
            self.config_fields['password'] = QLineEdit()
            self.config_fields['password'].setEchoMode(QLineEdit.Password)
            self.config_fields['password'].setPlaceholderText("password (optional)")
            self.config_layout.addRow("Password:", self.config_fields['password'])
            
        elif source_type == 'clickup_api':
            # API Key
            self.config_fields['api_key'] = QLineEdit()
            self.config_fields['api_key'].setEchoMode(QLineEdit.Password)
            self.config_fields['api_key'].setPlaceholderText("Your ClickUp API key")
            self.config_layout.addRow("API Key:", self.config_fields['api_key'])
            
            # Team ID
            self.config_fields['team_id'] = QLineEdit()
            self.config_fields['team_id'].setPlaceholderText("Team ID (optional)")
            self.config_layout.addRow("Team ID:", self.config_fields['team_id'])
    
    def browse_folder(self):
        """Browse for folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.config_fields['folder_path'].setText(folder)
    
    def browse_file(self):
        """Browse for file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Database File", "", "SQLite Files (*.db *.sqlite)")
        if file_path:
            self.config_fields['database_path'].setText(file_path)
    
    def test_connection(self):
        """Test the connection with current settings"""
        # Get configuration
        config = self.get_config()
        
        if not config:
            QMessageBox.warning(self, "Warning", "Please fill in the required fields.")
            return
        
        # Show testing dialog
        QMessageBox.information(self, "Test Connection", "Connection test would be performed here.\nThis is a mock implementation.")
    
    def get_config(self) -> Optional[Dict]:
        """Get the current configuration"""
        source_type = self.source_type.currentText()
        name = self.source_name.text().strip()
        
        if not name:
            return None
        
        config = {}
        
        for key, field in self.config_fields.items():
            if isinstance(field, QLineEdit):
                value = field.text().strip()
                if key == 'port' and value.isdigit():
                    value = int(value)
                config[key] = value
            elif isinstance(field, QCheckBox):
                config[key] = field.isChecked()
        
        return {
            "type": source_type,
            "name": name,
            "config": config,
            "active": True
        }

class SettingsDashboard(QMainWindow):
    """Comprehensive settings dashboard for AI Avatar Assistant"""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, data_source_manager, parent=None):
        super().__init__(parent)
        self.data_source_manager = data_source_manager
        self.setWindowTitle("AI Avatar Assistant - Settings")
        self.setFixedSize(1000, 700)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        central_widget_layout = QVBoxLayout()
        central_widget_layout.addWidget(self.tab_widget)
        central_widget.setLayout(central_widget_layout)
        
        # Create tabs
        self.create_data_sources_tab()
        self.create_ai_settings_tab()
        self.create_system_settings_tab()
        self.create_about_tab()
        
        # Apply styles
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e8e8e8;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #3498db;
            }
        """)
    
    def create_data_sources_tab(self):
        """Create data sources management tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Data Sources")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin: 10px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add data source button
        add_btn = QPushButton("+ Add Data Source")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        add_btn.clicked.connect(self.add_data_source)
        header_layout.addWidget(add_btn)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Sync All")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        refresh_btn.clicked.connect(self.sync_all_sources)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Data sources list
        self.sources_scroll = QScrollArea()
        self.sources_widget = QWidget()
        self.sources_layout = QVBoxLayout()
        self.sources_widget.setLayout(self.sources_layout)
        self.sources_scroll.setWidget(self.sources_widget)
        self.sources_scroll.setWidgetResizable(True)
        layout.addWidget(self.sources_scroll)
        
        # Status bar
        self.sources_status = QLabel("No data sources configured")
        self.sources_status.setStyleSheet("color: #7f8c8d; font-style: italic; margin: 10px;")
        layout.addWidget(self.sources_status)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Data Sources")
    
    def create_ai_settings_tab(self):
        """Create AI assistant settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Header
        title = QLabel("AI Assistant Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin: 10px;")
        layout.addWidget(title)
        
        # Settings form
        form_layout = QFormLayout()
        
        # Project estimation settings
        estimation_group = QGroupBox("Project Estimation")
        estimation_layout = QFormLayout()
        
        self.auto_estimation = QCheckBox("Enable automatic project estimation")
        self.auto_estimation.setChecked(True)
        estimation_layout.addRow("Auto Estimation:", self.auto_estimation)
        
        self.estimation_confidence = QSlider(Qt.Horizontal)
        self.estimation_confidence.setRange(50, 95)
        self.estimation_confidence.setValue(80)
        confidence_label = QLabel("80%")
        self.estimation_confidence.valueChanged.connect(lambda v: confidence_label.setText(f"{v}%"))
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(self.estimation_confidence)
        confidence_layout.addWidget(confidence_label)
        confidence_widget = QWidget()
        confidence_widget.setLayout(confidence_layout)
        estimation_layout.addRow("Min Confidence:", confidence_widget)
        
        self.use_historical_data = QCheckBox("Use historical project data for estimates")
        self.use_historical_data.setChecked(True)
        estimation_layout.addRow("Historical Data:", self.use_historical_data)
        
        estimation_group.setLayout(estimation_layout)
        layout.addWidget(estimation_group)
        
        # Team recommendation settings
        team_group = QGroupBox("Team Recommendations")
        team_layout = QFormLayout()
        
        self.auto_team_matching = QCheckBox("Enable automatic team member matching")
        self.auto_team_matching.setChecked(True)
        team_layout.addRow("Auto Matching:", self.auto_team_matching)
        
        self.skill_weight = QSlider(Qt.Horizontal)
        self.skill_weight.setRange(10, 90)
        self.skill_weight.setValue(60)
        skill_label = QLabel("60%")
        self.skill_weight.valueChanged.connect(lambda v: skill_label.setText(f"{v}%"))
        skill_layout = QHBoxLayout()
        skill_layout.addWidget(self.skill_weight)
        skill_layout.addWidget(skill_label)
        skill_widget = QWidget()
        skill_widget.setLayout(skill_layout)
        team_layout.addRow("Skill Weight:", skill_widget)
        
        self.consider_availability = QCheckBox("Consider team member availability")
        self.consider_availability.setChecked(True)
        team_layout.addRow("Check Availability:", self.consider_availability)
        
        team_group.setLayout(team_layout)
        layout.addWidget(team_group)
        
        # ClickUp integration settings
        clickup_group = QGroupBox("ClickUp Integration")
        clickup_layout = QFormLayout()
        
        self.clickup_enabled = QCheckBox("Enable ClickUp integration")
        clickup_layout.addRow("Enable:", self.clickup_enabled)
        
        self.clickup_api_key = QLineEdit()
        self.clickup_api_key.setEchoMode(QLineEdit.Password)
        self.clickup_api_key.setPlaceholderText("Enter your ClickUp API key")
        clickup_layout.addRow("API Key:", self.clickup_api_key)
        
        self.clickup_team_id = QLineEdit()
        self.clickup_team_id.setPlaceholderText("Enter your team ID")
        clickup_layout.addRow("Team ID:", self.clickup_team_id)
        
        self.clickup_sync_interval = QSpinBox()
        self.clickup_sync_interval.setRange(5, 120)
        self.clickup_sync_interval.setValue(30)
        self.clickup_sync_interval.setSuffix(" minutes")
        clickup_layout.addRow("Sync Interval:", self.clickup_sync_interval)
        
        clickup_group.setLayout(clickup_layout)
        layout.addWidget(clickup_group)
        
        layout.addStretch()
        
        # Save button
        save_btn = QPushButton("Save AI Settings")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        save_btn.clicked.connect(self.save_ai_settings)
        layout.addWidget(save_btn)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "AI Settings")
    
    def create_system_settings_tab(self):
        """Create system settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Header
        title = QLabel("System Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin: 10px;")
        layout.addWidget(title)
        
        # General settings
        general_group = QGroupBox("General")
        general_layout = QFormLayout()
        
        self.auto_start = QCheckBox("Start with system")
        general_layout.addRow("Auto Start:", self.auto_start)
        
        self.minimize_to_tray = QCheckBox("Minimize to system tray")
        self.minimize_to_tray.setChecked(True)
        general_layout.addRow("System Tray:", self.minimize_to_tray)
        
        self.show_notifications = QCheckBox("Show desktop notifications")
        self.show_notifications.setChecked(True)
        general_layout.addRow("Notifications:", self.show_notifications)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Data management settings
        data_group = QGroupBox("Data Management")
        data_layout = QFormLayout()
        
        self.cache_duration = QSpinBox()
        self.cache_duration.setRange(60, 3600)
        self.cache_duration.setValue(300)
        self.cache_duration.setSuffix(" seconds")
        data_layout.addRow("Cache Duration:", self.cache_duration)
        
        self.auto_sync_interval = QSpinBox()
        self.auto_sync_interval.setRange(10, 120)
        self.auto_sync_interval.setValue(30)
        self.auto_sync_interval.setSuffix(" minutes")
        data_layout.addRow("Auto Sync Interval:", self.auto_sync_interval)
        
        self.max_log_files = QSpinBox()
        self.max_log_files.setRange(1, 20)
        self.max_log_files.setValue(5)
        data_layout.addRow("Max Log Files:", self.max_log_files)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Export/Import settings
        export_group = QGroupBox("Data Export/Import")
        export_layout = QVBoxLayout()
        
        export_btn_layout = QHBoxLayout()
        
        export_config_btn = QPushButton("Export Configuration")
        export_config_btn.clicked.connect(self.export_configuration)
        export_btn_layout.addWidget(export_config_btn)
        
        import_config_btn = QPushButton("Import Configuration")
        import_config_btn.clicked.connect(self.import_configuration)
        export_btn_layout.addWidget(import_config_btn)
        
        export_data_btn = QPushButton("Export All Data")
        export_data_btn.clicked.connect(self.export_all_data)
        export_btn_layout.addWidget(export_data_btn)
        
        export_layout.addLayout(export_btn_layout)
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        
        # Save button
        save_btn = QPushButton("Save System Settings")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        save_btn.clicked.connect(self.save_system_settings)
        layout.addWidget(save_btn)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "System")
    
    def create_about_tab(self):
        """Create about tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Logo and title
        title_layout = QHBoxLayout()
        title_layout.addStretch()
        
        title_label = QLabel("AI Avatar Assistant")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin: 20px;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Version and info
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)
        
        version_label = QLabel("Version 1.0.0")
        version_label.setStyleSheet("font-size: 16px; color: #7f8c8d; margin: 10px;")
        version_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(version_label)
        
        description = QLabel("""
        An intelligent AI assistant with dynamic tooltips, project estimation,
        team recommendations, and comprehensive data source management.
        
        Features:
        • Real-time analytics and insights
        • Project estimation with difficulty analysis
        • Team member recommendations
        • Multiple data source integration
        • Voice notifications and reporting
        • ClickUp API integration
        """)
        description.setStyleSheet("""
            font-size: 14px;
            color: #34495e;
            margin: 20px;
            line-height: 1.5;
        """)
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(description)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Status information
        status_group = QGroupBox("System Status")
        status_layout = QFormLayout()
        
        # Data sources status
        status = self.data_source_manager.get_data_source_status()
        sources_status = f"{status['active_sources']}/{status['total_sources']} active"
        status_layout.addRow("Data Sources:", QLabel(sources_status))
        
        # Last sync
        last_sync = status.get('last_sync')
        if last_sync:
            last_sync_str = last_sync.strftime('%Y-%m-%d %H:%M:%S') if hasattr(last_sync, 'strftime') else str(last_sync)
        else:
            last_sync_str = "Never"
        status_layout.addRow("Last Sync:", QLabel(last_sync_str))
        
        # Data counts
        unified_cache = self.data_source_manager.unified_cache
        projects_count = len(unified_cache.get('projects', []))
        tasks_count = len(unified_cache.get('tasks', []))
        members_count = len(unified_cache.get('team_members', []))
        
        status_layout.addRow("Projects:", QLabel(str(projects_count)))
        status_layout.addRow("Tasks:", QLabel(str(tasks_count)))
        status_layout.addRow("Team Members:", QLabel(str(members_count)))
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "About")
    
    def load_settings(self):
        """Load existing settings"""
        self.refresh_data_sources()
        
        # Load other settings from config files or data manager
        # This would typically load from a settings file
    
    def refresh_data_sources(self):
        """Refresh the data sources list"""
        # Clear existing widgets
        for i in reversed(range(self.sources_layout.count())):
            item = self.sources_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        # Add data source widgets
        sources = self.data_source_manager.data_sources
        
        if not sources:
            no_sources_label = QLabel("No data sources configured. Click 'Add Data Source' to get started.")
            no_sources_label.setStyleSheet("""
                color: #7f8c8d;
                font-style: italic;
                padding: 20px;
                text-align: center;
            """)
            no_sources_label.setAlignment(Qt.AlignCenter)
            self.sources_layout.addWidget(no_sources_label)
        else:
            for source_id, source_data in sources.items():
                widget = DataSourceWidget(source_id, source_data.__dict__)
                widget.source_changed.connect(self.on_source_changed)
                widget.source_removed.connect(self.on_source_removed)
                widget.test_requested.connect(self.on_test_source)
                self.sources_layout.addWidget(widget)
        
        self.sources_layout.addStretch()
        
        # Update status
        status = self.data_source_manager.get_data_source_status()
        self.sources_status.setText(f"{status['active_sources']} active out of {status['total_sources']} sources")
    
    def add_data_source(self):
        """Add a new data source"""
        dialog = AddDataSourceDialog(self)
        
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_config()
            if config:
                try:
                    source_id = self.data_source_manager.add_data_source(
                        config['type'],
                        config['name'],
                        config['config']
                    )
                    
                    QMessageBox.information(self, "Success", f"Data source '{config['name']}' added successfully!")
                    self.refresh_data_sources()
                    
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add data source:\n{str(e)}")
    
    def on_source_changed(self, source_id: str, config: Dict):
        """Handle data source configuration change"""
        if source_id in self.data_source_manager.data_sources:
            source = self.data_source_manager.data_sources[source_id]
            source.name = config.get('name', source.name)
            source.config = config.get('config', source.config)
            source.is_active = config.get('active', source.is_active)
            
            self.data_source_manager.save_configuration()
    
    def on_source_removed(self, source_id: str):
        """Handle data source removal"""
        reply = QMessageBox.question(
            self, 
            "Remove Data Source", 
            "Are you sure you want to remove this data source?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.data_source_manager.remove_data_source(source_id)
            self.refresh_data_sources()
    
    def on_test_source(self, source_id: str):
        """Test a data source connection"""
        if source_id in self.data_source_manager.data_sources:
            source = self.data_source_manager.data_sources[source_id]
            
            if self.data_source_manager.test_connection(source):
                QMessageBox.information(self, "Test Successful", f"Connection to '{source.name}' successful!")
            else:
                QMessageBox.warning(self, "Test Failed", f"Failed to connect to '{source.name}'.")
    
    def sync_all_sources(self):
        """Sync all data sources"""
        try:
            self.data_source_manager.sync_all_sources()
            QMessageBox.information(self, "Sync Complete", "All data sources have been synchronized.")
            self.refresh_data_sources()
        except Exception as e:
            QMessageBox.critical(self, "Sync Error", f"Failed to sync data sources:\n{str(e)}")
    
    def save_ai_settings(self):
        """Save AI assistant settings"""
        settings = {
            "estimation": {
                "auto_estimation": self.auto_estimation.isChecked(),
                "min_confidence": self.estimation_confidence.value() / 100,
                "use_historical_data": self.use_historical_data.isChecked()
            },
            "team_recommendations": {
                "auto_matching": self.auto_team_matching.isChecked(),
                "skill_weight": self.skill_weight.value() / 100,
                "consider_availability": self.consider_availability.isChecked()
            },
            "clickup": {
                "enabled": self.clickup_enabled.isChecked(),
                "api_key": self.clickup_api_key.text(),
                "team_id": self.clickup_team_id.text(),
                "sync_interval": self.clickup_sync_interval.value()
            }
        }
        
        # Save settings (this would typically be saved to a file)
        self.settings_changed.emit(settings)
        QMessageBox.information(self, "Settings Saved", "AI settings have been saved successfully.")
    
    def save_system_settings(self):
        """Save system settings"""
        settings = {
            "general": {
                "auto_start": self.auto_start.isChecked(),
                "minimize_to_tray": self.minimize_to_tray.isChecked(),
                "show_notifications": self.show_notifications.isChecked()
            },
            "data": {
                "cache_duration": self.cache_duration.value(),
                "auto_sync_interval": self.auto_sync_interval.value(),
                "max_log_files": self.max_log_files.value()
            }
        }
        
        # Update data source manager settings
        self.data_source_manager.watch_interval = self.auto_sync_interval.value() * 60  # Convert to seconds
        self.data_source_manager.save_configuration()
        
        self.settings_changed.emit(settings)
        QMessageBox.information(self, "Settings Saved", "System settings have been saved successfully.")
    
    def export_configuration(self):
        """Export configuration to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Configuration", 
            f"ai_assistant_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                # Export data source configuration
                self.data_source_manager.save_configuration()
                
                with open(self.data_source_manager.config_path, 'r') as f:
                    config = json.load(f)
                
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                QMessageBox.information(self, "Export Successful", f"Configuration exported to:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export configuration:\n{str(e)}")
    
    def import_configuration(self):
        """Import configuration from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Import Configuration", 
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                # Backup current configuration
                backup_path = f"{self.data_source_manager.config_path}.backup"
                self.data_source_manager.save_configuration()
                
                import shutil
                shutil.copy(self.data_source_manager.config_path, backup_path)
                
                # Import new configuration
                with open(self.data_source_manager.config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                # Reload configuration
                self.data_source_manager.load_configuration()
                self.refresh_data_sources()
                
                QMessageBox.information(self, "Import Successful", "Configuration imported successfully!\nPrevious configuration backed up.")
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import configuration:\n{str(e)}")
    
    def export_all_data(self):
        """Export all unified data"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export All Data", 
            f"ai_assistant_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                self.data_source_manager.export_unified_data(file_path)
                QMessageBox.information(self, "Export Successful", f"All data exported to:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data:\n{str(e)}")

# Test the settings dashboard
if __name__ == "__main__":
    import sys
    from ai_avatar_assistant.core.data_source_manager import DataSourceManager
    
    app = QApplication(sys.argv)
    
    # Create mock data source manager
    data_manager = DataSourceManager("test_sources.json")
    
    # Create and show settings dashboard
    dashboard = SettingsDashboard(data_manager)
    dashboard.show()
    
    sys.exit(app.exec_())