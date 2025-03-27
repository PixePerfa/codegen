from typing import Dict, List, Any, Optional
import re
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import File
from codegen.sdk.core.symbol import Symbol

def generate_refactoring_suggestions(codebase: Codebase, file_path: Optional[str] = None) -> Dict[str, Any]:
    if file_path:
        files = [codebase.get_file(file_path)]
    else:
        files = codebase.files(extensions="*")
    
    results = {}
    
    for file in files:
        if not hasattr(file, "symbols"):
            continue
        
        file_suggestions = {
            "extract_method": find_extract_method_opportunities(file),
            "rename_symbol": find_rename_opportunities(file),
            "move_method": find_move_method_opportunities(file, codebase),
            "simplify_conditional": find_complex_conditionals(file)
        }
        
        if file_suggestions["extract_method"] or file_suggestions["rename_symbol"] or \
           file_suggestions["move_method"] or file_suggestions["simplify_conditional"]:
            results[file.path] = file_suggestions
    
    return results

def find_extract_method_opportunities(file: File) -> List[Dict[str, Any]]:
    opportunities = []
    
    for symbol in file.symbols:
        if symbol.symbol_type.name in ["FUNCTION", "METHOD"]:
            symbol_content = file.content[symbol.start:symbol.end]
            lines = symbol_content.splitlines()
            
            # Look for long functions
            if len(lines) > 30:
                # Find logical blocks that could be extracted
                blocks = find_logical_blocks(symbol_content)
                
                for block in blocks:
                    if block["lines"] > 10:  # Only suggest extracting substantial blocks
                        opportunities.append({
                            "type": "extract_method",
                            "symbol": symbol.name,
                            "start_line": symbol.line + block["start_line"],
                            "end_line": symbol.line + block["end_line"],
                            "suggested_name": block["suggested_name"],
                            "reason": f"Extract {block['lines']} lines to a new method"
                        })
    
    return opportunities

def find_logical_blocks(content: str) -> List[Dict[str, Any]]:
    lines = content.splitlines()
    blocks = []
    
    # Simple heuristic: look for indented blocks
    current_block = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue
        
        indent = len(line) - len(line.lstrip())
        
        # Start of a new block with comments above it
        if i > 0 and stripped and (lines[i-1].strip().startswith("#") or lines[i-1].strip().startswith("//")) and indent == 0:
            if current_block and current_block["lines"] > 5:
                blocks.append(current_block)
            
            # Try to extract a name from the comment
            comment = lines[i-1].strip().lstrip("#").lstrip("/").strip()
            suggested_name = "extracted_" + "_".join(re.findall(r'\b[a-z]+\b', comment.lower())[:3])
            if not suggested_name or suggested_name == "extracted_":
                suggested_name = f"extracted_block_{len(blocks) + 1}"
            
            current_block = {
                "start_line": i,
                "lines": 0,
                "suggested_name": suggested_name
            }
        
        # Start of a control structure (potential logical block)
        elif stripped.startswith(("if ", "for ", "while ", "try:", "with ")):
            if current_block and current_block["lines"] > 5:
                blocks.append(current_block)
            
            # Extract name from the control structure
            words = re.findall(r'\b[a-z]+\b', stripped.lower())
            if "if" in words:
                suggested_name = "check_" + "_".join([w for w in words if w not in ["if", "else", "elif"]])
            elif "for" in words:
                suggested_name = "process_" + "_".join([w for w in words if w not in ["for", "in"]])
            elif "while" in words:
                suggested_name = "process_while_" + "_".join([w for w in words if w not in ["while"]])
            else:
                suggested_name = f"extracted_block_{len(blocks) + 1}"
            
            if len(suggested_name) > 30:
                suggested_name = suggested_name[:30]
            
            current_block = {
                "start_line": i,
                "lines": 0,
                "suggested_name": suggested_name
            }
        
        if current_block:
            current_block["lines"] += 1
            current_block["end_line"] = i
    
    # Add the last block if it exists
    if current_block and current_block["lines"] > 5:
        blocks.append(current_block)
    
    return blocks

def find_rename_opportunities(file: File) -> List[Dict[str, Any]]:
    opportunities = []
    
    for symbol in file.symbols:
        name = symbol.name
        
        # Check for very short names
        if len(name) <= 1 and symbol.symbol_type.name not in ["PARAMETER"]:
            opportunities.append({
                "type": "rename_symbol",
                "symbol": name,
                "line": symbol.line,
                "suggested_name": "descriptive_" + name,
                "reason": f"Symbol name '{name}' is too short"
            })
        
        # Check for unclear names
        elif symbol.symbol_type.name in ["FUNCTION", "METHOD"] and name in ["process", "handle", "do", "execute", "run", "perform"]:
            opportunities.append({
                "type": "rename_symbol",
                "symbol": name,
                "line": symbol.line,
                "suggested_name": name + "_specific_action",
                "reason": f"Function name '{name}' is too generic"
            })
        
        # Check for inconsistent naming
        elif symbol.symbol_type.name == "CLASS" and not re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
            pascal_case = ''.join(word.capitalize() for word in re.findall(r'[a-zA-Z0-9]+', name))
            opportunities.append({
                "type": "rename_symbol",
                "symbol": name,
                "line": symbol.line,
                "suggested_name": pascal_case,
                "reason": f"Class name '{name}' should use PascalCase"
            })
        
        elif symbol.symbol_type.name in ["FUNCTION", "METHOD"] and not re.match(r'^[a-z][a-z0-9_]*$', name):
            snake_case = '_'.join(word.lower() for word in re.findall(r'[a-zA-Z0-9]+', name))
            opportunities.append({
                "type": "rename_symbol",
                "symbol": name,
                "line": symbol.line,
                "suggested_name": snake_case,
                "reason": f"Function name '{name}' should use snake_case"
            })
    
    return opportunities

def find_move_method_opportunities(file: File, codebase: Codebase) -> List[Dict[str, Any]]:
    opportunities = []
    
    # Get all classes in the codebase
    all_classes = codebase.classes
    
    for symbol in file.symbols:
        if symbol.symbol_type.name == "METHOD":
            # Check if this method primarily uses another class's data
            method_content = file.content[symbol.start:symbol.end]
            
            # Find all references to "self" and other classes
            self_refs = len(re.findall(r'\bself\.[a-zA-Z0-9_]+\b', method_content))
            
            # Check references to other classes
            for cls in all_classes:
                if cls.file.path == file.path:
                    continue  # Skip classes in the same file
                
                class_name = cls.name
                class_refs = len(re.findall(r'\b' + class_name + r'\b', method_content))
                
                # If method references another class more than self
                if class_refs > self_refs and class_refs > 2:
                    opportunities.append({
                        "type": "move_method",
                        "symbol": symbol.name,
                        "line": symbol.line,
                        "target_class": class_name,
                        "target_file": cls.file.path,
                        "reason": f"Method '{symbol.name}' uses {class_name} more than its own class"
                    })
    
    return opportunities

def find_complex_conditionals(file: File) -> List[Dict[str, Any]]:
    opportunities = []
    
    for symbol in file.symbols:
        if symbol.symbol_type.name in ["FUNCTION", "METHOD"]:
            symbol_content = file.content[symbol.start:symbol.end]
            
            # Find complex conditionals
            conditionals = re.finditer(r'if\s+(.+?):', symbol_content)
            
            for match in conditionals:
                condition = match.group(1)
                
                # Count logical operators
                and_count = len(re.findall(r'\band\b', condition))
                or_count = len(re.findall(r'\bor\b', condition))
                not_count = len(re.findall(r'\bnot\b', condition))
                
                # Count comparison operators
                comparison_count = len(re.findall(r'[=!<>]=?', condition))
                
                complexity = and_count + or_count + not_count + comparison_count
                
                if complexity >= 3:
                    # Calculate line number
                    line_offset = symbol_content[:match.start()].count('\n')
                    line_number = symbol.line + line_offset
                    
                    opportunities.append({
                        "type": "simplify_conditional",
                        "symbol": symbol.name,
                        "line": line_number,
                        "complexity": complexity,
                        "condition": condition,
                        "reason": f"Complex conditional with {complexity} operators"
                    })
    
    return opportunities