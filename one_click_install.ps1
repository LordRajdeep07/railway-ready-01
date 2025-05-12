# One-Click Requirements Installer for Disease Outbreak Prediction System
# This script installs all required Python packages from requirements.txt

# Function to display colored text
function Write-ColorOutput {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Text,
        [Parameter(Mandatory=$true)]
        [string]$Color
    )
    
    $originalColor = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $Color
    Write-Output $Text
    $host.UI.RawUI.ForegroundColor = $originalColor
}

# Clear the screen
Clear-Host

# Display header
Write-ColorOutput "====================================================" "Cyan"
Write-ColorOutput "  DISEASE OUTBREAK PREDICTION - REQUIREMENTS SETUP  " "Cyan"
Write-ColorOutput "====================================================" "Cyan"
Write-ColorOutput "`nThis script will install all required Python packages.`n" "White"

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-ColorOutput "✓ Python detected: $pythonVersion" "Green"
} catch {
    Write-ColorOutput "✗ Python not found! Please install Python 3.8 or newer." "Red"
    Write-ColorOutput "  Download from: https://www.python.org/downloads/" "Yellow"
    Write-ColorOutput "`nPress any key to exit..." "Gray"
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 1
}

# Check if pip is installed
try {
    $pipVersion = python -m pip --version
    Write-ColorOutput "✓ Pip detected: $pipVersion" "Green"
} catch {
    Write-ColorOutput "✗ Pip not found! Attempting to install pip..." "Yellow"
    try {
        python -m ensurepip --upgrade
        Write-ColorOutput "✓ Pip installed successfully" "Green"
    } catch {
        Write-ColorOutput "✗ Failed to install pip. Please install pip manually." "Red"
        Write-ColorOutput "`nPress any key to exit..." "Gray"
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
        exit 1
    }
}

# Check if requirements.txt exists
$requirementsPath = Join-Path $PSScriptRoot "requirements.txt"
if (-not (Test-Path $requirementsPath)) {
    Write-ColorOutput "✗ requirements.txt not found in the current directory!" "Red"
    Write-ColorOutput "`nPress any key to exit..." "Gray"
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 1
}

# Update pip
Write-ColorOutput "`nUpdating pip to latest version..." "Yellow"
try {
    python -m pip install --upgrade pip
    Write-ColorOutput "✓ Pip updated successfully" "Green"
} catch {
    Write-ColorOutput "! Warning: Could not update pip, continuing with current version" "Yellow"
}

# Install virtualenv if not already installed
Write-ColorOutput "`nChecking for virtualenv..." "Yellow"
try {
    python -m pip show virtualenv | Out-Null
    Write-ColorOutput "✓ virtualenv is already installed" "Green"
} catch {
    Write-ColorOutput "Installing virtualenv..." "Yellow"
    try {
        python -m pip install virtualenv
        Write-ColorOutput "✓ virtualenv installed successfully" "Green"
    } catch {
        Write-ColorOutput "! Warning: Could not install virtualenv, continuing without it" "Yellow"
    }
}

# Create and activate virtual environment (optional)
$useVirtualEnv = $false
Write-ColorOutput "`nDo you want to install packages in a virtual environment? (Recommended) [Y/N]" "Cyan"
$response = Read-Host
if ($response -eq "Y" -or $response -eq "y") {
    $useVirtualEnv = $true
    $venvPath = Join-Path $PSScriptRoot "venv"
    
    # Create virtual environment
    Write-ColorOutput "`nCreating virtual environment..." "Yellow"
    try {
        python -m virtualenv $venvPath
        Write-ColorOutput "✓ Virtual environment created at: $venvPath" "Green"
        
        # Activate virtual environment
        Write-ColorOutput "Activating virtual environment..." "Yellow"
        & "$venvPath\Scripts\Activate.ps1"
        Write-ColorOutput "✓ Virtual environment activated" "Green"
    } catch {
        Write-ColorOutput "! Warning: Could not create/activate virtual environment, continuing without it" "Yellow"
        $useVirtualEnv = $false
    }
}

# Install requirements
Write-ColorOutput "`nInstalling required packages from requirements.txt..." "Yellow"
Write-ColorOutput "This may take several minutes depending on your internet connection." "Yellow"

try {
    python -m pip install -r $requirementsPath
    Write-ColorOutput "`n✓ All packages installed successfully!" "Green"
} catch {
    Write-ColorOutput "`n✗ Error installing packages. Details:" "Red"
    Write-ColorOutput $_.Exception.Message "Red"
    Write-ColorOutput "`nTrying to install packages one by one..." "Yellow"
    
    # Read requirements.txt and install packages one by one
    $packages = Get-Content $requirementsPath
    $failedPackages = @()
    
    foreach ($package in $packages) {
        if ($package.Trim() -ne "") {
            Write-ColorOutput "Installing $package..." "Yellow"
            try {
                python -m pip install $package
                Write-ColorOutput "✓ Installed $package" "Green"
            } catch {
                Write-ColorOutput "✗ Failed to install $package" "Red"
                $failedPackages += $package
            }
        }
    }
    
    if ($failedPackages.Count -gt 0) {
        Write-ColorOutput "`n! The following packages could not be installed:" "Red"
        foreach ($package in $failedPackages) {
            Write-ColorOutput "  - $package" "Red"
        }
    } else {
        Write-ColorOutput "`n✓ All packages installed successfully!" "Green"
    }
}

# Display completion message
Write-ColorOutput "`n====================================================" "Cyan"
Write-ColorOutput "  INSTALLATION COMPLETE" "Cyan"
Write-ColorOutput "====================================================" "Cyan"

if ($useVirtualEnv) {
    Write-ColorOutput "`nVirtual environment is active. To deactivate, type: deactivate" "Yellow"
    Write-ColorOutput "To activate this environment in the future, run: $venvPath\Scripts\Activate.ps1" "Yellow"
}

Write-ColorOutput "`nTo run the application:" "White"
Write-ColorOutput "  1. Navigate to the project directory" "White"
Write-ColorOutput "  2. Run: python src/app.py" "White"

Write-ColorOutput "`nPress any key to exit..." "Gray"
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown') 