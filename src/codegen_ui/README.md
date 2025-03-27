# Codegen UI

A graphical user interface for the Codegen SDK that allows you to visualize and manipulate codebases through an intuitive interface.

## Features

- **Project Management**: Select and manage multiple codebases
- **File Explorer**: Browse and navigate through the codebase's file structure
- **Symbol Browser**: View and navigate classes, functions, and other symbols
- **Code Editor**: Edit files with syntax highlighting and code completion
- **Code Search**: Search for code patterns across the codebase
- **Code Transformation**: Apply code transformations like renaming symbols and moving code

## Architecture

The Codegen UI consists of two main components:

1. **Backend API**: A FastAPI-based REST API that interfaces with the Codegen SDK
2. **Frontend UI**: A React-based web application that provides the user interface

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm 6 or higher

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/PixePerfa/codegen.git
   cd codegen
   ```

2. Set up the environment:
   ```
   cd src/codegen_ui
   python setup.py setup
   ```

### Running the UI

You can run the backend and frontend separately or together:

- Run both together:
  ```
  python setup.py all
  ```

- Run just the backend:
  ```
  python setup.py backend
  ```

- Run just the frontend:
  ```
  python setup.py frontend
  ```

The UI will be available at http://localhost:3000, and the API will be available at http://localhost:8000.

## Usage

### Creating a Project

1. Open the UI in your browser at http://localhost:3000
2. Click "New Project" on the home page
3. Enter the path to your codebase and select the language (optional)
4. Click "Create"

### Browsing Files

1. Select a project from the home page
2. Use the file explorer in the left panel to navigate through the codebase
3. Click on a file to open it in the editor

### Browsing Symbols

1. Select a project from the home page
2. Click on the "Symbols" tab in the left panel
3. Browse through classes, functions, and other symbols
4. Click on a symbol to open its file in the editor

### Searching Code

1. Select a project from the home page
2. Click on the "Search" tab in the left panel
3. Enter a search query and optional file pattern
4. Click "Search" to find matching code
5. Click on a result to open the file in the editor

### Transforming Code

1. Select a project from the home page
2. Click on the "Transform" tab in the left panel
3. Select an operation (e.g., rename symbol, move symbol)
4. Enter the required parameters
5. Click "Execute Transformation" to apply the changes

## Development

### Backend

The backend is built with FastAPI and provides a RESTful API for the frontend to interact with the Codegen SDK. The main components are:

- `main.py`: The main FastAPI application
- API endpoints for projects, files, symbols, search, and transformations

### Frontend

The frontend is built with React, TypeScript, and Chakra UI. The main components are:

- `App.tsx`: The main application component
- `ProjectsPage.tsx`: The home page showing all projects
- `ProjectPage.tsx`: The project page showing the file explorer, editor, and other tools
- Components for file explorer, symbol browser, code editor, search, and transformations

## License

This project is licensed under the same license as the Codegen SDK.