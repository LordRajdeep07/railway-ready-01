#!/usr/bin/env python
"""
Environment checker for Disease Outbreak Prediction Dashboard
"""
import os
import sys
import importlib
import platform
import subprocess
from colorama import init, Fore, Style

# Initialize colorama
init()

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}" + "="*50)
    print(f" {text}")
    print("="*50 + f"{Style.RESET_ALL}\n")

def print_success(text):
    """Print a success message"""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_warning(text):
    """Print a warning message"""
    print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")

def print_error(text):
    """Print an error message"""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def check_python_version():
    """Check Python version"""
    print_header("Checking Python Version")
    version = platform.python_version()
    print(f"Python version: {version}")
    
    major, minor, _ = map(int, version.split('.'))
    if major >= 3 and minor >= 8:
        print_success("Python version is compatible (3.8+)")
    else:
        print_error("Python version should be 3.8 or higher")

def check_dependencies():
    """Check required dependencies"""
    print_header("Checking Required Dependencies")
    
    required_packages = [
        "dash",
        "dash_bootstrap_components",
        "flask",
        "flask_login",
        "numpy",
        "pandas",
        "plotly",
        "sklearn",
        "joblib",
        "requests"
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            if package == "sklearn":
                # sklearn is imported as scikit-learn but used as sklearn
                importlib.import_module("sklearn")
            else:
                importlib.import_module(package)
            print_success(f"{package} is installed")
        except ImportError:
            print_error(f"{package} is not installed")
            missing.append(package)
    
    if missing:
        print("\nMissing packages. Install them using:")
        print(f"{Fore.YELLOW}pip install -r requirements.txt{Style.RESET_ALL}")

def check_directory_structure():
    """Check directory structure"""
    print_header("Checking Directory Structure")
    
    required_dirs = ["src", "static", "templates", "models", "data"]
    
    for directory in required_dirs:
        if os.path.isdir(directory):
            print_success(f"{directory}/ directory exists")
        else:
            print_warning(f"{directory}/ directory not found")

def check_files():
    """Check important files"""
    print_header("Checking Important Files")
    
    required_files = [
        "src/app.py",
        "static/style.css",
        "static/loading.css",
        "requirements.txt",
        "README.md"
    ]
    
    for file in required_files:
        if os.path.isfile(file):
            print_success(f"{file} exists")
        else:
            print_warning(f"{file} not found")

def main():
    """Main function"""
    print_header("DISEASE OUTBREAK PREDICTION DASHBOARD - ENVIRONMENT CHECK")
    
    check_python_version()
    check_dependencies()
    check_directory_structure()
    check_files()
    
    print_header("Environment Check Complete")
    print("If all checks passed, you can run the application with:")
    print(f"{Fore.CYAN}python run.py{Style.RESET_ALL}")
    
if __name__ == "__main__":
    main() 