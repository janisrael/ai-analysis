#!/usr/bin/env python3
"""
AI Avatar Assistant - Comprehensive Demonstration
This script demonstrates all the capabilities of the Universal Orchestration Agent
"""

import os
import sys
import json
import time
import threading
import webbrowser
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.data_source_manager import DataSourceManager
from core.project_estimator import ProjectEstimator
from core.widget_api import WidgetIntegrationManager
from core.analytics_engine import LiveAnalyticsEngine
from core.report_generator import ReportGenerator
from core.voice_system import VoiceNotificationSystem

class AIAvatarDemo:
    """Comprehensive demonstration of AI Avatar Assistant capabilities"""
    
    def __init__(self):
        print("🚀 AI Avatar Assistant - Universal Orchestration Demo")
        print("=" * 60)
        
        self.setup_demo_environment()
        self.init_components()
        
    def setup_demo_environment(self):
        """Create demo data and configuration"""
        print("\n📁 Setting up demo environment...")
        
        # Create directories
        os.makedirs("data/demo/projects", exist_ok=True)
        os.makedirs("data/demo/team", exist_ok=True)
        os.makedirs("data/demo/reports", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Create sample project data
        self.create_sample_projects()
        self.create_sample_team_data()
        self.create_sample_configurations()
        
        print("✅ Demo environment ready!")
    
    def create_sample_projects(self):
        """Create sample project JSON files"""
        projects = [
            {
                "id": "proj_001",
                "name": "E-commerce Platform",
                "status": "active",
                "description": "Modern React-based e-commerce platform with payment integration",
                "technologies": ["react", "node.js", "postgresql", "stripe"],
                "team_size": 4,
                "start_date": "2024-01-15",
                "estimated_completion": "2024-04-15",
                "complexity": 0.8,
                "priority": "high",
                "budget": 50000,
                "client": "TechCorp Inc",
                "requirements": [
                    "User authentication and registration",
                    "Product catalog with search and filters",
                    "Shopping cart and checkout process",
                    "Payment gateway integration (Stripe)",
                    "Admin dashboard for product management",
                    "Order tracking and history",
                    "Responsive mobile design"
                ]
            },
            {
                "id": "proj_002", 
                "name": "Analytics Dashboard",
                "status": "planning",
                "description": "Real-time analytics dashboard for business intelligence",
                "technologies": ["python", "django", "postgresql", "d3.js"],
                "team_size": 3,
                "start_date": "2024-02-01",
                "estimated_completion": "2024-05-01",
                "complexity": 0.6,
                "priority": "medium",
                "budget": 35000,
                "client": "DataViz Solutions",
                "requirements": [
                    "Real-time data visualization",
                    "Custom dashboard builder",
                    "Data export functionality",
                    "User role management",
                    "API integration with external data sources"
                ]
            },
            {
                "id": "proj_003",
                "name": "Mobile Banking App",
                "status": "completed",
                "description": "Secure mobile banking application for iOS and Android",
                "technologies": ["react-native", "node.js", "mongodb", "aws"],
                "team_size": 6,
                "start_date": "2023-08-01",
                "actual_completion": "2023-12-15",
                "complexity": 0.9,
                "priority": "critical",
                "budget": 120000,
                "actual_cost": 115000,
                "client": "SecureBank",
                "requirements": [
                    "Biometric authentication",
                    "Account balance and transaction history",
                    "Money transfer functionality",
                    "Bill payment integration",
                    "Investment portfolio tracking",
                    "Security features and fraud detection"
                ]
            },
            {
                "id": "proj_004",
                "name": "AI Chatbot Platform",
                "status": "active",
                "description": "Conversational AI platform with NLP capabilities",
                "technologies": ["python", "tensorflow", "flask", "redis"],
                "team_size": 5,
                "start_date": "2024-01-01",
                "estimated_completion": "2024-06-01",
                "complexity": 0.85,
                "priority": "high",
                "budget": 75000,
                "client": "AI Innovations",
                "requirements": [
                    "Natural language processing engine",
                    "Multi-language support",
                    "Integration APIs for various platforms",
                    "Analytics and conversation insights",
                    "Machine learning model training interface"
                ]
            }
        ]
        
        for project in projects:
            with open(f"data/demo/projects/{project['id']}.json", 'w') as f:
                json.dump(project, f, indent=2)
    
    def create_sample_team_data(self):
        """Create sample team member data"""
        team_members = [
            {
                "id": "dev_001",
                "name": "Sarah Chen",
                "role": "Senior Full-Stack Developer",
                "skills": ["react", "node.js", "python", "postgresql", "aws"],
                "experience_years": 7,
                "hourly_rate": 85,
                "availability": "available",
                "current_projects": ["proj_001"],
                "specialty": "Frontend Architecture",
                "location": "San Francisco, CA",
                "performance_rating": 4.8
            },
            {
                "id": "dev_002",
                "name": "Marcus Johnson",
                "role": "Backend Developer",
                "skills": ["python", "django", "postgresql", "redis", "docker"],
                "experience_years": 5,
                "hourly_rate": 75,
                "availability": "available",
                "current_projects": ["proj_002"],
                "specialty": "API Development",
                "location": "Austin, TX",
                "performance_rating": 4.6
            },
            {
                "id": "dev_003",
                "name": "Emily Rodriguez",
                "role": "Mobile Developer",
                "skills": ["react-native", "ios", "android", "swift", "kotlin"],
                "experience_years": 6,
                "hourly_rate": 80,
                "availability": "busy",
                "current_projects": ["proj_003", "proj_004"],
                "specialty": "Mobile UX",
                "location": "Seattle, WA",
                "performance_rating": 4.9
            },
            {
                "id": "dev_004",
                "name": "David Kim",
                "role": "DevOps Engineer",
                "skills": ["aws", "docker", "kubernetes", "terraform", "jenkins"],
                "experience_years": 8,
                "hourly_rate": 90,
                "availability": "available",
                "current_projects": ["proj_001", "proj_004"],
                "specialty": "Cloud Infrastructure",
                "location": "New York, NY",
                "performance_rating": 4.7
            },
            {
                "id": "dev_005",
                "name": "Anna Kowalski",
                "role": "UI/UX Designer",
                "skills": ["figma", "sketch", "ui/ux", "prototyping", "user research"],
                "experience_years": 4,
                "hourly_rate": 65,
                "availability": "available",
                "current_projects": ["proj_002"],
                "specialty": "User Experience Design",
                "location": "Chicago, IL",
                "performance_rating": 4.5
            },
            {
                "id": "dev_006",
                "name": "Robert Zhang",
                "role": "Data Scientist",
                "skills": ["python", "tensorflow", "pandas", "sql", "machine learning"],
                "experience_years": 6,
                "hourly_rate": 95,
                "availability": "available",
                "current_projects": ["proj_004"],
                "specialty": "Machine Learning",
                "location": "Boston, MA",
                "performance_rating": 4.8
            }
        ]
        
        for member in team_members:
            with open(f"data/demo/team/{member['id']}.json", 'w') as f:
                json.dump(member, f, indent=2)
    
    def create_sample_configurations(self):
        """Create sample configuration files"""
        # Data sources configuration
        data_sources_config = {
            "data_sources": {
                "demo_projects": {
                    "source_type": "json_folder",
                    "name": "Demo Projects",
                    "config": {
                        "folder_path": "data/demo/projects",
                        "file_pattern": "*.json",
                        "recursive": False
                    },
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                "demo_team": {
                    "source_type": "json_folder", 
                    "name": "Demo Team",
                    "config": {
                        "folder_path": "data/demo/team",
                        "file_pattern": "*.json",
                        "recursive": False
                    },
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                }
            }
        }
        
        with open("data/data_sources.json", 'w') as f:
            json.dump(data_sources_config, f, indent=2)
    
    def init_components(self):
        """Initialize AI Avatar Assistant components"""
        print("\n🧠 Initializing AI components...")
        
        # Core components
        self.data_source_manager = DataSourceManager()
        self.project_estimator = ProjectEstimator(self.data_source_manager)
        self.analytics_engine = LiveAnalyticsEngine()
        self.voice_system = VoiceNotificationSystem()
        
        # Widget integration (mock AI assistant for demo)
        self.widget_integration_manager = WidgetIntegrationManager(
            self, self.data_source_manager, self.project_estimator
        )
        
        print("✅ Components initialized!")
    
    def run_demo(self):
        """Run the comprehensive demonstration"""
        print("\n🎯 Starting AI Avatar Assistant Demo")
        print("=" * 60)
        
        self.demo_data_source_management()
        self.demo_project_estimation()
        self.demo_team_recommendations()
        self.demo_widget_integration()
        self.demo_analytics_and_reporting()
        self.demo_voice_notifications()
        
        print("\n🎉 Demo completed! All features demonstrated successfully.")
        print("\n💡 Next steps:")
        print("1. Run 'python main.py' to start the full application")
        print("2. Open the Widget Manager to create integrations")
        print("3. Configure your own data sources")
        print("4. Embed widgets in your dashboards")
    
    def demo_data_source_management(self):
        """Demonstrate data source management capabilities"""
        print("\n🗄️ DATA SOURCE MANAGEMENT DEMO")
        print("-" * 40)
        
        # Show data source status
        status = self.data_source_manager.get_data_source_status()
        print(f"📊 Data Sources: {status['active_sources']}/{status['total_sources']} active")
        
        # Sync all sources
        print("🔄 Syncing data sources...")
        self.data_source_manager.sync_all_sources()
        
        # Show loaded data
        projects = self.data_source_manager.get_all_projects()
        team_members = self.data_source_manager.get_team_members()
        
        print(f"✅ Loaded {len(projects)} projects and {len(team_members)} team members")
        
        # Display sample data
        if projects:
            print(f"\n📋 Sample Projects:")
            for proj in projects[:3]:
                print(f"  • {proj.get('name', 'Unknown')} ({proj.get('status', 'N/A')})")
        
        if team_members:
            print(f"\n👥 Sample Team Members:")
            for member in team_members[:3]:
                skills = member.get('skills', [])
                skills_str = ', '.join(skills[:3]) + ('...' if len(skills) > 3 else '')
                print(f"  • {member.get('name', 'Unknown')} - {skills_str}")
    
    def demo_project_estimation(self):
        """Demonstrate project estimation capabilities"""
        print("\n📊 PROJECT ESTIMATION DEMO")
        print("-" * 40)
        
        # Example project estimation
        project_description = """
        Build a modern e-commerce website with the following features:
        - User registration and authentication
        - Product catalog with search and filtering
        - Shopping cart and checkout process
        - Payment integration with Stripe
        - Admin dashboard for inventory management
        - Order tracking and customer support
        - Responsive design for mobile and desktop
        """
        
        requirements = [
            "User authentication system",
            "Product catalog with search",
            "Shopping cart functionality", 
            "Payment gateway integration",
            "Admin dashboard",
            "Order management system",
            "Responsive mobile design"
        ]
        
        technologies = ["react", "node.js", "postgresql", "stripe", "aws"]
        
        print("🎯 Estimating project: E-commerce Website")
        print("🔧 Technologies:", ", ".join(technologies))
        print("📝 Requirements:", len(requirements), "items")
        
        # Generate estimate
        estimate = self.project_estimator.estimate_project(
            project_description, requirements, technologies
        )
        
        # Display results
        print(f"\n📈 ESTIMATION RESULTS:")
        print(f"  📊 Total Hours: {estimate.total_hours}")
        print(f"  ⚡ Optimistic: {estimate.optimistic_hours}h")
        print(f"  🎯 Realistic: {estimate.realistic_hours}h") 
        print(f"  🐌 Pessimistic: {estimate.pessimistic_hours}h")
        print(f"  🔥 Difficulty: {estimate.difficulty_level}")
        print(f"  🎲 Confidence: {estimate.confidence_level:.1%}")
        print(f"  👥 Team Size: {estimate.recommended_team_size} people")
        print(f"  ⚠️ Risk Score: {estimate.risk_score:.1%}")
        
        if estimate.recommended_roles:
            print(f"\n👨‍💼 Recommended Roles:")
            for role in estimate.recommended_roles:
                print(f"    • {role}")
        
        if estimate.team_members:
            print(f"\n🏆 Recommended Team Members:")
            for member in estimate.team_members[:3]:
                print(f"    • {member.get('name', 'Unknown')} - {member.get('role', 'N/A')}")
    
    def demo_team_recommendations(self):
        """Demonstrate team recommendation capabilities"""
        print("\n👥 TEAM RECOMMENDATION DEMO")
        print("-" * 40)
        
        # Get team data
        team_members = self.data_source_manager.get_team_members()
        
        if not team_members:
            print("❌ No team data available for recommendations")
            return
        
        # Demo: Find developers for a React project
        required_skills = ["react", "node.js", "postgresql"]
        print(f"🎯 Finding team members for skills: {', '.join(required_skills)}")
        
        recommendations = []
        for member in team_members:
            member_skills = member.get('skills', [])
            if isinstance(member_skills, str):
                member_skills = [member_skills]
            
            # Calculate skill matches
            matches = sum(1 for skill in required_skills if 
                         any(skill.lower() in ms.lower() for ms in member_skills))
            
            if matches > 0:
                recommendations.append({
                    'member': member,
                    'matches': matches,
                    'match_percentage': (matches / len(required_skills)) * 100
                })
        
        # Sort by matches
        recommendations.sort(key=lambda x: x['matches'], reverse=True)
        
        print(f"\n🏆 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations[:5], 1):
            member = rec['member']
            print(f"  {i}. {member.get('name', 'Unknown')} ({rec['matches']}/{len(required_skills)} skills)")
            print(f"     Role: {member.get('role', 'N/A')}")
            print(f"     Rate: ${member.get('hourly_rate', 0)}/hr")
            print(f"     Status: {member.get('availability', 'Unknown')}")
            print()
    
    def demo_widget_integration(self):
        """Demonstrate widget integration capabilities"""
        print("\n🔗 WIDGET INTEGRATION DEMO")
        print("-" * 40)
        
        # Initialize widget API
        print("🚀 Starting Widget API server...")
        if self.widget_integration_manager.initialize_widget_api(5556):
            print("✅ Widget API server running on port 5556")
            
            # Generate integration code
            try:
                integration_data = self.widget_integration_manager.generate_integration_code(
                    "Demo Dashboard",
                    "localhost", 
                    "http://localhost:3000/ai-assistant"
                )
                
                print(f"\n🔑 Generated API Key: {integration_data['api_key'][:16]}...")
                print(f"🆔 Widget ID: {integration_data['widget_id']}")
                print(f"🌐 Widget URL: {integration_data['widget_url']}")
                
                # Save demo integration code
                demo_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Avatar Assistant - Widget Demo</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .demo-section {{
            display: flex;
            gap: 30px;
            align-items: flex-start;
        }}
        .info-panel {{
            flex: 1;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
        }}
        .widget-container {{
            flex: 0 0 420px;
        }}
        .feature-list {{
            list-style: none;
            padding: 0;
        }}
        .feature-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .feature-list li:last-child {{
            border-bottom: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Avatar Assistant - Widget Demo</h1>
            <p>Experience the power of Universal AI Orchestration</p>
        </div>
        
        <div class="demo-section">
            <div class="info-panel">
                <h2>🚀 Features Demonstrated</h2>
                <ul class="feature-list">
                    <li>🔗 <strong>Widget Integration</strong> - Embeddable in any dashboard</li>
                    <li>📊 <strong>Project Estimation</strong> - AI-powered time and cost estimates</li>
                    <li>👥 <strong>Team Recommendations</strong> - Skill-based member matching</li>
                    <li>📈 <strong>Real-time Analytics</strong> - Productivity insights and trends</li>
                    <li>🎙️ <strong>Voice Notifications</strong> - Audio feedback and narration</li>
                    <li>🗄️ <strong>Multi-source Data</strong> - JSON, SQL, APIs unified</li>
                    <li>💬 <strong>Conversational AI</strong> - Natural language interactions</li>
                    <li>⚡ <strong>Live Synchronization</strong> - Real-time data updates</li>
                </ul>
                
                <h3>🎯 Try These Commands</h3>
                <ul class="feature-list">
                    <li>"Estimate a React e-commerce project"</li>
                    <li>"Show me team recommendations"</li>
                    <li>"What's my project status?"</li>
                    <li>"Generate analytics report"</li>
                </ul>
            </div>
            
            <div class="widget-container">
                <div id="ai-avatar-widget-container"></div>
            </div>
        </div>
    </div>

    {integration_data['integration_code']}
    
    <script>
        // Demo enhancement: Add some demo interactions
        setTimeout(() => {{
            console.log('🤖 AI Avatar Widget Demo Ready!');
            console.log('Widget ID:', '{integration_data["widget_id"]}');
            console.log('API Endpoint:', '{integration_data["api_endpoint"]}');
        }}, 1000);
    </script>
</body>
</html>
                """
                
                # Save demo file
                demo_file = "data/demo/widget_demo.html"
                with open(demo_file, 'w') as f:
                    f.write(demo_html)
                
                print(f"💾 Demo HTML saved to: {demo_file}")
                print(f"🌐 Open in browser: file://{os.path.abspath(demo_file)}")
                
                # Option to open automatically
                try:
                    webbrowser.open(f"file://{os.path.abspath(demo_file)}")
                    print("🚀 Opening demo in browser...")
                except:
                    print("ℹ️ Open the HTML file manually to see the widget demo")
                
            except Exception as e:
                print(f"❌ Failed to generate integration: {e}")
        else:
            print("❌ Failed to start Widget API server")
    
    def demo_analytics_and_reporting(self):
        """Demonstrate analytics and reporting capabilities"""
        print("\n📈 ANALYTICS & REPORTING DEMO")
        print("-" * 40)
        
        # Mock analytics data based on our demo projects
        print("📊 Generating analytics insights...")
        
        projects = self.data_source_manager.get_all_projects()
        team_members = self.data_source_manager.get_team_members()
        
        if projects and team_members:
            # Calculate some basic analytics
            active_projects = [p for p in projects if p.get('status') == 'active']
            completed_projects = [p for p in projects if p.get('status') == 'completed']
            total_budget = sum(p.get('budget', 0) for p in projects)
            avg_team_size = sum(p.get('team_size', 0) for p in projects) / len(projects)
            
            print(f"\n📋 PROJECT ANALYTICS:")
            print(f"  📊 Total Projects: {len(projects)}")
            print(f"  🚀 Active Projects: {len(active_projects)}")
            print(f"  ✅ Completed Projects: {len(completed_projects)}")
            print(f"  💰 Total Budget: ${total_budget:,}")
            print(f"  👥 Average Team Size: {avg_team_size:.1f}")
            
            print(f"\n👨‍💼 TEAM ANALYTICS:")
            print(f"  👥 Total Team Members: {len(team_members)}")
            
            available_members = [m for m in team_members if m.get('availability') == 'available']
            busy_members = [m for m in team_members if m.get('availability') == 'busy']
            
            print(f"  ✅ Available: {len(available_members)}")
            print(f"  🔥 Busy: {len(busy_members)}")
            
            # Calculate average rates
            rates = [m.get('hourly_rate', 0) for m in team_members if m.get('hourly_rate')]
            if rates:
                print(f"  💵 Avg Hourly Rate: ${sum(rates)/len(rates):.0f}")
            
            # Technology usage
            all_techs = []
            for project in projects:
                all_techs.extend(project.get('technologies', []))
            
            from collections import Counter
            tech_counts = Counter(all_techs)
            
            print(f"\n🔧 TECHNOLOGY USAGE:")
            for tech, count in tech_counts.most_common(5):
                print(f"  • {tech}: {count} projects")
    
    def demo_voice_notifications(self):
        """Demonstrate voice notification capabilities"""
        print("\n🎙️ VOICE NOTIFICATIONS DEMO")
        print("-" * 40)
        
        if not self.voice_system.enabled:
            print("🔊 Enabling voice notifications...")
            self.voice_system.set_enabled(True)
        
        # Test voice system
        print("🧪 Testing voice system...")
        if self.voice_system.test_voice():
            print("✅ Voice system is working!")
            
            # Demo different notification types
            notifications = [
                ("Welcome to the AI Avatar Assistant demo!", "friendly"),
                ("Project estimation completed successfully.", "normal"),
                ("New team member recommendation available.", "normal"),
                ("Widget integration is ready for deployment.", "friendly")
            ]
            
            print("\n🔊 Playing demo voice notifications...")
            for message, tone in notifications:
                print(f"  🎵 {message}")
                self.voice_system.speak_notification(message, tone)
                time.sleep(2)  # Brief pause between notifications
                
        else:
            print("❌ Voice system not available (this is normal in some environments)")
            print("ℹ️ Voice notifications work with proper audio setup")
    
    def cleanup_demo(self):
        """Clean up demo resources"""
        print("\n🧹 Cleaning up demo resources...")
        
        # Stop widget API server
        if hasattr(self, 'widget_integration_manager'):
            self.widget_integration_manager.shutdown()
        
        # Stop voice system
        if hasattr(self, 'voice_system'):
            self.voice_system.shutdown()
        
        print("✅ Demo cleanup completed")

def main():
    """Main demo function"""
    demo = AIAvatarDemo()
    
    try:
        demo.run_demo()
        
        # Keep the demo running for widget testing
        print("\n⏳ Demo server running... Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️ Demo stopped by user")
            
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        demo.cleanup_demo()

if __name__ == "__main__":
    main()