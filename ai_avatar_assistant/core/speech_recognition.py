#!/usr/bin/env python3
"""
AI Avatar Assistant - Speech Recognition System
Advanced speech-to-text capabilities for voice interactions
"""

import os
import json
import time
import threading
import queue
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

class SpeechRecognitionSystem:
    """Advanced speech recognition system for voice interactions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_enabled = False
        self.is_listening = False
        self.recognition_engine = None
        self.microphone = None
        self.audio_queue = queue.Queue()
        self.recognition_thread = None
        self.callbacks = {}
        self.config = self.load_configuration()
        self.setup_recognition()
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load speech recognition configuration"""
        config_path = "data/speech_config.json"
        default_config = {
            "engine": "auto",  # auto, google, sphinx, wit, bing, azure
            "language": "en-US",
            "timeout": 5,
            "phrase_timeout": 0.3,
            "energy_threshold": 4000,
            "dynamic_energy": True,
            "pause_threshold": 0.8,
            "wake_words": ["hey assistant", "ai avatar", "hello bot"],
            "commands": {
                "estimate": ["estimate", "calculate", "how long", "time needed"],
                "team": ["who should", "recommend", "find team", "assign"],
                "analytics": ["show analytics", "report", "status", "insights"],
                "help": ["help", "what can you do", "commands"]
            },
            "confidence_threshold": 0.7,
            "noise_suppression": True,
            "auto_gain": True
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            else:
                os.makedirs("data", exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                self.logger.info("Created default speech recognition configuration")
        except Exception as e:
            self.logger.error(f"Error loading speech config: {e}")
        
        return default_config
    
    def setup_recognition(self):
        """Setup speech recognition engine"""
        try:
            # Try to import speech recognition library
            import speech_recognition as sr
            
            self.recognizer = sr.Recognizer()
            
            # Configure recognizer settings
            if self.config.get("dynamic_energy", True):
                self.recognizer.dynamic_energy_threshold = True
            else:
                self.recognizer.energy_threshold = self.config.get("energy_threshold", 4000)
            
            self.recognizer.pause_threshold = self.config.get("pause_threshold", 0.8)
            
            # Setup microphone
            try:
                self.microphone = sr.Microphone()
                
                # Adjust for ambient noise
                with self.microphone as source:
                    self.logger.info("Adjusting for ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                
                self.is_enabled = True
                self.logger.info("Speech recognition system initialized successfully")
                
            except Exception as e:
                self.logger.warning(f"Microphone setup failed: {e}")
                self.is_enabled = False
                
        except ImportError:
            self.logger.warning("SpeechRecognition library not available. Install with: pip install SpeechRecognition")
            self.is_enabled = False
        except Exception as e:
            self.logger.error(f"Speech recognition setup failed: {e}")
            self.is_enabled = False
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register callback for speech events"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
        self.logger.info(f"Registered callback for {event_type}")
    
    def trigger_callback(self, event_type: str, data: Dict[str, Any]):
        """Trigger callbacks for specific events"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Error in {event_type} callback: {e}")
    
    def start_listening(self):
        """Start continuous speech recognition"""
        if not self.is_enabled:
            self.logger.warning("Speech recognition not enabled")
            return False
        
        if self.is_listening:
            self.logger.warning("Already listening")
            return True
        
        self.is_listening = True
        self.recognition_thread = threading.Thread(target=self._recognition_loop, daemon=True)
        self.recognition_thread.start()
        
        self.logger.info("Started speech recognition")
        return True
    
    def stop_listening(self):
        """Stop speech recognition"""
        self.is_listening = False
        if self.recognition_thread:
            self.recognition_thread.join(timeout=2)
        self.logger.info("Stopped speech recognition")
    
    def _recognition_loop(self):
        """Main recognition loop"""
        import speech_recognition as sr
        
        while self.is_listening:
            try:
                # Listen for audio
                with self.microphone as source:
                    self.logger.debug("Listening for speech...")
                    audio = self.recognizer.listen(
                        source, 
                        timeout=self.config.get("timeout", 5),
                        phrase_time_limit=self.config.get("phrase_timeout", 0.3)
                    )
                
                # Process audio in separate thread to avoid blocking
                processing_thread = threading.Thread(
                    target=self._process_audio,
                    args=(audio,),
                    daemon=True
                )
                processing_thread.start()
                
            except sr.WaitTimeoutError:
                # Normal timeout, continue listening
                continue
            except Exception as e:
                self.logger.error(f"Recognition loop error: {e}")
                time.sleep(1)
    
    def _process_audio(self, audio):
        """Process recognized audio"""
        import speech_recognition as sr
        
        try:
            # Try different recognition engines based on config
            engine = self.config.get("engine", "auto")
            language = self.config.get("language", "en-US")
            
            text = None
            confidence = 0.0
            
            if engine == "google" or engine == "auto":
                try:
                    result = self.recognizer.recognize_google(audio, language=language, show_all=True)
                    if result and 'alternative' in result:
                        text = result['alternative'][0]['transcript']
                        confidence = result['alternative'][0].get('confidence', 0.5)
                except Exception as e:
                    self.logger.debug(f"Google recognition failed: {e}")
            
            if not text and (engine == "sphinx" or engine == "auto"):
                try:
                    text = self.recognizer.recognize_sphinx(audio, language=language)
                    confidence = 0.6  # Default confidence for Sphinx
                except Exception as e:
                    self.logger.debug(f"Sphinx recognition failed: {e}")
            
            if text and confidence >= self.config.get("confidence_threshold", 0.7):
                self.logger.info(f"Recognized: '{text}' (confidence: {confidence:.2f})")
                self._process_recognized_text(text, confidence)
            else:
                self.logger.debug("Recognition confidence too low or no text recognized")
                
        except Exception as e:
            self.logger.error(f"Audio processing error: {e}")
    
    def _process_recognized_text(self, text: str, confidence: float):
        """Process and interpret recognized text"""
        text_lower = text.lower().strip()
        
        # Check for wake words
        if self._check_wake_words(text_lower):
            self.trigger_callback("wake_word_detected", {
                "text": text,
                "confidence": confidence,
                "timestamp": datetime.now()
            })
            return
        
        # Classify intent
        intent = self._classify_intent(text_lower)
        
        # Trigger appropriate callback
        self.trigger_callback("speech_recognized", {
            "text": text,
            "confidence": confidence,
            "intent": intent,
            "timestamp": datetime.now()
        })
        
        if intent:
            self.trigger_callback(f"intent_{intent}", {
                "text": text,
                "confidence": confidence,
                "timestamp": datetime.now()
            })
    
    def _check_wake_words(self, text: str) -> bool:
        """Check if text contains wake words"""
        wake_words = self.config.get("wake_words", [])
        for wake_word in wake_words:
            if wake_word.lower() in text:
                return True
        return False
    
    def _classify_intent(self, text: str) -> Optional[str]:
        """Classify the intent of recognized text"""
        commands = self.config.get("commands", {})
        
        for intent, keywords in commands.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return intent
        
        return "general"
    
    def recognize_once(self, timeout: float = 10) -> Optional[Dict[str, Any]]:
        """Perform one-time speech recognition"""
        if not self.is_enabled:
            return None
        
        import speech_recognition as sr
        
        try:
            with self.microphone as source:
                self.logger.info("Listening for speech...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            
            # Try recognition
            text = self.recognizer.recognize_google(audio, language=self.config.get("language", "en-US"))
            
            return {
                "text": text,
                "confidence": 0.8,  # Default confidence
                "timestamp": datetime.now()
            }
            
        except sr.UnknownValueError:
            self.logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Recognition service error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Recognition error: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if speech recognition is available"""
        return self.is_enabled
    
    def get_status(self) -> Dict[str, Any]:
        """Get current speech recognition status"""
        return {
            "enabled": self.is_enabled,
            "listening": self.is_listening,
            "engine": self.config.get("engine", "auto"),
            "language": self.config.get("language", "en-US"),
            "microphone_available": self.microphone is not None,
            "callbacks_registered": len(self.callbacks)
        }
    
    def update_configuration(self, new_config: Dict[str, Any]):
        """Update speech recognition configuration"""
        self.config.update(new_config)
        
        # Save updated config
        config_path = "data/speech_config.json"
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info("Speech recognition configuration updated")
        except Exception as e:
            self.logger.error(f"Error saving speech config: {e}")
    
    def test_microphone(self) -> Dict[str, Any]:
        """Test microphone and return audio info"""
        if not self.is_enabled:
            return {"available": False, "error": "Speech recognition not enabled"}
        
        import speech_recognition as sr
        
        try:
            with self.microphone as source:
                self.logger.info("Testing microphone - please speak...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            # Try to recognize the test audio
            try:
                text = self.recognizer.recognize_google(audio, language=self.config.get("language", "en-US"))
                return {
                    "available": True,
                    "test_successful": True,
                    "recognized_text": text,
                    "energy_threshold": self.recognizer.energy_threshold
                }
            except:
                return {
                    "available": True,
                    "test_successful": False,
                    "message": "Audio captured but recognition failed",
                    "energy_threshold": self.recognizer.energy_threshold
                }
                
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }

class VoiceCommandProcessor:
    """Process voice commands and integrate with AI Assistant"""
    
    def __init__(self, ai_assistant, speech_system):
        self.ai_assistant = ai_assistant
        self.speech_system = speech_system
        self.logger = logging.getLogger(__name__)
        self.setup_callbacks()
    
    def setup_callbacks(self):
        """Setup speech recognition callbacks"""
        self.speech_system.register_callback("speech_recognized", self.handle_speech)
        self.speech_system.register_callback("intent_estimate", self.handle_estimate_request)
        self.speech_system.register_callback("intent_team", self.handle_team_request)
        self.speech_system.register_callback("intent_analytics", self.handle_analytics_request)
        self.speech_system.register_callback("intent_help", self.handle_help_request)
        self.speech_system.register_callback("wake_word_detected", self.handle_wake_word)
    
    def handle_speech(self, data: Dict[str, Any]):
        """Handle general speech recognition"""
        text = data.get("text", "")
        confidence = data.get("confidence", 0.0)
        
        self.logger.info(f"Processing speech: '{text}' (confidence: {confidence:.2f})")
        
        # Send to conversational AI
        if hasattr(self.ai_assistant, 'chat_interface'):
            self.ai_assistant.chat_interface.add_voice_message(text, confidence)
    
    def handle_estimate_request(self, data: Dict[str, Any]):
        """Handle project estimation voice requests"""
        text = data.get("text", "")
        self.logger.info(f"Estimation request: {text}")
        
        # Extract project details from speech
        # This could be enhanced with NLP to parse requirements
        response = "I heard your estimation request. Please provide more details about the project."
        
        if hasattr(self.ai_assistant, 'voice_system'):
            self.ai_assistant.voice_system.speak(response)
    
    def handle_team_request(self, data: Dict[str, Any]):
        """Handle team recommendation voice requests"""
        text = data.get("text", "")
        self.logger.info(f"Team request: {text}")
        
        response = "I can help you find the right team members. What skills are you looking for?"
        
        if hasattr(self.ai_assistant, 'voice_system'):
            self.ai_assistant.voice_system.speak(response)
    
    def handle_analytics_request(self, data: Dict[str, Any]):
        """Handle analytics voice requests"""
        text = data.get("text", "")
        self.logger.info(f"Analytics request: {text}")
        
        # Could trigger analytics dashboard or generate voice report
        response = "Let me gather the latest analytics for you."
        
        if hasattr(self.ai_assistant, 'voice_system'):
            self.ai_assistant.voice_system.speak(response)
    
    def handle_help_request(self, data: Dict[str, Any]):
        """Handle help voice requests"""
        text = data.get("text", "")
        self.logger.info(f"Help request: {text}")
        
        response = """I can help you with project estimation, team recommendations, 
        analytics insights, and general questions. What would you like to know?"""
        
        if hasattr(self.ai_assistant, 'voice_system'):
            self.ai_assistant.voice_system.speak(response)
    
    def handle_wake_word(self, data: Dict[str, Any]):
        """Handle wake word detection"""
        text = data.get("text", "")
        self.logger.info(f"Wake word detected: {text}")
        
        # Could trigger avatar animation, sound effect, or visual feedback
        response = "Yes, I'm listening. How can I help?"
        
        if hasattr(self.ai_assistant, 'voice_system'):
            self.ai_assistant.voice_system.speak(response)