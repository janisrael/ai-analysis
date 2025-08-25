import os
import json
import sqlite3
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import threading
import time
from pathlib import Path
import hashlib
import glob

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import psycopg2
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

class DataSource:
    """Represents a single data source (JSON folder or SQL database)"""
    
    def __init__(self, source_id: str, source_type: str, name: str, config: Dict):
        self.source_id = source_id
        self.source_type = source_type  # 'json_folder', 'sqlite', 'mysql', 'postgresql', 'mongodb', 'clickup_api'
        self.name = name
        self.config = config
        self.is_active = True
        self.last_sync = None
        self.connection = None
        self.cached_data = {}
        self.watch_thread = None
        self.is_watching = False

class DataSourceManager:
    """Manages multiple data sources including JSON folders and external databases"""
    
    def __init__(self, config_path: str = "data/data_sources.json"):
        self.config_path = config_path
        self.data_sources = {}
        self.logger = logging.getLogger(__name__)
        
        # File watcher settings
        self.watch_interval = 30  # seconds
        self.auto_sync = True
        
        # Data cache
        self.unified_cache = {
            "projects": [],
            "tasks": [],
            "team_members": [],
            "skills": [],
            "estimates": [],
            "performance_data": [],
            "last_updated": None
        }
        
        # Load configuration
        self.load_configuration()
        
        # Start monitoring
        if self.auto_sync:
            self.start_monitoring()
    
    def load_configuration(self):
        """Load data source configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                # Load data sources
                for source_config in config.get("data_sources", []):
                    source = DataSource(
                        source_config["id"],
                        source_config["type"],
                        source_config["name"],
                        source_config["config"]
                    )
                    source.is_active = source_config.get("active", True)
                    self.data_sources[source.source_id] = source
                
                # Load settings
                self.watch_interval = config.get("settings", {}).get("watch_interval", 30)
                self.auto_sync = config.get("settings", {}).get("auto_sync", True)
                
                self.logger.info(f"Loaded {len(self.data_sources)} data sources")
            else:
                # Create default configuration
                self.create_default_configuration()
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.create_default_configuration()
    
    def create_default_configuration(self):
        """Create default configuration with sample data sources"""
        default_config = {
            "data_sources": [
                {
                    "id": "local_tasks",
                    "type": "sqlite",
                    "name": "Local Task Database",
                    "config": {
                        "database_path": "data/tasks.db"
                    },
                    "active": True
                },
                {
                    "id": "project_json",
                    "type": "json_folder",
                    "name": "Project JSON Files",
                    "config": {
                        "folder_path": "data/projects",
                        "file_pattern": "*.json",
                        "recursive": True
                    },
                    "active": True
                }
            ],
            "settings": {
                "watch_interval": 30,
                "auto_sync": True,
                "cache_duration": 300
            },
            "external_connections": {
                "clickup": {
                    "api_key": "",
                    "team_id": "",
                    "enabled": False
                },
                "dashboard_db": {
                    "type": "mysql",
                    "host": "localhost",
                    "port": 3306,
                    "database": "",
                    "username": "",
                    "password": "",
                    "enabled": False
                }
            }
        }
        
        # Create directories
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        os.makedirs("data/projects", exist_ok=True)
        
        # Save configuration
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        
        self.logger.info("Created default data source configuration")
    
    def save_configuration(self):
        """Save current configuration to file"""
        try:
            config = {
                "data_sources": [],
                "settings": {
                    "watch_interval": self.watch_interval,
                    "auto_sync": self.auto_sync
                }
            }
            
            # Add data sources
            for source in self.data_sources.values():
                config["data_sources"].append({
                    "id": source.source_id,
                    "type": source.source_type,
                    "name": source.name,
                    "config": source.config,
                    "active": source.is_active
                })
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    def add_data_source(self, source_type: str, name: str, config: Dict) -> str:
        """Add a new data source"""
        source_id = hashlib.md5(f"{source_type}_{name}_{time.time()}".encode()).hexdigest()[:8]
        
        source = DataSource(source_id, source_type, name, config)
        self.data_sources[source_id] = source
        
        # Test connection
        if self.test_connection(source):
            self.save_configuration()
            self.logger.info(f"Added data source: {name} ({source_type})")
            return source_id
        else:
            del self.data_sources[source_id]
            raise Exception(f"Failed to connect to {name}")
    
    def remove_data_source(self, source_id: str):
        """Remove a data source"""
        if source_id in self.data_sources:
            source = self.data_sources[source_id]
            if source.connection:
                try:
                    source.connection.close()
                except:
                    pass
            
            del self.data_sources[source_id]
            self.save_configuration()
            self.logger.info(f"Removed data source: {source_id}")
    
    def test_connection(self, source: DataSource) -> bool:
        """Test connection to a data source"""
        try:
            if source.source_type == "json_folder":
                return self.test_json_folder(source)
            elif source.source_type == "sqlite":
                return self.test_sqlite(source)
            elif source.source_type == "mysql":
                return self.test_mysql(source)
            elif source.source_type == "postgresql":
                return self.test_postgresql(source)
            elif source.source_type == "mongodb":
                return self.test_mongodb(source)
            elif source.source_type == "clickup_api":
                return self.test_clickup(source)
            else:
                return False
        except Exception as e:
            self.logger.error(f"Connection test failed for {source.name}: {e}")
            return False
    
    def test_json_folder(self, source: DataSource) -> bool:
        """Test JSON folder access"""
        folder_path = source.config.get("folder_path")
        if not folder_path or not os.path.exists(folder_path):
            return False
        
        # Try to read a sample file
        pattern = source.config.get("file_pattern", "*.json")
        files = glob.glob(os.path.join(folder_path, pattern))
        
        if files:
            try:
                with open(files[0], 'r') as f:
                    json.load(f)
                return True
            except:
                pass
        
        return os.path.isdir(folder_path)  # At least the folder exists
    
    def test_sqlite(self, source: DataSource) -> bool:
        """Test SQLite database connection"""
        db_path = source.config.get("database_path")
        if not db_path:
            return False
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        except:
            return False
    
    def test_mysql(self, source: DataSource) -> bool:
        """Test MySQL database connection"""
        if not MYSQL_AVAILABLE:
            return False
        
        try:
            config = source.config
            conn = mysql.connector.connect(
                host=config.get("host"),
                port=config.get("port", 3306),
                database=config.get("database"),
                user=config.get("username"),
                password=config.get("password")
            )
            conn.close()
            return True
        except:
            return False
    
    def test_postgresql(self, source: DataSource) -> bool:
        """Test PostgreSQL database connection"""
        if not POSTGRESQL_AVAILABLE:
            return False
        
        try:
            config = source.config
            conn = psycopg2.connect(
                host=config.get("host"),
                port=config.get("port", 5432),
                database=config.get("database"),
                user=config.get("username"),
                password=config.get("password")
            )
            conn.close()
            return True
        except:
            return False
    
    def test_mongodb(self, source: DataSource) -> bool:
        """Test MongoDB connection"""
        if not MONGODB_AVAILABLE:
            return False
        
        try:
            config = source.config
            client = pymongo.MongoClient(
                host=config.get("host", "localhost"),
                port=config.get("port", 27017),
                username=config.get("username"),
                password=config.get("password")
            )
            client.server_info()
            client.close()
            return True
        except:
            return False
    
    def test_clickup(self, source: DataSource) -> bool:
        """Test ClickUp API connection"""
        try:
            import requests
            
            api_key = source.config.get("api_key")
            if not api_key:
                return False
            
            headers = {"Authorization": api_key}
            response = requests.get("https://api.clickup.com/api/v2/team", headers=headers)
            return response.status_code == 200
        except:
            return False
    
    def start_monitoring(self):
        """Start monitoring data sources for changes"""
        if not self.auto_sync:
            return
        
        def monitor_loop():
            while self.auto_sync:
                try:
                    self.sync_all_sources()
                    time.sleep(self.watch_interval)
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(10)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        self.logger.info("Started data source monitoring")
    
    def sync_all_sources(self):
        """Sync data from all active sources"""
        for source in self.data_sources.values():
            if source.is_active:
                self.sync_source(source)
        
        self.update_unified_cache()
    
    def sync_source(self, source: DataSource):
        """Sync data from a specific source"""
        try:
            if source.source_type == "json_folder":
                self.sync_json_folder(source)
            elif source.source_type == "sqlite":
                self.sync_sqlite(source)
            elif source.source_type == "mysql":
                self.sync_mysql(source)
            elif source.source_type == "postgresql":
                self.sync_postgresql(source)
            elif source.source_type == "mongodb":
                self.sync_mongodb(source)
            elif source.source_type == "clickup_api":
                self.sync_clickup(source)
            
            source.last_sync = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error syncing {source.name}: {e}")
    
    def sync_json_folder(self, source: DataSource):
        """Sync data from JSON folder"""
        folder_path = source.config.get("folder_path")
        pattern = source.config.get("file_pattern", "*.json")
        recursive = source.config.get("recursive", False)
        
        if not folder_path or not os.path.exists(folder_path):
            return
        
        data = {
            "projects": [],
            "tasks": [],
            "team_members": [],
            "skills": [],
            "estimates": [],
            "performance_data": []
        }
        
        # Find JSON files
        if recursive:
            files = glob.glob(os.path.join(folder_path, "**", pattern), recursive=True)
        else:
            files = glob.glob(os.path.join(folder_path, pattern))
        
        # Read and categorize JSON files
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                # Determine data type based on filename or content
                filename = os.path.basename(file_path).lower()
                
                if 'project' in filename or 'project' in file_data:
                    data["projects"].extend(file_data if isinstance(file_data, list) else [file_data])
                elif 'task' in filename or 'task' in file_data:
                    data["tasks"].extend(file_data if isinstance(file_data, list) else [file_data])
                elif 'team' in filename or 'member' in filename:
                    data["team_members"].extend(file_data if isinstance(file_data, list) else [file_data])
                elif 'skill' in filename:
                    data["skills"].extend(file_data if isinstance(file_data, list) else [file_data])
                elif 'estimate' in filename:
                    data["estimates"].extend(file_data if isinstance(file_data, list) else [file_data])
                elif 'performance' in filename:
                    data["performance_data"].extend(file_data if isinstance(file_data, list) else [file_data])
                else:
                    # Try to categorize by content structure
                    self.categorize_json_data(file_data, data)
                    
            except Exception as e:
                self.logger.warning(f"Failed to read {file_path}: {e}")
        
        source.cached_data = data
        self.logger.debug(f"Synced {len(files)} JSON files from {source.name}")
    
    def categorize_json_data(self, file_data: Any, data: Dict):
        """Categorize JSON data based on content structure"""
        if not isinstance(file_data, (list, dict)):
            return
        
        items = file_data if isinstance(file_data, list) else [file_data]
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            # Check for project indicators
            if any(key in item for key in ['project_name', 'project_id', 'project_type', 'deadline', 'client']):
                data["projects"].append(item)
            # Check for task indicators
            elif any(key in item for key in ['task_name', 'task_id', 'status', 'assignee', 'priority']):
                data["tasks"].append(item)
            # Check for team member indicators
            elif any(key in item for key in ['name', 'email', 'role', 'skills', 'hourly_rate']):
                data["team_members"].append(item)
            # Check for skill indicators
            elif any(key in item for key in ['skill_name', 'category', 'level', 'experience']):
                data["skills"].append(item)
            # Check for estimate indicators
            elif any(key in item for key in ['estimated_hours', 'difficulty', 'complexity', 'effort']):
                data["estimates"].append(item)
    
    def sync_sqlite(self, source: DataSource):
        """Sync data from SQLite database"""
        db_path = source.config.get("database_path")
        if not db_path or not os.path.exists(db_path):
            return
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            data = {
                "projects": [],
                "tasks": [],
                "team_members": [],
                "skills": [],
                "estimates": [],
                "performance_data": []
            }
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Sync relevant tables
            for table in tables:
                if 'project' in table.lower():
                    cursor.execute(f"SELECT * FROM {table}")
                    data["projects"].extend([dict(row) for row in cursor.fetchall()])
                elif 'task' in table.lower():
                    cursor.execute(f"SELECT * FROM {table}")
                    data["tasks"].extend([dict(row) for row in cursor.fetchall()])
                elif 'team' in table.lower() or 'member' in table.lower() or 'user' in table.lower():
                    cursor.execute(f"SELECT * FROM {table}")
                    data["team_members"].extend([dict(row) for row in cursor.fetchall()])
            
            conn.close()
            source.cached_data = data
            
        except Exception as e:
            self.logger.error(f"Error syncing SQLite {source.name}: {e}")
    
    def sync_mysql(self, source: DataSource):
        """Sync data from MySQL database"""
        if not MYSQL_AVAILABLE:
            return
        
        try:
            config = source.config
            conn = mysql.connector.connect(
                host=config.get("host"),
                port=config.get("port", 3306),
                database=config.get("database"),
                user=config.get("username"),
                password=config.get("password")
            )
            
            cursor = conn.cursor(dictionary=True)
            
            data = {
                "projects": [],
                "tasks": [],
                "team_members": [],
                "skills": [],
                "estimates": [],
                "performance_data": []
            }
            
            # Get table names
            cursor.execute("SHOW TABLES")
            tables = [row[f'Tables_in_{config.get("database")}'] for row in cursor.fetchall()]
            
            # Sync relevant tables
            for table in tables:
                if 'project' in table.lower():
                    cursor.execute(f"SELECT * FROM {table}")
                    data["projects"].extend(cursor.fetchall())
                elif 'task' in table.lower():
                    cursor.execute(f"SELECT * FROM {table}")
                    data["tasks"].extend(cursor.fetchall())
                elif 'team' in table.lower() or 'member' in table.lower() or 'user' in table.lower():
                    cursor.execute(f"SELECT * FROM {table}")
                    data["team_members"].extend(cursor.fetchall())
            
            conn.close()
            source.cached_data = data
            
        except Exception as e:
            self.logger.error(f"Error syncing MySQL {source.name}: {e}")
    
    def sync_postgresql(self, source: DataSource):
        """Sync data from PostgreSQL database"""
        if not POSTGRESQL_AVAILABLE:
            return
        
        try:
            config = source.config
            conn = psycopg2.connect(
                host=config.get("host"),
                port=config.get("port", 5432),
                database=config.get("database"),
                user=config.get("username"),
                password=config.get("password")
            )
            
            cursor = conn.cursor()
            
            data = {
                "projects": [],
                "tasks": [],
                "team_members": [],
                "skills": [],
                "estimates": [],
                "performance_data": []
            }
            
            # Get table names
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Sync relevant tables
            for table in tables:
                if 'project' in table.lower():
                    cursor.execute(f"SELECT * FROM {table}")
                    columns = [desc[0] for desc in cursor.description]
                    data["projects"].extend([dict(zip(columns, row)) for row in cursor.fetchall()])
                elif 'task' in table.lower():
                    cursor.execute(f"SELECT * FROM {table}")
                    columns = [desc[0] for desc in cursor.description]
                    data["tasks"].extend([dict(zip(columns, row)) for row in cursor.fetchall()])
            
            conn.close()
            source.cached_data = data
            
        except Exception as e:
            self.logger.error(f"Error syncing PostgreSQL {source.name}: {e}")
    
    def sync_mongodb(self, source: DataSource):
        """Sync data from MongoDB"""
        if not MONGODB_AVAILABLE:
            return
        
        try:
            config = source.config
            client = pymongo.MongoClient(
                host=config.get("host", "localhost"),
                port=config.get("port", 27017),
                username=config.get("username"),
                password=config.get("password")
            )
            
            db = client[config.get("database")]
            
            data = {
                "projects": [],
                "tasks": [],
                "team_members": [],
                "skills": [],
                "estimates": [],
                "performance_data": []
            }
            
            # Get collection names
            collections = db.list_collection_names()
            
            # Sync relevant collections
            for collection_name in collections:
                collection = db[collection_name]
                if 'project' in collection_name.lower():
                    data["projects"].extend(list(collection.find()))
                elif 'task' in collection_name.lower():
                    data["tasks"].extend(list(collection.find()))
                elif 'team' in collection_name.lower() or 'member' in collection_name.lower():
                    data["team_members"].extend(list(collection.find()))
            
            client.close()
            source.cached_data = data
            
        except Exception as e:
            self.logger.error(f"Error syncing MongoDB {source.name}: {e}")
    
    def sync_clickup(self, source: DataSource):
        """Sync data from ClickUp API"""
        try:
            import requests
            
            api_key = source.config.get("api_key")
            team_id = source.config.get("team_id")
            
            if not api_key:
                return
            
            headers = {"Authorization": api_key}
            
            data = {
                "projects": [],
                "tasks": [],
                "team_members": [],
                "skills": [],
                "estimates": [],
                "performance_data": []
            }
            
            # Get team members
            if team_id:
                response = requests.get(f"https://api.clickup.com/api/v2/team/{team_id}", headers=headers)
                if response.status_code == 200:
                    team_data = response.json()
                    data["team_members"] = team_data.get("team", {}).get("members", [])
            
            # Get spaces (projects)
            response = requests.get("https://api.clickup.com/api/v2/team", headers=headers)
            if response.status_code == 200:
                teams = response.json().get("teams", [])
                for team in teams:
                    team_id = team["id"]
                    
                    # Get spaces
                    spaces_response = requests.get(f"https://api.clickup.com/api/v2/team/{team_id}/space", headers=headers)
                    if spaces_response.status_code == 200:
                        spaces = spaces_response.json().get("spaces", [])
                        data["projects"].extend(spaces)
                        
                        # Get tasks from each space
                        for space in spaces:
                            # Get folders
                            folders_response = requests.get(f"https://api.clickup.com/api/v2/space/{space['id']}/folder", headers=headers)
                            if folders_response.status_code == 200:
                                folders = folders_response.json().get("folders", [])
                                
                                for folder in folders:
                                    # Get lists
                                    lists_response = requests.get(f"https://api.clickup.com/api/v2/folder/{folder['id']}/list", headers=headers)
                                    if lists_response.status_code == 200:
                                        lists = lists_response.json().get("lists", [])
                                        
                                        for list_item in lists:
                                            # Get tasks
                                            tasks_response = requests.get(f"https://api.clickup.com/api/v2/list/{list_item['id']}/task", headers=headers)
                                            if tasks_response.status_code == 200:
                                                tasks = tasks_response.json().get("tasks", [])
                                                data["tasks"].extend(tasks)
            
            source.cached_data = data
            
        except Exception as e:
            self.logger.error(f"Error syncing ClickUp {source.name}: {e}")
    
    def update_unified_cache(self):
        """Update the unified data cache from all sources"""
        unified = {
            "projects": [],
            "tasks": [],
            "team_members": [],
            "skills": [],
            "estimates": [],
            "performance_data": [],
            "last_updated": datetime.now()
        }
        
        # Merge data from all sources
        for source in self.data_sources.values():
            if source.is_active and source.cached_data:
                for data_type in unified.keys():
                    if data_type != "last_updated" and data_type in source.cached_data:
                        unified[data_type].extend(source.cached_data[data_type])
        
        # Remove duplicates (basic deduplication by id or name)
        for data_type in ["projects", "tasks", "team_members"]:
            unique_items = []
            seen_ids = set()
            
            for item in unified[data_type]:
                # Try different ID fields
                item_id = item.get("id") or item.get("task_id") or item.get("project_id") or item.get("name") or item.get("title")
                
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    unique_items.append(item)
                elif not item_id:
                    unique_items.append(item)  # Include items without IDs
            
            unified[data_type] = unique_items
        
        self.unified_cache = unified
        self.logger.info(f"Updated unified cache: {len(unified['projects'])} projects, {len(unified['tasks'])} tasks, {len(unified['team_members'])} team members")
    
    def get_all_projects(self) -> List[Dict]:
        """Get all projects from all sources"""
        return self.unified_cache.get("projects", [])
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks from all sources"""
        return self.unified_cache.get("tasks", [])
    
    def get_team_members(self) -> List[Dict]:
        """Get all team members from all sources"""
        return self.unified_cache.get("team_members", [])
    
    def get_skills_data(self) -> List[Dict]:
        """Get skills data from all sources"""
        return self.unified_cache.get("skills", [])
    
    def get_performance_data(self) -> List[Dict]:
        """Get performance data from all sources"""
        return self.unified_cache.get("performance_data", [])
    
    def search_data(self, query: str, data_type: str = None) -> List[Dict]:
        """Search across all data sources"""
        results = []
        query_lower = query.lower()
        
        search_types = [data_type] if data_type else ["projects", "tasks", "team_members"]
        
        for search_type in search_types:
            data = self.unified_cache.get(search_type, [])
            
            for item in data:
                # Search in all string fields
                matches = False
                for key, value in item.items():
                    if isinstance(value, str) and query_lower in value.lower():
                        matches = True
                        break
                
                if matches:
                    item_with_type = item.copy()
                    item_with_type["_data_type"] = search_type
                    results.append(item_with_type)
        
        return results
    
    def get_data_source_status(self) -> Dict:
        """Get status of all data sources"""
        status = {
            "total_sources": len(self.data_sources),
            "active_sources": sum(1 for s in self.data_sources.values() if s.is_active),
            "last_sync": max((s.last_sync for s in self.data_sources.values() if s.last_sync), default=None),
            "sources": []
        }
        
        for source in self.data_sources.values():
            source_status = {
                "id": source.source_id,
                "name": source.name,
                "type": source.source_type,
                "active": source.is_active,
                "last_sync": source.last_sync.isoformat() if source.last_sync else None,
                "data_counts": {}
            }
            
            if source.cached_data:
                for data_type, data_list in source.cached_data.items():
                    if isinstance(data_list, list):
                        source_status["data_counts"][data_type] = len(data_list)
            
            status["sources"].append(source_status)
        
        return status
    
    def export_unified_data(self, output_path: str):
        """Export unified data to JSON file"""
        try:
            # Convert datetime to string for JSON serialization
            export_data = self.unified_cache.copy()
            if export_data.get("last_updated"):
                export_data["last_updated"] = export_data["last_updated"].isoformat()
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported unified data to {output_path}")
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")

# Test the data source manager
if __name__ == "__main__":
    import tempfile
    import os
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_sources.json")
        
        # Create test data
        projects_dir = os.path.join(temp_dir, "projects")
        os.makedirs(projects_dir)
        
        # Sample project data
        sample_project = {
            "project_name": "Website Redesign",
            "client": "Acme Corp",
            "deadline": "2024-02-15",
            "status": "in_progress",
            "team_members": ["john", "jane", "bob"],
            "estimated_hours": 120,
            "difficulty": "medium"
        }
        
        with open(os.path.join(projects_dir, "website_project.json"), 'w') as f:
            json.dump(sample_project, f)
        
        # Test data source manager
        print("🧪 Testing Data Source Manager...")
        
        manager = DataSourceManager(config_path)
        
        # Add JSON folder source
        manager.add_data_source(
            "json_folder",
            "Test Projects",
            {
                "folder_path": projects_dir,
                "file_pattern": "*.json",
                "recursive": False
            }
        )
        
        # Sync data
        manager.sync_all_sources()
        
        # Test queries
        projects = manager.get_all_projects()
        print(f"✅ Found {len(projects)} projects")
        
        search_results = manager.search_data("website")
        print(f"✅ Search found {len(search_results)} results")
        
        status = manager.get_data_source_status()
        print(f"✅ {status['active_sources']} active sources out of {status['total_sources']}")
        
        print("✅ Data Source Manager test completed!")