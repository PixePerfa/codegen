# CodeGen UI

A comprehensive graphical user interface for the CodeGen SDK, allowing users to access all of the library's features through an intuitive interface.

## Features

- **Project Management**: Load and manage multiple codebases
- **File Explorer**: Browse and navigate through the codebase's file structure
- **Symbol Browser**: View and navigate classes, functions, and other symbols
- **Code Editor**: Edit files with syntax highlighting and code completion
- **Code Search**: Search for code patterns across the codebase
- **Code Transformation**: Apply code transformations like renaming symbols and moving code
- **Dependency Visualization**: Visualize code dependencies with an interactive graph
- **Code Metrics**: View code metrics and complexity analysis
- **Batch Operations**: Apply operations across multiple files at once
- **Git Integration**: Perform Git operations directly from the UI

## Installation

1. Clone the repository:
```bash
git clone https://github.com/PixePerfa/codegen.git
cd codegen
```

2. Set up the environment:
```bash
cd src/codegen_ui
python setup.py setup
```

## Usage

1. Start the UI:
```bash
cd src/codegen_ui
python setup.py all
```

2. Open your browser and navigate to http://localhost:3000

3. Create a new project by providing the path to your codebase

## Components

### File Explorer
- Browse through the file structure of your codebase
- Filter files by name
- View file content in the code editor

### Symbol Browser
- View all symbols (classes, functions, etc.) in your codebase
- Filter symbols by name or type
- Navigate to symbol definitions

### Code Search
- Search for code patterns using regular expressions
- Filter search results by file pattern
- Navigate to search results

### Code Transformation
- Rename symbols across the codebase
- Move symbols between files
- Rename files with automatic import updates

### Dependency Graph
- Visualize code dependencies with an interactive graph
- Filter dependencies by type
- Navigate to symbols by clicking on nodes

### Code Metrics
- View code metrics like total files, symbols, classes, and functions
- Analyze code complexity
- Identify complex functions that might need refactoring

### Batch Operations
- Apply operations to multiple files at once
- Replace text using regular expressions
- Add or remove imports across multiple files

### Git Operations
- View Git status
- Create and checkout branches
- Commit changes
- Pull and push changes

## Development

### Backend
The backend is built with FastAPI and provides a RESTful API for the frontend to interact with the CodeGen SDK.

### Frontend
The frontend is built with React, TypeScript, and Chakra UI, providing a modern and responsive user interface.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.