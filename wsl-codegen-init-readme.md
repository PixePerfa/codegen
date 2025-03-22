# WSL Codegen Init Script

This script initializes a Codegen project in a Windows folder through WSL2, combining the steps of creating a directory in WSL2 and running `codegen init` in a single command.

## Features

- Initializes a Codegen project in WSL2 from Windows
- Verifies that both Windows and WSL2 paths are accessible
- Creates the destination directory in WSL2 if it doesn't exist
- Optional integration with the Windows to WSL2 sync tool
- Detailed logging of all operations

## Requirements

- Windows 10/11 with WSL2 installed
- PowerShell 5.1 or later
- Codegen installed in your WSL2 distribution
- A running WSL2 distribution

## Usage

1. Save the `wsl-codegen-init.ps1` script to your Windows system
2. Open PowerShell
3. Run the script with the required parameters:

```powershell
.\wsl-codegen-init.ps1 -WindowsPath "C:\Users\L\Desktop\WORKSPACE" -WslPath "/home/l/Workspace"
```

### Parameters

- `-WindowsPath`: The Windows folder where your project will be located (required)
- `-DistroName`: The name of your WSL2 distribution (default: "Ubuntu")
- `-WslPath`: The destination path inside WSL2 (required)
- `-SetupSync`: If specified, also sets up continuous sync from Windows to WSL2 (requires windows-wsl2-sync.ps1)

## Combining with Continuous Sync

To initialize a Codegen project and set up continuous sync in one command:

1. Make sure both `wsl-codegen-init.ps1` and `windows-wsl2-sync.ps1` are in the same directory
2. Run the command with the `-SetupSync` switch:

```powershell
.\wsl-codegen-init.ps1 -WindowsPath "C:\Users\L\Desktop\WORKSPACE" -WslPath "/home/l/Workspace" -SetupSync
```

This will:
1. Initialize the Codegen project in WSL2
2. Start the continuous sync in a new window

## How It Works

1. The script verifies that the Windows path exists
2. It checks that WSL2 is accessible and the specified distribution exists
3. It creates the destination directory in WSL2 if it doesn't exist
4. It runs `codegen init` in the WSL2 directory
5. If `-SetupSync` is specified, it starts the continuous sync process

## Troubleshooting

- If the script fails to access WSL2, ensure your WSL2 distribution is running
- If Codegen initialization fails, check that Codegen is properly installed in your WSL2 distribution
- For sync issues, refer to the windows-wsl2-sync-readme.md file