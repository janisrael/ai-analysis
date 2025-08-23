#!/usr/bin/env python3
"""
AI Avatar Assistant - Ollama Integration Test
Test the complete integration between AI Avatar Assistant and Ollama
"""

import sys
import os
import json
import time
import requests
from datetime import datetime

def test_ollama_service():
    """Test if Ollama service is running and accessible"""
    print("🔧 Testing Ollama Service...")
    
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            models = [model['name'] for model in models_data.get('models', [])]
            print(f"  ✅ Ollama service is running")
            print(f"  📦 Available models: {', '.join(models)}")
            return True, models
        else:
            print(f"  ❌ Ollama service error: HTTP {response.status_code}")
            return False, []
    except Exception as e:
        print(f"  ❌ Cannot connect to Ollama service: {e}")
        print(f"  💡 Make sure Ollama is running: ollama serve")
        return False, []

def test_llm_config():
    """Test LLM configuration file"""
    print("\n⚙️ Testing LLM Configuration...")
    
    config_path = "data/llm_config.json"
    if not os.path.exists(config_path):
        print(f"  ❌ Configuration file not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"  ✅ Configuration loaded successfully")
        print(f"  🎯 Preferred provider: {config.get('preferred_provider')}")
        
        local_config = config.get('providers', {}).get('local', {})
        if local_config.get('enabled'):
            print(f"  🤖 Local model: {local_config.get('model')}")
            print(f"  🌐 Base URL: {local_config.get('base_url')}")
            return True
        else:
            print(f"  ⚠️ Local provider is not enabled")
            return False
            
    except Exception as e:
        print(f"  ❌ Error reading configuration: {e}")
        return False

def test_llm_integration():
    """Test LLM Manager integration"""
    print("\n🧠 Testing LLM Manager Integration...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from core.llm_integration import LLMManager
        
        llm_manager = LLMManager()
        print(f"  ✅ LLM Manager initialized successfully")
        
        # Test basic response
        test_prompt = "Estimate a simple React website project with 3 pages"
        context = {
            "user_request": "project_estimation",
            "technologies": ["react", "javascript"],
            "team_size": 2
        }
        
        print(f"  🤔 Testing prompt: {test_prompt}")
        
        start_time = time.time()
        response = llm_manager.generate_response(test_prompt, context)
        response_time = time.time() - start_time
        
        print(f"  🤖 Response received in {response_time:.2f} seconds")
        print(f"  📝 Model used: {response.model}")
        print(f"  📊 Confidence: {response.confidence:.1%}")
        print(f"  💬 Response preview: {response.content[:200]}...")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

def test_project_estimation():
    """Test project estimation with Ollama"""
    print("\n📊 Testing Project Estimation...")
    
    try:
        # Test direct API call
        payload = {
            "model": "llama2",
            "prompt": """You are an AI project estimator. Estimate this project:

Project: E-commerce website
- React frontend with responsive design
- Node.js backend with REST API
- User authentication and profiles
- Product catalog with search/filtering
- Shopping cart and checkout
- Payment integration (Stripe)
- Admin dashboard for inventory management

Provide: development hours, team recommendations, timeline, and risk factors.""",
            "stream": False
        }
        
        response = requests.post(
            'http://localhost:11434/api/generate',
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '')
            
            print(f"  ✅ Project estimation completed")
            print(f"  📋 Estimation summary:")
            # Show first few lines of the response
            lines = ai_response.split('\n')[:8]
            for line in lines:
                if line.strip():
                    print(f"     {line.strip()}")
            
            if len(lines) > 8:
                print(f"     ... (truncated, full response available)")
            
            return True
        else:
            print(f"  ❌ API error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Project estimation test failed: {e}")
        return False

def test_conversational_ai():
    """Test conversational AI with neural-chat"""
    print("\n💬 Testing Conversational AI...")
    
    try:
        # Test neural-chat for conversation
        payload = {
            "model": "neural-chat", 
            "prompt": "Hello! I'm working on a new project and need some guidance. Can you help me plan my development workflow?",
            "stream": False
        }
        
        response = requests.post(
            'http://localhost:11434/api/generate', 
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '')
            
            print(f"  ✅ Conversational AI test passed")
            print(f"  🗣️ Response preview: {ai_response[:150]}...")
            return True
        else:
            print(f"  ❌ API error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Conversational AI test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all integration tests"""
    print("🚀 AI Avatar Assistant - Ollama Integration Test")
    print("=" * 60)
    print("🎯 Testing complete integration with local AI models")
    print()
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Ollama Service
    service_ok, models = test_ollama_service()
    if service_ok:
        tests_passed += 1
    
    # Test 2: Configuration  
    config_ok = test_llm_config()
    if config_ok:
        tests_passed += 1
    
    # Test 3: LLM Integration
    integration_ok = test_llm_integration()
    if integration_ok:
        tests_passed += 1
    
    # Test 4: Project Estimation
    estimation_ok = test_project_estimation()
    if estimation_ok:
        tests_passed += 1
    
    # Test 5: Conversational AI
    conversation_ok = test_conversational_ai()
    if conversation_ok:
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
    print(f"📈 Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("\n🎉 PERFECT! Ollama integration is working flawlessly!")
        print("\n🚀 What you can do now:")
        print("  • Start AI Avatar Assistant: python3 main.py")
        print("  • Use chat interface with local AI")
        print("  • Get project estimations from llama2")
        print("  • Enjoy conversational AI with neural-chat")
        print("  • All completely FREE and PRIVATE!")
        
        print("\n🔄 Model switching:")
        print("  • For technical analysis: Change model to 'codellama'")
        print("  • For complex reasoning: Try 'mistral'")
        print("  • Download more models: ollama pull <model-name>")
        
    elif tests_passed >= 3:
        print("\n✅ Good! Most features are working.")
        print("🔧 Some minor issues detected - check output above.")
    else:
        print("\n⚠️ Integration needs attention.")
        print("🔧 Please fix the issues shown above.")
    
    print(f"\n💾 System Status:")
    print(f"  • Ollama Service: {'✅ Running' if service_ok else '❌ Not running'}")
    print(f"  • Available Models: {', '.join(models) if models else 'None'}")
    print(f"  • Configuration: {'✅ Valid' if config_ok else '❌ Invalid'}")
    print(f"  • Integration: {'✅ Working' if integration_ok else '❌ Failed'}")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)