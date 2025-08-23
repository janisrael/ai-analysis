# AI Avatar Assistant 🤖

An intelligent AI-powered assistant with a floating avatar that dynamically monitors your tasks and provides helpful suggestions through interactive tooltips.

## Features ✨

- **Floating Avatar**: A customizable AI assistant that stays visible on your desktop
- **Dynamic Tooltips**: Smart notifications with action buttons for quick task management
- **Intelligent Monitoring**: AI-powered analysis of deadlines, priorities, and productivity patterns
- **Task Management**: Built-in SQLite database for storing and managing tasks
- **Background Scheduling**: Automatic event detection and reminder system
- **System Tray Integration**: Runs quietly in the background with system tray controls
- **Customizable Personality**: Configurable AI personality and behavior settings

## Screenshots

*Note: The avatar appears as a floating circular AI assistant on your desktop with animated tooltips showing task notifications and action buttons.*

## Installation 🚀

### Prerequisites

- Python 3.8 or higher
- PyQt5
- APScheduler

### Setup

1. **Clone or download this project**
   ```bash
   cd ai_avatar_assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create sample data (optional but recommended for testing)**
   ```bash
   python create_sample_data.py
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## Usage 📖

### Starting the Assistant

Run the main application:
```bash
python main.py
```

The AI avatar will appear on your desktop (bottom-right by default) and the application will run in the system tray.

### Basic Interactions

- **Click the Avatar**: Opens the main assistant menu
- **System Tray**: Right-click the tray icon for options
- **Tooltips**: Interactive notifications with action buttons appear automatically
- **Drag Avatar**: You can drag the avatar to reposition it on your screen

### Managing Tasks

Tasks can be managed through:
- The tooltip action buttons
- System tray menu ("Add Task", "Show Tasks")
- Avatar click menu

### Configuration

Edit `data/config.json` to customize:
- Avatar position and size
- Notification settings and silent hours
- AI personality (friendly, professional, casual)
- Check intervals and behavior

Example configuration:
```json
{
    "avatar": {
        "position": "bottom_right",
        "size": 64,
        "animation_speed": 1.0
    },
    "notifications": {
        "enabled": true,
        "silent_hours_start": "22:00",
        "silent_hours_end": "08:00",
        "auto_hide_timeout": 10,
        "check_interval": 300
    },
    "ai": {
        "personality": "friendly",
        "confidence_threshold": 0.7
    }
}
```

## Project Structure 📁

```
ai_avatar_assistant/
├── main.py                 # Main application entry point
├── create_sample_data.py   # Script to create test data
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── ui/
│   ├── avatar.py          # Avatar widget with animations
│   └── tooltip.py         # Tooltip system with action buttons
├── core/
│   ├── database.py        # SQLite task storage
│   ├── ai_engine.py       # AI recommendation engine
│   ├── actions.py         # Action system for button handlers
│   └── scheduler.py       # Background event scheduler
├── data/
│   ├── config.json        # Configuration settings
│   ├── tasks.db          # SQLite database (created automatically)
│   └── assistant.log     # Application logs
└── assets/
    └── icons/            # Icon assets (optional)
```

## Key Components 🧩

### 1. Avatar Widget (`ui/avatar.py`)
- Floating, draggable AI assistant
- Smooth animations (pulse, bounce, glow)
- Customizable appearance and position
- Mood indicators (happy, urgent, thinking, etc.)

### 2. Tooltip System (`ui/tooltip.py`)
- Dynamic notification bubbles
- Interactive action buttons
- Auto-positioning near avatar
- Fade in/out animations
- Auto-hide with configurable timeout

### 3. AI Engine (`core/ai_engine.py`)
- Intelligent task analysis
- Urgency calculation based on deadlines and priority
- Productivity pattern recognition
- Personality-based messaging
- Learning from user actions

### 4. Action System (`core/actions.py`)
- Extensible action framework
- Task management operations
- External integrations (calendar, email)
- System actions (settings, focus mode)
- Result feedback and logging

### 5. Event Scheduler (`core/scheduler.py`)
- Background monitoring
- Cron-based scheduling
- Silent hours support
- Event triggering and callbacks
- Notification pause/resume

### 6. Database (`core/database.py`)
- SQLite-based task storage
- Event and action logging
- Flexible metadata support
- Automatic reminder creation

## Available Actions 🎯

The assistant supports many actions triggered through tooltip buttons:

**Task Management:**
- `open_task` - View/edit task details
- `mark_done` - Mark task as completed
- `snooze` - Snooze notifications temporarily
- `reschedule` - Change task deadline
- `extend_deadline` - Add more time to deadline

**Productivity:**
- `show_tasks` - Display task overview
- `prioritize_tasks` - Help prioritize tasks
- `start_focus_mode` - Enter focused work mode
- `get_suggestions` - Get AI productivity tips

**System:**
- `dismiss` - Close current notification
- `pause_notifications` - Pause all notifications
- `settings` - Open settings (configuration)

**External:**
- `open_calendar` - Open default calendar app
- `open_email` - Open default email app
- `open_file` - Open specific files
- `open_url` - Open web links

## Customization 🎨

### Avatar Appearance
- Size: Configurable in config.json (default: 64px)
- Position: bottom_right, bottom_left, top_right, top_left, center
- Animation Speed: Multiplier for animation timing
- Custom Images: Place avatar.png or avatar.gif in assets/ folder

### AI Personality
Three built-in personalities:
- **Friendly**: Warm, encouraging messages with emojis
- **Professional**: Formal, business-appropriate tone
- **Casual**: Relaxed, informal communication style

### Notification Behavior
- Silent Hours: Configure quiet periods
- Auto-hide Timeout: How long tooltips stay visible
- Check Interval: How often to scan for events
- Urgency Thresholds: When to show different types of alerts

## Development 🛠️

### Adding New Actions

1. Add action handler to `core/actions.py`:
```python
def my_custom_action(self, context: Dict) -> Dict:
    # Your action logic here
    return {"success": True, "message": "Action completed"}
```

2. Register in `register_action_handlers()`:
```python
"my_action": self.my_custom_action,
```

3. Add button label in `ui/tooltip.py`:
```python
"my_action": "🔧 Custom",
```

### Adding New Events

Events can be scheduled through the scheduler:
```python
scheduler.add_one_time_event(event_data, trigger_time)
scheduler.add_recurring_event(event_data, interval_seconds)
```

### Extending AI Intelligence

The AI engine can be enhanced by:
- Adding new analysis methods to `ai_engine.py`
- Implementing machine learning models
- Adding external API integrations
- Expanding the personality system

## Testing 🧪

### Create Test Data
```bash
python create_sample_data.py --clear
```

This creates various sample tasks with different priorities and deadlines to test the assistant's behavior.

### Manual Testing
1. Add tasks with near-term deadlines
2. Click the avatar to test menu interactions
3. Try different action buttons in tooltips
4. Test system tray functionality
5. Verify notifications during work hours

### Logs
Check `data/assistant.log` for debugging information and system events.

## Troubleshooting 🔧

### Common Issues

**Avatar doesn't appear:**
- Check if PyQt5 is properly installed
- Verify system tray is available
- Check display scaling settings

**No notifications:**
- Verify silent hours configuration
- Check if notifications are paused
- Look for errors in assistant.log

**Database errors:**
- Ensure data/ directory is writable
- Check SQLite installation
- Try recreating with `--clear` flag

**Performance issues:**
- Reduce check_interval in config
- Disable animations by setting speed to 0
- Check system resources

### Dependencies

If you encounter import errors:
```bash
pip install --upgrade PyQt5 APScheduler requests Pillow python-dateutil
```

For older systems, you might need:
```bash
pip install PyQt5==5.12.3  # Use older version if needed
```

## Future Enhancements 🚀

Planned features for future versions:
- Voice interaction support
- Cross-platform synchronization
- Natural language task input
- Integration with popular productivity tools
- Mobile companion app
- Advanced machine learning models
- Plugin system for custom extensions

## Contributing 🤝

This is an independent project designed as a demonstration of AI assistant capabilities. Feel free to:
- Fork and modify for your needs
- Add new features and improvements
- Create custom actions and integrations
- Share feedback and suggestions

## License 📄

This project is provided as-is for educational and personal use. Modify and distribute as needed.

## Support 💬

For questions or issues:
1. Check the troubleshooting section
2. Review the logs in `data/assistant.log`
3. Examine the configuration in `data/config.json`
4. Try recreating sample data with `--clear` flag

---

**Enjoy your AI Avatar Assistant! 🤖✨**

*The assistant learns from your interactions and becomes more helpful over time. Click on the avatar anytime you need assistance with your tasks!*