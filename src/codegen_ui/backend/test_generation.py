from typing import Dict, List, Any, Optional
import re
import ast
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import File
from codegen.sdk.core.symbol import Symbol

def generate_tests(codebase: Codebase, file_path: Optional[str] = None) -> Dict[str, Any]:
    if file_path:
        files = [codebase.get_file(file_path)]
    else:
        files = codebase.files(extensions=".py")  # Only Python files for now
    
    results = {}
    
    for file in files:
        if not hasattr(file, "symbols"):
            continue
        
        # Skip test files
        if "test_" in file.path or "tests/" in file.path:
            continue
        
        file_tests = {
            "unit_tests": generate_unit_tests(file),
            "test_file_path": get_test_file_path(file.path),
            "coverage": estimate_coverage(file)
        }
        
        results[file.path] = file_tests
    
    return results

def get_test_file_path(file_path: str) -> str:
    # Convert a source file path to a test file path
    parts = file_path.split("/")
    filename = parts[-1]
    
    if filename.endswith(".py"):
        test_filename = "test_" + filename
    else:
        base_name = filename.split(".")[0]
        extension = "".join(filename.split(".")[1:])
        test_filename = f"test_{base_name}.{extension}"
    
    # Check if there's a tests directory at the same level
    if len(parts) > 1:
        if "tests" in parts:
            # Already in a tests directory structure
            return file_path.replace(filename, test_filename)
        else:
            # Try to find an appropriate tests directory
            test_path = "/".join(parts[:-1]) + "/tests/" + test_filename
            return test_path
    
    return "tests/" + test_filename

def generate_unit_tests(file: File) -> List[Dict[str, Any]]:
    tests = []
    
    # Parse the Python file
    try:
        tree = ast.parse(file.content)
    except SyntaxError:
        # If we can't parse the file, return empty tests
        return []
    
    # Find all functions and methods
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip private methods and dunder methods
            if node.name.startswith("_") and not (node.name.startswith("__") and node.name.endswith("__")):
                continue
            
            # Generate test for this function
            test = generate_test_for_function(node, file)
            if test:
                tests.append(test)
    
    return tests

def generate_test_for_function(node: ast.FunctionDef, file: File) -> Optional[Dict[str, Any]]:
    function_name = node.name
    
    # Get the class name if this is a method
    class_name = None
    for parent in ast.walk(file.ast):
        if isinstance(parent, ast.ClassDef) and node in parent.body:
            class_name = parent.name
            break
    
    # Extract parameters
    params = []
    for arg in node.args.args:
        if arg.arg != "self" and arg.arg != "cls":
            params.append(arg.arg)
    
    # Extract return type from type annotations if available
    return_type = None
    if node.returns:
        if isinstance(node.returns, ast.Name):
            return_type = node.returns.id
        elif isinstance(node.returns, ast.Subscript):
            if isinstance(node.returns.value, ast.Name):
                return_type = node.returns.value.id
    
    # Extract docstring
    docstring = ast.get_docstring(node)
    
    # Generate test code
    test_code = generate_test_code(function_name, class_name, params, return_type, docstring)
    
    return {
        "function_name": function_name,
        "class_name": class_name,
        "line": node.lineno,
        "parameters": params,
        "return_type": return_type,
        "test_code": test_code
    }

def generate_test_code(function_name: str, class_name: Optional[str], params: List[str], 
                      return_type: Optional[str], docstring: Optional[str]) -> str:
    # Generate a test function name
    test_function_name = f"test_{function_name}"
    
    # Generate imports
    imports = ["import unittest"]
    if class_name:
        imports.append(f"from module import {class_name}")
    else:
        imports.append(f"from module import {function_name}")
    
    # Generate parameter values based on parameter names and types
    param_values = []
    for param in params:
        if "id" in param.lower() or "key" in param.lower():
            param_values.append(f"{param} = 1")
        elif "name" in param.lower():
            param_values.append(f'{param} = "test"')
        elif "list" in param.lower() or "array" in param.lower():
            param_values.append(f"{param} = []")
        elif "dict" in param.lower() or "map" in param.lower():
            param_values.append(f"{param} = {{}}")
        elif "bool" in param.lower() or "flag" in param.lower():
            param_values.append(f"{param} = True")
        else:
            param_values.append(f'{param} = "value"')
    
    # Generate the test function
    if class_name:
        setup = f"self.obj = {class_name}()"
        call = f"result = self.obj.{function_name}({', '.join(params)})"
    else:
        setup = ""
        call = f"result = {function_name}({', '.join(params)})"
    
    # Generate assertions based on return type
    if return_type == "bool":
        assertion = "self.assertIsInstance(result, bool)"
    elif return_type == "int":
        assertion = "self.assertIsInstance(result, int)"
    elif return_type == "str":
        assertion = "self.assertIsInstance(result, str)"
    elif return_type == "list" or return_type == "List":
        assertion = "self.assertIsInstance(result, list)"
    elif return_type == "dict" or return_type == "Dict":
        assertion = "self.assertIsInstance(result, dict)"
    elif return_type == "None" or return_type is None:
        assertion = "self.assertIsNone(result)"
    else:
        assertion = f"# TODO: Add assertions for {return_type} return type"
    
    # Combine everything into a test class
    test_class = f"""
class Test{class_name or function_name.capitalize()}(unittest.TestCase):
    def {test_function_name}(self):
        # Setup
        {setup}
        
        # Test parameters
        {chr(10).join(param_values)}
        
        # Call the function
        {call}
        
        # Assertions
        {assertion}
        
if __name__ == "__main__":
    unittest.main()
"""
    
    return test_class.strip()

def estimate_coverage(file: File) -> Dict[str, Any]:
    # Check if there's a corresponding test file
    test_file_path = get_test_file_path(file.path)
    
    # Count testable symbols in the file
    testable_symbols = 0
    tested_symbols = 0
    
    for symbol in file.symbols:
        if symbol.symbol_type.name in ["FUNCTION", "METHOD", "CLASS"]:
            # Skip private symbols
            if symbol.name.startswith("_") and not (symbol.name.startswith("__") and symbol.name.endswith("__")):
                continue
            
            testable_symbols += 1
    
    # Estimate coverage based on symbol count
    # In a real implementation, we would check if the test file exists and analyze it
    coverage_percent = 0
    
    return {
        "testable_symbols": testable_symbols,
        "estimated_tested_symbols": tested_symbols,
        "coverage_percent": coverage_percent,
        "test_file_path": test_file_path
    }