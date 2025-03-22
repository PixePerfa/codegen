# WSL Codegen Init Combined Script
# This script initializes a Codegen project in a Windows folder through WSL2 and sets up continuous sync
# Usage: .\wsl-codegen-init-combined.ps1 -WindowsPath "C:\Users\L\Desktop\WORKSPACE" -DistroName "MCP-Tower" -WslPath "/home/l/Workspace"

param (
    [Parameter(Mandatory=$true)]
    [string]$WindowsPath,
    
    [Parameter(Mandatory=$false)]
    [string]$DistroName = "Ubuntu",
    
    [Parameter(Mandatory=$true)]
    [string]$WslPath
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
    Write-Log "Windows path does not exist. Creating it: $WindowsPath"
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

# Function to perform the sync operation using WSL commands directly
function Sync-Folders {
    param (
        [string]$Source,
        [string]$Destination
    )
    
    try {
        Write-Log "Starting sync from $Source to $Destination in $DistroName"
        
        # Create destination directory if it doesn't exist
        $createDirCmd = "mkdir -p `"$Destination`""
        wsl -d $DistroName -e bash -c $createDirCmd
        
        # Use rsync through WSL for reliable syncing
        # Convert Windows path to WSL path
        $wslSourcePath = $Source.Replace("\", "/").Replace(":", "")
        $wslSourcePath = "/mnt/" + $wslSourcePath.ToLower()
        
        # Build the rsync command
        $rsyncCmd = "rsync -avz --delete `"$wslSourcePath/`" `"$Destination/`""
        
        Write-Log "Executing: $rsyncCmd"
        $result = wsl -d $DistroName -e bash -c $rsyncCmd
        
        Write-Log "Sync completed successfully"
        Write-Log $result
    }
    catch {
        Write-Log "Error during sync: $_" -Level "ERROR"
    }
}

# Verify rsync is installed in the WSL distribution
$rsyncCheck = wsl -d $DistroName -e which rsync
if ($LASTEXITCODE -ne 0) {
    Write-Log "rsync is not installed in the WSL distribution. Installing rsync..." -Level "WARNING"
    wsl -d $DistroName -e apt-get update
    wsl -d $DistroName -e apt-get install -y rsync
    
    # Verify installation
    $rsyncCheck = wsl -d $DistroName -e which rsync
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Failed to install rsync. Please install it manually with 'apt-get install rsync'" -Level "ERROR"
        exit 1
    }
}

# Perform initial sync
Write-Log "Performing initial sync..."
Sync-Folders -Source $WindowsPath -Destination $WslPath

# Set up FileSystemWatcher to monitor for changes
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $WindowsPath
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $false
$watcher.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor 
                        [System.IO.NotifyFilters]::DirectoryName -bor 
                        [System.IO.NotifyFilters]::LastWrite -bor 
                        [System.IO.NotifyFilters]::Size

# Create a timer to batch changes and prevent excessive syncs
$timer = New-Object System.Timers.Timer
$timer.Interval = 5000 # 5 seconds
$timer.AutoReset = $false
$script:changeDetected = $false

# Event handler for the timer
Register-ObjectEvent -InputObject $timer -EventName Elapsed -Action {
    if ($script:changeDetected) {
        Sync-Folders -Source $WindowsPath -Destination $WslPath
        $script:changeDetected = $false
    }
    $timer.Stop()
} | Out-Null

# Event handlers for file system changes
$handlers = @(
    'Created',
    'Changed',
    'Deleted',
    'Renamed'
) | ForEach-Object {
    $eventName = $_
    Register-ObjectEvent -InputObject $watcher -EventName $eventName -Action {
        $path = $Event.SourceEventArgs.FullPath
        $changeType = $Event.SourceEventArgs.ChangeType
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        
        Write-Host "[$timestamp] [CHANGE] $changeType detected on $path"
        
        # Set the flag and restart the timer
        $script:changeDetected = $true
        $timer.Stop()
        $timer.Start()
    }
}

# Start monitoring
$watcher.EnableRaisingEvents = $true
Write-Log "Monitoring started for $WindowsPath"
Write-Log "Changes will be synced to $WslPath in $DistroName"
Write-Log "Press Ctrl+C to stop monitoring"

try {
    # Keep the script running
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    # Clean up
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    $timer.Dispose()
    $handlers | ForEach-Object { Unregister-Event -SourceIdentifier $_.Name }
    Write-Log "Monitoring stopped"
}