import sys
import threading
import queue
import logging
from typing import Optional, Dict, List
import json
import os

class VoiceNotificationSystem:
    """Text-to-speech voice notification system for the AI Avatar Assistant"""
    
    def __init__(self, config_path="data/config.json"):
        self.config = self.load_config(config_path)
        self.voice_config = self.config.get("voice", {})
        self.logger = logging.getLogger(__name__)
        
        # Voice settings
        self.enabled = self.voice_config.get("enabled", False)
        self.voice_rate = self.voice_config.get("rate", 200)  # Words per minute
        self.voice_volume = self.voice_config.get("volume", 0.8)  # 0.0 to 1.0
        self.voice_gender = self.voice_config.get("gender", "female")  # male/female
        self.language = self.voice_config.get("language", "en")
        
        # TTS engine
        self.tts_engine = None
        self.is_initialized = False
        
        # Speech queue for managing multiple notifications
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.speech_thread = None
        
        # Voice personas for different notification types
        self.voice_personas = {
            "urgent": {"rate": 250, "emphasis": "strong"},
            "normal": {"rate": 200, "emphasis": "moderate"},
            "calm": {"rate": 180, "emphasis": "reduced"},
            "friendly": {"rate": 190, "emphasis": "cheerful"}
        }
        
        self.initialize_tts()
    
    def load_config(self, config_path):
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def initialize_tts(self):
        """Initialize the text-to-speech engine"""
        if not self.enabled:
            self.logger.info("Voice notifications disabled in configuration")
            return False
        
        try:
            # Try pyttsx3 first (cross-platform)
            import pyttsx3
            
            self.tts_engine = pyttsx3.init()
            
            # Configure voice properties
            self.configure_voice()
            
            self.is_initialized = True
            self.logger.info("Voice notification system initialized with pyttsx3")
            
            # Start speech processing thread
            self.start_speech_thread()
            
            return True
            
        except ImportError:
            self.logger.warning("pyttsx3 not available, trying platform-specific TTS")
            return self.initialize_platform_tts()
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            return False
    
    def initialize_platform_tts(self):
        """Initialize platform-specific TTS as fallback"""
        try:
            if sys.platform.startswith('win'):
                return self.initialize_windows_tts()
            elif sys.platform.startswith('darwin'):
                return self.initialize_macos_tts()
            else:
                return self.initialize_linux_tts()
        except Exception as e:
            self.logger.error(f"Failed to initialize platform TTS: {e}")
            return False
    
    def initialize_windows_tts(self):
        """Initialize Windows SAPI TTS"""
        try:
            import win32com.client
            
            self.tts_engine = win32com.client.Dispatch("SAPI.SpVoice")
            self.is_initialized = True
            self.platform_tts = "windows"
            self.logger.info("Voice notification system initialized with Windows SAPI")
            return True
        except ImportError:
            self.logger.warning("Windows SAPI not available")
            return False
    
    def initialize_macos_tts(self):
        """Initialize macOS TTS"""
        try:
            import subprocess
            
            # Test if 'say' command is available
            result = subprocess.run(['which', 'say'], capture_output=True, text=True)
            if result.returncode == 0:
                self.platform_tts = "macos"
                self.is_initialized = True
                self.logger.info("Voice notification system initialized with macOS say")
                return True
        except Exception as e:
            self.logger.warning(f"macOS TTS not available: {e}")
        
        return False
    
    def initialize_linux_tts(self):
        """Initialize Linux TTS (espeak/festival)"""
        try:
            import subprocess
            
            # Try espeak first
            result = subprocess.run(['which', 'espeak'], capture_output=True, text=True)
            if result.returncode == 0:
                self.platform_tts = "linux_espeak"
                self.is_initialized = True
                self.logger.info("Voice notification system initialized with espeak")
                return True
            
            # Try festival as fallback
            result = subprocess.run(['which', 'festival'], capture_output=True, text=True)
            if result.returncode == 0:
                self.platform_tts = "linux_festival"
                self.is_initialized = True
                self.logger.info("Voice notification system initialized with festival")
                return True
                
        except Exception as e:
            self.logger.warning(f"Linux TTS not available: {e}")
        
        return False
    
    def configure_voice(self):
        """Configure voice properties for pyttsx3"""
        if not self.tts_engine or not hasattr(self.tts_engine, 'setProperty'):
            return
        
        try:
            # Set speech rate
            self.tts_engine.setProperty('rate', self.voice_rate)
            
            # Set volume
            self.tts_engine.setProperty('volume', self.voice_volume)
            
            # Set voice (try to find preferred gender)
            voices = self.tts_engine.getProperty('voices')
            if voices:
                preferred_voice = None
                
                # Look for voice matching preferred gender
                for voice in voices:
                    voice_name = voice.name.lower()
                    voice_id = voice.id.lower()
                    
                    if self.voice_gender == "female":
                        if any(keyword in voice_name or keyword in voice_id 
                              for keyword in ['female', 'woman', 'zira', 'hazel', 'susan']):
                            preferred_voice = voice.id
                            break
                    else:  # male
                        if any(keyword in voice_name or keyword in voice_id 
                              for keyword in ['male', 'man', 'david', 'mark', 'alex']):
                            preferred_voice = voice.id
                            break
                
                if preferred_voice:
                    self.tts_engine.setProperty('voice', preferred_voice)
                elif voices:
                    # Use first available voice as fallback
                    self.tts_engine.setProperty('voice', voices[0].id)
            
            self.logger.info(f"Voice configured: rate={self.voice_rate}, volume={self.voice_volume}")
            
        except Exception as e:
            self.logger.warning(f"Failed to configure voice properties: {e}")
    
    def start_speech_thread(self):
        """Start background thread for processing speech queue"""
        if self.speech_thread and self.speech_thread.is_alive():
            return
        
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
        self.logger.info("Speech processing thread started")
    
    def _speech_worker(self):
        """Background worker for processing speech queue"""
        while True:
            try:
                # Get speech request from queue (blocking)
                speech_request = self.speech_queue.get(timeout=1)
                
                if speech_request is None:  # Shutdown signal
                    break
                
                self.is_speaking = True
                self._speak_text(speech_request)
                self.is_speaking = False
                
                # Mark task as done
                self.speech_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in speech worker: {e}")
                self.is_speaking = False
    
    def _speak_text(self, speech_request):
        """Actually speak the text using the configured TTS engine"""
        text = speech_request.get("text", "")
        persona = speech_request.get("persona", "normal")
        
        if not text or not self.is_initialized:
            return
        
        try:
            if hasattr(self.tts_engine, 'say'):  # pyttsx3
                # Apply persona settings
                if persona in self.voice_personas:
                    persona_settings = self.voice_personas[persona]
                    self.tts_engine.setProperty('rate', persona_settings.get("rate", self.voice_rate))
                
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                
                # Reset to default rate
                self.tts_engine.setProperty('rate', self.voice_rate)
                
            elif hasattr(self, 'platform_tts'):
                self._speak_platform_specific(text, persona)
                
        except Exception as e:
            self.logger.error(f"Error speaking text: {e}")
    
    def _speak_platform_specific(self, text, persona):
        """Speak using platform-specific TTS"""
        import subprocess
        
        try:
            if self.platform_tts == "windows":
                # Windows SAPI
                self.tts_engine.Speak(text)
                
            elif self.platform_tts == "macos":
                # macOS say command
                rate = self.voice_personas.get(persona, {}).get("rate", self.voice_rate)
                cmd = ['say', '-r', str(rate), text]
                subprocess.run(cmd, check=True)
                
            elif self.platform_tts == "linux_espeak":
                # Linux espeak
                rate = self.voice_personas.get(persona, {}).get("rate", self.voice_rate)
                cmd = ['espeak', '-s', str(rate), text]
                subprocess.run(cmd, check=True)
                
            elif self.platform_tts == "linux_festival":
                # Linux festival
                cmd = ['festival', '--tts']
                process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
                process.communicate(input=text)
                
        except Exception as e:
            self.logger.error(f"Error with platform-specific TTS: {e}")
    
    def speak_notification(self, text: str, urgency: str = "normal", interrupt: bool = False):
        """Queue a notification for speech"""
        if not self.enabled or not self.is_initialized:
            return False
        
        # Clean up text for speech
        clean_text = self.prepare_text_for_speech(text)
        
        if not clean_text:
            return False
        
        # Map urgency to persona
        persona_map = {
            "low": "calm",
            "normal": "normal", 
            "high": "friendly",
            "urgent": "urgent",
            "critical": "urgent"
        }
        
        persona = persona_map.get(urgency, "normal")
        
        speech_request = {
            "text": clean_text,
            "persona": persona,
            "urgency": urgency,
            "interrupt": interrupt
        }
        
        if interrupt and self.is_speaking:
            # Clear queue and stop current speech for urgent interruptions
            self.stop_all_speech()
        
        try:
            self.speech_queue.put(speech_request, timeout=1)
            return True
        except queue.Full:
            self.logger.warning("Speech queue is full, skipping notification")
            return False
    
    def prepare_text_for_speech(self, text: str) -> str:
        """Clean and prepare text for speech synthesis"""
        import re
        
        # Remove emojis and special characters
        clean_text = re.sub(r'[^\w\s\.\!\?\,\-\:\;]', '', text)
        
        # Replace common abbreviations and symbols
        replacements = {
            '&': 'and',
            '@': 'at',
            '#': 'number',
            '%': 'percent',
            '$': 'dollars',
            '€': 'euros',
            '£': 'pounds',
            '...': ' ',
            '--': ' ',
            'AI': 'A I',
            'API': 'A P I',
            'URL': 'U R L',
            'UI': 'U I',
            'UX': 'U X'
        }
        
        for old, new in replacements.items():
            clean_text = clean_text.replace(old, new)
        
        # Remove extra whitespace
        clean_text = ' '.join(clean_text.split())
        
        # Limit length for speech
        max_length = self.voice_config.get("max_length", 200)
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length] + "..."
        
        return clean_text.strip()
    
    def speak_task_notification(self, task_title: str, notification_type: str):
        """Speak task-related notifications"""
        message_templates = {
            "deadline_soon": f"Attention: The task '{task_title}' is due soon.",
            "deadline_now": f"Alert: The task '{task_title}' deadline has arrived.",
            "completed": f"Great job! Task '{task_title}' has been completed.",
            "overdue": f"Warning: The task '{task_title}' is overdue.",
            "reminder": f"Reminder: Don't forget about the task '{task_title}'.",
            "focus_start": f"Starting focus session for '{task_title}'. Good luck!",
            "focus_complete": f"Focus session completed for '{task_title}'. Time for a break!"
        }
        
        message = message_templates.get(notification_type, f"Notification for task: {task_title}")
        urgency = "urgent" if notification_type in ["deadline_now", "overdue"] else "normal"
        
        return self.speak_notification(message, urgency)
    
    def speak_system_status(self, status_info: Dict):
        """Speak system status information"""
        messages = []
        
        if "pending_tasks" in status_info:
            count = status_info["pending_tasks"]
            if count > 0:
                messages.append(f"You have {count} pending task{'s' if count != 1 else ''}")
        
        if "focus_sessions" in status_info:
            count = status_info["focus_sessions"]
            messages.append(f"You completed {count} focus session{'s' if count != 1 else ''} today")
        
        if "urgent_tasks" in status_info:
            count = status_info["urgent_tasks"]
            if count > 0:
                messages.append(f"You have {count} urgent task{'s' if count != 1 else ''}")
        
        if messages:
            message = ". ".join(messages) + "."
            return self.speak_notification(message, "normal")
        
        return False
    
    def speak_greeting(self, time_of_day: str = ""):
        """Speak a greeting message"""
        greetings = {
            "morning": "Good morning! Ready to tackle your tasks today?",
            "afternoon": "Good afternoon! Hope you're having a productive day.",
            "evening": "Good evening! Let's review what you've accomplished today.",
            "": "Hello! Your AI assistant is here to help you stay productive."
        }
        
        message = greetings.get(time_of_day, greetings[""])
        return self.speak_notification(message, "friendly")
    
    def stop_all_speech(self):
        """Stop all current and queued speech"""
        try:
            # Clear the queue
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
                except queue.Empty:
                    break
            
            # Stop current speech
            if hasattr(self.tts_engine, 'stop'):
                self.tts_engine.stop()
            
            self.is_speaking = False
            self.logger.info("All speech stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping speech: {e}")
    
    def set_enabled(self, enabled: bool):
        """Enable or disable voice notifications"""
        self.enabled = enabled
        if not enabled:
            self.stop_all_speech()
        
        # Update configuration
        self.voice_config["enabled"] = enabled
        self.save_config()
    
    def set_voice_rate(self, rate: int):
        """Set speech rate (words per minute)"""
        self.voice_rate = max(50, min(400, rate))  # Clamp between 50-400 WPM
        self.voice_config["rate"] = self.voice_rate
        
        if self.tts_engine and hasattr(self.tts_engine, 'setProperty'):
            self.tts_engine.setProperty('rate', self.voice_rate)
        
        self.save_config()
    
    def set_voice_volume(self, volume: float):
        """Set speech volume (0.0 to 1.0)"""
        self.voice_volume = max(0.0, min(1.0, volume))
        self.voice_config["volume"] = self.voice_volume
        
        if self.tts_engine and hasattr(self.tts_engine, 'setProperty'):
            self.tts_engine.setProperty('volume', self.voice_volume)
        
        self.save_config()
    
    def save_config(self):
        """Save voice configuration"""
        try:
            config_file = "data/config.json"
            
            # Load current config
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except FileNotFoundError:
                config = {}
            
            # Update voice settings
            config["voice"] = self.voice_config
            
            # Save updated config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
                
        except Exception as e:
            self.logger.error(f"Failed to save voice configuration: {e}")
    
    def get_available_voices(self) -> List[Dict]:
        """Get list of available voices"""
        voices = []
        
        if self.tts_engine and hasattr(self.tts_engine, 'getProperty'):
            try:
                system_voices = self.tts_engine.getProperty('voices')
                for voice in system_voices:
                    voices.append({
                        "id": voice.id,
                        "name": voice.name,
                        "language": getattr(voice, 'languages', ['en'])[0] if hasattr(voice, 'languages') else 'en',
                        "gender": "female" if any(keyword in voice.name.lower() 
                                                for keyword in ['female', 'woman']) else "male"
                    })
            except Exception as e:
                self.logger.error(f"Error getting available voices: {e}")
        
        return voices
    
    def test_voice(self, test_text: str = "This is a test of the voice notification system."):
        """Test the voice system with sample text"""
        return self.speak_notification(test_text, "normal")
    
    def shutdown(self):
        """Shutdown the voice system"""
        self.stop_all_speech()
        
        # Signal speech thread to stop
        self.speech_queue.put(None)
        
        if self.speech_thread and self.speech_thread.is_alive():
            self.speech_thread.join(timeout=2)
        
        if self.tts_engine and hasattr(self.tts_engine, 'stop'):
            self.tts_engine.stop()
        
        self.logger.info("Voice notification system shutdown")

# Test the voice system
if __name__ == "__main__":
    import time
    
    print("Testing Voice Notification System...")
    
    voice_system = VoiceNotificationSystem()
    
    if voice_system.is_initialized:
        print("✅ Voice system initialized")
        
        # Test basic notification
        print("🔊 Testing basic notification...")
        voice_system.speak_notification("Hello! This is a test of the voice notification system.")
        time.sleep(3)
        
        # Test task notification
        print("🔊 Testing task notification...")
        voice_system.speak_task_notification("Complete project report", "deadline_soon")
        time.sleep(3)
        
        # Test system status
        print("🔊 Testing system status...")
        status = {"pending_tasks": 5, "focus_sessions": 2, "urgent_tasks": 1}
        voice_system.speak_system_status(status)
        time.sleep(3)
        
        # Test greeting
        print("🔊 Testing greeting...")
        voice_system.speak_greeting("morning")
        time.sleep(2)
        
        print("✅ Voice system tests completed")
        
    else:
        print("❌ Voice system not available")
        print("To enable voice notifications:")
        print("1. Install pyttsx3: pip install pyttsx3")
        print("2. Or install platform-specific TTS:")
        print("   - Windows: Built-in SAPI")
        print("   - macOS: Built-in 'say' command")
        print("   - Linux: sudo apt-get install espeak")
    
    voice_system.shutdown()