#!/usr/bin/env python3
"""
AI Avatar Assistant - Installation Script

This script helps install and set up the AI Avatar Assistant on your system.
"""

import os
import sys
import subprocess
import platform
import json
import shutil
from pathlib import Path

class AIAvatarInstaller:
    """Installer for AI Avatar Assistant"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.python_version = sys.version_info
        self.project_dir = Path(__file__).parent
        self.data_dir = self.project_dir / "data"
        self.assets_dir = self.project_dir / "assets"
        
    def print_header(self):
        """Print installation header"""
        print("=" * 60)
        print("🤖 AI Avatar Assistant - Installation Script")
        print("=" * 60)
        print(f"Python Version: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        print(f"Operating System: {platform.system()} {platform.release()}")
        print(f"Architecture: {platform.machine()}")
        print()
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        print("🐍 Checking Python version...")
        
        if self.python_version < (3, 8):
            print("❌ Python 3.8 or higher is required!")
            print(f"   Current version: {self.python_version.major}.{self.python_version.minor}")
            print("   Please upgrade Python and try again.")
            return False
        
        print(f"✅ Python {self.python_version.major}.{self.python_version.minor} is compatible")
        return True
    
    def check_pip(self):
        """Check if pip is available"""
        print("\n📦 Checking pip availability...")
        
        try:
            import pip
            print("✅ pip is available")
            return True
        except ImportError:
            try:
                subprocess.run([sys.executable, "-m", "ensurepip", "--default-pip"], 
                             check=True, capture_output=True)
                print("✅ pip installed successfully")
                return True
            except subprocess.CalledProcessError:
                print("❌ pip is not available and could not be installed")
                print("   Please install pip manually and try again.")
                return False
    
    def install_dependencies(self):
        """Install required Python packages"""
        print("\n📚 Installing dependencies...")
        
        requirements_file = self.project_dir / "requirements.txt"
        if not requirements_file.exists():
            print("❌ requirements.txt not found!")
            return False
        
        try:
            # Upgrade pip first
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            print("✅ pip upgraded")
            
            # Install requirements
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                         check=True)
            print("✅ All dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            print("   You can try installing manually with:")
            print(f"   pip install -r {requirements_file}")
            return False
    
    def create_directories(self):
        """Create necessary directories"""
        print("\n📁 Creating directories...")
        
        directories = [
            self.data_dir,
            self.assets_dir,
            self.assets_dir / "icons"
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created: {directory}")
            except Exception as e:
                print(f"❌ Failed to create {directory}: {e}")
                return False
        
        return True
    
    def create_configuration(self):
        """Create default configuration files"""
        print("\n⚙️ Creating configuration...")
        
        config_file = self.data_dir / "config.json"
        
        if config_file.exists():
            print("✅ Configuration file already exists")
            return True
        
        default_config = {
            "avatar": {
                "position": "bottom_right",
                "always_on_top": True,
                "size": 64,
                "animation_speed": 1.0
            },
            "notifications": {
                "enabled": True,
                "silent_hours_start": "22:00",
                "silent_hours_end": "08:00",
                "auto_hide_timeout": 10,
                "check_interval": 300
            },
            "ai": {
                "personality": "friendly",
                "confidence_threshold": 0.7,
                "learning_enabled": True
            },
            "integrations": {
                "google_calendar": False,
                "email_check": False,
                "system_monitoring": True
            },
            "external_apis": {
                "openweather_api_key": "",
                "news_api_key": "",
                "default_city": "London",
                "news_country": "us",
                "enabled_integrations": {
                    "weather": False,
                    "news": False,
                    "quotes": True,
                    "world_time": True,
                    "system_stats": True
                }
            }
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            print(f"✅ Created configuration file: {config_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to create configuration: {e}")
            return False
    
    def create_startup_scripts(self):
        """Create startup scripts for different platforms"""
        print("\n🚀 Creating startup scripts...")
        
        if self.system == "windows":
            self.create_windows_startup()
        elif self.system == "darwin":  # macOS
            self.create_macos_startup()
        else:  # Linux and others
            self.create_linux_startup()
        
        return True
    
    def create_windows_startup(self):
        """Create Windows startup script"""
        script_content = f'''@echo off
cd /d "{self.project_dir}"
"{sys.executable}" main.py
pause
'''
        
        bat_file = self.project_dir / "start_assistant.bat"
        try:
            with open(bat_file, 'w') as f:
                f.write(script_content)
            print(f"✅ Created Windows startup script: {bat_file}")
            
            # Create shortcut instructions
            print("   To start automatically with Windows:")
            print(f"   1. Right-click 'start_assistant.bat' and create a shortcut")
            print(f"   2. Move the shortcut to: %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup")
            
        except Exception as e:
            print(f"❌ Failed to create Windows startup script: {e}")
    
    def create_macos_startup(self):
        """Create macOS startup script"""
        script_content = f'''#!/bin/bash
cd "{self.project_dir}"
"{sys.executable}" main.py
'''
        
        script_file = self.project_dir / "start_assistant.sh"
        try:
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # Make executable
            os.chmod(script_file, 0o755)
            print(f"✅ Created macOS startup script: {script_file}")
            
            print("   To start automatically with macOS:")
            print("   1. Open 'System Preferences' > 'Users & Groups'")
            print("   2. Select your user and click 'Login Items'")
            print(f"   3. Add '{script_file}' to the list")
            
        except Exception as e:
            print(f"❌ Failed to create macOS startup script: {e}")
    
    def create_linux_startup(self):
        """Create Linux startup script"""
        script_content = f'''#!/bin/bash
cd "{self.project_dir}"
"{sys.executable}" main.py
'''
        
        script_file = self.project_dir / "start_assistant.sh"
        try:
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # Make executable
            os.chmod(script_file, 0o755)
            print(f"✅ Created Linux startup script: {script_file}")
            
            # Create desktop entry
            desktop_entry = f'''[Desktop Entry]
Name=AI Avatar Assistant
Comment=Intelligent AI assistant with floating avatar
Exec={script_file}
Icon={self.assets_dir}/avatar.png
Type=Application
Categories=Utility;Office;
StartupNotify=true
'''
            
            desktop_file = self.project_dir / "ai-avatar-assistant.desktop"
            with open(desktop_file, 'w') as f:
                f.write(desktop_entry)
            
            print(f"✅ Created desktop entry: {desktop_file}")
            print("   To start automatically with Linux:")
            print("   1. Copy the .desktop file to ~/.config/autostart/")
            print(f"   2. Or run: cp {desktop_file} ~/.config/autostart/")
            
        except Exception as e:
            print(f"❌ Failed to create Linux startup script: {e}")
    
    def test_installation(self):
        """Test the installation by importing modules"""
        print("\n🧪 Testing installation...")
        
        test_modules = [
            ("PyQt5.QtWidgets", "PyQt5"),
            ("apscheduler.schedulers.qt", "APScheduler"),
            ("requests", "Requests"),
            ("PIL", "Pillow")
        ]
        
        failed_imports = []
        
        for module, package in test_modules:
            try:
                __import__(module)
                print(f"✅ {package} imported successfully")
            except ImportError:
                print(f"❌ {package} failed to import")
                failed_imports.append(package)
        
        if failed_imports:
            print(f"\n⚠️  Some packages failed to import: {', '.join(failed_imports)}")
            print("   You may need to install them manually:")
            for package in failed_imports:
                print(f"   pip install {package.lower()}")
            return False
        
        print("\n✅ All modules imported successfully!")
        return True
    
    def create_sample_data(self):
        """Offer to create sample data"""
        print("\n📊 Sample Data Creation")
        
        response = input("Would you like to create sample tasks for testing? (y/n): ").lower()
        
        if response in ['y', 'yes']:
            try:
                # Import and run the sample data creation
                from create_sample_data import create_sample_tasks
                create_sample_tasks()
                print("✅ Sample data created successfully")
            except Exception as e:
                print(f"❌ Failed to create sample data: {e}")
                print("   You can create it later by running: python create_sample_data.py")
    
    def print_post_install_instructions(self):
        """Print post-installation instructions"""
        print("\n" + "=" * 60)
        print("🎉 Installation Complete!")
        print("=" * 60)
        
        print("\n📋 Next Steps:")
        print("1. Run the application:")
        if self.system == "windows":
            print("   - Double-click 'start_assistant.bat'")
        else:
            print("   - Run './start_assistant.sh' or 'python main.py'")
        
        print("\n2. Optional Configuration:")
        print("   - Edit 'data/config.json' to customize settings")
        print("   - Add API keys for weather and news features")
        print("   - Adjust avatar position and notification preferences")
        
        print("\n3. External API Setup (Optional):")
        print("   - Weather: Get free API key from https://openweathermap.org/api")
        print("   - News: Get free API key from https://newsapi.org/")
        print("   - Add keys to 'data/config.json' under 'external_apis'")
        
        print("\n4. Test the System:")
        print("   - Run 'python test_system.py' to verify everything works")
        
        print("\n🆘 Need Help?")
        print("   - Check 'README.md' for detailed usage instructions")
        print("   - Look at logs in 'data/assistant.log' for troubleshooting")
        
        print("\n✨ Enjoy your AI Avatar Assistant!")
    
    def run_installation(self):
        """Run the complete installation process"""
        self.print_header()
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Checking pip", self.check_pip),
            ("Installing dependencies", self.install_dependencies),
            ("Creating directories", self.create_directories),
            ("Creating configuration", self.create_configuration),
            ("Creating startup scripts", self.create_startup_scripts),
            ("Testing installation", self.test_installation),
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                print(f"\n❌ Installation failed at: {step_name}")
                print("   Please resolve the issues above and try again.")
                return False
        
        # Optional sample data
        self.create_sample_data()
        
        # Success!
        self.print_post_install_instructions()
        return True

def main():
    """Main installation function"""
    installer = AIAvatarInstaller()
    
    try:
        success = installer.run_installation()
        exit_code = 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation cancelled by user")
        exit_code = 1
    except Exception as e:
        print(f"\n❌ Unexpected error during installation: {e}")
        print("   Please report this issue with the error details above.")
        exit_code = 1
    
    input("\nPress Enter to exit...")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()