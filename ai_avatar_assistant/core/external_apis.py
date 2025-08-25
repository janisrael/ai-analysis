import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import os

class ExternalAPIManager:
    """Manages external API integrations for enhanced functionality"""
    
    def __init__(self, config_path="data/config.json"):
        self.config = self.load_config(config_path)
        self.api_config = self.config.get("external_apis", {})
        self.logger = logging.getLogger(__name__)
        
        # Cache for API responses
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def load_config(self, config_path):
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp', 0)
        return (datetime.now().timestamp() - cached_time) < self.cache_duration
    
    def get_cached_data(self, cache_key: str):
        """Get cached data if valid"""
        if self.is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        return None
    
    def set_cache(self, cache_key: str, data):
        """Set cached data with timestamp"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
    
    # Weather API Integration
    def get_weather_info(self, city: str = None) -> Optional[Dict]:
        """Get current weather information"""
        try:
            # Use OpenWeatherMap API (free tier)
            api_key = self.api_config.get("openweather_api_key")
            if not api_key:
                return None
            
            if not city:
                city = self.api_config.get("default_city", "London")
            
            cache_key = f"weather_{city}"
            cached_data = self.get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": api_key,
                "units": "metric"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            weather_info = {
                "city": data["name"],
                "temperature": round(data["main"]["temp"]),
                "description": data["weather"][0]["description"].title(),
                "humidity": data["main"]["humidity"],
                "icon": data["weather"][0]["icon"],
                "feels_like": round(data["main"]["feels_like"])
            }
            
            self.set_cache(cache_key, weather_info)
            return weather_info
            
        except Exception as e:
            self.logger.error(f"Failed to get weather info: {e}")
            return None
    
    # News API Integration
    def get_news_headlines(self, category: str = "general", count: int = 5) -> Optional[List[Dict]]:
        """Get latest news headlines"""
        try:
            api_key = self.api_config.get("news_api_key")
            if not api_key:
                return None
            
            cache_key = f"news_{category}_{count}"
            cached_data = self.get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": api_key,
                "category": category,
                "country": self.api_config.get("news_country", "us"),
                "pageSize": count
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            headlines = []
            
            for article in data.get("articles", []):
                headlines.append({
                    "title": article["title"],
                    "description": article.get("description", ""),
                    "url": article["url"],
                    "source": article["source"]["name"],
                    "published": article["publishedAt"]
                })
            
            self.set_cache(cache_key, headlines)
            return headlines
            
        except Exception as e:
            self.logger.error(f"Failed to get news headlines: {e}")
            return None
    
    # Quote API Integration
    def get_daily_quote(self) -> Optional[Dict]:
        """Get inspirational quote of the day"""
        try:
            cache_key = "daily_quote"
            cached_data = self.get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            # Use quotable.io (free API)
            url = "https://api.quotable.io/random"
            params = {
                "maxLength": 150,
                "tags": "inspirational|motivational|success"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            quote_info = {
                "text": data["content"],
                "author": data["author"],
                "length": data["length"]
            }
            
            # Cache for 24 hours for daily quotes
            self.cache[cache_key] = {
                'data': quote_info,
                'timestamp': datetime.now().timestamp()
            }
            
            return quote_info
            
        except Exception as e:
            self.logger.error(f"Failed to get daily quote: {e}")
            return None
    
    # Time Zone API Integration
    def get_world_time(self, timezone: str = "UTC") -> Optional[Dict]:
        """Get current time in specified timezone"""
        try:
            cache_key = f"time_{timezone}"
            cached_data = self.get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            # Use worldtimeapi.org (free API)
            url = f"http://worldtimeapi.org/api/timezone/{timezone}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            time_info = {
                "timezone": data["timezone"],
                "datetime": data["datetime"],
                "utc_datetime": data["utc_datetime"],
                "day_of_week": data["day_of_week"],
                "day_of_year": data["day_of_year"],
                "week_number": data["week_number"]
            }
            
            self.set_cache(cache_key, time_info)
            return time_info
            
        except Exception as e:
            self.logger.error(f"Failed to get world time: {e}")
            return None
    
    # System Information
    def get_system_stats(self) -> Dict:
        """Get system performance statistics"""
        try:
            import psutil
            
            stats = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
                "battery": None
            }
            
            # Battery info if available
            try:
                battery = psutil.sensors_battery()
                if battery:
                    stats["battery"] = {
                        "percent": battery.percent,
                        "plugged": battery.power_plugged,
                        "time_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                    }
            except:
                pass
            
            return stats
            
        except ImportError:
            # psutil not installed
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "battery": None,
                "error": "psutil not installed"
            }
        except Exception as e:
            self.logger.error(f"Failed to get system stats: {e}")
            return {"error": str(e)}
    
    # Productivity Tips API
    def get_productivity_tip(self) -> Optional[Dict]:
        """Get a productivity tip"""
        # Static tips for now, could be enhanced with external API
        tips = [
            {
                "title": "Pomodoro Technique",
                "tip": "Work for 25 minutes, then take a 5-minute break. This helps maintain focus and prevents burnout.",
                "category": "time_management"
            },
            {
                "title": "Two-Minute Rule",
                "tip": "If a task takes less than 2 minutes to complete, do it immediately rather than adding it to your todo list.",
                "category": "efficiency"
            },
            {
                "title": "Eisenhower Matrix",
                "tip": "Categorize tasks by urgency and importance: Do, Schedule, Delegate, or Delete.",
                "category": "prioritization"
            },
            {
                "title": "Time Blocking",
                "tip": "Assign specific time blocks to different activities. This helps prevent tasks from expanding beyond their allocated time.",
                "category": "scheduling"
            },
            {
                "title": "Digital Minimalism",
                "tip": "Reduce digital distractions by turning off non-essential notifications during focused work time.",
                "category": "focus"
            },
            {
                "title": "Energy Management",
                "tip": "Schedule your most important tasks during your peak energy hours of the day.",
                "category": "energy"
            }
        ]
        
        import random
        return random.choice(tips)
    
    # Integration Status Check
    def check_api_status(self) -> Dict:
        """Check status of all configured APIs"""
        status = {
            "weather": False,
            "news": False,
            "quotes": True,  # quotable.io doesn't require API key
            "worldtime": True,  # worldtimeapi.org doesn't require API key
            "system_stats": True
        }
        
        # Check if API keys are configured
        if self.api_config.get("openweather_api_key"):
            status["weather"] = True
        
        if self.api_config.get("news_api_key"):
            status["news"] = True
        
        return status
    
    # Generate contextual notifications
    def get_contextual_notification(self) -> Optional[Dict]:
        """Generate a contextual notification based on external data"""
        try:
            current_hour = datetime.now().hour
            
            # Morning briefing (8-10 AM)
            if 8 <= current_hour <= 10:
                weather = self.get_weather_info()
                quote = self.get_daily_quote()
                
                if weather and quote:
                    return {
                        "type": "morning_briefing",
                        "title": "🌅 Good Morning!",
                        "message": f"Today's weather: {weather['temperature']}°C, {weather['description']}.\n\n" +
                                  f"💡 Daily inspiration: \"{quote['text']}\" - {quote['author']}",
                        "actions": ["start_focus_mode", "show_tasks", "get_suggestions"],
                        "urgency": 0.4,
                        "metadata": {"weather": weather, "quote": quote}
                    }
            
            # Afternoon productivity check (2-4 PM)
            elif 14 <= current_hour <= 16:
                tip = self.get_productivity_tip()
                system_stats = self.get_system_stats()
                
                if tip:
                    message = f"💡 Productivity Tip: {tip['title']}\n{tip['tip']}"
                    
                    if system_stats.get("cpu_percent", 0) > 80:
                        message += f"\n\n⚠️ Your system is running at {system_stats['cpu_percent']}% CPU. Consider closing some applications."
                    
                    return {
                        "type": "productivity_tip",
                        "title": "📈 Afternoon Check-in",
                        "message": message,
                        "actions": ["start_focus_mode", "show_tasks", "dismiss"],
                        "urgency": 0.3,
                        "metadata": {"tip": tip, "system_stats": system_stats}
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to generate contextual notification: {e}")
            return None


# Configuration template for external APIs
def create_api_config_template():
    """Create a template for external API configuration"""
    template = {
        "external_apis": {
            "openweather_api_key": "YOUR_OPENWEATHER_API_KEY_HERE",
            "news_api_key": "YOUR_NEWS_API_KEY_HERE",
            "default_city": "London",
            "news_country": "us",
            "enabled_integrations": {
                "weather": True,
                "news": True,
                "quotes": True,
                "world_time": True,
                "system_stats": True
            }
        }
    }
    return template

# Test the external APIs
if __name__ == "__main__":
    import sys
    import os
    
    # Create test configuration
    os.makedirs("data", exist_ok=True)
    
    api_manager = ExternalAPIManager()
    
    print("Testing External API Integrations...")
    
    # Test quote API (no key required)
    print("\n📖 Testing Daily Quote:")
    quote = api_manager.get_daily_quote()
    if quote:
        print(f"✓ Quote: \"{quote['text']}\" - {quote['author']}")
    else:
        print("❌ Failed to get quote")
    
    # Test productivity tip
    print("\n💡 Testing Productivity Tip:")
    tip = api_manager.get_productivity_tip()
    if tip:
        print(f"✓ Tip: {tip['title']} - {tip['tip']}")
    else:
        print("❌ Failed to get tip")
    
    # Test system stats
    print("\n💻 Testing System Stats:")
    stats = api_manager.get_system_stats()
    if stats and 'error' not in stats:
        print(f"✓ CPU: {stats['cpu_percent']}%, Memory: {stats['memory_percent']}%, Disk: {stats['disk_percent']}%")
    else:
        print(f"❌ System stats error: {stats.get('error', 'Unknown error')}")
    
    # Test API status
    print("\n🔌 API Status:")
    status = api_manager.check_api_status()
    for api, is_available in status.items():
        print(f"  {api}: {'✓' if is_available else '❌'}")
    
    print("\nTo enable weather and news features, add API keys to data/config.json:")
    print("- OpenWeatherMap: https://openweathermap.org/api")
    print("- News API: https://newsapi.org/")