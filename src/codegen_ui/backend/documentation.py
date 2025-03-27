from typing import Dict, List, Any, Optional
import re
import ast
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import File
from codegen.sdk.core.symbol import Symbol

def generate_documentation(codebase: Codebase, file_path: Optional[str] = None) -> Dict[str, Any]:
    if file_path:
        files = [codebase.get_file(file_path)]
    else:
        files = codebase.files(extensions="*")
    
    results = {}
    
    for file in files:
        if not hasattr(file, "symbols"):
            continue
        
        file_docs = {
            "module_doc": generate_module_doc(file),
            "class_docs": generate_class_docs(file),
            "function_docs": generate_function_docs(file),
            "missing_docs": find_missing_docs(file)
        }
        
        results[file.path] = file_docs
    
    return results

def generate_module_doc(file: File) -> Dict[str, Any]:
    # Extract module docstring
    module_doc = ""
    try:
        tree = ast.parse(file.content)
        module_doc = ast.get_docstring(tree) or ""
    except SyntaxError:
        pass
    
    # Generate module documentation
    imports = []
    try:
        tree = ast.parse(file.content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for name in node.names:
                        imports.append(f"{node.module}.{name.name}")
    except SyntaxError:
        pass
    
    # Extract module name from file path
    module_name = file.path.split("/")[-1]
    if module_name.endswith(".py"):
        module_name = module_name[:-3]
    
    return {
        "name": module_name,
        "docstring": module_doc,
        "imports": imports,
        "suggested_doc": generate_module_docstring(file, module_name)
    }

def generate_module_docstring(file: File, module_name: str) -> str:
    # Generate a docstring for the module based on its contents
    classes = [s for s in file.symbols if s.symbol_type.name == "CLASS"]
    functions = [s for s in file.symbols if s.symbol_type.name == "FUNCTION"]
    
    class_names = [cls.name for cls in classes]
    function_names = [func.name for func in functions if not func.name.startswith("_")]
    
    docstring = f"""
{module_name}
{'=' * len(module_name)}

This module provides functionality for working with {module_name.replace('_', ' ')}.

Classes:
{chr(10).join([f'- {cls}' for cls in class_names]) if class_names else 'None'}

Functions:
{chr(10).join([f'- {func}' for func in function_names]) if function_names else 'None'}
"""
    
    return docstring.strip()

def generate_class_docs(file: File) -> List[Dict[str, Any]]:
    class_docs = []
    
    for symbol in file.symbols:
        if symbol.symbol_type.name != "CLASS":
            continue
        
        # Extract class docstring
        class_doc = ""
        try:
            tree = ast.parse(file.content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == symbol.name:
                    class_doc = ast.get_docstring(node) or ""
                    break
        except SyntaxError:
            pass
        
        # Get methods
        methods = []
        for method in symbol.methods:
            method_doc = ""
            try:
                tree = ast.parse(file.content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == method.name:
                        method_doc = ast.get_docstring(node) or ""
                        break
            except SyntaxError:
                pass
            
            methods.append({
                "name": method.name,
                "docstring": method_doc,
                "line": method.line,
                "suggested_doc": generate_method_docstring(method, file)
            })
        
        class_docs.append({
            "name": symbol.name,
            "docstring": class_doc,
            "line": symbol.line,
            "methods": methods,
            "suggested_doc": generate_class_docstring(symbol, file)
        })
    
    return class_docs

def generate_class_docstring(symbol: Symbol, file: File) -> str:
    # Generate a docstring for the class based on its methods and attributes
    methods = [m for m in symbol.methods if not m.name.startswith("_") or (m.name.startswith("__") and m.name.endswith("__"))]
    method_names = [m.name for m in methods]
    
    # Try to determine the class's purpose from its name and methods
    purpose = symbol.name.replace("_", " ")
    if "Exception" in symbol.name or "Error" in symbol.name:
        purpose = f"Exception class for {purpose.lower()}"
    elif "Manager" in symbol.name or "Controller" in symbol.name:
        purpose = f"Manages {purpose.lower().replace('manager', '').replace('controller', '')}"
    elif "Service" in symbol.name:
        purpose = f"Provides services for {purpose.lower().replace('service', '')}"
    
    docstring = f"""
{symbol.name}
{'-' * len(symbol.name)}

{purpose}.

Methods:
{chr(10).join([f'- {method}' for method in method_names]) if method_names else 'None'}
"""
    
    return docstring.strip()

def generate_function_docs(file: File) -> List[Dict[str, Any]]:
    function_docs = []
    
    for symbol in file.symbols:
        if symbol.symbol_type.name != "FUNCTION":
            continue
        
        # Skip private functions
        if symbol.name.startswith("_") and not (symbol.name.startswith("__") and symbol.name.endswith("__")):
            continue
        
        # Extract function docstring
        function_doc = ""
        try:
            tree = ast.parse(file.content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == symbol.name:
                    function_doc = ast.get_docstring(node) or ""
                    break
        except SyntaxError:
            pass
        
        function_docs.append({
            "name": symbol.name,
            "docstring": function_doc,
            "line": symbol.line,
            "suggested_doc": generate_function_docstring(symbol, file)
        })
    
    return function_docs

def generate_function_docstring(symbol: Symbol, file: File) -> str:
    # Generate a docstring for the function based on its parameters and return type
    params = []
    return_type = None
    
    try:
        tree = ast.parse(file.content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == symbol.name:
                # Extract parameters
                for arg in node.args.args:
                    if arg.arg != "self" and arg.arg != "cls":
                        param_type = "Any"
                        if hasattr(arg, "annotation") and arg.annotation:
                            if isinstance(arg.annotation, ast.Name):
                                param_type = arg.annotation.id
                            elif isinstance(arg.annotation, ast.Subscript):
                                if isinstance(arg.annotation.value, ast.Name):
                                    param_type = arg.annotation.value.id
                        
                        params.append((arg.arg, param_type))
                
                # Extract return type
                if node.returns:
                    if isinstance(node.returns, ast.Name):
                        return_type = node.returns.id
                    elif isinstance(node.returns, ast.Subscript):
                        if isinstance(node.returns.value, ast.Name):
                            return_type = node.returns.value.id
                
                break
    except SyntaxError:
        pass
    
    # Generate docstring
    purpose = symbol.name.replace("_", " ")
    
    docstring = f"""
{purpose.capitalize()}.

Parameters:
{chr(10).join([f'- {param}: {param_type}' for param, param_type in params]) if params else 'None'}

Returns:
{return_type if return_type else 'None'}
"""
    
    return docstring.strip()

def generate_method_docstring(symbol: Symbol, file: File) -> str:
    # Similar to function docstring but for methods
    return generate_function_docstring(symbol, file)

def find_missing_docs(file: File) -> List[Dict[str, Any]]:
    missing_docs = []
    
    try:
        tree = ast.parse(file.content)
        
        # Check module docstring
        if not ast.get_docstring(tree):
            missing_docs.append({
                "type": "module",
                "name": file.path.split("/")[-1],
                "line": 1
            })
        
        # Check classes and functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    missing_docs.append({
                        "type": "class",
                        "name": node.name,
                        "line": node.lineno
                    })
                
                # Check methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                        if not ast.get_docstring(item):
                            missing_docs.append({
                                "type": "method",
                                "name": f"{node.name}.{item.name}",
                                "line": item.lineno
                            })
            
            elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                # Skip if it's a method (already checked above)
                is_method = False
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef) and node in parent.body:
                        is_method = True
                        break
                
                if not is_method and not ast.get_docstring(node):
                    missing_docs.append({
                        "type": "function",
                        "name": node.name,
                        "line": node.lineno
                    })
    
    except SyntaxError:
        pass
    
    return missing_docs