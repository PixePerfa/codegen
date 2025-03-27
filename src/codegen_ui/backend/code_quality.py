from typing import Dict, List, Any, Optional
import re
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import File

def analyze_code_quality(codebase: Codebase, file_path: Optional[str] = None) -> Dict[str, Any]:
    if file_path:
        files = [codebase.get_file(file_path)]
    else:
        files = codebase.files(extensions="*")
    
    results = {}
    
    for file in files:
        if not hasattr(file, "symbols"):
            continue
        
        file_results = {
            "complexity": analyze_file_complexity(file),
            "maintainability": analyze_maintainability(file),
            "issues": find_code_issues(file),
            "style_violations": check_style_violations(file)
        }
        
        results[file.path] = file_results
    
    return results

def analyze_file_complexity(file: File) -> Dict[str, Any]:
    complexity = {
        "cyclomatic_complexity": {},
        "cognitive_complexity": {},
        "lines_of_code": len(file.content.splitlines()),
        "comment_ratio": calculate_comment_ratio(file)
    }
    
    for symbol in file.symbols:
        if symbol.symbol_type.name in ["FUNCTION", "METHOD"]:
            # Calculate cyclomatic complexity
            symbol_content = file.content[symbol.start:symbol.end]
            
            # Simple approximation of cyclomatic complexity
            # Count branches (if, else, for, while, etc.)
            branches = (
                len(re.findall(r'\bif\b', symbol_content)) +
                len(re.findall(r'\belse\b', symbol_content)) +
                len(re.findall(r'\bfor\b', symbol_content)) +
                len(re.findall(r'\bwhile\b', symbol_content)) +
                len(re.findall(r'\bcatch\b', symbol_content)) +
                len(re.findall(r'\bcase\b', symbol_content)) +
                len(re.findall(r'\b\|\|\b', symbol_content)) +
                len(re.findall(r'\b&&\b', symbol_content))
            )
            
            cyclomatic = branches + 1
            
            # Simple approximation of cognitive complexity
            # Add nesting levels to cyclomatic complexity
            nesting = calculate_nesting_level(symbol_content)
            cognitive = cyclomatic + nesting
            
            complexity["cyclomatic_complexity"][symbol.name] = cyclomatic
            complexity["cognitive_complexity"][symbol.name] = cognitive
    
    return complexity

def calculate_nesting_level(content: str) -> int:
    lines = content.splitlines()
    max_indent = 0
    
    for line in lines:
        # Count leading spaces/tabs
        indent = len(line) - len(line.lstrip())
        max_indent = max(max_indent, indent)
    
    # Approximate nesting level based on indentation
    # Assuming 4 spaces or 1 tab per level
    return max_indent // 4

def calculate_comment_ratio(file: File) -> float:
    lines = file.content.splitlines()
    comment_lines = 0
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*") or stripped.endswith("*/"):
            comment_lines += 1
    
    if not lines:
        return 0
    
    return comment_lines / len(lines)

def analyze_maintainability(file: File) -> Dict[str, Any]:
    # Calculate maintainability index
    # MI = 171 - 5.2 * ln(avg_cc) - 0.23 * avg_loc - 16.2 * ln(avg_comments)
    
    avg_cc = 1.0  # Default value
    if hasattr(file, "symbols"):
        complexities = []
        for symbol in file.symbols:
            if symbol.symbol_type.name in ["FUNCTION", "METHOD"]:
                symbol_content = file.content[symbol.start:symbol.end]
                branches = (
                    len(re.findall(r'\bif\b', symbol_content)) +
                    len(re.findall(r'\belse\b', symbol_content)) +
                    len(re.findall(r'\bfor\b', symbol_content)) +
                    len(re.findall(r'\bwhile\b', symbol_content)) +
                    len(re.findall(r'\bcatch\b', symbol_content))
                )
                complexities.append(branches + 1)
        
        if complexities:
            avg_cc = sum(complexities) / len(complexities)
    
    lines = file.content.splitlines()
    avg_loc = len(lines)
    
    comment_lines = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*") or stripped.endswith("*/"):
            comment_lines += 1
    
    avg_comments = max(1, comment_lines)  # Avoid log(0)
    
    import math
    maintainability_index = 171 - 5.2 * math.log(avg_cc) - 0.23 * avg_loc - 16.2 * math.log(avg_comments)
    
    # Normalize to 0-100 scale
    maintainability_index = max(0, min(100, maintainability_index))
    
    return {
        "maintainability_index": maintainability_index,
        "rating": get_maintainability_rating(maintainability_index)
    }

def get_maintainability_rating(index: float) -> str:
    if index >= 85:
        return "A"
    elif index >= 70:
        return "B"
    elif index >= 55:
        return "C"
    elif index >= 40:
        return "D"
    else:
        return "F"

def find_code_issues(file: File) -> List[Dict[str, Any]]:
    issues = []
    
    # Check for long functions
    for symbol in file.symbols:
        if symbol.symbol_type.name in ["FUNCTION", "METHOD"]:
            symbol_content = file.content[symbol.start:symbol.end]
            lines = symbol_content.splitlines()
            
            if len(lines) > 50:
                issues.append({
                    "type": "long_function",
                    "symbol": symbol.name,
                    "line": symbol.line,
                    "message": f"Function '{symbol.name}' is too long ({len(lines)} lines)"
                })
    
    # Check for duplicate code
    # This is a simplified check for identical lines
    line_counts = {}
    lines = file.content.splitlines()
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if len(stripped) > 10 and not stripped.startswith("#") and not stripped.startswith("//"):
            if stripped in line_counts:
                line_counts[stripped].append(i + 1)
            else:
                line_counts[stripped] = [i + 1]
    
    for line, occurrences in line_counts.items():
        if len(occurrences) > 3:
            issues.append({
                "type": "duplicate_code",
                "line": occurrences[0],
                "message": f"Duplicate code found at lines {', '.join(map(str, occurrences))}"
            })
    
    # Check for too many parameters
    for symbol in file.symbols:
        if symbol.symbol_type.name in ["FUNCTION", "METHOD"] and hasattr(symbol, "parameters"):
            if len(symbol.parameters) > 5:
                issues.append({
                    "type": "too_many_parameters",
                    "symbol": symbol.name,
                    "line": symbol.line,
                    "message": f"Function '{symbol.name}' has too many parameters ({len(symbol.parameters)})"
                })
    
    return issues

def check_style_violations(file: File) -> List[Dict[str, Any]]:
    violations = []
    
    # Check line length
    lines = file.content.splitlines()
    for i, line in enumerate(lines):
        if len(line) > 100:
            violations.append({
                "type": "line_too_long",
                "line": i + 1,
                "message": f"Line {i + 1} is too long ({len(line)} characters)"
            })
    
    # Check naming conventions
    for symbol in file.symbols:
        name = symbol.name
        
        if symbol.symbol_type.name == "CLASS":
            # Classes should use CamelCase
            if not re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
                violations.append({
                    "type": "naming_convention",
                    "symbol": name,
                    "line": symbol.line,
                    "message": f"Class '{name}' should use CamelCase"
                })
        
        elif symbol.symbol_type.name in ["FUNCTION", "METHOD"]:
            # Functions should use snake_case
            if not re.match(r'^[a-z][a-z0-9_]*$', name):
                violations.append({
                    "type": "naming_convention",
                    "symbol": name,
                    "line": symbol.line,
                    "message": f"Function '{name}' should use snake_case"
                })
    
    return violations