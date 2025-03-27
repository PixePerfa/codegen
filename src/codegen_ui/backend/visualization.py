from typing import Dict, List, Any, Optional
import re
import networkx as nx
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import File
from codegen.sdk.core.symbol import Symbol

def generate_visualizations(codebase: Codebase, file_path: Optional[str] = None) -> Dict[str, Any]:
    results = {
        "dependency_graph": generate_dependency_graph(codebase, file_path),
        "inheritance_graph": generate_inheritance_graph(codebase, file_path),
        "call_graph": generate_call_graph(codebase, file_path),
        "module_graph": generate_module_graph(codebase),
        "complexity_heatmap": generate_complexity_heatmap(codebase, file_path)
    }
    
    return results

def generate_dependency_graph(codebase: Codebase, file_path: Optional[str] = None) -> Dict[str, Any]:
    # Create a graph of symbol dependencies
    graph = nx.DiGraph()
    
    # Get symbols to include
    if file_path:
        file = codebase.get_file(file_path)
        symbols = file.symbols
    else:
        symbols = codebase.symbols
    
    # Add nodes for each symbol
    for symbol in symbols:
        graph.add_node(symbol.name, 
                      type=symbol.symbol_type.name, 
                      file=symbol.file.path,
                      line=symbol.line)
    
    # Add edges for dependencies
    for symbol in symbols:
        if hasattr(symbol, "dependencies"):
            for dep in symbol.dependencies:
                if dep.name in graph:
                    graph.add_edge(symbol.name, dep.name)
    
    # Convert to a format suitable for visualization
    nodes = []
    for node, attrs in graph.nodes(data=True):
        nodes.append({
            "id": node,
            "label": node,
            "type": attrs.get("type", "UNKNOWN"),
            "file": attrs.get("file", ""),
            "line": attrs.get("line", 0)
        })
    
    edges = []
    for source, target in graph.edges():
        edges.append({
            "source": source,
            "target": target
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }

def generate_inheritance_graph(codebase: Codebase, file_path: Optional[str] = None) -> Dict[str, Any]:
    # Create a graph of class inheritance
    graph = nx.DiGraph()
    
    # Get classes to include
    if file_path:
        file = codebase.get_file(file_path)
        classes = [s for s in file.symbols if s.symbol_type.name == "CLASS"]
    else:
        classes = codebase.classes
    
    # Add nodes for each class
    for cls in classes:
        graph.add_node(cls.name, 
                      file=cls.file.path,
                      line=cls.line)
    
    # Add edges for inheritance
    for cls in classes:
        if hasattr(cls, "bases"):
            for base in cls.bases:
                if base.name in graph:
                    graph.add_edge(cls.name, base.name)
    
    # Convert to a format suitable for visualization
    nodes = []
    for node, attrs in graph.nodes(data=True):
        nodes.append({
            "id": node,
            "label": node,
            "file": attrs.get("file", ""),
            "line": attrs.get("line", 0)
        })
    
    edges = []
    for source, target in graph.edges():
        edges.append({
            "source": source,
            "target": target
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }

def generate_call_graph(codebase: Codebase, file_path: Optional[str] = None) -> Dict[str, Any]:
    # Create a graph of function calls
    graph = nx.DiGraph()
    
    # Get functions to include
    if file_path:
        file = codebase.get_file(file_path)
        functions = [s for s in file.symbols if s.symbol_type.name in ["FUNCTION", "METHOD"]]
    else:
        functions = [s for s in codebase.symbols if s.symbol_type.name in ["FUNCTION", "METHOD"]]
    
    # Add nodes for each function
    for func in functions:
        graph.add_node(func.name, 
                      type=func.symbol_type.name,
                      file=func.file.path,
                      line=func.line)
    
    # Add edges for function calls
    for func in functions:
        # This is a simplified approach - in a real implementation, we would
        # parse the function body to find actual function calls
        func_content = func.file.content[func.start:func.end]
        
        for other_func in functions:
            if other_func.name == func.name:
                continue
            
            # Check if the function name appears in the content
            # This is a very simple heuristic and would need to be improved
            if re.search(r'\b' + re.escape(other_func.name) + r'\s*\(', func_content):
                graph.add_edge(func.name, other_func.name)
    
    # Convert to a format suitable for visualization
    nodes = []
    for node, attrs in graph.nodes(data=True):
        nodes.append({
            "id": node,
            "label": node,
            "type": attrs.get("type", "UNKNOWN"),
            "file": attrs.get("file", ""),
            "line": attrs.get("line", 0)
        })
    
    edges = []
    for source, target in graph.edges():
        edges.append({
            "source": source,
            "target": target
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }

def generate_module_graph(codebase: Codebase) -> Dict[str, Any]:
    # Create a graph of module imports
    graph = nx.DiGraph()
    
    # Get all files
    files = codebase.files(extensions="*")
    
    # Add nodes for each file
    for file in files:
        module_name = file.path.split("/")[-1]
        if module_name.endswith(".py"):
            module_name = module_name[:-3]
        
        graph.add_node(module_name, file=file.path)
    
    # Add edges for imports
    for file in files:
        if not hasattr(file, "imports"):
            continue
        
        source_module = file.path.split("/")[-1]
        if source_module.endswith(".py"):
            source_module = source_module[:-3]
        
        for imp in file.imports:
            # Extract the module name from the import
            if imp.module:
                target_module = imp.module.split(".")[-1]
                
                # Check if the target module is in our graph
                if target_module in graph:
                    graph.add_edge(source_module, target_module)
    
    # Convert to a format suitable for visualization
    nodes = []
    for node, attrs in graph.nodes(data=True):
        nodes.append({
            "id": node,
            "label": node,
            "file": attrs.get("file", "")
        })
    
    edges = []
    for source, target in graph.edges():
        edges.append({
            "source": source,
            "target": target
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }

def generate_complexity_heatmap(codebase: Codebase, file_path: Optional[str] = None) -> Dict[str, Any]:
    # Generate a heatmap of code complexity
    if file_path:
        files = [codebase.get_file(file_path)]
    else:
        files = codebase.files(extensions="*")
    
    heatmap_data = []
    
    for file in files:
        if not hasattr(file, "symbols"):
            continue
        
        file_data = {
            "path": file.path,
            "symbols": []
        }
        
        for symbol in file.symbols:
            if symbol.symbol_type.name in ["FUNCTION", "METHOD"]:
                # Calculate complexity
                symbol_content = file.content[symbol.start:symbol.end]
                lines = symbol_content.splitlines()
                
                # Simple approximation of cyclomatic complexity
                branches = (
                    len(re.findall(r'\bif\b', symbol_content)) +
                    len(re.findall(r'\belse\b', symbol_content)) +
                    len(re.findall(r'\bfor\b', symbol_content)) +
                    len(re.findall(r'\bwhile\b', symbol_content)) +
                    len(re.findall(r'\bcatch\b', symbol_content)) +
                    len(re.findall(r'\bcase\b', symbol_content))
                )
                
                complexity = branches + 1
                
                file_data["symbols"].append({
                    "name": symbol.name,
                    "type": symbol.symbol_type.name,
                    "line": symbol.line,
                    "complexity": complexity,
                    "lines": len(lines)
                })
        
        heatmap_data.append(file_data)
    
    return heatmap_data

def generate_treemap(codebase: Codebase) -> Dict[str, Any]:
    # Generate a treemap of the codebase structure
    files = codebase.files(extensions="*")
    
    # Build a tree structure
    root = {"name": "root", "children": []}
    
    for file in files:
        path_parts = file.path.split("/")
        
        # Navigate the tree
        current = root
        for i, part in enumerate(path_parts[:-1]):
            # Find or create the directory node
            dir_node = None
            for child in current["children"]:
                if child["name"] == part and "children" in child:
                    dir_node = child
                    break
            
            if not dir_node:
                dir_node = {"name": part, "children": []}
                current["children"].append(dir_node)
            
            current = dir_node
        
        # Add the file node
        file_node = {"name": path_parts[-1]}
        
        # Add file size
        file_node["size"] = len(file.content)
        
        # Add symbols if available
        if hasattr(file, "symbols"):
            file_node["symbols"] = len(file.symbols)
        
        current["children"].append(file_node)
    
    return root