from typing import Dict, Any, Optional
from codegen.sdk.core.codebase import Codebase

def commit_changes(codebase: Codebase) -> Dict[str, Any]:
    """
    Commit changes to the codebase.
    
    Args:
        codebase: The Codegen codebase instance
        
    Returns:
        Dict with status and message
    """
    try:
        codebase.commit()
        return {
            "status": "success",
            "message": "Changes committed successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to commit changes: {str(e)}"
        }

def reset_codebase(codebase: Codebase) -> Dict[str, Any]:
    """
    Reset the codebase to its original state.
    
    Args:
        codebase: The Codegen codebase instance
        
    Returns:
        Dict with status and message
    """
    try:
        codebase.reset()
        return {
            "status": "success",
            "message": "Codebase reset successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to reset codebase: {str(e)}"
        }

def find_symbol_usages(codebase: Codebase, symbol_name: str) -> Dict[str, Any]:
    """
    Find all usages of a symbol in the codebase.
    
    Args:
        codebase: The Codegen codebase instance
        symbol_name: The name of the symbol to find usages for
        
    Returns:
        Dict with status and usages information
    """
    try:
        symbol = codebase.get_symbol(symbol_name)
        usages = symbol.usages
        
        result = []
        for usage in usages:
            result.append({
                "file_path": usage.file.path,
                "line": usage.line,
                "column": usage.column,
                "context": usage.context if hasattr(usage, "context") else None
            })
        
        return {
            "status": "success",
            "symbol": {
                "name": symbol.name,
                "type": symbol.symbol_type.name,
                "file_path": symbol.file.path,
                "line": symbol.line,
                "column": symbol.column
            },
            "usages": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to find symbol usages: {str(e)}"
        }

def regex_search(codebase: Codebase, pattern: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
    """
    Search the codebase using regular expressions.
    
    Args:
        codebase: The Codegen codebase instance
        pattern: The regex pattern to search for
        file_pattern: Optional file pattern to limit the search
        
    Returns:
        Dict with status and search results
    """
    try:
        import re
        import os
        
        results = []
        
        # Get files to search
        if file_pattern:
            import fnmatch
            files = [f for f in codebase.files(extensions="*") 
                    if fnmatch.fnmatch(f.path, file_pattern)]
        else:
            files = codebase.files(extensions="*")
        
        # Search each file
        for file in files:
            try:
                content = file.content
                matches = []
                
                for i, line in enumerate(content.splitlines(), 1):
                    for match in re.finditer(pattern, line):
                        matches.append({
                            "line_number": i,
                            "line": line,
                            "match": match.group(0),
                            "start": match.start(),
                            "end": match.end()
                        })
                
                if matches:
                    results.append({
                        "file_path": file.path,
                        "matches": matches
                    })
            except Exception as e:
                # Skip files that can't be searched
                continue
        
        return {
            "status": "success",
            "pattern": pattern,
            "file_pattern": file_pattern,
            "results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to perform regex search: {str(e)}"
        }