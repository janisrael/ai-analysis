#!/bin/bash
# AI Avatar Assistant - Production Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${ENVIRONMENT:-production}
WORKERS=${WORKERS:-4}
TIMEOUT=${TIMEOUT:-120}
BIND_ADDRESS=${BIND_ADDRESS:-0.0.0.0:5555}
LOG_LEVEL=${LOG_LEVEL:-info}

echo -e "${BLUE}🚀 Starting AI Avatar Assistant in ${ENVIRONMENT} mode${NC}"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Check if running in container
if [ -f /.dockerenv ]; then
    log "Running in Docker container"
    CONTAINER_MODE=true
else
    log "Running on host system"
    CONTAINER_MODE=false
fi

# Create necessary directories
log "Creating directories..."
mkdir -p data logs reports temp

# Set proper permissions
chmod 755 data logs reports temp

# Check Python version
log "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
if [[ ${python_version:0:3} < "3.8" ]]; then
    error "Python 3.8+ is required. Found: $python_version"
    exit 1
fi
log "Python version: $python_version ✓"

# Check dependencies
log "Checking core dependencies..."

# Check if we can import required modules
python3 -c "
import sys
required_modules = [
    'flask', 'requests', 'apscheduler', 'psutil',
    'sqlite3', 'json', 'datetime', 'threading'
]

missing = []
for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)

if missing:
    print(f'Missing modules: {missing}')
    sys.exit(1)
print('All core dependencies available ✓')
"

if [ $? -ne 0 ]; then
    error "Missing required dependencies"
    exit 1
fi

# Initialize database if needed
log "Initializing database..."
python3 -c "
from core.database import TaskDatabase
try:
    db = TaskDatabase()
    print('Database initialized ✓')
except Exception as e:
    print(f'Database initialization failed: {e}')
    exit(1)
"

# Initialize data sources
log "Initializing data sources..."
python3 -c "
from core.data_source_manager import DataSourceManager
try:
    dsm = DataSourceManager()
    status = dsm.get_data_source_status()
    print(f'Data sources: {status[\"active_sources\"]}/{status[\"total_sources\"]} active ✓')
except Exception as e:
    print(f'Data source initialization failed: {e}')
    exit(1)
"

# Check voice system (optional)
log "Checking voice system..."
python3 -c "
from core.voice_system import VoiceNotificationSystem
try:
    voice = VoiceNotificationSystem()
    if voice.is_available():
        print('Voice system available ✓')
    else:
        print('Voice system not available (optional)')
except Exception as e:
    print(f'Voice system check failed: {e} (optional)')
"

# Run pre-flight checks
log "Running pre-flight checks..."
python3 -c "
import os
import json
from datetime import datetime

# Check configuration files
config_files = [
    'data/config.json',
    'data/data_sources.json'
]

for config_file in config_files:
    if not os.path.exists(config_file):
        print(f'Creating default {config_file}')
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        if 'config.json' in config_file:
            default_config = {
                'avatar': {'position': 'bottom_right', 'size': 64},
                'notifications': {'enabled': True, 'check_interval': 300},
                'ai': {'personality': 'friendly'},
                'voice': {'enabled': True, 'engine': 'pyttsx3'},
                'analytics': {'enabled': True, 'auto_refresh': True},
                'collaboration': {'enabled': True, 'max_sessions': 10},
                'automation': {'enabled': True, 'check_interval': 30}
            }
        else:
            default_config = {
                'data_sources': {},
                'updated_at': datetime.now().isoformat()
            }
        
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)

print('Configuration files ready ✓')
"

# Determine startup mode
if [ "$ENVIRONMENT" = "development" ]; then
    log "Starting in development mode..."
    
    # Development mode - direct Python execution
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    
    log "Starting AI Avatar Assistant..."
    python3 main.py
    
elif [ "$ENVIRONMENT" = "production" ]; then
    log "Starting in production mode..."
    
    # Production mode - check for Gunicorn
    if command -v gunicorn &> /dev/null; then
        log "Using Gunicorn WSGI server"
        
        # Create Gunicorn configuration
        cat > gunicorn.conf.py << EOF
# Gunicorn configuration for AI Avatar Assistant

bind = "$BIND_ADDRESS"
workers = $WORKERS
worker_class = "sync"
worker_connections = 1000
timeout = $TIMEOUT
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
reload = False

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "$LOG_LEVEL"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Process naming
proc_name = "ai_avatar_assistant"

# Server socket
backlog = 2048
EOF

        log "Starting Gunicorn server on $BIND_ADDRESS with $WORKERS workers"
        exec gunicorn --config gunicorn.conf.py "core.wsgi:create_app()"
        
    else
        warn "Gunicorn not available, falling back to development server"
        export FLASK_ENV=production
        python3 main.py
    fi
    
elif [ "$ENVIRONMENT" = "widget-only" ]; then
    log "Starting in widget-only mode..."
    
    # Widget-only mode - just the API server
    python3 -c "
from core.widget_api import WidgetIntegrationManager
from core.data_source_manager import DataSourceManager
from core.project_estimator import ProjectEstimator

class MockAI:
    def __init__(self):
        self.analytics_engine = self
    def get_visual_analytics_data(self):
        return {'test': True}

data_manager = DataSourceManager()
estimator = ProjectEstimator(data_manager)
mock_ai = MockAI()

widget_manager = WidgetIntegrationManager(mock_ai, data_manager, estimator)
widget_manager.initialize_widget_api()

print('Widget API server started ✓')
input('Press Enter to stop...')
"

else
    error "Unknown environment: $ENVIRONMENT"
    error "Valid environments: development, production, widget-only"
    exit 1
fi