#!/usr/bin/env python3
"""
Quick syntax and import validation for all Python files.
"""
import ast
import os
import sys
from pathlib import Path

def check_syntax(file_path):
    """Check if Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, "OK"
    except SyntaxError as e:
        return False, f"Syntax Error: Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Check all Python files for syntax errors."""
    project_root = Path(__file__).parent
    python_files = list(project_root.rglob("*.py"))
    
    # Filter out certain directories
    python_files = [f for f in python_files if not any(part in f.parts for part in ['.git', '__pycache__', 'venv', '.venv'])]
    
    print(f"Checking {len(python_files)} Python files for syntax errors...")
    
    errors = []
    for file_path in python_files:
        rel_path = file_path.relative_to(project_root)
        is_valid, message = check_syntax(file_path)
        
        if is_valid:
            print(f"✅ {rel_path}")
        else:
            print(f"❌ {rel_path}: {message}")
            errors.append((rel_path, message))
    
    print(f"\nResults: {len(python_files) - len(errors)}/{len(python_files)} files passed")
    
    if errors:
        print("\nFiles with syntax errors:")
        for file_path, error in errors:
            print(f"  {file_path}: {error}")
        return False
    else:
        print("🎉 All files have valid syntax!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
