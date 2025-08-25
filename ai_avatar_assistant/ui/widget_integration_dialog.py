import os
import json
import pyperclip
from typing import Dict, Optional
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class WidgetIntegrationDialog(QDialog):
    """Dialog for managing AI Avatar Assistant widget integrations"""
    
    integration_created = pyqtSignal(dict)  # Emitted when new integration is created
    
    def __init__(self, widget_integration_manager, parent=None):
        super().__init__(parent)
        self.widget_manager = widget_integration_manager
        self.setWindowTitle("Widget Integration Manager")
        self.setModal(True)
        self.setFixedSize(800, 700)
        
        # Current integration data
        self.current_integration = None
        
        self.init_ui()
        self.load_existing_integrations()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Widget Integration Manager")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin: 10px 0;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Server status
        self.status_label = QLabel("Server Status: Unknown")
        self.status_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.create_new_integration_tab()
        self.create_existing_integrations_tab()
        self.create_testing_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Update server status
        self.update_server_status()
        
        self.setLayout(layout)
    
    def create_new_integration_tab(self):
        """Create the new integration tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Introduction
        intro_text = QLabel("""
Create a new widget integration to embed the AI Avatar Assistant in your external dashboard.
The widget provides full orchestration capabilities including project estimation, team recommendations,
analytics, and conversational AI - all accessible through a secure API.
        """)
        intro_text.setWordWrap(True)
        intro_text.setStyleSheet("color: #34495e; margin: 10px 0; line-height: 1.4;")
        layout.addWidget(intro_text)
        
        # Configuration form
        form_group = QGroupBox("Integration Configuration")
        form_layout = QFormLayout()
        
        # Client name
        self.client_name = QLineEdit()
        self.client_name.setPlaceholderText("e.g., ClickUp Dashboard, Project Manager")
        form_layout.addRow("Client Name:", self.client_name)
        
        # Domain
        self.domain = QLineEdit()
        self.domain.setPlaceholderText("e.g., dashboard.example.com, localhost")
        form_layout.addRow("Domain:", self.domain)
        
        # Widget URL
        self.widget_url = QLineEdit()
        self.widget_url.setPlaceholderText("e.g., https://dashboard.example.com/ai-assistant")
        form_layout.addRow("Widget URL:", self.widget_url)
        
        # Widget configuration
        config_group = QGroupBox("Widget Settings")
        config_layout = QFormLayout()
        
        # Widget dimensions
        dimensions_layout = QHBoxLayout()
        
        self.widget_width = QLineEdit("400px")
        self.widget_width.setFixedWidth(100)
        dimensions_layout.addWidget(QLabel("Width:"))
        dimensions_layout.addWidget(self.widget_width)
        
        dimensions_layout.addWidget(QLabel("Height:"))
        self.widget_height = QLineEdit("500px")
        self.widget_height.setFixedWidth(100)
        dimensions_layout.addWidget(self.widget_height)
        
        dimensions_layout.addStretch()
        
        dimensions_widget = QWidget()
        dimensions_widget.setLayout(dimensions_layout)
        config_layout.addRow("Dimensions:", dimensions_widget)
        
        # Permissions
        permissions_layout = QVBoxLayout()
        
        self.perm_chat = QCheckBox("Chat & Conversation")
        self.perm_chat.setChecked(True)
        permissions_layout.addWidget(self.perm_chat)
        
        self.perm_estimate = QCheckBox("Project Estimation")
        self.perm_estimate.setChecked(True)
        permissions_layout.addWidget(self.perm_estimate)
        
        self.perm_analytics = QCheckBox("Analytics & Reporting")
        self.perm_analytics.setChecked(True)
        permissions_layout.addWidget(self.perm_analytics)
        
        self.perm_team = QCheckBox("Team Data Access")
        self.perm_team.setChecked(True)
        permissions_layout.addWidget(self.perm_team)
        
        permissions_widget = QWidget()
        permissions_widget.setLayout(permissions_layout)
        config_layout.addRow("Permissions:", permissions_widget)
        
        config_group.setLayout(config_layout)
        form_layout.addRow(config_group)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Generate button
        generate_btn = QPushButton("🚀 Generate Widget Integration")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        generate_btn.clicked.connect(self.generate_integration)
        layout.addWidget(generate_btn)
        
        # Result area
        self.result_group = QGroupBox("Integration Code")
        self.result_group.setVisible(False)
        result_layout = QVBoxLayout()
        
        # API details
        api_details_layout = QFormLayout()
        
        self.api_key_display = QLineEdit()
        self.api_key_display.setReadOnly(True)
        self.api_key_display.setEchoMode(QLineEdit.Password)
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(self.api_key_display)
        
        show_key_btn = QPushButton("👁")
        show_key_btn.setFixedSize(30, 30)
        show_key_btn.clicked.connect(self.toggle_api_key_visibility)
        api_key_layout.addWidget(show_key_btn)
        
        copy_key_btn = QPushButton("📋")
        copy_key_btn.setFixedSize(30, 30)
        copy_key_btn.clicked.connect(self.copy_api_key)
        api_key_layout.addWidget(copy_key_btn)
        
        api_key_widget = QWidget()
        api_key_widget.setLayout(api_key_layout)
        api_details_layout.addRow("API Key:", api_key_widget)
        
        self.widget_id_display = QLineEdit()
        self.widget_id_display.setReadOnly(True)
        api_details_layout.addRow("Widget ID:", self.widget_id_display)
        
        self.widget_url_display = QLineEdit()
        self.widget_url_display.setReadOnly(True)
        api_details_layout.addRow("Widget URL:", self.widget_url_display)
        
        result_layout.addLayout(api_details_layout)
        
        # Integration code
        code_label = QLabel("Copy this code into your external dashboard:")
        code_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        result_layout.addWidget(code_label)
        
        self.integration_code = QTextEdit()
        self.integration_code.setReadOnly(True)
        self.integration_code.setMaximumHeight(200)
        self.integration_code.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        result_layout.addWidget(self.integration_code)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        copy_code_btn = QPushButton("📋 Copy Integration Code")
        copy_code_btn.clicked.connect(self.copy_integration_code)
        action_layout.addWidget(copy_code_btn)
        
        test_widget_btn = QPushButton("🧪 Test Widget")
        test_widget_btn.clicked.connect(self.test_widget)
        action_layout.addWidget(test_widget_btn)
        
        save_integration_btn = QPushButton("💾 Save Integration")
        save_integration_btn.clicked.connect(self.save_integration)
        action_layout.addWidget(save_integration_btn)
        
        result_layout.addLayout(action_layout)
        
        self.result_group.setLayout(result_layout)
        layout.addWidget(self.result_group)
        
        layout.addStretch()
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "🔧 New Integration")
    
    def create_existing_integrations_tab(self):
        """Create the existing integrations tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Existing Widget Integrations")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_existing_integrations)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Integrations list
        self.integrations_table = QTableWidget()
        self.integrations_table.setColumnCount(6)
        self.integrations_table.setHorizontalHeaderLabels([
            "Client Name", "Domain", "Widget ID", "Status", "Last Used", "Actions"
        ])
        
        header = self.integrations_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.integrations_table.setAlternatingRowColors(True)
        self.integrations_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.integrations_table)
        
        # Status summary
        self.summary_label = QLabel("No integrations found")
        self.summary_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin: 10px;")
        layout.addWidget(self.summary_label)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "📋 Existing Integrations")
    
    def create_testing_tab(self):
        """Create the testing tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Testing area
        test_group = QGroupBox("Widget Testing")
        test_layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("""
Test your widget integration before deploying to production.
Enter your widget details below to simulate the embedded experience.
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #34495e; margin: 10px 0;")
        test_layout.addWidget(instructions)
        
        # Test form
        test_form_layout = QFormLayout()
        
        self.test_widget_id = QLineEdit()
        self.test_widget_id.setPlaceholderText("Enter widget ID to test")
        test_form_layout.addRow("Widget ID:", self.test_widget_id)
        
        self.test_api_key = QLineEdit()
        self.test_api_key.setPlaceholderText("Enter API key for testing")
        self.test_api_key.setEchoMode(QLineEdit.Password)
        test_form_layout.addRow("API Key:", self.test_api_key)
        
        test_layout.addLayout(test_form_layout)
        
        # Test buttons
        test_buttons_layout = QHBoxLayout()
        
        test_connection_btn = QPushButton("🔗 Test Connection")
        test_connection_btn.clicked.connect(self.test_connection)
        test_buttons_layout.addWidget(test_connection_btn)
        
        test_chat_btn = QPushButton("💬 Test Chat")
        test_chat_btn.clicked.connect(self.test_chat)
        test_buttons_layout.addWidget(test_chat_btn)
        
        test_estimate_btn = QPushButton("📊 Test Estimation")
        test_estimate_btn.clicked.connect(self.test_estimation)
        test_buttons_layout.addWidget(test_estimate_btn)
        
        open_widget_btn = QPushButton("🌐 Open Widget")
        open_widget_btn.clicked.connect(self.open_widget_in_browser)
        test_buttons_layout.addWidget(open_widget_btn)
        
        test_layout.addLayout(test_buttons_layout)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # Test results
        results_group = QGroupBox("Test Results")
        results_layout = QVBoxLayout()
        
        self.test_results = QTextEdit()
        self.test_results.setMaximumHeight(200)
        self.test_results.setReadOnly(True)
        self.test_results.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        results_layout.addWidget(self.test_results)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Server management
        server_group = QGroupBox("Server Management")
        server_layout = QVBoxLayout()
        
        server_status_layout = QHBoxLayout()
        
        self.server_status_detail = QLabel("Server Status: Loading...")
        server_status_layout.addWidget(self.server_status_detail)
        
        server_status_layout.addStretch()
        
        start_server_btn = QPushButton("▶️ Start Server")
        start_server_btn.clicked.connect(self.start_server)
        server_status_layout.addWidget(start_server_btn)
        
        stop_server_btn = QPushButton("⏹️ Stop Server")
        stop_server_btn.clicked.connect(self.stop_server)
        server_status_layout.addWidget(stop_server_btn)
        
        server_layout.addLayout(server_status_layout)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        layout.addStretch()
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "🧪 Testing")
    
    def update_server_status(self):
        """Update server status display"""
        if self.widget_manager and self.widget_manager.widget_server:
            status = self.widget_manager.widget_server.get_widget_status()
            
            if status["server_running"]:
                status_text = f"Server Running on Port {status['port']}"
                status_color = "#27ae60"
            else:
                status_text = "Server Stopped"
                status_color = "#e74c3c"
            
            self.status_label.setText(f"Server Status: {status_text}")
            self.status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
            
            # Update detailed status
            if hasattr(self, 'server_status_detail'):
                detail_text = f"Server: {'Running' if status['server_running'] else 'Stopped'} | Port: {status['port']} | Widgets: {status['active_widgets']}/{status['total_widgets']} | API Keys: {status['active_api_keys']}/{status['total_api_keys']}"
                self.server_status_detail.setText(detail_text)
        else:
            self.status_label.setText("Server Status: Not Initialized")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def generate_integration(self):
        """Generate a new widget integration"""
        try:
            # Validate inputs
            client_name = self.client_name.text().strip()
            domain = self.domain.text().strip()
            widget_url = self.widget_url.text().strip()
            
            if not all([client_name, domain, widget_url]):
                QMessageBox.warning(self, "Validation Error", "Please fill in all required fields.")
                return
            
            # Initialize widget API if not already running
            if not self.widget_manager.widget_server:
                if not self.widget_manager.initialize_widget_api():
                    QMessageBox.critical(self, "Error", "Failed to initialize widget API server.")
                    return
            
            # Get widget configuration
            widget_config = {
                "width": self.widget_width.text(),
                "height": self.widget_height.text(),
                "permissions": []
            }
            
            if self.perm_chat.isChecked():
                widget_config["permissions"].append("chat")
            if self.perm_estimate.isChecked():
                widget_config["permissions"].append("estimate")
            if self.perm_analytics.isChecked():
                widget_config["permissions"].append("analytics")
            if self.perm_team.isChecked():
                widget_config["permissions"].append("team")
            
            # Generate integration
            integration_data = self.widget_manager.generate_integration_code(
                client_name, domain, widget_url
            )
            
            if integration_data["success"]:
                # Store current integration
                self.current_integration = integration_data
                
                # Update UI
                self.api_key_display.setText(integration_data["api_key"])
                self.widget_id_display.setText(integration_data["widget_id"])
                self.widget_url_display.setText(integration_data["widget_url"])
                self.integration_code.setPlainText(integration_data["integration_code"])
                
                # Show result group
                self.result_group.setVisible(True)
                
                # Update test fields
                self.test_widget_id.setText(integration_data["widget_id"])
                self.test_api_key.setText(integration_data["api_key"])
                
                # Update status
                self.update_server_status()
                
                # Emit signal
                self.integration_created.emit(integration_data)
                
                QMessageBox.information(self, "Success", f"Widget integration created successfully!\nWidget ID: {integration_data['widget_id']}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate integration:\n{str(e)}")
    
    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_display.echoMode() == QLineEdit.Password:
            self.api_key_display.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_display.setEchoMode(QLineEdit.Password)
    
    def copy_api_key(self):
        """Copy API key to clipboard"""
        if self.current_integration:
            pyperclip.copy(self.current_integration["api_key"])
            QMessageBox.information(self, "Copied", "API key copied to clipboard!")
    
    def copy_integration_code(self):
        """Copy integration code to clipboard"""
        code = self.integration_code.toPlainText()
        if code:
            pyperclip.copy(code)
            QMessageBox.information(self, "Copied", "Integration code copied to clipboard!")
    
    def test_widget(self):
        """Test the generated widget"""
        if not self.current_integration:
            QMessageBox.warning(self, "No Integration", "Please generate an integration first.")
            return
        
        # Switch to testing tab
        self.tab_widget.setCurrentIndex(2)
        
        # Fill test fields
        self.test_widget_id.setText(self.current_integration["widget_id"])
        self.test_api_key.setText(self.current_integration["api_key"])
        
        # Run connection test
        self.test_connection()
    
    def save_integration(self):
        """Save the current integration"""
        if not self.current_integration:
            QMessageBox.warning(self, "No Integration", "Please generate an integration first.")
            return
        
        try:
            # Save integration details to file
            integrations_file = "data/saved_integrations.json"
            
            saved_integrations = []
            if os.path.exists(integrations_file):
                with open(integrations_file, 'r') as f:
                    saved_integrations = json.load(f)
            
            # Add current integration
            integration_record = {
                "client_name": self.client_name.text(),
                "domain": self.domain.text(),
                "widget_url": self.widget_url.text(),
                "widget_id": self.current_integration["widget_id"],
                "api_key": self.current_integration["api_key"],
                "created_at": QDateTime.currentDateTime().toString(),
                "active": True
            }
            
            saved_integrations.append(integration_record)
            
            # Save to file
            os.makedirs(os.path.dirname(integrations_file), exist_ok=True)
            with open(integrations_file, 'w') as f:
                json.dump(saved_integrations, f, indent=2)
            
            QMessageBox.information(self, "Saved", "Integration saved successfully!")
            self.load_existing_integrations()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save integration:\n{str(e)}")
    
    def load_existing_integrations(self):
        """Load existing integrations"""
        try:
            integrations_file = "data/saved_integrations.json"
            
            if not os.path.exists(integrations_file):
                self.integrations_table.setRowCount(0)
                self.summary_label.setText("No saved integrations found")
                return
            
            with open(integrations_file, 'r') as f:
                integrations = json.load(f)
            
            self.integrations_table.setRowCount(len(integrations))
            
            for row, integration in enumerate(integrations):
                # Client name
                self.integrations_table.setItem(row, 0, QTableWidgetItem(integration.get("client_name", "")))
                
                # Domain
                self.integrations_table.setItem(row, 1, QTableWidgetItem(integration.get("domain", "")))
                
                # Widget ID
                self.integrations_table.setItem(row, 2, QTableWidgetItem(integration.get("widget_id", "")))
                
                # Status
                status = "Active" if integration.get("active", True) else "Inactive"
                status_item = QTableWidgetItem(status)
                if status == "Active":
                    status_item.setForeground(QColor("#27ae60"))
                else:
                    status_item.setForeground(QColor("#e74c3c"))
                self.integrations_table.setItem(row, 3, status_item)
                
                # Last used
                last_used = integration.get("last_used", "Never")
                self.integrations_table.setItem(row, 4, QTableWidgetItem(last_used))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(4, 2, 4, 2)
                
                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(25, 25)
                edit_btn.clicked.connect(lambda checked, r=row: self.edit_integration(r))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("🗑️")
                delete_btn.setFixedSize(25, 25)
                delete_btn.clicked.connect(lambda checked, r=row: self.delete_integration(r))
                actions_layout.addWidget(delete_btn)
                
                actions_widget.setLayout(actions_layout)
                self.integrations_table.setCellWidget(row, 5, actions_widget)
            
            self.summary_label.setText(f"Found {len(integrations)} saved integrations")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load integrations:\n{str(e)}")
    
    def edit_integration(self, row: int):
        """Edit an existing integration"""
        QMessageBox.information(self, "Edit Integration", f"Edit functionality for row {row} not yet implemented.")
    
    def delete_integration(self, row: int):
        """Delete an integration"""
        reply = QMessageBox.question(
            self, 
            "Delete Integration", 
            "Are you sure you want to delete this integration?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                integrations_file = "data/saved_integrations.json"
                
                with open(integrations_file, 'r') as f:
                    integrations = json.load(f)
                
                # Remove the integration
                del integrations[row]
                
                # Save back to file
                with open(integrations_file, 'w') as f:
                    json.dump(integrations, f, indent=2)
                
                QMessageBox.information(self, "Deleted", "Integration deleted successfully!")
                self.load_existing_integrations()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete integration:\n{str(e)}")
    
    def test_connection(self):
        """Test connection to widget API"""
        widget_id = self.test_widget_id.text().strip()
        api_key = self.test_api_key.text().strip()
        
        if not widget_id or not api_key:
            self.test_results.append("❌ Please enter Widget ID and API Key")
            return
        
        try:
            import requests
            
            # Test status endpoint
            url = f"http://localhost:5555/api/status"
            params = {"widget_id": widget_id, "api_key": api_key}
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.test_results.append("✅ Connection test successful!")
                    self.test_results.append(f"   Server Status: {data['status']['server_status']}")
                    self.test_results.append(f"   Data Sources: {data['status']['data_sources']['active_sources']}/{data['status']['data_sources']['total_sources']}")
                else:
                    self.test_results.append("❌ Connection failed: Invalid response")
            else:
                self.test_results.append(f"❌ Connection failed: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.test_results.append("❌ Connection failed: Server not running")
        except Exception as e:
            self.test_results.append(f"❌ Connection test error: {str(e)}")
    
    def test_chat(self):
        """Test chat functionality"""
        widget_id = self.test_widget_id.text().strip()
        api_key = self.test_api_key.text().strip()
        
        if not widget_id or not api_key:
            self.test_results.append("❌ Please enter Widget ID and API Key")
            return
        
        try:
            import requests
            
            url = f"http://localhost:5555/api/chat"
            data = {
                "widget_id": widget_id,
                "api_key": api_key,
                "message": "Hello, can you help me estimate a project?",
                "context": {"test": True}
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.test_results.append("✅ Chat test successful!")
                    self.test_results.append(f"   Response: {result['response']['message'][:100]}...")
                else:
                    self.test_results.append("❌ Chat test failed: Invalid response")
            else:
                self.test_results.append(f"❌ Chat test failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.test_results.append(f"❌ Chat test error: {str(e)}")
    
    def test_estimation(self):
        """Test project estimation functionality"""
        widget_id = self.test_widget_id.text().strip()
        api_key = self.test_api_key.text().strip()
        
        if not widget_id or not api_key:
            self.test_results.append("❌ Please enter Widget ID and API Key")
            return
        
        try:
            import requests
            
            url = f"http://localhost:5555/api/estimate"
            data = {
                "widget_id": widget_id,
                "api_key": api_key,
                "project_description": "Build a simple e-commerce website",
                "requirements": ["User authentication", "Product catalog", "Shopping cart"],
                "technologies": ["react", "node.js", "postgresql"]
            }
            
            response = requests.post(url, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    estimate = result["estimate"]
                    self.test_results.append("✅ Estimation test successful!")
                    self.test_results.append(f"   Project: {estimate['project_name']}")
                    self.test_results.append(f"   Hours: {estimate['total_hours']} ({estimate['difficulty_level']})")
                    self.test_results.append(f"   Confidence: {estimate['confidence_level']:.1%}")
                else:
                    self.test_results.append("❌ Estimation test failed: Invalid response")
            else:
                self.test_results.append(f"❌ Estimation test failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.test_results.append(f"❌ Estimation test error: {str(e)}")
    
    def open_widget_in_browser(self):
        """Open widget in browser"""
        widget_id = self.test_widget_id.text().strip()
        
        if not widget_id:
            self.test_results.append("❌ Please enter Widget ID")
            return
        
        try:
            import webbrowser
            
            widget_url = f"http://localhost:5555/widget/embed/{widget_id}"
            webbrowser.open(widget_url)
            
            self.test_results.append(f"🌐 Opened widget in browser: {widget_url}")
            
        except Exception as e:
            self.test_results.append(f"❌ Failed to open widget: {str(e)}")
    
    def start_server(self):
        """Start the widget API server"""
        try:
            if not self.widget_manager.widget_server:
                if self.widget_manager.initialize_widget_api():
                    self.test_results.append("✅ Widget API server started")
                    self.update_server_status()
                else:
                    self.test_results.append("❌ Failed to start widget API server")
            else:
                self.test_results.append("ℹ️ Widget API server is already running")
                
        except Exception as e:
            self.test_results.append(f"❌ Server start error: {str(e)}")
    
    def stop_server(self):
        """Stop the widget API server"""
        try:
            if self.widget_manager.widget_server:
                self.widget_manager.shutdown()
                self.test_results.append("⏹️ Widget API server stopped")
                self.update_server_status()
            else:
                self.test_results.append("ℹ️ Widget API server is not running")
                
        except Exception as e:
            self.test_results.append(f"❌ Server stop error: {str(e)}")

# Test the widget integration dialog
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Mock widget integration manager
    class MockWidgetManager:
        def __init__(self):
            self.widget_server = None
        
        def initialize_widget_api(self):
            print("Mock: Initializing widget API")
            return True
        
        def generate_integration_code(self, client_name, domain, widget_url):
            return {
                "success": True,
                "api_key": "ak_mock_key_12345678",
                "widget_id": "widget_mock123456",
                "widget_url": "http://localhost:5555/widget/embed/widget_mock123456",
                "integration_code": "<!-- Mock integration code -->\n<script>console.log('Mock widget');</script>",
                "api_endpoint": "http://localhost:5555/api"
            }
        
        def shutdown(self):
            print("Mock: Shutting down widget API")
    
    manager = MockWidgetManager()
    dialog = WidgetIntegrationDialog(manager)
    dialog.show()
    
    sys.exit(app.exec_())