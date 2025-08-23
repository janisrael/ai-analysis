import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

class TaskDatabase:
    def __init__(self, db_path: str = "data/tasks.db"):
        self.db_path = db_path
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    deadline DATETIME,
                    priority INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # Events table for notifications
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT,
                    trigger_time DATETIME,
                    is_triggered BOOLEAN DEFAULT FALSE,
                    task_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            ''')
            
            # User actions history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    context TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    task_id INTEGER,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            ''')
            
            conn.commit()
    
    def add_task(self, title: str, description: str = "", deadline: datetime = None, 
                 priority: int = 1, metadata: Dict = None) -> int:
        """Add a new task to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (title, description, deadline, priority, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, description, deadline, priority, json.dumps(metadata or {})))
            
            task_id = cursor.lastrowid
            
            # Create deadline event if deadline is set
            if deadline:
                self.add_event("deadline_reminder", f"Task '{title}' is due soon!", 
                             deadline - timedelta(hours=2), task_id)
                self.add_event("deadline_warning", f"Task '{title}' is due!", 
                             deadline, task_id)
            
            conn.commit()
            return task_id
    
    def get_tasks(self, status: str = None, upcoming_hours: int = None) -> List[Dict]:
        """Get tasks from database with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM tasks"
            params = []
            
            conditions = []
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            if upcoming_hours:
                future_time = datetime.now() + timedelta(hours=upcoming_hours)
                conditions.append("deadline <= ? AND deadline > ?")
                params.extend([future_time, datetime.now()])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY deadline ASC, priority DESC"
            
            cursor.execute(query, params)
            tasks = []
            for row in cursor.fetchall():
                task = dict(row)
                if task['metadata']:
                    task['metadata'] = json.loads(task['metadata'])
                tasks.append(task)
            
            return tasks
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        """Update task status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tasks 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (status, task_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
    
    def add_event(self, event_type: str, title: str, trigger_time: datetime, 
                  task_id: int = None, message: str = "") -> int:
        """Add an event/notification"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO events (event_type, title, message, trigger_time, task_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (event_type, title, message, trigger_time, task_id))
            
            event_id = cursor.lastrowid
            conn.commit()
            return event_id
    
    def get_pending_events(self) -> List[Dict]:
        """Get events that should be triggered now"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT e.*, t.title as task_title, t.status as task_status
                FROM events e
                LEFT JOIN tasks t ON e.task_id = t.id
                WHERE e.is_triggered = FALSE AND e.trigger_time <= ?
                ORDER BY e.trigger_time ASC
            ''', (datetime.now(),))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_event_triggered(self, event_id: int) -> bool:
        """Mark an event as triggered"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE events SET is_triggered = TRUE WHERE id = ?
            ''', (event_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
    
    def log_user_action(self, action_type: str, context: str = "", task_id: int = None):
        """Log user action for learning purposes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_actions (action_type, context, task_id)
                VALUES (?, ?, ?)
            ''', (action_type, context, task_id))
            conn.commit()