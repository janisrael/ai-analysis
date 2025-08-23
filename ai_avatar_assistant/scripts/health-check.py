#!/usr/bin/env python3
"""
AI Avatar Assistant - Health Check Script
Comprehensive health monitoring for production deployment
"""

import os
import sys
import json
import time
import requests
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class HealthChecker:
    """Comprehensive health check for AI Avatar Assistant"""
    
    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []
        self.start_time = time.time()
        
        # Configuration
        self.widget_api_port = int(os.getenv('WIDGET_API_PORT', '5555'))
        self.web_port = int(os.getenv('WEB_PORT', '8080'))
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///data/ai_avatar.db')
        
    def add_check(self, name: str, status: str, message: str, details: Optional[Dict] = None):
        """Add a health check result"""
        self.checks.append({
            "name": name,
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
        
        if status == "warning":
            self.warnings.append(f"{name}: {message}")
        elif status == "error":
            self.errors.append(f"{name}: {message}")
    
    def check_core_dependencies(self) -> bool:
        """Check if core Python dependencies are available"""
        try:
            required_modules = [
                'flask', 'requests', 'apscheduler', 'psutil',
                'sqlite3', 'json', 'datetime', 'threading'
            ]
            
            missing = []
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing.append(module)
            
            if missing:
                self.add_check(
                    "Core Dependencies",
                    "error",
                    f"Missing required modules: {', '.join(missing)}",
                    {"missing_modules": missing}
                )
                return False
            else:
                self.add_check(
                    "Core Dependencies",
                    "healthy",
                    "All core dependencies available"
                )
                return True
                
        except Exception as e:
            self.add_check(
                "Core Dependencies",
                "error",
                f"Failed to check dependencies: {str(e)}"
            )
            return False
    
    def check_filesystem(self) -> bool:
        """Check filesystem health and permissions"""
        try:
            required_dirs = ['data', 'logs', 'reports', 'temp']
            issues = []
            
            for dir_name in required_dirs:
                if not os.path.exists(dir_name):
                    try:
                        os.makedirs(dir_name, exist_ok=True)
                    except Exception as e:
                        issues.append(f"Cannot create {dir_name}: {str(e)}")
                        continue
                
                # Check write permissions
                test_file = os.path.join(dir_name, 'health_check_test.tmp')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                except Exception as e:
                    issues.append(f"Cannot write to {dir_name}: {str(e)}")
            
            # Check disk space
            try:
                stat = os.statvfs('.')
                free_bytes = stat.f_bavail * stat.f_frsize
                free_gb = free_bytes / (1024**3)
                
                if free_gb < 1:
                    issues.append(f"Low disk space: {free_gb:.2f}GB available")
                elif free_gb < 5:
                    self.add_check(
                        "Disk Space",
                        "warning",
                        f"Disk space getting low: {free_gb:.2f}GB available"
                    )
            except:
                issues.append("Cannot check disk space")
            
            if issues:
                self.add_check(
                    "Filesystem",
                    "error",
                    f"Filesystem issues: {'; '.join(issues)}",
                    {"issues": issues}
                )
                return False
            else:
                self.add_check(
                    "Filesystem",
                    "healthy",
                    "Filesystem is healthy"
                )
                return True
                
        except Exception as e:
            self.add_check(
                "Filesystem",
                "error",
                f"Filesystem check failed: {str(e)}"
            )
            return False
    
    def check_database(self) -> bool:
        """Check database connectivity and integrity"""
        try:
            # Check SQLite database
            if self.database_url.startswith('sqlite'):
                db_path = self.database_url.replace('sqlite:///', '')
                
                if not os.path.exists(db_path):
                    self.add_check(
                        "Database",
                        "warning",
                        f"Database file does not exist: {db_path}"
                    )
                    return True  # Will be created on first run
                
                # Test connection
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = ['tasks', 'events', 'user_actions']
                missing_tables = [t for t in expected_tables if t not in tables]
                
                if missing_tables:
                    self.add_check(
                        "Database",
                        "warning",
                        f"Missing tables: {', '.join(missing_tables)}",
                        {"missing_tables": missing_tables}
                    )
                else:
                    # Test a simple query
                    cursor.execute("SELECT COUNT(*) FROM tasks")
                    task_count = cursor.fetchone()[0]
                    
                    self.add_check(
                        "Database",
                        "healthy",
                        f"Database is healthy ({task_count} tasks)",
                        {"task_count": task_count, "tables": tables}
                    )
                
                conn.close()
                return True
                
            else:
                # For other database types, just mark as not checked
                self.add_check(
                    "Database",
                    "warning",
                    "Database type not supported in health check"
                )
                return True
                
        except Exception as e:
            self.add_check(
                "Database",
                "error",
                f"Database check failed: {str(e)}"
            )
            return False
    
    def check_widget_api(self) -> bool:
        """Check if Widget API is responding"""
        try:
            url = f"http://localhost:{self.widget_api_port}/api/status"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.add_check(
                    "Widget API",
                    "healthy",
                    f"Widget API is responding",
                    {"status_code": response.status_code, "response": data}
                )
                return True
            else:
                self.add_check(
                    "Widget API",
                    "error",
                    f"Widget API returned status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
                
        except requests.exceptions.ConnectionError:
            self.add_check(
                "Widget API",
                "error",
                f"Cannot connect to Widget API on port {self.widget_api_port}"
            )
            return False
        except Exception as e:
            self.add_check(
                "Widget API",
                "error",
                f"Widget API check failed: {str(e)}"
            )
            return False
    
    def check_core_components(self) -> bool:
        """Check if core AI components can be imported and initialized"""
        try:
            # Test imports
            sys.path.insert(0, '/app' if os.path.exists('/app') else '.')
            
            components_status = {}
            
            # Test DataSourceManager
            try:
                from core.data_source_manager import DataSourceManager
                dsm = DataSourceManager()
                status = dsm.get_data_source_status()
                components_status["data_source_manager"] = {
                    "status": "healthy",
                    "active_sources": status.get("active_sources", 0),
                    "total_sources": status.get("total_sources", 0)
                }
            except Exception as e:
                components_status["data_source_manager"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Test ProjectEstimator
            try:
                from core.project_estimator import ProjectEstimator
                estimator = ProjectEstimator(dsm if 'dsm' in locals() else None)
                components_status["project_estimator"] = {"status": "healthy"}
            except Exception as e:
                components_status["project_estimator"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Test VoiceSystem
            try:
                from core.voice_system import VoiceNotificationSystem
                voice = VoiceNotificationSystem()
                components_status["voice_system"] = {
                    "status": "healthy" if voice.is_available() else "warning",
                    "available": voice.is_available()
                }
            except Exception as e:
                components_status["voice_system"] = {
                    "status": "warning",
                    "error": str(e)
                }
            
            # Test AnalyticsEngine
            try:
                from core.analytics_engine import LiveAnalyticsEngine
                analytics = LiveAnalyticsEngine()
                analytics_data = analytics.get_visual_analytics_data()
                components_status["analytics_engine"] = {
                    "status": "healthy",
                    "charts": len(analytics_data.get("charts", [])),
                    "metrics": len(analytics_data.get("metrics", {}))
                }
            except Exception as e:
                components_status["analytics_engine"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Determine overall status
            errors = [name for name, status in components_status.items() 
                     if status["status"] == "error"]
            warnings = [name for name, status in components_status.items() 
                       if status["status"] == "warning"]
            
            if errors:
                self.add_check(
                    "Core Components",
                    "error",
                    f"Failed components: {', '.join(errors)}",
                    components_status
                )
                return False
            elif warnings:
                self.add_check(
                    "Core Components",
                    "warning",
                    f"Components with warnings: {', '.join(warnings)}",
                    components_status
                )
                return True
            else:
                self.add_check(
                    "Core Components",
                    "healthy",
                    "All core components are healthy",
                    components_status
                )
                return True
                
        except Exception as e:
            self.add_check(
                "Core Components",
                "error",
                f"Core components check failed: {str(e)}"
            )
            return False
    
    def check_system_resources(self) -> bool:
        """Check system resource usage"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('.')
            disk_percent = (disk.used / disk.total) * 100
            
            # Process count
            process_count = len(psutil.pids())
            
            resources = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk_percent,
                "disk_free_gb": disk.free / (1024**3),
                "process_count": process_count
            }
            
            # Determine status
            issues = []
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory_percent > 90:
                issues.append(f"High memory usage: {memory_percent:.1f}%")
            if disk_percent > 90:
                issues.append(f"High disk usage: {disk_percent:.1f}%")
            
            if issues:
                self.add_check(
                    "System Resources",
                    "warning",
                    f"Resource concerns: {'; '.join(issues)}",
                    resources
                )
            else:
                self.add_check(
                    "System Resources",
                    "healthy",
                    f"System resources are healthy",
                    resources
                )
            
            return True
            
        except Exception as e:
            self.add_check(
                "System Resources",
                "error",
                f"System resource check failed: {str(e)}"
            )
            return False
    
    def check_configuration(self) -> bool:
        """Check configuration files"""
        try:
            config_files = [
                'data/config.json',
                'data/data_sources.json'
            ]
            
            config_status = {}
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    try:
                        with open(config_file, 'r') as f:
                            config_data = json.load(f)
                        config_status[config_file] = {
                            "status": "healthy",
                            "size": len(json.dumps(config_data)),
                            "keys": list(config_data.keys())
                        }
                    except Exception as e:
                        config_status[config_file] = {
                            "status": "error",
                            "error": str(e)
                        }
                else:
                    config_status[config_file] = {
                        "status": "warning",
                        "message": "File does not exist"
                    }
            
            errors = [f for f, s in config_status.items() if s["status"] == "error"]
            warnings = [f for f, s in config_status.items() if s["status"] == "warning"]
            
            if errors:
                self.add_check(
                    "Configuration",
                    "error",
                    f"Configuration errors in: {', '.join(errors)}",
                    config_status
                )
                return False
            elif warnings:
                self.add_check(
                    "Configuration",
                    "warning",
                    f"Configuration warnings: {', '.join(warnings)}",
                    config_status
                )
                return True
            else:
                self.add_check(
                    "Configuration",
                    "healthy",
                    "All configuration files are healthy",
                    config_status
                )
                return True
                
        except Exception as e:
            self.add_check(
                "Configuration",
                "error",
                f"Configuration check failed: {str(e)}"
            )
            return False
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        print("🔍 Running AI Avatar Assistant Health Check...")
        
        # Run all checks
        checks = [
            ("Core Dependencies", self.check_core_dependencies),
            ("Filesystem", self.check_filesystem),
            ("Database", self.check_database),
            ("Configuration", self.check_configuration),
            ("Core Components", self.check_core_components),
            ("System Resources", self.check_system_resources),
            ("Widget API", self.check_widget_api),
        ]
        
        results = {}
        for check_name, check_func in checks:
            print(f"  Checking {check_name}...")
            try:
                results[check_name] = check_func()
            except Exception as e:
                self.add_check(
                    check_name,
                    "error",
                    f"Check failed with exception: {str(e)}"
                )
                results[check_name] = False
        
        # Calculate overall health
        total_checks = len(self.checks)
        healthy_checks = len([c for c in self.checks if c["status"] == "healthy"])
        warning_checks = len([c for c in self.checks if c["status"] == "warning"])
        error_checks = len([c for c in self.checks if c["status"] == "error"])
        
        overall_status = "healthy"
        if error_checks > 0:
            overall_status = "unhealthy"
        elif warning_checks > 0:
            overall_status = "degraded"
        
        duration = time.time() - self.start_time
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "duration_seconds": round(duration, 2),
            "summary": {
                "total_checks": total_checks,
                "healthy": healthy_checks,
                "warnings": warning_checks,
                "errors": error_checks
            },
            "checks": self.checks,
            "warnings": self.warnings,
            "errors": self.errors
        }
        
        return health_report
    
    def print_summary(self, health_report: Dict[str, Any]):
        """Print health check summary"""
        status = health_report["overall_status"]
        summary = health_report["summary"]
        
        # Status emoji
        if status == "healthy":
            status_emoji = "✅"
        elif status == "degraded":
            status_emoji = "⚠️"
        else:
            status_emoji = "❌"
        
        print(f"\n{status_emoji} Health Check Complete - Status: {status.upper()}")
        print(f"📊 Summary: {summary['healthy']} healthy, {summary['warnings']} warnings, {summary['errors']} errors")
        print(f"⏱️ Duration: {health_report['duration_seconds']}s")
        
        if self.warnings:
            print("\n⚠️ Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  • {error}")
        
        print()

def main():
    """Main health check entry point"""
    checker = HealthChecker()
    health_report = checker.run_all_checks()
    checker.print_summary(health_report)
    
    # Save health report
    os.makedirs('logs', exist_ok=True)
    report_path = f"logs/health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(health_report, f, indent=2)
    
    # Exit with appropriate code
    if health_report["overall_status"] == "unhealthy":
        sys.exit(1)
    elif health_report["overall_status"] == "degraded":
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()