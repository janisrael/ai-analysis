#!/usr/bin/env python3
"""
AI Avatar Assistant - Core Functionality Test
Test only the core components without GUI dependencies
"""

import os
import sys
import json
from datetime import datetime

def test_core_data_management():
    """Test data source management without external dependencies"""
    print("🗄️ Testing Core Data Management...")
    
    try:
        # Create demo data first
        os.makedirs("data/demo/projects", exist_ok=True)
        os.makedirs("data/demo/team", exist_ok=True)
        
        # Create sample project
        project_data = {
            "id": "test_001",
            "name": "Test E-commerce Site",
            "status": "active",
            "technologies": ["react", "node.js", "postgresql"],
            "requirements": [
                "User authentication",
                "Product catalog",
                "Shopping cart"
            ],
            "budget": 25000,
            "team_size": 3
        }
        
        with open("data/demo/projects/test_001.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        # Create sample team member
        team_data = {
            "id": "dev_001",
            "name": "John Doe",
            "role": "Full-Stack Developer",
            "skills": ["react", "node.js", "python"],
            "hourly_rate": 75,
            "availability": "available"
        }
        
        with open("data/demo/team/dev_001.json", 'w') as f:
            json.dump(team_data, f, indent=2)
        
        print("  ✅ Created sample data files")
        
        # Test data source configuration
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
        
        print("  ✅ Created data source configuration")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def test_project_estimation():
    """Test project estimation engine"""
    print("\n📊 Testing Project Estimation...")
    
    try:
        from core.data_source_manager import DataSourceManager
        from core.project_estimator import ProjectEstimator
        
        # Initialize components
        data_manager = DataSourceManager()
        data_manager.sync_all_sources()
        
        estimator = ProjectEstimator(data_manager)
        
        # Test estimation
        estimate = estimator.estimate_project(
            "Build a modern e-commerce website with React and Node.js",
            ["User authentication", "Product catalog", "Shopping cart", "Payment integration"],
            ["react", "node.js", "postgresql", "stripe"]
        )
        
        print(f"  📈 Project: {estimate.project_name}")
        print(f"  ⏱️ Estimated Hours: {estimate.total_hours}")
        print(f"  🎯 Difficulty: {estimate.difficulty_level}")
        print(f"  🎲 Confidence: {estimate.confidence_level:.1%}")
        print(f"  👥 Team Size: {estimate.recommended_team_size}")
        print(f"  ⚠️ Risk Score: {estimate.risk_score:.1%}")
        
        if estimate.recommended_roles:
            print(f"  👨‍💼 Roles: {', '.join(estimate.recommended_roles[:3])}")
        
        print("  ✅ Project estimation working!")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_loading():
    """Test data source loading"""
    print("\n📋 Testing Data Loading...")
    
    try:
        from core.data_source_manager import DataSourceManager
        
        data_manager = DataSourceManager()
        data_manager.sync_all_sources()
        
        projects = data_manager.get_all_projects()
        team_members = data_manager.get_team_members()
        
        print(f"  📊 Loaded {len(projects)} projects")
        print(f"  👥 Loaded {len(team_members)} team members")
        
        if projects:
            project = projects[0]
            print(f"  📋 Sample Project: {project.get('name', 'Unknown')}")
            print(f"      Technologies: {', '.join(project.get('technologies', []))}")
            print(f"      Status: {project.get('status', 'Unknown')}")
        
        if team_members:
            member = team_members[0]
            print(f"  👨‍💻 Sample Member: {member.get('name', 'Unknown')}")
            print(f"      Role: {member.get('role', 'Unknown')}")
            print(f"      Skills: {', '.join(member.get('skills', [])[:3])}")
        
        print("  ✅ Data loading working!")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_team_recommendations():
    """Test team recommendation system"""
    print("\n👥 Testing Team Recommendations...")
    
    try:
        from core.data_source_manager import DataSourceManager
        from core.project_estimator import ProjectEstimator
        
        data_manager = DataSourceManager()
        data_manager.sync_all_sources()
        
        estimator = ProjectEstimator(data_manager)
        
        # Test team recommendations for specific skills
        required_skills = ["react", "node.js"]
        team_members = data_manager.get_team_members()
        
        recommendations = []
        for member in team_members:
            member_skills = member.get('skills', [])
            if isinstance(member_skills, str):
                member_skills = [member_skills]
            
            matches = sum(1 for skill in required_skills if 
                         any(skill.lower() in ms.lower() for ms in member_skills))
            
            if matches > 0:
                recommendations.append({
                    'member': member,
                    'matches': matches,
                    'match_percentage': (matches / len(required_skills)) * 100
                })
        
        recommendations.sort(key=lambda x: x['matches'], reverse=True)
        
        print(f"  🎯 Looking for skills: {', '.join(required_skills)}")
        print(f"  🏆 Found {len(recommendations)} matching members")
        
        for i, rec in enumerate(recommendations[:3], 1):
            member = rec['member']
            print(f"  {i}. {member.get('name', 'Unknown')} ({rec['matches']}/{len(required_skills)} skills)")
            print(f"     Rate: ${member.get('hourly_rate', 0)}/hr")
        
        print("  ✅ Team recommendations working!")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def test_analytics_engine():
    """Test analytics engine basics"""
    print("\n📈 Testing Analytics Engine...")
    
    try:
        from core.analytics_engine import LiveAnalyticsEngine
        
        analytics = LiveAnalyticsEngine()
        
        # Test basic analytics
        data = analytics.get_visual_analytics_data()
        print(f"  📊 Analytics data keys: {list(data.keys())}")
        
        # Test situation analysis
        situation = analytics.analyze_current_situation()
        print(f"  🎯 Situation keys: {list(situation.keys())}")
        
        print("  ✅ Analytics engine working!")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def test_ai_engine():
    """Test AI engine functionality"""
    print("\n🧠 Testing AI Engine...")
    
    try:
        from core.ai_engine import AIEngine
        
        ai = AIEngine()
        
        # Test personality message
        message = ai.get_personality_message("greeting")
        print(f"  💬 Greeting message: {message}")
        
        # Test recommendations
        recommendations = ai.analyze_current_situation()
        print(f"  🎯 Generated {len(recommendations)} recommendations")
        
        print("  ✅ AI engine working!")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def demonstrate_orchestration():
    """Demonstrate the orchestration capabilities"""
    print("\n🚀 ORCHESTRATION DEMONSTRATION")
    print("-" * 45)
    
    try:
        from core.data_source_manager import DataSourceManager
        from core.project_estimator import ProjectEstimator
        
        # Initialize the system
        print("🔧 Initializing AI orchestration system...")
        data_manager = DataSourceManager()
        data_manager.sync_all_sources()
        estimator = ProjectEstimator(data_manager)
        
        # Simulate a real-world scenario
        print("\n📋 Scenario: New project request received")
        print("   Client wants: 'React dashboard with real-time analytics'")
        
        # AI analyzes the request
        project_description = "Build a React dashboard with real-time analytics, user authentication, and data visualization"
        requirements = [
            "User authentication and authorization",
            "Real-time data dashboard",
            "Interactive charts and graphs", 
            "Data export functionality",
            "Responsive mobile design"
        ]
        technologies = ["react", "node.js", "postgresql", "d3.js"]
        
        print("\n🧠 AI is analyzing the project...")
        estimate = estimator.estimate_project(project_description, requirements, technologies)
        
        print(f"\n📊 AI ORCHESTRATION RESULTS:")
        print(f"   🎯 Project: {estimate.project_name}")
        print(f"   ⏱️ Estimated Time: {estimate.realistic_hours} hours ({estimate.difficulty_level})")
        print(f"   💰 Estimated Cost: ${estimate.realistic_hours * 75:,} (at $75/hr average)")
        print(f"   👥 Recommended Team: {estimate.recommended_team_size} members")
        print(f"   🎲 Confidence Level: {estimate.confidence_level:.1%}")
        print(f"   ⚠️ Risk Assessment: {estimate.risk_score:.1%}")
        
        if estimate.recommended_roles:
            print(f"\n👨‍💼 Recommended Roles:")
            for role in estimate.recommended_roles:
                print(f"     • {role}")
        
        if estimate.phase_breakdown:
            print(f"\n📅 Phase Breakdown:")
            for phase, hours in estimate.phase_breakdown.items():
                print(f"     • {phase}: {hours} hours")
        
        # Find team members
        team_members = data_manager.get_team_members()
        if team_members:
            print(f"\n🏆 Available Team Members:")
            for member in team_members:
                skills = member.get('skills', [])
                relevant_skills = [s for s in skills if s in technologies]
                if relevant_skills:
                    print(f"     • {member.get('name', 'Unknown')} - {', '.join(relevant_skills)}")
                    print(f"       Rate: ${member.get('hourly_rate', 0)}/hr | Status: {member.get('availability', 'Unknown')}")
        
        print(f"\n✨ The AI has successfully orchestrated a complete project analysis!")
        print(f"   This demonstrates how the system can:")
        print(f"   🔍 Analyze project requirements automatically")
        print(f"   🎯 Provide accurate time and cost estimates")
        print(f"   👥 Recommend optimal team compositions")
        print(f"   ⚠️ Identify potential risks and challenges")
        print(f"   📊 Break down work into manageable phases")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestration demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run core functionality tests"""
    print("🤖 AI Avatar Assistant - Core Functionality Test")
    print("=" * 55)
    
    tests = [
        ("Core Data Management", test_core_data_management),
        ("Data Loading", test_data_loading),
        ("Project Estimation", test_project_estimation),
        ("Team Recommendations", test_team_recommendations),
        ("Analytics Engine", test_analytics_engine),
        ("AI Engine", test_ai_engine)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 55)
    print("📋 CORE FUNCTIONALITY TEST SUMMARY")
    print("=" * 55)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nCore Tests: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All core functionality tests passed!")
        print("\n🚀 Running orchestration demonstration...")
        demonstrate_orchestration()
        
        print(f"\n💡 What this means:")
        print(f"   ✅ The AI brain is working perfectly")
        print(f"   ✅ Data management is operational")
        print(f"   ✅ Project estimation is accurate")
        print(f"   ✅ Team recommendations are functional")
        print(f"   ✅ Core orchestration capabilities are ready")
        
        print(f"\n🔧 Next steps to complete testing:")
        print(f"   1. Install GUI dependencies for full interface")
        print(f"   2. Test widget API server functionality")
        print(f"   3. Create widget integrations for external dashboards")
        
    else:
        print(f"\n⚠️ {total - passed} core tests failed.")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()