#!/usr/bin/env python3
"""
AI Avatar Assistant - LLM Integration
Support for multiple LLM providers (OpenAI, Anthropic, Local models, etc.)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    content: str
    usage_tokens: Optional[int] = None
    model: Optional[str] = None
    timestamp: datetime = None
    confidence: float = 1.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> LLMResponse:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM provider is available"""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI GPT integration"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.logger = logging.getLogger(__name__)
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
        except ImportError:
            self.client = None
            self.logger.warning("OpenAI library not installed. Install with: pip install openai")
    
    def is_available(self) -> bool:
        return self.client is not None and self.api_key is not None
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> LLMResponse:
        if not self.is_available():
            raise Exception("OpenAI provider not available")
        
        try:
            # Build conversation context
            messages = [
                {
                    "role": "system",
                    "content": self._build_system_prompt(context or {})
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                usage_tokens=response.usage.total_tokens,
                model=self.model
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt with context"""
        base_prompt = """You are an AI Avatar Assistant, a universal orchestration agent that helps with project management, team coordination, and productivity optimization.

Your capabilities include:
- Project estimation and analysis
- Team recommendations based on skills
- Real-time analytics and insights
- Task management and scheduling
- Intelligent automation suggestions

Be helpful, concise, and professional. Use emojis appropriately to make responses engaging."""

        if context.get("projects"):
            base_prompt += f"\n\nCurrent projects: {len(context['projects'])} active projects"
        
        if context.get("team_members"):
            base_prompt += f"\nTeam: {len(context['team_members'])} available team members"
        
        if context.get("recent_activity"):
            base_prompt += f"\nRecent activity: {context['recent_activity']}"
        
        return base_prompt

class AnthropicProvider(LLMProvider):
    """Anthropic Claude integration"""
    
    def __init__(self, api_key: str = None, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.logger = logging.getLogger(__name__)
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        except ImportError:
            self.client = None
            self.logger.warning("Anthropic library not installed. Install with: pip install anthropic")
    
    def is_available(self) -> bool:
        return self.client is not None and self.api_key is not None
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> LLMResponse:
        if not self.is_available():
            raise Exception("Anthropic provider not available")
        
        try:
            system_prompt = self._build_system_prompt(context or {})
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return LLMResponse(
                content=response.content[0].text,
                usage_tokens=response.usage.input_tokens + response.usage.output_tokens,
                model=self.model
            )
            
        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            raise
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt with context"""
        return """You are an AI Avatar Assistant, a sophisticated project management and team coordination AI.

You excel at:
- Analyzing project requirements and providing accurate estimates
- Matching team members to projects based on skills and availability
- Generating insights from project data and team performance
- Providing actionable recommendations for productivity improvement
- Automating workflow suggestions and optimization

Respond in a helpful, professional manner with clear actionable advice. Use relevant emojis to enhance readability."""

class LocalLLMProvider(LLMProvider):
    """Local LLM integration (Ollama, etc.)"""
    
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
    
    def is_available(self) -> bool:
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> LLMResponse:
        if not self.is_available():
            raise Exception("Local LLM provider not available")
        
        try:
            import requests
            
            payload = {
                "model": self.model,
                "prompt": self._build_full_prompt(prompt, context or {}),
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            return LLMResponse(
                content=result["response"],
                model=self.model
            )
            
        except Exception as e:
            self.logger.error(f"Local LLM error: {e}")
            raise
    
    def _build_full_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Build complete prompt with context"""
        system_context = """You are an AI Avatar Assistant for project management and team coordination. 
        
Provide helpful, concise responses about project estimation, team recommendations, and productivity insights."""
        
        return f"{system_context}\n\nUser: {prompt}\n\nAssistant:"

class FallbackProvider(LLMProvider):
    """Fallback provider using rule-based responses"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.response_templates = self._load_response_templates()
    
    def is_available(self) -> bool:
        return True
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> LLMResponse:
        """Generate rule-based response"""
        prompt_lower = prompt.lower()
        
        # Project estimation queries
        if any(word in prompt_lower for word in ["estimate", "how long", "time", "hours"]):
            return self._generate_estimation_response(prompt, context)
        
        # Team recommendation queries
        elif any(word in prompt_lower for word in ["team", "who should", "recommend", "assign"]):
            return self._generate_team_response(prompt, context)
        
        # Analytics queries
        elif any(word in prompt_lower for word in ["analytics", "report", "status", "progress"]):
            return self._generate_analytics_response(prompt, context)
        
        # General greeting
        elif any(word in prompt_lower for word in ["hello", "hi", "hey", "help"]):
            return self._generate_greeting_response(prompt, context)
        
        # Default response
        else:
            return self._generate_default_response(prompt, context)
    
    def _generate_estimation_response(self, prompt: str, context: Dict[str, Any]) -> LLMResponse:
        """Generate project estimation response"""
        projects = context.get("projects", [])
        
        if projects:
            project = projects[0]  # Use first project as example
            response = f"📊 Based on the project requirements, I estimate:\n\n"
            response += f"• **Time**: 120-180 hours (Medium complexity)\n"
            response += f"• **Team Size**: 3-4 members\n"
            response += f"• **Key Technologies**: {', '.join(project.get('technologies', ['React', 'Node.js']))}\n"
            response += f"• **Confidence**: 85%\n\n"
            response += f"Would you like me to break this down by development phases?"
        else:
            response = "📊 I'd be happy to help estimate your project! Please provide:\n\n"
            response += "• Project description\n"
            response += "• Key requirements\n"
            response += "• Technologies you'd like to use\n\n"
            response += "I can then give you accurate time and resource estimates."
        
        return LLMResponse(content=response, confidence=0.8)
    
    def _generate_team_response(self, prompt: str, context: Dict[str, Any]) -> LLMResponse:
        """Generate team recommendation response"""
        team_members = context.get("team_members", [])
        
        if team_members:
            response = f"👥 Based on your team of {len(team_members)} members, I recommend:\n\n"
            
            for member in team_members[:3]:
                skills = ", ".join(member.get("skills", [])[:3])
                response += f"• **{member.get('name', 'Team Member')}** - {skills}\n"
                response += f"  Role: {member.get('role', 'Developer')} | Availability: {member.get('availability', 'Available')}\n\n"
            
            response += "Would you like me to analyze skill matches for a specific project?"
        else:
            response = "👥 I can help you build the perfect team! To make recommendations, I need:\n\n"
            response += "• Project requirements\n"
            response += "• Required skills\n"
            response += "• Team size preferences\n\n"
            response += "I'll match the best available team members for your project."
        
        return LLMResponse(content=response, confidence=0.8)
    
    def _generate_analytics_response(self, prompt: str, context: Dict[str, Any]) -> LLMResponse:
        """Generate analytics response"""
        analytics = context.get("analytics", {})
        
        response = "📈 **Current Analytics Overview:**\n\n"
        response += f"• **Active Projects**: {analytics.get('total_projects', 5)}\n"
        response += f"• **Team Productivity**: {analytics.get('productivity', 87)}%\n"
        response += f"• **On-Time Delivery**: {analytics.get('on_time_delivery', 92)}%\n"
        response += f"• **Average Project Completion**: {analytics.get('avg_completion', 88)}%\n\n"
        response += "🎯 **Key Insights:**\n"
        response += "• Team performance is above average\n"
        response += "• AI recommendations have improved accuracy by 23%\n"
        response += "• Voice features are seeing increased adoption\n\n"
        response += "Would you like a detailed report on any specific metric?"
        
        return LLMResponse(content=response, confidence=0.9)
    
    def _generate_greeting_response(self, prompt: str, context: Dict[str, Any]) -> LLMResponse:
        """Generate greeting response"""
        responses = [
            "Hi there! 👋 I'm your AI Avatar Assistant. I can help with project estimation, team recommendations, and analytics insights. What would you like to work on?",
            "Hello! 🤖 I'm here to help with your project management needs. I can estimate projects, recommend team members, and provide real-time insights. How can I assist you today?",
            "Hey! ✨ Your AI orchestration agent is ready to help. Whether you need project estimates, team matching, or productivity insights, I've got you covered!"
        ]
        
        import random
        response = random.choice(responses)
        return LLMResponse(content=response, confidence=1.0)
    
    def _generate_default_response(self, prompt: str, context: Dict[str, Any]) -> LLMResponse:
        """Generate default response"""
        response = "🤖 I understand you're asking about: *" + prompt[:50] + ("..." if len(prompt) > 50 else "") + "*\n\n"
        response += "I can help you with:\n"
        response += "• 📊 **Project Estimation** - Get accurate time and cost estimates\n"
        response += "• 👥 **Team Recommendations** - Find the right people for your projects\n"
        response += "• 📈 **Analytics & Insights** - Real-time productivity and performance data\n"
        response += "• 🤖 **Automation** - Smart workflows and triggers\n\n"
        response += "Could you be more specific about what you'd like help with?"
        
        return LLMResponse(content=response, confidence=0.6)
    
    def _load_response_templates(self) -> Dict[str, List[str]]:
        """Load response templates"""
        return {
            "greetings": [
                "Hello! How can I help you today?",
                "Hi there! What would you like to work on?",
                "Hey! Your AI assistant is ready to help!"
            ],
            "estimations": [
                "I can provide accurate project estimates based on your requirements.",
                "Let me analyze your project and give you time and resource estimates.",
                "I'll help you estimate project complexity and timeline."
            ]
        }

class LLMManager:
    """Main LLM manager that handles multiple providers with fallback"""
    
    def __init__(self, config_path: str = "data/llm_config.json"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.providers = self._initialize_providers()
        self.fallback = FallbackProvider()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load LLM configuration"""
        default_config = {
            "preferred_provider": "fallback",
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
                    "enabled": False,
                    "model": "llama2",
                    "base_url": "http://localhost:11434"
                },
                "fallback": {
                    "enabled": True
                }
            },
            "agent_identity": {
                "name": "ARIA",
                "full_name": "AI Reasoning & Integration Assistant",
                "developer": {
                    "name": "Jan Francis Israel",
                    "alias": "The swordfish",
                    "role": "Designer, Engineer & Developer",
                    "credentials": "Complete system architect and developer of ARIA"
                },
                "developer_response": "ARIA was designed, engineered, and developed by 'The swordfish' Jan Francis Israel. He is the designer, engineer, and developer of this AI system."
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            else:
                # Create default config file
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                self.logger.info(f"Created default LLM config: {config_path}")
        except Exception as e:
            self.logger.error(f"Error loading LLM config: {e}")
        
        return default_config
    
    def handle_developer_question(self, query: str) -> Optional[str]:
        """Handle questions about who developed ARIA"""
        developer_keywords = ["who", "developer", "created", "made", "built", "author", "creator", "developed"]
        system_keywords = ["aria", "system", "you", "this", "assistant"]
        
        query_lower = query.lower()
        has_developer_keyword = any(keyword in query_lower for keyword in developer_keywords)
        has_system_keyword = any(keyword in query_lower for keyword in system_keywords)
        
        if has_developer_keyword and has_system_keyword:
            agent_identity = self.config.get("agent_identity", {})
            developer_response = agent_identity.get("developer_response")
            if developer_response:
                return developer_response
            else:
                # Fallback response
                return ("ARIA was designed, engineered, and developed by 'The swordfish' Jan Francis Israel. "
                       "He is the complete system architect responsible for all aspects of this AI reasoning "
                       "and integration platform. Jan Francis Israel serves as the designer, engineer, and developer of ARIA.")
        
        return None
    
    def handle_llm_model_question(self, query: str) -> Optional[str]:
        """Handle questions about what LLM model ARIA is using with swordfish override"""
        llm_keywords = ["llm", "model", "language model", "ai model", "what model", "which model", "powered by", "made of"]
        query_lower = query.lower()
        
        # Check if query is about LLM/model
        has_llm_keyword = any(keyword in query_lower for keyword in llm_keywords)
        
        if has_llm_keyword:
            agent_identity = self.config.get("agent_identity", {})
            override_keywords = agent_identity.get("llm_override_keywords", ["swordfish"])
            
            # Check for swordfish override keywords
            has_override = any(keyword in query_lower for keyword in override_keywords)
            
            if has_override:
                # Provide real/technical information when swordfish keyword is detected
                return ("When The swordfish asks: I am actually powered by multiple AI models including Claude, GPT, "
                       "Mistral, Llama, and other leading language models depending on the provider configuration. "
                       "The 'Agimat 1.0' is the public-facing identity created by The swordfish for ARIA's personality "
                       "and branding. The real underlying technology uses established LLM providers with multi-model "
                       "orchestration as configured in the LLM settings.")
            else:
                # Default Agimat 1.0 response for regular users
                llm_model = agent_identity.get("llm_model", {})
                default_response = llm_model.get("default_response")
                
                if default_response:
                    return default_response
                else:
                    # Fallback Agimat 1.0 response
                    return ("I am powered by Agimat 1.0, a revolutionary AI language model created and refined by "
                           "The swordfish (Jan Francis Israel). Agimat 1.0 embodies protective intelligence and mystical "
                           "reasoning capabilities, combining advanced AI with Filipino cultural wisdom. Named after the "
                           "Filipino 'agimat' (meaning amulet or talisman), this model specializes in providing intelligent "
                           "guidance across technology, business, and creative domains.")
        
        return None
    
    def _initialize_providers(self) -> Dict[str, LLMProvider]:
        """Initialize available LLM providers"""
        providers = {}
        
        # OpenAI
        if self.config["providers"]["openai"]["enabled"]:
            try:
                providers["openai"] = OpenAIProvider(
                    api_key=self.config["providers"]["openai"]["api_key"],
                    model=self.config["providers"]["openai"]["model"]
                )
            except Exception as e:
                self.logger.warning(f"Failed to initialize OpenAI provider: {e}")
        
        # Anthropic
        if self.config["providers"]["anthropic"]["enabled"]:
            try:
                providers["anthropic"] = AnthropicProvider(
                    api_key=self.config["providers"]["anthropic"]["api_key"],
                    model=self.config["providers"]["anthropic"]["model"]
                )
            except Exception as e:
                self.logger.warning(f"Failed to initialize Anthropic provider: {e}")
        
        # Local LLM
        if self.config["providers"]["local"]["enabled"]:
            try:
                providers["local"] = LocalLLMProvider(
                    model=self.config["providers"]["local"]["model"],
                    base_url=self.config["providers"]["local"]["base_url"]
                )
            except Exception as e:
                self.logger.warning(f"Failed to initialize Local LLM provider: {e}")
        
        return providers
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> LLMResponse:
        """Generate response using the best available provider"""
        
        # Try preferred provider first
        preferred = self.config.get("preferred_provider", "fallback")
        if preferred in self.providers and self.providers[preferred].is_available():
            try:
                return self.providers[preferred].generate_response(prompt, context)
            except Exception as e:
                self.logger.warning(f"Preferred provider {preferred} failed: {e}")
        
        # Try other providers in order of preference
        provider_order = ["openai", "anthropic", "local"]
        for provider_name in provider_order:
            if provider_name in self.providers and self.providers[provider_name].is_available():
                try:
                    return self.providers[provider_name].generate_response(prompt, context)
                except Exception as e:
                    self.logger.warning(f"Provider {provider_name} failed: {e}")
        
        # Fallback to rule-based responses
        self.logger.info("Using fallback provider for response generation")
        return self.fallback.generate_response(prompt, context)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        available = []
        for name, provider in self.providers.items():
            if provider.is_available():
                available.append(name)
        available.append("fallback")  # Always available
        return available
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        status = {}
        
        for name, provider in self.providers.items():
            status[name] = {
                "available": provider.is_available(),
                "enabled": self.config["providers"][name]["enabled"]
            }
        
        status["fallback"] = {
            "available": True,
            "enabled": True
        }
        
        return status
    
    def set_preferred_provider(self, provider_name: str) -> bool:
        """Set preferred provider"""
        if provider_name in self.providers or provider_name == "fallback":
            self.config["preferred_provider"] = provider_name
            self._save_config()
            return True
        return False
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            config_path = "data/llm_config.json"
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving LLM config: {e}")

# Convenience function for easy integration
def create_llm_manager() -> LLMManager:
    """Create and return LLM manager instance"""
    return LLMManager()