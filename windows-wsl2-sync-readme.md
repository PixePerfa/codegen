# Windows to WSL2 One-Way Sync

This tool provides a continuous one-way synchronization from a Windows folder to a WSL2 folder. It monitors the Windows folder for any changes and automatically syncs them to the specified WSL2 location.

## Features

- Real-time monitoring of Windows folder for changes
- Efficient file copying using `robocopy`
- Batched synchronization to prevent excessive operations
- Detailed logging of all activities
- Handles file creation, modification, deletion, and renaming

## Requirements

- Windows 10/11 with WSL2 installed
- PowerShell 5.1 or later
- A running WSL2 distribution

## Usage

1. Save the `windows-wsl2-sync.ps1` script to your Windows system
2. Open PowerShell as Administrator
3. Run the script with the required parameters:

```powershell
.\windows-wsl2-sync.ps1 -SourcePath "C:\Users\L\Desktop\WORKSPACE" -DistroName "Ubuntu" -DestPath "/home/l/Workspace"
```

### Parameters

- `-SourcePath`: The Windows folder to monitor (required)
- `-DistroName`: The name of your WSL2 distribution (default: "Ubuntu")
- `-DestPath`: The destination path inside WSL2 (required)

## How It Works

1. The script first verifies that both the source and destination paths are accessible
2. It performs an initial sync to ensure both folders are in sync
3. It then sets up a `FileSystemWatcher` to monitor the Windows folder for changes
4. When changes are detected, it waits for 5 seconds of inactivity before syncing
5. This batching prevents excessive sync operations when many files change at once
6. The script uses `robocopy` with the `/MIR` option to efficiently mirror the folders

## Running as a Background Service

To run this script as a background service that starts automatically:

1. Create a scheduled task in Windows Task Scheduler
2. Set it to run at system startup with highest privileges
3. Configure the action to run PowerShell with the script and parameters

Example PowerShell command to create a scheduled task:

```powershell
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\path\to\windows-wsl2-sync.ps1 -SourcePath 'C:\Users\L\Desktop\WORKSPACE' -DestPath '/home/l/Workspace'"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
Register-ScheduledTask -TaskName "Windows-WSL2-Sync" -Action $action -Trigger $trigger -Principal $principal -Settings $settings
```

## Troubleshooting

- If the script fails to access the WSL2 path, ensure your WSL2 distribution is running
- If files aren't syncing, check that the paths are correct and that you have appropriate permissions
- For performance issues with large directories, consider adjusting the robocopy parameters or timer interval