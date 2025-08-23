#!/usr/bin/env python3
"""
AI Avatar Assistant - System Test
Quick test script to verify all components are working
"""

import os
import sys
import time
import subprocess

def test_dependencies():
    """Test if all required dependencies are installed"""
    print("🔧 Testing Dependencies...")
    
    required_packages = [
        'PyQt5',
        'flask', 
        'requests',
        'apscheduler',
        'psutil'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def test_directory_structure():
    """Test if required directories exist"""
    print("\n📁 Testing Directory Structure...")
    
    required_dirs = [
        'core',
        'ui', 
        'data',
        'logs'
    ]
    
    optional_dirs = [
        'assets',
        'data/demo',
        'data/reports'
    ]
    
    all_good = True
    
    # Test required directories
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ (missing)")
            all_good = False
    
    # Create optional directories
    for dir_name in optional_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            print(f"  📁 Created {dir_name}/")
        else:
            print(f"  ✅ {dir_name}/")
    
    return all_good

def test_core_components():
    """Test core components can be imported"""
    print("\n🧠 Testing Core Components...")
    
    components = [
        'core.ai_engine',
        'core.data_source_manager',
        'core.project_estimator', 
        'core.analytics_engine',
        'core.voice_system',
        'core.widget_api'
    ]
    
    all_good = True
    
    for component in components:
        try:
            __import__(component)
            print(f"  ✅ {component}")
        except Exception as e:
            print(f"  ❌ {component} - {str(e)}")
            all_good = False
    
    return all_good

def test_ui_components():
    """Test UI components can be imported"""
    print("\n🎨 Testing UI Components...")
    
    # Check if we can import PyQt5
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication([])  # Create minimal app for testing
        
        components = [
            'ui.avatar',
            'ui.tooltip',
            'ui.chat_interface',
            'ui.analytics_dashboard',
            'ui.settings_dashboard',
            'ui.widget_integration_dialog'
        ]
        
        all_good = True
        
        for component in components:
            try:
                __import__(component)
                print(f"  ✅ {component}")
            except Exception as e:
                print(f"  ❌ {component} - {str(e)}")
                all_good = False
        
        app.quit()
        return all_good
        
    except Exception as e:
        print(f"  ❌ PyQt5 not available - {str(e)}")
        return False

def test_demo_data():
    """Test if demo data can be created"""
    print("\n📊 Testing Demo Data Creation...")
    
    try:
        # Run the demo setup
        exec(open('demo.py').read().split('def main()')[0])
        demo = AIAvatarDemo()
        print("  ✅ Demo data created successfully")
        return True
    except Exception as e:
        print(f"  ❌ Demo data creation failed - {str(e)}")
        return False

def test_widget_api():
    """Test if widget API can start"""
    print("\n🔗 Testing Widget API...")
    
    try:
        from core.widget_api import WidgetIntegrationManager
        from core.data_source_manager import DataSourceManager
        from core.project_estimator import ProjectEstimator
        
        # Create minimal components
        data_manager = DataSourceManager()
        estimator = ProjectEstimator(data_manager)
        
        class MockAI:
            def __init__(self):
                self.analytics_engine = self
            def get_visual_analytics_data(self):
                return {"test": True}
        
        mock_ai = MockAI()
        widget_manager = WidgetIntegrationManager(mock_ai, data_manager, estimator)
        
        # Try to initialize (but don't actually start server)
        print("  ✅ Widget API components loaded")
        return True
        
    except Exception as e:
        print(f"  ❌ Widget API test failed - {str(e)}")
        return False

def run_quick_demo():
    """Run a quick demo of key features"""
    print("\n🎯 Running Quick Demo...")
    
    try:
        from core.data_source_manager import DataSourceManager
        from core.project_estimator import ProjectEstimator
        
        # Test data source manager
        print("  🗄️ Testing Data Source Manager...")
        data_manager = DataSourceManager()
        status = data_manager.get_data_source_status()
        print(f"    Data sources: {status['active_sources']}/{status['total_sources']}")
        
        # Test project estimator
        print("  📊 Testing Project Estimator...")
        estimator = ProjectEstimator(data_manager)
        
        # Simple estimation test
        estimate = estimator.estimate_project(
            "Build a simple React website",
            ["User interface", "Backend API"],
            ["react", "node.js"]
        )
        
        print(f"    Estimated hours: {estimate.total_hours}")
        print(f"    Difficulty: {estimate.difficulty_level}")
        print(f"    Confidence: {estimate.confidence_level:.1%}")
        
        print("  ✅ Quick demo completed successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Quick demo failed - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🤖 AI Avatar Assistant - System Test")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Directory Structure", test_directory_structure),
        ("Core Components", test_core_components),
        ("UI Components", test_ui_components),
        ("Widget API", test_widget_api),
        ("Quick Demo", run_quick_demo)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Run 'python demo.py' for a comprehensive demonstration")
        print("2. Run 'python main.py' to start the full application")
        print("3. Open the Widget Manager to create integrations")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Ensure you're in the ai_avatar_assistant directory")
        print("3. Check Python version (requires 3.8+)")

if __name__ == "__main__":
    main()