#!/usr/bin/env python3
"""
Test script for AI Avatar Assistant components
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database():
    """Test database functionality"""
    print("🗄️  Testing Database...")
    
    try:
        from core.database import TaskDatabase
        
        db = TaskDatabase()
        
        # Test adding a task
        task_id = db.add_task(
            title="Test Task",
            description="This is a test task",
            deadline=datetime.now() + timedelta(hours=1),
            priority=3
        )
        
        print(f"✓ Created test task with ID: {task_id}")
        
        # Test retrieving tasks
        tasks = db.get_tasks()
        print(f"✓ Retrieved {len(tasks)} tasks from database")
        
        # Test updating task status
        success = db.update_task_status(task_id, "completed")
        print(f"✓ Updated task status: {success}")
        
        # Test events
        event_id = db.add_event(
            event_type="test",
            title="Test Event",
            trigger_time=datetime.now() + timedelta(minutes=5)
        )
        print(f"✓ Created test event with ID: {event_id}")
        
        print("✅ Database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_ai_engine():
    """Test AI engine functionality"""
    print("\n🧠 Testing AI Engine...")
    
    try:
        from core.ai_engine import AIEngine
        
        ai = AIEngine()
        
        # Test situation analysis
        recommendations = ai.analyze_current_situation()
        print(f"✓ Generated {len(recommendations)} recommendations")
        
        # Test urgency calculation
        urgency = ai.calculate_urgency(timedelta(hours=2), 4)
        print(f"✓ Calculated urgency: {urgency}")
        
        # Test time formatting
        time_str = ai.format_time_delta(timedelta(hours=2, minutes=30))
        print(f"✓ Formatted time delta: {time_str}")
        
        # Test personality message
        message = ai.get_personality_message("greeting")
        print(f"✓ Generated personality message: {message}")
        
        print("✅ AI Engine tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ AI Engine test failed: {e}")
        return False

def test_action_system():
    """Test action system functionality"""
    print("\n⚡ Testing Action System...")
    
    try:
        from core.actions import ActionSystem
        
        actions = ActionSystem()
        
        # Test action execution
        result = actions.execute_action("dismiss", {})
        print(f"✓ Executed dismiss action: {result.get('success', False)}")
        
        # Test getting available actions
        available = actions.get_available_actions()
        print(f"✓ Found {len(available)} available actions")
        
        # Test task-specific actions
        task_actions = actions.get_available_actions("task")
        print(f"✓ Found {len(task_actions)} task-specific actions")
        
        print("✅ Action System tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Action System test failed: {e}")
        return False

def test_scheduler():
    """Test scheduler functionality"""
    print("\n⏰ Testing Scheduler...")
    
    try:
        from core.scheduler import EventScheduler
        
        scheduler = EventScheduler()
        
        # Test scheduler status
        status = scheduler.get_status()
        print(f"✓ Scheduler status: running={status.get('running', False)}")
        
        # Test silent hours
        is_silent = scheduler.is_silent_hours()
        print(f"✓ Silent hours check: {is_silent}")
        
        # Test notification pause
        is_paused = scheduler.is_notifications_paused()
        print(f"✓ Notifications paused: {is_paused}")
        
        # Test event callback registration
        def test_callback(event_data):
            print(f"  Test callback received: {event_data.get('title', 'No title')}")
        
        scheduler.register_event_callback("test", test_callback)
        print("✓ Registered test callback")
        
        print("✅ Scheduler tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        return False

def test_ui_components():
    """Test UI components (without showing them)"""
    print("\n🖼️  Testing UI Components...")
    
    try:
        # Test imports without creating actual widgets
        from ui.avatar import AvatarWidget
        from ui.tooltip import TooltipWidget
        
        print("✓ Avatar widget import successful")
        print("✓ Tooltip widget import successful")
        
        # Test configuration loading
        from PyQt5.QtWidgets import QApplication
        import sys
        
        # Create minimal QApplication for testing
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        # Test widget creation (but don't show)
        avatar = AvatarWidget()
        tooltip = TooltipWidget()
        
        print("✓ Created avatar widget")
        print("✓ Created tooltip widget")
        
        print("✅ UI Component tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ UI Component test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n⚙️  Testing Configuration...")
    
    try:
        import json
        
        # Ensure config file exists
        os.makedirs("data", exist_ok=True)
        
        config_path = "data/config.json"
        if not os.path.exists(config_path):
            # Create default config for testing
            default_config = {
                "avatar": {"position": "bottom_right", "size": 64},
                "notifications": {"enabled": True, "check_interval": 300},
                "ai": {"personality": "friendly"}
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            print("✓ Created default configuration")
        
        # Test loading configuration
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"✓ Loaded configuration with {len(config)} sections")
        
        # Validate required sections
        required_sections = ["avatar", "notifications", "ai"]
        for section in required_sections:
            if section in config:
                print(f"✓ Found required section: {section}")
            else:
                print(f"⚠️  Missing section: {section}")
        
        print("✅ Configuration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_dependencies():
    """Test that all required dependencies are available"""
    print("\n📦 Testing Dependencies...")
    
    dependencies = [
        ("PyQt5", "PyQt5.QtWidgets"),
        ("APScheduler", "apscheduler.schedulers.qt"),
        ("JSON", "json"),
        ("SQLite3", "sqlite3"),
        ("Datetime", "datetime"),
        ("Logging", "logging"),
        ("OS", "os"),
        ("Sys", "sys")
    ]
    
    all_passed = True
    
    for name, module in dependencies:
        try:
            __import__(module)
            print(f"✓ {name} available")
        except ImportError as e:
            print(f"❌ {name} missing: {e}")
            all_passed = False
    
    if all_passed:
        print("✅ All dependencies available!")
    else:
        print("❌ Some dependencies are missing!")
    
    return all_passed

def run_all_tests():
    """Run all tests and return summary"""
    print("🚀 Starting AI Avatar Assistant System Tests...\n")
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Configuration", test_configuration),
        ("Database", test_database),
        ("AI Engine", test_ai_engine),
        ("Action System", test_action_system),
        ("Scheduler", test_scheduler),
        ("UI Components", test_ui_components)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The AI Avatar Assistant is ready to run.")
        print("To start the application, run: python main.py")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the issues above.")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)