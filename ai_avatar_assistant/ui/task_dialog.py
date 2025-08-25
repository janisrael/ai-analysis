import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLineEdit, QTextEdit, QDateTimeEdit, QSpinBox, 
                             QComboBox, QPushButton, QLabel, QGroupBox,
                             QCheckBox, QTabWidget, QWidget, QListWidget,
                             QListWidgetItem, QMessageBox, QProgressBar)
from PyQt5.QtCore import QDateTime, QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap
from datetime import datetime, timedelta
import json

class TaskDialog(QDialog):
    """Comprehensive task creation and editing dialog"""
    
    task_saved = pyqtSignal(dict)  # Emitted when task is saved
    task_deleted = pyqtSignal(int)  # Emitted when task is deleted
    
    def __init__(self, task_data=None, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.is_editing = task_data is not None
        
        self.init_ui()
        if self.is_editing:
            self.populate_fields()
        
        self.setup_validators()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Edit Task" if self.is_editing else "Create New Task")
        self.setModal(True)
        self.resize(500, 600)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Create tabs
        self.tab_widget = QTabWidget()
        
        # Basic Info Tab
        self.basic_tab = self.create_basic_tab()
        self.tab_widget.addTab(self.basic_tab, "📝 Basic Info")
        
        # Schedule Tab
        self.schedule_tab = self.create_schedule_tab()
        self.tab_widget.addTab(self.schedule_tab, "⏰ Schedule")
        
        # Advanced Tab
        self.advanced_tab = self.create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "⚙️ Advanced")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = self.create_button_layout()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_basic_tab(self):
        """Create the basic information tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter task title...")
        layout.addRow("Title *:", self.title_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Describe your task in detail...")
        self.description_edit.setMaximumHeight(100)
        layout.addRow("Description:", self.description_edit)
        
        # Category
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        categories = ["Work", "Personal", "Learning", "Health", "Finance", 
                     "Shopping", "Travel", "Projects", "Meetings", "Other"]
        self.category_combo.addItems(categories)
        layout.addRow("Category:", self.category_combo)
        
        # Priority
        priority_layout = QHBoxLayout()
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 5)
        self.priority_spin.setValue(3)
        self.priority_spin.valueChanged.connect(self.update_priority_label)
        
        self.priority_label = QLabel("Normal")
        self.priority_label.setStyleSheet("color: #4A90E2; font-weight: bold;")
        
        priority_layout.addWidget(self.priority_spin)
        priority_layout.addWidget(self.priority_label)
        priority_layout.addStretch()
        
        layout.addRow("Priority:", priority_layout)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["pending", "in_progress", "completed", "cancelled"])
        layout.addRow("Status:", self.status_combo)
        
        widget.setLayout(layout)
        return widget
    
    def create_schedule_tab(self):
        """Create the scheduling tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Deadline Group
        deadline_group = QGroupBox("📅 Deadline")
        deadline_layout = QFormLayout()
        
        self.has_deadline_check = QCheckBox("Set deadline")
        self.has_deadline_check.toggled.connect(self.toggle_deadline)
        deadline_layout.addRow(self.has_deadline_check)
        
        self.deadline_edit = QDateTimeEdit()
        self.deadline_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setEnabled(False)
        deadline_layout.addRow("Due date:", self.deadline_edit)
        
        deadline_group.setLayout(deadline_layout)
        layout.addWidget(deadline_group)
        
        # Reminders Group
        reminders_group = QGroupBox("🔔 Reminders")
        reminders_layout = QVBoxLayout()
        
        self.reminder_checks = {}
        reminder_options = [
            ("15_min", "15 minutes before"),
            ("1_hour", "1 hour before"),
            ("2_hours", "2 hours before"),
            ("1_day", "1 day before"),
            ("1_week", "1 week before")
        ]
        
        for key, label in reminder_options:
            check = QCheckBox(label)
            self.reminder_checks[key] = check
            reminders_layout.addWidget(check)
        
        reminders_group.setLayout(reminders_layout)
        layout.addWidget(reminders_group)
        
        # Recurrence Group
        recurrence_group = QGroupBox("🔄 Recurrence")
        recurrence_layout = QFormLayout()
        
        self.is_recurring_check = QCheckBox("Recurring task")
        self.is_recurring_check.toggled.connect(self.toggle_recurrence)
        recurrence_layout.addRow(self.is_recurring_check)
        
        self.recurrence_combo = QComboBox()
        self.recurrence_combo.addItems([
            "Daily", "Weekly", "Monthly", "Yearly", "Custom"
        ])
        self.recurrence_combo.setEnabled(False)
        recurrence_layout.addRow("Repeat:", self.recurrence_combo)
        
        recurrence_group.setLayout(recurrence_layout)
        layout.addWidget(recurrence_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_advanced_tab(self):
        """Create the advanced options tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Estimation Group
        estimation_group = QGroupBox("⏱️ Time Estimation")
        estimation_layout = QFormLayout()
        
        self.estimated_hours = QSpinBox()
        self.estimated_hours.setRange(0, 999)
        self.estimated_hours.setSuffix(" hours")
        estimation_layout.addRow("Estimated duration:", self.estimated_hours)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        estimation_layout.addRow("Progress:", self.progress_bar)
        
        estimation_group.setLayout(estimation_layout)
        layout.addWidget(estimation_group)
        
        # Dependencies Group
        dependencies_group = QGroupBox("🔗 Dependencies")
        dependencies_layout = QVBoxLayout()
        
        self.dependencies_list = QListWidget()
        self.dependencies_list.setMaximumHeight(100)
        dependencies_layout.addWidget(QLabel("Depends on:"))
        dependencies_layout.addWidget(self.dependencies_list)
        
        dep_buttons = QHBoxLayout()
        self.add_dep_btn = QPushButton("Add Dependency")
        self.remove_dep_btn = QPushButton("Remove")
        dep_buttons.addWidget(self.add_dep_btn)
        dep_buttons.addWidget(self.remove_dep_btn)
        dep_buttons.addStretch()
        
        dependencies_layout.addLayout(dep_buttons)
        dependencies_group.setLayout(dependencies_layout)
        layout.addWidget(dependencies_group)
        
        # Tags Group
        tags_group = QGroupBox("🏷️ Tags")
        tags_layout = QFormLayout()
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Enter tags separated by commas...")
        tags_layout.addRow("Tags:", self.tags_edit)
        
        tags_group.setLayout(tags_layout)
        layout.addWidget(tags_group)
        
        # Notes Group
        notes_group = QGroupBox("📋 Additional Notes")
        notes_layout = QVBoxLayout()
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add any additional notes or comments...")
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)
        
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_button_layout(self):
        """Create the dialog button layout"""
        layout = QHBoxLayout()
        
        # Left side buttons (if editing)
        if self.is_editing:
            self.delete_btn = QPushButton("🗑️ Delete Task")
            self.delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF6B6B;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FF5252;
                }
            """)
            self.delete_btn.clicked.connect(self.delete_task)
            layout.addWidget(self.delete_btn)
        
        layout.addStretch()
        
        # Right side buttons
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("💾 Save Task")
        self.save_btn.setStyleSheet("""
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
        self.save_btn.clicked.connect(self.save_task)
        self.save_btn.setDefault(True)
        layout.addWidget(self.save_btn)
        
        return layout
    
    def setup_validators(self):
        """Setup field validators and connections"""
        # Enable/disable save button based on title
        self.title_edit.textChanged.connect(self.validate_form)
        
        # Connect other signals
        self.add_dep_btn.clicked.connect(self.add_dependency)
        self.remove_dep_btn.clicked.connect(self.remove_dependency)
    
    def populate_fields(self):
        """Populate fields with existing task data"""
        if not self.task_data:
            return
        
        # Basic info
        self.title_edit.setText(self.task_data.get('title', ''))
        self.description_edit.setPlainText(self.task_data.get('description', ''))
        self.priority_spin.setValue(self.task_data.get('priority', 3))
        self.status_combo.setCurrentText(self.task_data.get('status', 'pending'))
        
        # Category
        metadata = self.task_data.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        
        category = metadata.get('category', '')
        if category:
            index = self.category_combo.findText(category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            else:
                self.category_combo.setCurrentText(category)
        
        # Deadline
        deadline = self.task_data.get('deadline')
        if deadline:
            if isinstance(deadline, str):
                deadline_dt = datetime.fromisoformat(deadline)
            else:
                deadline_dt = deadline
            
            self.has_deadline_check.setChecked(True)
            self.deadline_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(deadline_dt.timestamp())))
        
        # Advanced fields
        self.estimated_hours.setValue(metadata.get('estimated_hours', 0))
        
        tags = metadata.get('tags', [])
        if tags:
            self.tags_edit.setText(', '.join(tags))
        
        notes = metadata.get('notes', '')
        self.notes_edit.setPlainText(notes)
    
    def update_priority_label(self, value):
        """Update priority label based on spin box value"""
        labels = {1: "Low", 2: "Below Normal", 3: "Normal", 4: "High", 5: "Critical"}
        colors = {1: "#4CAF50", 2: "#8BC34A", 3: "#4A90E2", 4: "#FF9800", 5: "#FF5722"}
        
        label = labels.get(value, "Normal")
        color = colors.get(value, "#4A90E2")
        
        self.priority_label.setText(label)
        self.priority_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def toggle_deadline(self, checked):
        """Toggle deadline fields"""
        self.deadline_edit.setEnabled(checked)
    
    def toggle_recurrence(self, checked):
        """Toggle recurrence fields"""
        self.recurrence_combo.setEnabled(checked)
    
    def validate_form(self):
        """Validate form and enable/disable save button"""
        title = self.title_edit.text().strip()
        self.save_btn.setEnabled(len(title) > 0)
    
    def add_dependency(self):
        """Add a task dependency"""
        # This would open a task selection dialog in a full implementation
        # For now, just add a placeholder
        item = QListWidgetItem("Example Dependency Task")
        self.dependencies_list.addItem(item)
    
    def remove_dependency(self):
        """Remove selected dependency"""
        current = self.dependencies_list.currentRow()
        if current >= 0:
            self.dependencies_list.takeItem(current)
    
    def collect_task_data(self):
        """Collect all form data into a task dictionary"""
        # Basic info
        task_data = {
            'title': self.title_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'priority': self.priority_spin.value(),
            'status': self.status_combo.currentText()
        }
        
        # Deadline
        if self.has_deadline_check.isChecked():
            deadline_qt = self.deadline_edit.dateTime()
            deadline_dt = datetime.fromtimestamp(deadline_qt.toSecsSinceEpoch())
            task_data['deadline'] = deadline_dt
        else:
            task_data['deadline'] = None
        
        # Metadata
        metadata = {
            'category': self.category_combo.currentText(),
            'estimated_hours': self.estimated_hours.value(),
            'notes': self.notes_edit.toPlainText().strip(),
            'progress': self.progress_bar.value()
        }
        
        # Tags
        tags_text = self.tags_edit.text().strip()
        if tags_text:
            metadata['tags'] = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        
        # Reminders
        active_reminders = []
        for key, check in self.reminder_checks.items():
            if check.isChecked():
                active_reminders.append(key)
        
        if active_reminders:
            metadata['reminders'] = active_reminders
        
        # Recurrence
        if self.is_recurring_check.isChecked():
            metadata['recurrence'] = self.recurrence_combo.currentText()
        
        task_data['metadata'] = metadata
        
        # Add ID if editing
        if self.is_editing and self.task_data:
            task_data['id'] = self.task_data.get('id')
        
        return task_data
    
    def save_task(self):
        """Save the task and emit signal"""
        if not self.validate_task_data():
            return
        
        task_data = self.collect_task_data()
        self.task_saved.emit(task_data)
        self.accept()
    
    def validate_task_data(self):
        """Validate task data before saving"""
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation Error", 
                              "Task title is required.")
            return False
        
        # Check deadline is in the future (if set)
        if self.has_deadline_check.isChecked():
            deadline_qt = self.deadline_edit.dateTime()
            deadline_dt = datetime.fromtimestamp(deadline_qt.toSecsSinceEpoch())
            if deadline_dt <= datetime.now():
                reply = QMessageBox.question(self, "Past Deadline", 
                                           "The deadline is in the past. Continue anyway?",
                                           QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return False
        
        return True
    
    def delete_task(self):
        """Delete the current task"""
        reply = QMessageBox.question(self, "Delete Task", 
                                   "Are you sure you want to delete this task?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.task_data and 'id' in self.task_data:
                self.task_deleted.emit(self.task_data['id'])
            self.accept()

class QuickTaskDialog(QDialog):
    """Simple quick task creation dialog"""
    
    task_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize simple UI"""
        self.setWindowTitle("Quick Add Task")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Task:"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("What needs to be done?")
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        
        # Quick options
        options_layout = QHBoxLayout()
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Normal", "High", "Critical"])
        self.priority_combo.setCurrentIndex(1)  # Normal
        options_layout.addWidget(QLabel("Priority:"))
        options_layout.addWidget(self.priority_combo)
        
        self.due_combo = QComboBox()
        self.due_combo.addItems(["No deadline", "In 1 hour", "Today", "Tomorrow", "This week"])
        options_layout.addWidget(QLabel("Due:"))
        options_layout.addWidget(self.due_combo)
        
        layout.addLayout(options_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Add Task")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        save_btn.clicked.connect(self.save_quick_task)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Focus on title
        self.title_edit.setFocus()
        self.title_edit.returnPressed.connect(self.save_quick_task)
    
    def save_quick_task(self):
        """Save quick task"""
        title = self.title_edit.text().strip()
        if not title:
            return
        
        # Calculate deadline
        deadline = None
        due_text = self.due_combo.currentText()
        now = datetime.now()
        
        if due_text == "In 1 hour":
            deadline = now + timedelta(hours=1)
        elif due_text == "Today":
            deadline = now.replace(hour=23, minute=59, second=59)
        elif due_text == "Tomorrow":
            deadline = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)
        elif due_text == "This week":
            days_until_sunday = 6 - now.weekday()
            deadline = (now + timedelta(days=days_until_sunday)).replace(hour=23, minute=59, second=59)
        
        # Map priority
        priority_map = {"Low": 1, "Normal": 3, "High": 4, "Critical": 5}
        priority = priority_map.get(self.priority_combo.currentText(), 3)
        
        task_data = {
            'title': title,
            'description': '',
            'priority': priority,
            'status': 'pending',
            'deadline': deadline,
            'metadata': {'category': 'General', 'quick_add': True}
        }
        
        self.task_saved.emit(task_data)
        self.accept()


# Test the dialogs
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test full dialog
    dialog = TaskDialog()
    dialog.task_saved.connect(lambda data: print(f"Task saved: {data}"))
    dialog.show()
    
    # Test quick dialog
    quick_dialog = QuickTaskDialog()
    quick_dialog.task_saved.connect(lambda data: print(f"Quick task saved: {data}"))
    # quick_dialog.show()
    
    sys.exit(app.exec_())