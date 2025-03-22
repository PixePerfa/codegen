# Setup Scheduled Task for Windows to WSL2 Sync
# This script creates a scheduled task to run the sync script at system startup
# Run this script as Administrator

param (
    [Parameter(Mandatory=$true)]
    [string]$ScriptPath,
    
    [Parameter(Mandatory=$true)]
    [string]$SourcePath,
    
    [Parameter(Mandatory=$false)]
    [string]$DistroName = "Ubuntu",
    
    [Parameter(Mandatory=$true)]
    [string]$DestPath,
    
    [Parameter(Mandatory=$false)]
    [string]$TaskName = "Windows-WSL2-Sync"
)

# Verify the script exists
if (-not (Test-Path -Path $ScriptPath)) {
    Write-Error "Script not found at path: $ScriptPath"
    exit 1
}

# Verify the source path exists
if (-not (Test-Path -Path $SourcePath)) {
    Write-Error "Source path does not exist: $SourcePath"
    exit 1
}

# Escape single quotes in paths for the argument string
$SourcePathEscaped = $SourcePath.Replace("'", "''")
$DestPathEscaped = $DestPath.Replace("'", "''")
$ScriptPathEscaped = $ScriptPath.Replace("'", "''")

# Create the argument string
$ArgumentString = "-NoProfile -ExecutionPolicy Bypass -File '$ScriptPathEscaped' -SourcePath '$SourcePathEscaped' -DistroName '$DistroName' -DestPath '$DestPathEscaped'"

# Create the scheduled task action
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument $ArgumentString

# Create the trigger (at system startup)
$trigger = New-ScheduledTaskTrigger -AtStartup

# Set the principal (run with highest privileges)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Configure settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Register the scheduled task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force
    Write-Host "Scheduled task '$TaskName' created successfully."
    Write-Host "The sync script will run automatically at system startup."
} catch {
    Write-Error "Failed to create scheduled task: $_"
    exit 1
}

# Display task information
Write-Host "`nTask Details:"
Write-Host "-------------"
Write-Host "Task Name: $TaskName"
Write-Host "Script Path: $ScriptPath"
Write-Host "Source Path: $SourcePath"
Write-Host "WSL Distribution: $DistroName"
Write-Host "Destination Path: $DestPath"
Write-Host "`nTo manually start the task, run:"
Write-Host "Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "`nTo remove the task, run:"
Write-Host "Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"