#!/bin/bash

# Create and activate virtual environment
echo "Creating virtual environment..."
python -m venv venv
source venv/bin/activate || source venv/Scripts/activate

# Install required packages
echo "Installing required packages..."
pip install -r requirements.txt

# Set environment variables for development
export FLASK_APP=src/app.py
export FLASK_ENV=development
export SECRET_KEY="your-secret-key-here"

# Run the application
echo "Starting the application..."
python src/app.py

# Deactivate virtual environment when done
deactivate 