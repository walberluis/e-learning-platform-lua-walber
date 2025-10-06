#!/bin/bash

# E-Learning Platform Setup Script
# This script automatically installs Python, creates virtual environment, and sets up the complete platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="e-learning"
PYTHON_VERSION="3.11"
VENV_NAME=".venv"

# Function to check if we can use colors
can_use_colors() {
    # Check if we're in a terminal and not in a pipe
    if [ -t 1 ] && [ "${TERM:-}" != "dumb" ]; then
        # Check if we're in Git Bash/MINGW64 and handle accordingly
        if [[ "$OSTYPE" == "msys" ]] || [[ "$MSYSTEM" == "MINGW64" ]]; then
            # Use simpler color handling for Git Bash
            return 0
        else
            return 0
        fi
    else
        return 1
    fi
}

# Function to print colored output
print_status() {
    if can_use_colors; then
        printf "${BLUE}[INFO]${NC} %s\n" "$1" >&2
    else
        printf "[INFO] %s\n" "$1" >&2
    fi
}

print_success() {
    if can_use_colors; then
        printf "${GREEN}[SUCCESS]${NC} %s\n" "$1" >&2
    else
        printf "[SUCCESS] %s\n" "$1" >&2
    fi
}

print_warning() {
    if can_use_colors; then
        printf "${YELLOW}[WARNING]${NC} %s\n" "$1" >&2
    else
        printf "[WARNING] %s\n" "$1" >&2
    fi
}

print_error() {
    if can_use_colors; then
        printf "${RED}[ERROR]${NC} %s\n" "$1" >&2
    else
        printf "[ERROR] %s\n" "$1" >&2
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OS" == "Windows_NT" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to install Python on different OS
install_python() {
    local os=$(detect_os)
    print_status "Installing Python $PYTHON_VERSION for $os..."
    
    case $os in
        "linux")
            if command_exists apt-get; then
                sudo apt-get update
                sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
            elif command_exists yum; then
                sudo yum install -y python311 python311-pip python311-devel
            elif command_exists dnf; then
                sudo dnf install -y python3.11 python3.11-pip python3.11-devel
            else
                print_error "Unsupported Linux distribution. Please install Python 3.11 manually."
                exit 1
            fi
            ;;
        "macos")
            if command_exists brew; then
                brew install python@3.11
            else
                print_error "Homebrew not found. Please install Homebrew first or install Python 3.11 manually."
                exit 1
            fi
            ;;
        "windows")
            print_warning "Please install Python 3.11 from https://python.org/downloads/"
            print_warning "Make sure to check 'Add Python to PATH' during installation"
            read -p "Press Enter after installing Python..."
            ;;
        *)
            print_error "Unsupported operating system: $os"
            exit 1
            ;;
    esac
}

# Function to check Python installation
check_python() {
    print_status "Checking Python installation..."
    
    local python_cmd=""
    
    # Try different Python commands
    for cmd in python3.11 python3 python; do
        if command_exists $cmd; then
            local version=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
            if [[ "$version" == "3.11" ]] || [[ "$version" == "3.12" ]] || [[ "$version" == "3.13" ]]; then
                python_cmd=$cmd
                break
            fi
        fi
    done
    
    if [ -z "$python_cmd" ]; then
        print_warning "Python 3.11+ not found. Attempting to install..."
        install_python
        
        # Check again after installation
        for cmd in python3.11 python3 python; do
            if command_exists $cmd; then
                local version=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
                if [[ "$version" == "3.11" ]] || [[ "$version" == "3.12" ]] || [[ "$version" == "3.13" ]]; then
                    python_cmd=$cmd
                    break
                fi
            fi
        done
        
        if [ -z "$python_cmd" ]; then
            print_error "Failed to install or find Python 3.11+. Please install manually."
            exit 1
        fi
    fi
    
    # Return the python command (this should be the only output)
    echo "$python_cmd"
}

# Function to create virtual environment
create_virtual_environment() {
    local python_cmd=$1
    print_status "Creating virtual environment..."
    
    if [ -d "$VENV_NAME" ]; then
        print_warning "Virtual environment already exists at: $VENV_NAME"
        print_status "Removing existing virtual environment..."
        
        # Try to remove the existing virtual environment
        if rm -rf "$VENV_NAME" 2>/dev/null; then
            print_success "Existing virtual environment removed successfully"
        else
            print_error "Failed to remove existing virtual environment"
            print_error "Please remove it manually: rm -rf $VENV_NAME"
            exit 1
        fi
    fi
    
    print_status "Creating new virtual environment with $python_cmd..."
    
    # Create virtual environment with explicit command execution
    if ! "$python_cmd" -m venv "$VENV_NAME"; then
        print_error "Failed to create virtual environment"
        print_error "Please check if $python_cmd has venv module installed"
        exit 1
    fi
    
    print_success "Virtual environment created successfully: $VENV_NAME"
}

# Function to activate virtual environment
activate_virtual_environment() {
    print_status "Activating virtual environment..."
    
    if [[ "$OS" == "Windows_NT" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        source "$VENV_NAME/Scripts/activate"
    else
        source "$VENV_NAME/bin/activate"
    fi
    
    print_success "Virtual environment activated"
}

# Function to upgrade pip
upgrade_pip() {
    print_status "Upgrading pip..."
    python -m pip install --upgrade pip
    print_success "Pip upgraded successfully"
}

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Install core dependencies
    print_status "Installing core FastAPI dependencies..."
    pip install fastapi==0.115.13 uvicorn[standard]==0.34.3
    
    print_status "Installing database dependencies..."
    pip install sqlalchemy==2.0.23 alembic==1.12.1
    
    print_status "Installing validation dependencies..."
    pip install pydantic==2.11.7 email-validator==2.3.0
    
    print_status "Installing authentication dependencies..."
    pip install python-jose[cryptography]==3.5.0 passlib[bcrypt]==1.7.4 argon2-cffi==25.1.0
    
    print_status "Installing file handling dependencies..."
    pip install python-multipart==0.0.20 aiofiles==24.1.0
    
    print_status "Installing AI dependencies..."
    pip install google-generativeai==0.8.5
    
    print_status "Installing Lua scripting dependencies..."
    pip install lupa==2.5
    
    print_status "Installing HTTP client dependencies..."
    pip install httpx==0.25.2
    
    print_status "Installing template dependencies..."
    pip install jinja2==3.1.2
    
    print_status "Installing environment dependencies..."
    pip install python-dotenv==1.0.0
    
    print_status "Installing development dependencies..."
    pip install pytest==7.4.3 pytest-asyncio==0.21.1
    
    print_success "All dependencies installed successfully"
}

# Function to create .env file
create_env_file() {
    print_status "Creating environment configuration..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# E-Learning Platform Configuration

# Application Settings
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database Configuration (SQLite for development)
DATABASE_URL=sqlite:///./elearning.db
USE_SQLITE=true

# Security Settings
SECRET_KEY=your-super-secret-key-change-in-production-$(date +%s)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# File Storage
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# Logging
LOG_LEVEL=INFO
EOF
        print_success "Environment file created: .env"
        print_warning "Please add your GEMINI_API_KEY to the .env file"
    else
        print_success ".env file already exists with your custom configuration."
        
        # Check if GEMINI_API_KEY is configured
        if grep -q "GEMINI_API_KEY=your-gemini-api-key-here" .env; then
            print_warning "⚠️  Please update your GEMINI_API_KEY in the .env file"
        elif grep -q "GEMINI_API_KEY=.*[A-Za-z0-9]" .env; then
            print_success "✅ GEMINI_API_KEY is configured"
        else
            print_warning "⚠️  Please add your GEMINI_API_KEY to the .env file"
        fi
    fi
}

# Function to initialize database
initialize_database() {
    print_status "Initializing database..."
    
    python -c "
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from infrastructure.database.connection import init_database
    init_database()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    sys.exit(1)
"
    
    print_success "Database initialized"
}

# Function to create sample data
create_sample_data() {
    print_status "Creating sample data..."
    
    if [ -f "scripts/create_sample_data.py" ]; then
        python scripts/create_sample_data.py
        print_success "Sample data created"
    else
        print_warning "Sample data script not found. Skipping..."
    fi
}

# Function to run basic tests
run_tests() {
    print_status "Running basic tests..."
    
    python -c "
import sys
import os
sys.path.insert(0, os.getcwd())

# Suppress SQLAlchemy warnings
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

try:
    # Test imports
    from presentation.api.main import app
    from infrastructure.database.connection import engine
    from business.core.usuario_manager import UsuarioManager
    from infrastructure.security.auth import SecurityManager
    
    print('✅ All imports successful')
    print('✅ Application ready to start')
except Exception as e:
    print(f'❌ Test failed: {e}')
    sys.exit(1)
"
    
    print_success "Basic tests completed"
}

# Function to start the application
start_application() {
    print_status "Starting the E-Learning Platform..."
    
    print_success "🎉 Setup completed successfully!"
    echo ""
    print_status "📋 To start the application:"
    
    if [[ "$OS" == "Windows_NT" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        print_status "1. Activate virtual environment: $VENV_NAME\\Scripts\\activate"
    else
        print_status "1. Activate virtual environment: source $VENV_NAME/bin/activate"
    fi
    
    print_status "2. Start application: python -m uvicorn presentation.api.main:app --host 0.0.0.0 --port 8000 --reload"
    echo ""
    print_status "🌐 Application will be available at:"
    print_status "- Main application: http://localhost:8000"
    print_status "- API documentation: http://localhost:8000/docs"
    print_status "- Interactive API docs: http://localhost:8000/redoc"
    echo ""
    
    read -p "Do you want to start the application now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Starting application..."
        python -m uvicorn presentation.api.main:app --host 0.0.0.0 --port 8000 --reload
    fi
}

# Function to show usage information
show_usage() {
    echo "🎓 E-Learning Platform Setup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  --no-deps              Skip dependency installation"
    echo "  --no-db                Skip database initialization"
    echo "  --no-sample            Skip sample data creation"
    echo "  --no-start             Skip starting the application"
    echo ""
    echo "Examples:"
    echo "  $0                     Full setup with all options"
    echo "  $0 --no-sample         Setup without sample data"
    echo "  $0 --no-start          Setup without starting the application"
}

# Main function
main() {
    local install_deps=true
    local init_db=true
    local create_sample=true
    local start_app=true
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            --no-deps)
                install_deps=false
                shift
                ;;
            --no-db)
                init_db=false
                shift
                ;;
            --no-sample)
                create_sample=false
                shift
                ;;
            --no-start)
                start_app=false
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    echo "🎓 E-Learning Platform Setup"
    echo "================================"
    echo ""
    
    # Step 1: Check Python
    local python_cmd=$(check_python)
    print_success "Python found: $python_cmd"
    
    # Step 2: Create virtual environment
    create_virtual_environment "$python_cmd"
    
    # Step 3: Activate virtual environment
    activate_virtual_environment
    
    # Step 4: Upgrade pip
    upgrade_pip
    
    # Step 5: Install dependencies
    if [ "$install_deps" = true ]; then
        install_dependencies
    fi
    
    # Step 6: Create environment file
    create_env_file
    
    # Step 7: Initialize database
    if [ "$init_db" = true ]; then
        initialize_database
    fi
    
    # Step 8: Create sample data
    if [ "$create_sample" = true ]; then
        create_sample_data
    fi
    
    # Step 9: Run basic tests
    run_tests
    
    # Step 10: Start application
    if [ "$start_app" = true ]; then
        start_application
    else
        print_success "🎉 Setup completed successfully!"
        echo ""
        print_status "📋 To start the application manually:"
        
        if [[ "$OS" == "Windows_NT" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
            print_status "1. Activate virtual environment: $VENV_NAME\\Scripts\\activate"
        else
            print_status "1. Activate virtual environment: source $VENV_NAME/bin/activate"
        fi
        
        print_status "2. Start application: python -m uvicorn presentation.api.main:app --host 0.0.0.0 --port 8000 --reload"
        echo ""
        print_success "🎓 Happy learning with AI! 🤖📚"
    fi
}

# Run main function with all arguments
main "$@"