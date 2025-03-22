# Windows to WSL2 One-Way Sync Script
# This script monitors a Windows folder and syncs changes to a WSL2 folder
# Usage: .\windows-wsl2-sync.ps1 -SourcePath "C:\Users\L\Desktop\WORKSPACE" -DistroName "Ubuntu" -DestPath "/home/l/Workspace"

param (
    [Parameter(Mandatory=$true)]
    [string]$SourcePath,
    
    [Parameter(Mandatory=$false)]
    [string]$DistroName = "Ubuntu",
    
    [Parameter(Mandatory=$true)]
    [string]$DestPath
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

# Function to perform the sync operation
function Sync-Folders {
    param (
        [string]$Source,
        [string]$Destination
    )
    
    try {
        # Construct the WSL path
        $wslDestination = "\\wsl.localhost\$DistroName$DestPath"
        
        Write-Log "Starting sync from $Source to $wslDestination"
        
        # Use robocopy for efficient file copying
        # /MIR - Mirror directories (equivalent to /E plus /PURGE)
        # /W:1 - Wait time between retries (1 second)
        # /R:3 - Number of retries (3 times)
        # /NFL - No file list (don't log file names)
        # /NDL - No directory list (don't log directory names)
        # /NP - No progress (don't show percentage copied)
        # /MT:8 - Multi-threaded copying with 8 threads
        $robocopyArgs = @(
            $Source,
            $wslDestination,
            "/MIR",
            "/W:1",
            "/R:3",
            "/NFL",
            "/NDL",
            "/NP",
            "/MT:8"
        )
        
        $result = Start-Process -FilePath "robocopy" -ArgumentList $robocopyArgs -NoNewWindow -Wait -PassThru
        
        # Robocopy exit codes:
        # 0 - No files copied
        # 1 - Files copied successfully
        # 2 - Extra files or directories detected
        # 3 - Some files copied, some failed
        # 4 and above - Errors
        if ($result.ExitCode -lt 4) {
            Write-Log "Sync completed successfully (Exit code: $($result.ExitCode))"
        } else {
            Write-Log "Sync encountered errors (Exit code: $($result.ExitCode))" -Level "ERROR"
        }
    }
    catch {
        Write-Log "Error during sync: $_" -Level "ERROR"
    }
}

# Verify the source path exists
if (-not (Test-Path -Path $SourcePath)) {
    Write-Log "Source path does not exist: $SourcePath" -Level "ERROR"
    exit 1
}

# Verify WSL destination is accessible
$wslDestCheck = "\\wsl.localhost\$DistroName"
if (-not (Test-Path -Path $wslDestCheck)) {
    Write-Log "WSL distribution '$DistroName' is not accessible at $wslDestCheck" -Level "ERROR"
    Write-Log "Make sure WSL is running and the distribution name is correct" -Level "ERROR"
    exit 1
}

# Perform initial sync
Write-Log "Performing initial sync..."
Sync-Folders -Source $SourcePath -Destination $DestPath

# Set up FileSystemWatcher to monitor for changes
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $SourcePath
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
$changeDetected = $false

# Event handler for the timer
Register-ObjectEvent -InputObject $timer -EventName Elapsed -Action {
    if ($changeDetected) {
        Sync-Folders -Source $SourcePath -Destination $DestPath
        $changeDetected = $false
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
        $changeDetected = $true
        $timer.Stop()
        $timer.Start()
    }
}

# Start monitoring
$watcher.EnableRaisingEvents = $true
Write-Log "Monitoring started for $SourcePath"
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