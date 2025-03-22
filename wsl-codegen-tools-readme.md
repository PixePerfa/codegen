# WSL2 Codegen Integration Tools

This repository contains PowerShell scripts to help you integrate Codegen with Windows and WSL2. These tools allow you to initialize Codegen projects in WSL2 and set up continuous synchronization between Windows and WSL2 folders.

## Scripts Overview

### 1. All-in-One Solution

- **`wsl-codegen-init-combined.ps1`**: Initializes a Codegen project in WSL2 and sets up continuous sync in a single script.

### 2. Individual Components

- **`wsl-codegen-init-fixed.ps1`**: Initializes a Codegen project in WSL2.
- **`windows-wsl2-sync-fixed.ps1`**: Sets up continuous sync from Windows to WSL2.
- **`setup-scheduled-task-fixed.ps1`**: Creates a scheduled task to run the sync script at system startup.

## Quick Start

### Option 1: All-in-One Solution

```powershell
.\wsl-codegen-init-combined.ps1 -WindowsPath "C:\Users\L\Desktop\WORKSPACE" -DistroName "MCP-Tower" -WslPath "/home/l/Workspace"
```

This will:
1. Create the Windows folder if it doesn't exist
2. Create the WSL2 folder if it doesn't exist
3. Initialize Codegen in the WSL2 folder
4. Set up continuous sync from Windows to WSL2

### Option 2: Step-by-Step Approach

1. Initialize Codegen in WSL2:
```powershell
.\wsl-codegen-init-fixed.ps1 -WindowsPath "C:\Users\L\Desktop\WORKSPACE" -DistroName "MCP-Tower" -WslPath "/home/l/Workspace"
```

2. Set up continuous sync:
```powershell
.\windows-wsl2-sync-fixed.ps1 -SourcePath "C:\Users\L\Desktop\WORKSPACE" -DistroName "MCP-Tower" -DestPath "/home/l/Workspace"
```

3. (Optional) Create a scheduled task to run the sync at system startup:
```powershell
.\setup-scheduled-task-fixed.ps1 -ScriptPath "C:\path\to\windows-wsl2-sync-fixed.ps1" -SourcePath "C:\Users\L\Desktop\WORKSPACE" -DistroName "MCP-Tower" -DestPath "/home/l/Workspace"
```

## How It Works

### Codegen Initialization

The script uses the `wsl` command to run `codegen init` in your WSL2 distribution, creating a new Codegen project in the specified WSL2 folder.

### Synchronization

The sync script:
1. Uses `rsync` through WSL2 for reliable file synchronization
2. Monitors the Windows folder for changes using `FileSystemWatcher`
3. Batches changes to prevent excessive sync operations
4. Automatically installs `rsync` in your WSL2 distribution if needed

## Troubleshooting

### Common Issues

1. **WSL2 distribution not found**
   - Make sure your WSL2 distribution is running
   - Verify the distribution name with `wsl -l -v`

2. **Sync not working**
   - Check if `rsync` is installed in your WSL2 distribution
   - Verify that both Windows and WSL2 paths are accessible

3. **Codegen initialization fails**
   - Ensure Codegen is properly installed in your WSL2 distribution
   - Check if you have the necessary permissions in the WSL2 folder

### Logs

All scripts include detailed logging to help diagnose issues. Look for messages with `[ERROR]` or `[WARNING]` tags.

## Requirements

- Windows 10/11 with WSL2 installed
- PowerShell 5.1 or later
- Codegen installed in your WSL2 distribution
- A running WSL2 distribution