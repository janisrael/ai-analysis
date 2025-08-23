#!/usr/bin/env python3
"""
Create sample data for testing the AI Avatar Assistant
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import TaskDatabase

def create_sample_tasks():
    """Create sample tasks for testing"""
    db = TaskDatabase()
    
    # Sample tasks with various deadlines and priorities
    sample_tasks = [
        {
            "title": "Complete Project Report",
            "description": "Finish the quarterly project report for the management team",
            "deadline": datetime.now() + timedelta(hours=3),
            "priority": 5,
            "metadata": {"category": "work", "estimated_hours": 4}
        },
        {
            "title": "Team Meeting Preparation",
            "description": "Prepare agenda and materials for tomorrow's team meeting",
            "deadline": datetime.now() + timedelta(hours=18),
            "priority": 4,
            "metadata": {"category": "work", "meeting_type": "weekly"}
        },
        {
            "title": "Code Review",
            "description": "Review pull requests from team members",
            "deadline": datetime.now() + timedelta(days=1),
            "priority": 3,
            "metadata": {"category": "development", "pull_requests": 5}
        },
        {
            "title": "Update Documentation",
            "description": "Update API documentation with recent changes",
            "deadline": datetime.now() + timedelta(days=2),
            "priority": 2,
            "metadata": {"category": "documentation", "pages": 10}
        },
        {
            "title": "Client Call",
            "description": "Schedule and prepare for client feedback call",
            "deadline": datetime.now() + timedelta(hours=6),
            "priority": 4,
            "metadata": {"category": "client", "client_name": "Acme Corp"}
        },
        {
            "title": "Database Backup",
            "description": "Perform weekly database backup and verification",
            "deadline": datetime.now() + timedelta(days=3),
            "priority": 3,
            "metadata": {"category": "maintenance", "backup_type": "full"}
        },
        {
            "title": "Performance Optimization",
            "description": "Optimize database queries for the user dashboard",
            "deadline": datetime.now() + timedelta(days=5),
            "priority": 2,
            "metadata": {"category": "optimization", "target": "dashboard"}
        },
        {
            "title": "Security Audit",
            "description": "Conduct security audit of the authentication system",
            "deadline": datetime.now() + timedelta(days=7),
            "priority": 5,
            "metadata": {"category": "security", "scope": "authentication"}
        },
        {
            "title": "Training Session",
            "description": "Attend Python advanced features training session",
            "deadline": datetime.now() + timedelta(days=4),
            "priority": 3,
            "metadata": {"category": "learning", "duration": "4 hours"}
        },
        {
            "title": "Grocery Shopping",
            "description": "Buy groceries for the week including vegetables and fruits",
            "deadline": datetime.now() + timedelta(hours=12),
            "priority": 2,
            "metadata": {"category": "personal", "store": "local market"}
        }
    ]
    
    print("Creating sample tasks...")
    created_tasks = []
    
    for task_data in sample_tasks:
        task_id = db.add_task(
            title=task_data["title"],
            description=task_data["description"],
            deadline=task_data["deadline"],
            priority=task_data["priority"],
            metadata=task_data["metadata"]
        )
        created_tasks.append(task_id)
        print(f"✓ Created task: {task_data['title']} (ID: {task_id})")
    
    print(f"\nCreated {len(created_tasks)} sample tasks!")
    
    # Add some completed tasks for history
    completed_tasks = [
        {
            "title": "Weekly Planning",
            "description": "Plan tasks for the upcoming week",
            "deadline": datetime.now() - timedelta(days=1),
            "priority": 3,
            "metadata": {"category": "planning"}
        },
        {
            "title": "Email Cleanup",
            "description": "Clean up and organize email inbox",
            "deadline": datetime.now() - timedelta(hours=6),
            "priority": 2,
            "metadata": {"category": "organization"}
        }
    ]
    
    print("\nCreating completed tasks...")
    for task_data in completed_tasks:
        task_id = db.add_task(
            title=task_data["title"],
            description=task_data["description"],
            deadline=task_data["deadline"],
            priority=task_data["priority"],
            metadata=task_data["metadata"]
        )
        # Mark as completed
        db.update_task_status(task_id, "completed")
        print(f"✓ Created completed task: {task_data['title']} (ID: {task_id})")
    
    # Add some custom events
    print("\nCreating sample events...")
    
    # Daily standup reminder
    standup_time = datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)
    if standup_time < datetime.now():
        standup_time += timedelta(days=1)
    
    event_id = db.add_event(
        event_type="daily_reminder",
        title="Daily Standup",
        message="Time for the daily team standup meeting",
        trigger_time=standup_time
    )
    print(f"✓ Created daily standup event (ID: {event_id})")
    
    # Lunch break reminder
    lunch_time = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    if lunch_time < datetime.now():
        lunch_time += timedelta(days=1)
    
    event_id = db.add_event(
        event_type="break_reminder",
        title="Lunch Break",
        message="Take a break and have lunch!",
        trigger_time=lunch_time
    )
    print(f"✓ Created lunch break event (ID: {event_id})")
    
    print("\n🎉 Sample data creation completed!")
    print("\nYou can now run the AI Avatar Assistant to see it in action:")
    print("python main.py")
    
    # Show current task summary
    all_tasks = db.get_tasks()
    pending_tasks = db.get_tasks(status="pending")
    completed_tasks = db.get_tasks(status="completed")
    
    print(f"\n📊 Task Summary:")
    print(f"Total tasks: {len(all_tasks)}")
    print(f"Pending tasks: {len(pending_tasks)}")
    print(f"Completed tasks: {len(completed_tasks)}")
    
    # Show upcoming deadlines
    urgent_tasks = db.get_tasks(status="pending", upcoming_hours=24)
    if urgent_tasks:
        print(f"\n⚠️  Tasks due in next 24 hours:")
        for task in urgent_tasks:
            deadline_str = task['deadline'] if task['deadline'] else "No deadline"
            print(f"  • {task['title']} - Due: {deadline_str}")

def clear_all_data():
    """Clear all existing data (for testing)"""
    db = TaskDatabase()
    
    print("⚠️  Clearing all existing data...")
    
    # This would require additional methods in the database class
    # For now, just delete the database file
    import os
    if os.path.exists("data/tasks.db"):
        os.remove("data/tasks.db")
        print("✓ Database cleared")
    
    # Recreate database
    db.init_database()
    print("✓ Database recreated")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create sample data for AI Avatar Assistant")
    parser.add_argument("--clear", action="store_true", help="Clear existing data first")
    args = parser.parse_args()
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    if args.clear:
        clear_all_data()
    
    create_sample_tasks()

if __name__ == "__main__":
    main()