# WSL Codegen Init Script (Fixed Version)
# This script initializes a Codegen project in a Windows folder through WSL2
# Usage: .\wsl-codegen-init-fixed.ps1 -WindowsPath "C:\Users\L\Desktop\WORKSPACE" -DistroName "MCP-Tower" -WslPath "/home/l/Workspace"

param (
    [Parameter(Mandatory=$true)]
    [string]$WindowsPath,
    
    [Parameter(Mandatory=$false)]
    [string]$DistroName = "Ubuntu",
    
    [Parameter(Mandatory=$true)]
    [string]$WslPath,
    
    [Parameter(Mandatory=$false)]
    [switch]$SetupSync = $false
)

# Function to log messages with timestamp
function Write-Log {
    param (
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

# Verify the Windows path exists
if (-not (Test-Path -Path $WindowsPath)) {
    Write-Log "Windows path does not exist: $WindowsPath" -Level "ERROR"
    exit 1
}

# Create the Windows path if it doesn't exist
if (-not (Test-Path -Path $WindowsPath)) {
    Write-Log "Creating Windows path: $WindowsPath"
    New-Item -Path $WindowsPath -ItemType Directory -Force | Out-Null
    if (-not (Test-Path -Path $WindowsPath)) {
        Write-Log "Failed to create Windows path: $WindowsPath" -Level "ERROR"
        exit 1
    }
}

# Verify WSL is accessible
$wslCheck = wsl -l -v
if ($LASTEXITCODE -ne 0) {
    Write-Log "WSL is not accessible. Make sure WSL2 is installed and running." -Level "ERROR"
    exit 1
}

# Verify the specified distro exists
$distroExists = $wslCheck | Select-String -Pattern $DistroName
if (-not $distroExists) {
    Write-Log "WSL distribution '$DistroName' not found. Available distributions:" -Level "ERROR"
    Write-Log $wslCheck
    exit 1
}

# Create the destination directory in WSL if it doesn't exist
Write-Log "Creating destination directory in WSL if it doesn't exist..."
wsl -d $DistroName -e bash -c "mkdir -p $WslPath"
if ($LASTEXITCODE -ne 0) {
    Write-Log "Failed to create directory in WSL: $WslPath" -Level "ERROR"
    exit 1
}

# Initialize Codegen in the WSL directory
Write-Log "Initializing Codegen in WSL directory..."
$initResult = wsl -d $DistroName -e bash -c "cd $WslPath && codegen init"
if ($LASTEXITCODE -ne 0) {
    Write-Log "Failed to initialize Codegen in WSL directory: $WslPath" -Level "ERROR"
    Write-Log $initResult -Level "ERROR"
    exit 1
}

Write-Log "Codegen initialized successfully in WSL directory: $WslPath"
Write-Log $initResult

# If sync is requested, set up the continuous sync
if ($SetupSync) {
    # Check if windows-wsl2-sync-fixed.ps1 exists in the current directory
    $syncScriptPath = Join-Path -Path $PSScriptRoot -ChildPath "windows-wsl2-sync-fixed.ps1"
    if (-not (Test-Path -Path $syncScriptPath)) {
        Write-Log "Sync script not found at: $syncScriptPath" -Level "ERROR"
        Write-Log "Please download the windows-wsl2-sync-fixed.ps1 script first." -Level "ERROR"
        exit 1
    }
    
    # Run the sync script
    Write-Log "Setting up continuous sync from $WindowsPath to $WslPath..."
    Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$syncScriptPath`" -SourcePath `"$WindowsPath`" -DistroName `"$DistroName`" -DestPath `"$WslPath`"" -NoNewWindow
    
    Write-Log "Continuous sync started in a new window."
}

Write-Log "Setup complete! Your Codegen project is ready in both Windows and WSL2."
Write-Log "Windows path: $WindowsPath"
Write-Log "WSL path: $WslPath"