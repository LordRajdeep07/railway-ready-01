# Create and activate virtual environment
Write-Host "Creating virtual environment..."
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required packages
Write-Host "Installing required packages..."
pip install -r requirements.txt

# Set environment variables for development
$env:FLASK_APP = "src/app.py"
$env:FLASK_ENV = "development"
$env:SECRET_KEY = "your-secret-key-here"

# Run the application
Write-Host "Starting the application..."
python src/app.py

# Deactivate virtual environment when done
deactivate 