#!/usr/bin/env python
"""
Run script for Disease Outbreak Prediction Dashboard
"""
import os
import sys

def main():
    """
    Main function to run the application
    """
    print("Starting Disease Outbreak Prediction Dashboard...")
    
    # Add src directory to path
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
    sys.path.insert(0, src_dir)
    
    try:
        # Import and run the app
        from app import app
        app.run_server(debug=True)
    except ImportError as e:
        print(f"Error importing app: {e}")
        print("Make sure you've installed all required packages: pip install -r requirements.txt")
    except Exception as e:
        print(f"Error running app: {e}")
        
if __name__ == "__main__":
    main() 