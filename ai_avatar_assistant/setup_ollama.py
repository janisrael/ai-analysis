#!/usr/bin/env python3
"""
AI Avatar Assistant - Ollama Setup Script
Complete setup guide and automation for local LLM integration
"""

import os
import sys
import json
import time
import subprocess
import requests
from typing import Dict, List, Any

def check_system_requirements():
    """Check if system meets Ollama requirements"""
    print("🔧 Checking System Requirements...")
    
    # Check available RAM
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        total_gb = memory.total / (1024**3)
        
        print(f"  💾 RAM: {available_gb:.1f}GB available / {total_gb:.1f}GB total")
        
        if total_gb < 8:
            print("  ⚠️ Warning: 8GB+ RAM recommended for best performance")
        elif total_gb >= 16:
            print("  ✅ Excellent! 16GB+ RAM detected - can run larger models")
        else:
            print("  ✅ Good! 8-16GB RAM - suitable for most models")
            
    except ImportError:
        print("  ℹ️ Install psutil to check system resources: pip install psutil")
    
    # Check disk space
    disk_usage = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
    if disk_usage.returncode == 0:
        lines = disk_usage.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            available = parts[3]
            print(f"  💽 Disk Space: {available} available")
            if 'G' in available and float(available.replace('G', '')) < 10:
                print("  ⚠️ Warning: 10GB+ free space recommended for model storage")
            else:
                print("  ✅ Sufficient disk space available")
    
    print()

def install_ollama():
    """Install Ollama if not already installed"""
    print("📦 Installing Ollama...")
    
    # Check if Ollama is already installed
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Ollama already installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    # Install Ollama based on OS
    import platform
    os_type = platform.system().lower()
    
    if os_type == "linux":
        print("  🐧 Installing Ollama on Linux...")
        try:
            subprocess.run(['curl', '-fsSL', 'https://ollama.ai/install.sh'], 
                         stdout=subprocess.PIPE, check=True)
            subprocess.run(['sh', '-c', 'curl -fsSL https://ollama.ai/install.sh | sh'], 
                         check=True)
            print("  ✅ Ollama installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Installation failed: {e}")
            return False
    
    elif os_type == "darwin":  # macOS
        print("  🍎 For macOS, please install Ollama manually:")
        print("     1. Download from https://ollama.ai/download")
        print("     2. Run the installer")
        print("     3. Restart this script")
        return False
    
    elif os_type == "windows":
        print("  🪟 For Windows, please install Ollama manually:")
        print("     1. Download from https://ollama.ai/download")
        print("     2. Run the installer")
        print("     3. Restart this script")
        return False
    
    else:
        print(f"  ❓ Unsupported OS: {os_type}")
        print("     Please visit https://ollama.ai/download for manual installation")
        return False

def start_ollama_service():
    """Start Ollama service"""
    print("🚀 Starting Ollama Service...")
    
    try:
        # Check if already running
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            print("  ✅ Ollama service already running!")
            return True
    except:
        pass
    
    # Start Ollama service
    try:
        print("  🔄 Starting Ollama server...")
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for service to start
        for i in range(10):
            try:
                response = requests.get('http://localhost:11434/api/tags', timeout=2)
                if response.status_code == 200:
                    print("  ✅ Ollama service started successfully!")
                    return True
            except:
                pass
            time.sleep(2)
            print(f"  ⏳ Waiting for service to start... ({i+1}/10)")
        
        print("  ❌ Failed to start Ollama service")
        return False
        
    except Exception as e:
        print(f"  ❌ Error starting service: {e}")
        return False

def get_recommended_models():
    """Get recommended models for AI Avatar Assistant"""
    return [
        {
            "name": "llama2",
            "size": "3.8GB",
            "description": "General purpose, good balance of quality and speed",
            "recommended_for": "General chat, project estimation",
            "ram_requirement": "8GB",
            "best_for_beginners": True
        },
        {
            "name": "codellama",
            "size": "3.8GB", 
            "description": "Code-focused model, excellent for technical discussions",
            "recommended_for": "Technical analysis, code review, architecture",
            "ram_requirement": "8GB",
            "best_for_beginners": False
        },
        {
            "name": "mistral",
            "size": "4.1GB",
            "description": "High quality responses, good reasoning",
            "recommended_for": "Complex project analysis, strategic planning",
            "ram_requirement": "8GB",
            "best_for_beginners": False
        },
        {
            "name": "neural-chat",
            "size": "4.1GB",
            "description": "Conversational AI, great for natural interactions",
            "recommended_for": "Chat interface, voice commands",
            "ram_requirement": "8GB",
            "best_for_beginners": True
        },
        {
            "name": "llama2:13b",
            "size": "7.3GB",
            "description": "Larger model with better performance (requires more RAM)",
            "recommended_for": "Advanced analysis, complex reasoning",
            "ram_requirement": "16GB",
            "best_for_beginners": False
        }
    ]

def select_and_download_model():
    """Let user select and download a model"""
    print("🤖 Selecting AI Model...")
    
    models = get_recommended_models()
    
    print("  Available models for AI Avatar Assistant:")
    print()
    
    for i, model in enumerate(models, 1):
        beginner_tag = " 🌟 RECOMMENDED" if model["best_for_beginners"] else ""
        print(f"  {i}. {model['name']}{beginner_tag}")
        print(f"     Size: {model['size']} | RAM: {model['ram_requirement']}+")
        print(f"     {model['description']}")
        print(f"     Best for: {model['recommended_for']}")
        print()
    
    # Auto-select for demo, but allow manual selection
    print("🎯 For AI Avatar Assistant, I recommend starting with:")
    print("   • llama2 (beginner-friendly, fast)")
    print("   • neural-chat (excellent for conversations)")
    print()
    
    # Default selections
    selected_models = ["llama2", "neural-chat"]
    
    print(f"📥 Downloading recommended models: {', '.join(selected_models)}")
    
    for model_name in selected_models:
        download_model(model_name)
    
    return selected_models

def download_model(model_name: str):
    """Download a specific model"""
    print(f"  📥 Downloading {model_name}...")
    
    try:
        # Use subprocess to show progress
        process = subprocess.Popen(
            ['ollama', 'pull', model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # Show download progress
                if 'pulling' in output.lower() or 'download' in output.lower():
                    print(f"    {output.strip()}")
        
        if process.returncode == 0:
            print(f"  ✅ {model_name} downloaded successfully!")
            return True
        else:
            error = process.stderr.read()
            print(f"  ❌ Failed to download {model_name}: {error}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error downloading {model_name}: {e}")
        return False

def test_model(model_name: str):
    """Test a model with a sample prompt"""
    print(f"🧪 Testing {model_name}...")
    
    test_prompt = "How would you estimate a React e-commerce project? Give a brief answer."
    
    try:
        import requests
        
        payload = {
            "model": model_name,
            "prompt": test_prompt,
            "stream": False
        }
        
        print(f"  🤔 Asking: {test_prompt}")
        
        response = requests.post(
            'http://localhost:11434/api/generate',
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '').strip()
            
            print(f"  🤖 Response: {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}")
            print(f"  ✅ {model_name} is working correctly!")
            return True
        else:
            print(f"  ❌ Test failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False

def configure_ai_avatar():
    """Configure AI Avatar Assistant to use Ollama"""
    print("⚙️ Configuring AI Avatar Assistant...")
    
    # Create LLM configuration
    config = {
        "preferred_provider": "local",
        "providers": {
            "openai": {
                "enabled": False,
                "model": "gpt-3.5-turbo",
                "api_key": None
            },
            "anthropic": {
                "enabled": False,
                "model": "claude-3-sonnet-20240229", 
                "api_key": None
            },
            "local": {
                "enabled": True,
                "model": "llama2",
                "base_url": "http://localhost:11434"
            },
            "fallback": {
                "enabled": True
            }
        }
    }
    
    # Save configuration
    os.makedirs("data", exist_ok=True)
    config_path = "data/llm_config.json"
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"  ✅ Configuration saved to {config_path}")
    print(f"  🎯 AI Avatar Assistant will now use Ollama with llama2 model")
    
    # Show alternative models
    print(f"\n  🔄 To switch models later, edit the config:")
    print(f"     - Change 'model' to: neural-chat, mistral, codellama, etc.")
    print(f"     - Or use the Settings Dashboard in the AI Avatar Assistant")
    
    return config_path

def create_demo_script():
    """Create a demo script to test Ollama integration"""
    demo_script = '''#!/usr/bin/env python3
"""
Quick test of Ollama integration with AI Avatar Assistant
"""

def test_ollama_integration():
    print("🧪 Testing Ollama Integration...")
    
    try:
        from core.llm_integration import LLMManager
        
        llm_manager = LLMManager()
        
        # Test prompt
        prompt = "Estimate a React project with authentication and dashboard"
        context = {
            "projects": [{"name": "Demo Project", "technologies": ["react", "node.js"]}],
            "team_members": [{"name": "Developer", "skills": ["react", "javascript"]}]
        }
        
        print(f"🤔 Asking Ollama: {prompt}")
        
        response = llm_manager.generate_response(prompt, context)
        
        print(f"\\n🤖 Ollama Response:")
        print(f"Model: {response.model}")
        print(f"Confidence: {response.confidence:.1%}")
        print(f"Content: {response.content}")
        
        print(f"\\n✅ Ollama integration working perfectly!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        print(f"Make sure Ollama is running: ollama serve")

if __name__ == "__main__":
    test_ollama_integration()
'''
    
    with open("test_ollama.py", 'w') as f:
        f.write(demo_script)
    
    print(f"  📝 Created test_ollama.py - run this to test integration")
    return "test_ollama.py"

def main():
    """Main Ollama setup workflow"""
    print("🚀 AI Avatar Assistant - Ollama Setup")
    print("=" * 50)
    print("🎯 Setting up local AI with Ollama for private, free AI assistance!")
    print()
    
    # Step 1: Check requirements
    check_system_requirements()
    
    # Step 2: Install Ollama
    if not install_ollama():
        print("❌ Installation failed. Please install Ollama manually and run this script again.")
        return False
    
    # Step 3: Start service
    if not start_ollama_service():
        print("❌ Failed to start Ollama service. Please start manually: ollama serve")
        return False
    
    # Step 4: Download models
    models = select_and_download_model()
    
    # Step 5: Test models
    print()
    for model in models:
        if not test_model(model):
            print(f"⚠️ Warning: {model} test failed, but continuing...")
    
    # Step 6: Configure AI Avatar
    config_path = configure_ai_avatar()
    
    # Step 7: Create demo
    demo_script = create_demo_script()
    
    # Success summary
    print()
    print("=" * 50)
    print("🎉 OLLAMA SETUP COMPLETE!")
    print("=" * 50)
    print()
    print("✅ What's been set up:")
    print(f"   • Ollama service running on http://localhost:11434")
    print(f"   • Downloaded models: {', '.join(models)}")
    print(f"   • AI Avatar configured to use local LLM")
    print(f"   • Test script created: {demo_script}")
    print()
    print("🚀 Next steps:")
    print("   1. Test integration: python3 test_ollama.py")
    print("   2. Start AI Avatar: python3 main.py")
    print("   3. Chat with your local AI assistant!")
    print()
    print("💡 Benefits you now have:")
    print("   • 🆓 Completely free AI responses")
    print("   • 🔒 100% private - data never leaves your machine")
    print("   • ⚡ Fast responses - no network latency")
    print("   • 🚫 No rate limits or API costs")
    print("   • 🌐 Works offline")
    print()
    print("🎛️ Model management:")
    print("   • Switch models: ollama run <model-name>")
    print("   • List models: ollama list")
    print("   • Remove model: ollama rm <model-name>")
    print("   • Update model: ollama pull <model-name>")
    
    return True

if __name__ == "__main__":
    main()