#!/usr/bin/env python3
"""
AI Avatar Assistant - LLM Integration Demo
Demonstrate how to configure and use different LLM providers
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

def demo_llm_configuration():
    """Demonstrate LLM configuration options"""
    print("🧠 AI Avatar Assistant - LLM Integration Demo")
    print("=" * 55)
    
    print("🔧 Available LLM Providers:")
    print()
    
    providers = [
        {
            "name": "OpenAI GPT",
            "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            "setup": "Set OPENAI_API_KEY environment variable",
            "cost": "$0.001-0.03 per 1K tokens",
            "pros": ["High quality", "Fast", "Well-supported"],
            "cons": ["Requires API key", "Costs money"]
        },
        {
            "name": "Anthropic Claude",
            "models": ["claude-3-sonnet", "claude-3-opus", "claude-3-haiku"],
            "setup": "Set ANTHROPIC_API_KEY environment variable",
            "cost": "$0.003-0.075 per 1K tokens",
            "pros": ["Excellent reasoning", "Long context", "Safe"],
            "cons": ["Requires API key", "Costs money"]
        },
        {
            "name": "Local LLM (Ollama)",
            "models": ["llama2", "codellama", "mistral", "neural-chat"],
            "setup": "Install Ollama and pull models",
            "cost": "Free (uses local compute)",
            "pros": ["Free", "Private", "No API limits"],
            "cons": ["Requires local setup", "Resource intensive"]
        },
        {
            "name": "Fallback (Rule-based)",
            "models": ["Built-in patterns"],
            "setup": "Always available",
            "cost": "Free",
            "pros": ["No setup", "Fast", "Reliable"],
            "cons": ["Limited capabilities", "Not as intelligent"]
        }
    ]
    
    for i, provider in enumerate(providers, 1):
        print(f"{i}. **{provider['name']}**")
        print(f"   Models: {', '.join(provider['models'])}")
        print(f"   Setup: {provider['setup']}")
        print(f"   Cost: {provider['cost']}")
        print(f"   Pros: {', '.join(provider['pros'])}")
        print(f"   Cons: {', '.join(provider['cons'])}")
        print()

def demo_llm_responses():
    """Demonstrate responses from different providers"""
    print("💬 LLM Response Comparison")
    print("-" * 40)
    
    try:
        from core.llm_integration import LLMManager
        
        llm_manager = LLMManager()
        
        # Test prompt
        test_prompt = "How would you estimate a React e-commerce project with user auth, product catalog, and payment integration?"
        
        # Mock context
        context = {
            "projects": [
                {
                    "name": "E-commerce Platform",
                    "technologies": ["react", "node.js", "stripe", "postgresql"],
                    "status": "planning"
                }
            ],
            "team_members": [
                {"name": "Alice", "skills": ["react", "typescript"]},
                {"name": "Bob", "skills": ["node.js", "postgresql"]}
            ],
            "analytics": {
                "total_projects": 5,
                "avg_completion": 88
            }
        }
        
        print(f"🎯 Test Prompt: {test_prompt}")
        print()
        
        # Check available providers
        available_providers = llm_manager.get_available_providers()
        provider_status = llm_manager.get_provider_status()
        
        print("📊 Provider Status:")
        for provider_name, status in provider_status.items():
            status_icon = "✅" if status["available"] else "❌"
            enabled_icon = "🟢" if status["enabled"] else "🔴"
            print(f"  {status_icon} {provider_name} - Available: {status['available']}, Enabled: {status['enabled']} {enabled_icon}")
        print()
        
        # Generate response with current setup
        print("🤖 AI Response:")
        print("-" * 20)
        
        response = llm_manager.generate_response(test_prompt, context)
        
        print(f"Provider: {response.model or 'Fallback'}")
        print(f"Confidence: {response.confidence:.1%}")
        print(f"Tokens: {response.usage_tokens or 'N/A'}")
        print(f"Timestamp: {response.timestamp.strftime('%H:%M:%S')}")
        print()
        print("Response:")
        print(response.content)
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ LLM demo failed: {e}")
        return False

def show_configuration_examples():
    """Show how to configure different LLM providers"""
    print("⚙️ Configuration Examples")
    print("-" * 40)
    
    print("1. **OpenAI Configuration:**")
    print("```bash")
    print("# Set environment variable")
    print("export OPENAI_API_KEY=\"your-api-key-here\"")
    print()
    print("# Or in data/llm_config.json:")
    openai_config = {
        "preferred_provider": "openai",
        "providers": {
            "openai": {
                "enabled": True,
                "model": "gpt-3.5-turbo",
                "api_key": "your-api-key-here"
            }
        }
    }
    print(json.dumps(openai_config, indent=2))
    print("```")
    print()
    
    print("2. **Anthropic Configuration:**")
    print("```bash")
    print("# Set environment variable")
    print("export ANTHROPIC_API_KEY=\"your-api-key-here\"")
    print()
    print("# Or in data/llm_config.json:")
    anthropic_config = {
        "preferred_provider": "anthropic",
        "providers": {
            "anthropic": {
                "enabled": True,
                "model": "claude-3-sonnet-20240229",
                "api_key": "your-api-key-here"
            }
        }
    }
    print(json.dumps(anthropic_config, indent=2))
    print("```")
    print()
    
    print("3. **Local LLM (Ollama) Setup:**")
    print("```bash")
    print("# Install Ollama")
    print("curl -fsSL https://ollama.ai/install.sh | sh")
    print()
    print("# Pull a model")
    print("ollama pull llama2")
    print()
    print("# Start Ollama server")
    print("ollama serve")
    print()
    print("# Configure in data/llm_config.json:")
    local_config = {
        "preferred_provider": "local",
        "providers": {
            "local": {
                "enabled": True,
                "model": "llama2",
                "base_url": "http://localhost:11434"
            }
        }
    }
    print(json.dumps(local_config, indent=2))
    print("```")
    print()

def demo_integration_examples():
    """Show how to integrate LLM into the AI Avatar Assistant"""
    print("🔗 Integration Examples")
    print("-" * 40)
    
    print("**1. Chat Interface Integration:**")
    print("```python")
    print("""from core.llm_integration import create_llm_manager

class ChatInterface:
    def __init__(self):
        self.llm_manager = create_llm_manager()
    
    def process_message(self, user_message: str, context: dict):
        # Generate AI response
        response = self.llm_manager.generate_response(
            user_message, 
            context
        )
        
        return {
            'message': response.content,
            'confidence': response.confidence,
            'model': response.model
        }""")
    print("```")
    print()
    
    print("**2. Widget API Integration:**")
    print("```python")
    print("""@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    message = data.get('message')
    
    # Build context from project data
    context = {
        'projects': get_user_projects(),
        'team_members': get_team_members(),
        'analytics': get_analytics_data()
    }
    
    # Generate response
    llm_response = llm_manager.generate_response(message, context)
    
    return jsonify({
        'response': llm_response.content,
        'model': llm_response.model,
        'confidence': llm_response.confidence
    })""")
    print("```")
    print()
    
    print("**3. Voice Command Integration:**")
    print("```python")
    print("""def handle_voice_command(self, speech_text: str):
    # Convert speech to LLM prompt
    prompt = f"Voice command received: {speech_text}"
    
    context = {
        'input_method': 'voice',
        'user_preferences': self.get_user_preferences()
    }
    
    response = self.llm_manager.generate_response(prompt, context)
    
    # Convert response back to speech
    self.voice_system.speak(response.content)""")
    print("```")
    print()

def create_sample_config():
    """Create a sample LLM configuration file"""
    print("📝 Creating Sample Configuration")
    print("-" * 40)
    
    config = {
        "preferred_provider": "fallback",
        "providers": {
            "openai": {
                "enabled": False,
                "model": "gpt-3.5-turbo",
                "api_key": None,
                "note": "Set OPENAI_API_KEY environment variable or add key here"
            },
            "anthropic": {
                "enabled": False,
                "model": "claude-3-sonnet-20240229",
                "api_key": None,
                "note": "Set ANTHROPIC_API_KEY environment variable or add key here"
            },
            "local": {
                "enabled": False,
                "model": "llama2",
                "base_url": "http://localhost:11434",
                "note": "Install Ollama and run 'ollama serve' first"
            },
            "fallback": {
                "enabled": True,
                "note": "Always available rule-based responses"
            }
        },
        "instructions": {
            "setup_openai": [
                "1. Get API key from https://platform.openai.com/api-keys",
                "2. Set environment variable: export OPENAI_API_KEY='your-key'",
                "3. Set 'enabled': true in config",
                "4. Install: pip install openai"
            ],
            "setup_anthropic": [
                "1. Get API key from https://console.anthropic.com/",
                "2. Set environment variable: export ANTHROPIC_API_KEY='your-key'",
                "3. Set 'enabled': true in config",
                "4. Install: pip install anthropic"
            ],
            "setup_local": [
                "1. Install Ollama from https://ollama.ai/",
                "2. Run: ollama pull llama2",
                "3. Run: ollama serve",
                "4. Set 'enabled': true in config"
            ]
        }
    }
    
    # Save sample config
    config_path = "data/llm_config_sample.json"
    os.makedirs("data", exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"✅ Created sample configuration: {config_path}")
    print(f"📝 Copy this to data/llm_config.json and configure your preferred provider")
    print()

def main():
    """Run LLM integration demonstration"""
    
    # Show provider options
    demo_llm_configuration()
    
    # Show configuration examples
    show_configuration_examples()
    
    # Create sample config
    create_sample_config()
    
    # Test current setup
    demo_llm_responses()
    
    # Show integration examples
    demo_integration_examples()
    
    print("=" * 55)
    print("🎯 SUMMARY: LLM Integration Options")
    print("=" * 55)
    
    print("""
🚀 **Quick Start Options:**

1. **No Setup (Fallback)**: Works immediately with rule-based responses
2. **OpenAI GPT**: Best quality, requires API key, costs ~$0.001-0.03/1K tokens
3. **Anthropic Claude**: Excellent reasoning, requires API key, costs ~$0.003-0.075/1K tokens
4. **Local LLM**: Free but requires Ollama setup and local compute

🔧 **To Enable OpenAI:**
   export OPENAI_API_KEY="your-key"
   pip install openai

🔧 **To Enable Anthropic:**
   export ANTHROPIC_API_KEY="your-key"
   pip install anthropic

🔧 **To Enable Local LLM:**
   # Install Ollama from https://ollama.ai/
   ollama pull llama2
   ollama serve

⚙️ **Configuration:** Edit data/llm_config.json to set preferred provider

🎯 **Current Status:** Using fallback provider with intelligent rule-based responses
   - Handles project estimation queries
   - Provides team recommendations
   - Generates analytics insights
   - Responds to natural language questions

💡 **Next Steps:**
   1. Choose your preferred LLM provider
   2. Set up API keys or local installation
   3. Update data/llm_config.json configuration
   4. Restart the AI Avatar Assistant
   5. Enjoy enhanced conversational AI capabilities!
""")

if __name__ == "__main__":
    main()