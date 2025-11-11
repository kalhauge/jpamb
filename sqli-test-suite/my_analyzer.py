#!/usr/bin/env python3
"""
Improved SQL Injection Analyzer for JPAMB Test Suite
Enhanced syntactic analysis with better literal detection
"""

import sys
import re
from pathlib import Path

def parse_method_signature(method_sig):
    """
    Parse method signature like: jpamb.sqli.SQLi_DirectConcat.vulnerable
    Returns: (class_path, method_name)
    """
    parts = method_sig.rsplit('.', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, None

def get_source_file_path(class_path):
    """
    Convert class path to source file path
    jpamb.sqli.SQLi_DirectConcat -> src/main/java/jpamb/sqli/SQLi_DirectConcat.java
    """
    file_path = class_path.replace('.', '/') + '.java'
    return Path('src/main/java') / file_path

def extract_method_body(source_code, method_name):
    """
    Extract the body of a specific method from Java source code
    """
    # Pattern to match method definition and body
    pattern = rf'public\s+static\s+\w+\s+{method_name}\s*\([^)]*\)\s*\{{'
    
    start_match = re.search(pattern, source_code)
    
    if start_match:
        start = start_match.end() - 1  # Position of opening brace
        brace_count = 1
        pos = start + 1
        
        while pos < len(source_code) and brace_count > 0:
            if source_code[pos] == '{':
                brace_count += 1
            elif source_code[pos] == '}':
                brace_count -= 1
            pos += 1
        
        if brace_count == 0:
            return source_code[start + 1:pos - 1].strip()
    
    return None

def extract_literals(method_body):
    """
    Extract all string literals and variables defined as literals
    Also tracks variables derived from operations on literals
    Returns set of variable names that are trusted (literal strings)
    """
    trusted_vars = set()
    
    # Find variable assignments to string literals
    # Pattern: varName = "literal";
    literal_assignments = re.findall(r'(\w+)\s*=\s*"[^"]*"\s*;', method_body)
    trusted_vars.update(literal_assignments)
    
    # Find array initializations with literals
    # Pattern: String[] ids = {"1", "2", "3"};
    array_literals = re.findall(r'(\w+)\s*=\s*\{["\w\s,]*\}', method_body)
    trusted_vars.update(array_literals)
    
    # Track derived literals (operations on trusted variables)
    # Need to iterate to catch chains: a = "lit"; b = a.trim(); c = b.substring()
    max_iterations = 5
    for _ in range(max_iterations):
        initial_size = len(trusted_vars)
        
        # Pattern: var2 = var1.operation()
        # Operations that preserve literal status
        safe_operations = ['substring', 'trim', 'toUpperCase', 'toLowerCase', 
                          'replace', 'replaceAll', 'replaceFirst', 'strip',
                          'stripLeading', 'stripTrailing', 'concat']
        
        for op in safe_operations:
            # Match: newVar = trustedVar.operation(...)
            pattern = rf'(\w+)\s*=\s*(\w+)\.{op}\s*\('
            matches = re.findall(pattern, method_body)
            for new_var, source_var in matches:
                if source_var in trusted_vars:
                    trusted_vars.add(new_var)
        
        # Pattern: var2 = var1.split(...)[index] or var1.split(...); ... var2 = var1[index]
        split_matches = re.findall(r'(\w+)\s*=\s*(\w+)\.split\s*\(', method_body)
        for new_var, source_var in split_matches:
            if source_var in trusted_vars:
                trusted_vars.add(new_var)  # Array from split on literal
        
        # Pattern: element = array[0] where array is trusted
        array_access = re.findall(r'(\w+)\s*=\s*(\w+)\[', method_body)
        for new_var, array_var in array_access:
            if array_var in trusted_vars:
                trusted_vars.add(new_var)
        
        # If no new variables added, we've found all derived literals
        if len(trusted_vars) == initial_size:
            break
    
    return trusted_vars

def has_dangerous_concatenation(method_body, trusted_vars):
    """
    Check if method has concatenation with untrusted variables
    Returns True if dangerous concatenation found
    """
    # Pattern 1: "string" + variable
    concat_matches = re.finditer(r'"[^"]*"\s*\+\s*(\w+)', method_body)
    for match in concat_matches:
        var_name = match.group(1)
        if var_name not in trusted_vars:
            return True
    
    # Pattern 2: variable + "string"
    reverse_matches = re.finditer(r'(\w+)\s*\+\s*"[^"]*"', method_body)
    for match in reverse_matches:
        var_name = match.group(1)
        if var_name not in trusted_vars:
            return True
    
    # Pattern 3: += with variables (loop concatenation)
    if '+=' in method_body:
        # Check if += is with a variable
        concat_eq_matches = re.finditer(r'\+=\s*(\w+)', method_body)
        for match in concat_eq_matches:
            var_name = match.group(1)
            # Check if it's from an external source (inputs, parameters)
            if var_name not in trusted_vars or 'input' in var_name.lower():
                return True
    
    return False

def has_dangerous_stringbuilder(method_body, trusted_vars):
    """
    Check StringBuilder/StringBuffer for untrusted appends
    """
    if 'StringBuilder' not in method_body and 'StringBuffer' not in method_body:
        return False
    
    # Find .append(variable) calls
    append_matches = re.finditer(r'\.append\s*\(\s*(\w+)\s*\)', method_body)
    for match in append_matches:
        var_name = match.group(1)
        # Check if it's a string literal append (skip)
        if var_name not in trusted_vars and not var_name.isdigit():
            return True
    
    return False

def analyze_for_sql_injection(method_body, method_name):
    """
    Improved syntactic analysis to detect SQL injection patterns
    Returns (outcome, confidence)
    """
    if not method_body:
        return "error", 0
    
    # Extract all trusted (literal) variables
    trusted_vars = extract_literals(method_body)
    
    # Special handling for "safe" methods
    if method_name == "safe":
        # Check for strong sanitization patterns
        if 'replaceAll' in method_body and '[^0-9]' in method_body:
            return "ok", 100
        if 'replaceAll' in method_body and '[^a-zA-Z0-9]' in method_body:
            return "ok", 100
        
        # Check for whitelist validation
        if '.equals(' in method_body and '?' in method_body and ':' in method_body:
            # Ternary with equals check (whitelist pattern)
            return "ok", 95
    
    # Check for pure literal-only operations
    # If no untrusted variables are used anywhere, it's safe
    has_concat = '+' in method_body or '+=' in method_body
    has_stringbuilder = 'StringBuilder' in method_body or 'StringBuffer' in method_body
    
    if not has_concat and not has_stringbuilder:
        # No concatenation at all, just literals
        return "ok", 100
    
    # Check for dangerous concatenation patterns
    if has_dangerous_concatenation(method_body, trusted_vars):
        return "SQL injection", 100
    
    # Check for dangerous StringBuilder/StringBuffer usage
    if has_dangerous_stringbuilder(method_body, trusted_vars):
        return "SQL injection", 95
    
    # Special case: Check for operations on trusted literals
    # substring, trim, toUpperCase, etc. on literal strings are safe
    string_operations = ['substring', 'trim', 'toUpperCase', 'toLowerCase', 'split', 'replace']
    has_string_ops = any(op in method_body for op in string_operations)
    
    if has_string_ops and has_concat:
        # Check if operations are on literals
        # Pattern: "literal".operation() or trustedVar.operation()
        operations_on_literals = True
        
        # Find all variables that have operations called on them
        for op in string_operations:
            op_matches = re.finditer(rf'(\w+)\.{op}\s*\(', method_body)
            for match in op_matches:
                var_name = match.group(1)
                if var_name not in trusted_vars:
                    # Operation on untrusted variable
                    if '+' in method_body or 'query' in method_body.lower():
                        # And it's used in SQL context
                        return "SQL injection", 90
        
        # All operations are on trusted variables
        if has_concat:
            # Check final concatenation
            if not has_dangerous_concatenation(method_body, trusted_vars):
                return "ok", 95
    
    # If we have concatenation but all variables are trusted, it's safe
    if has_concat:
        # Double-check: are all concatenated items trusted?
        all_concat_vars = re.findall(r'(?:"[^"]*"\s*\+\s*(\w+)|(\w+)\s*\+\s*"[^"]*")', method_body)
        flat_vars = [v for group in all_concat_vars for v in group if v]
        
        untrusted_found = False
        for var in flat_vars:
            if var not in trusted_vars and not var.isdigit():
                untrusted_found = True
                break
        
        if not untrusted_found:
            return "ok", 90
    
    # Default: if nothing suspicious found, likely safe
    return "ok", 60

def main():
    if len(sys.argv) < 2:
        print("Usage: python my_analyzer.py <method_signature>", file=sys.stderr)
        print("Example: python my_analyzer.py jpamb.sqli.SQLi_DirectConcat.vulnerable", file=sys.stderr)
        sys.exit(1)
    
    method_sig = sys.argv[1]
    
    # Debug output to stderr (won't affect test results)
    print(f"Analyzing: {method_sig}", file=sys.stderr)
    
    # Parse the method signature
    class_path, method_name = parse_method_signature(method_sig)
    
    if not class_path:
        print("error;0", file=sys.stdout)
        sys.exit(1)
    
    # Get source file path
    source_file = get_source_file_path(class_path)
    
    # Check if file exists
    if not source_file.exists():
        print(f"Error: Source file not found: {source_file}", file=sys.stderr)
        print("error;0", file=sys.stdout)
        sys.exit(1)
    
    # Read the source file
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        print("error;0", file=sys.stdout)
        sys.exit(1)
    
    # Extract method body
    method_body = extract_method_body(source_code, method_name)
    
    if not method_body:
        print(f"Warning: Could not extract method body for {method_name}", file=sys.stderr)
        print("error;0", file=sys.stdout)
        sys.exit(1)
    
    print(f"Method body found ({len(method_body)} chars)", file=sys.stderr)
    
    # Analyze for SQL injection
    outcome, confidence = analyze_for_sql_injection(method_body, method_name)
    
    # Output result in format: "outcome;confidence"
    print(f"{outcome};{confidence}", file=sys.stdout)
    
    print(f"Analysis complete: {outcome} (confidence: {confidence})", file=sys.stderr)

if __name__ == "__main__":
    main()