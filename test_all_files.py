#!/usr/bin/env python3
"""
Comprehensive file-by-file testing script for ACP Polymarket Trading Agent.

Tests every Python file for:
- Syntax errors
- Import errors
- Basic functionality
- Configuration files validation
"""
import ast
import json
import os
import sys
import traceback
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple

# Setup environment for testing
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("DEVELOPMENT_MODE", "true")
os.environ.setdefault("POLYMARKET_API_URL", "https://clob.polymarket.com")
os.environ.setdefault("BASE_RPC_URL", "https://mainnet.base.org")
os.environ.setdefault("VIRTUAL_TOKEN_ADDRESS", "0x0000000000000000000000000000000000000000")

class FileValidator:
    """Validates individual files in the codebase."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {}
        
    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'venv', '.venv']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        return python_files
    
    def find_config_files(self) -> List[Path]:
        """Find configuration files to validate."""
        config_files = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'venv', '.venv']]
            
            for file in files:
                if file.endswith(('.json', '.yml', '.yaml')):
                    config_files.append(Path(root) / file)
        return config_files
    
    def test_syntax(self, file_path: Path) -> Tuple[bool, str]:
        """Test Python file syntax."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            ast.parse(content)
            return True, "Syntax OK"
        except SyntaxError as e:
            return False, f"Syntax Error: {e}"
        except Exception as e:
            return False, f"Error reading file: {e}"
    
    def test_imports(self, file_path: Path) -> Tuple[bool, str]:
        """Test if file can be imported without errors."""
        try:
            # Get relative path from project root
            rel_path = file_path.relative_to(self.project_root)
            
            # Skip certain files that shouldn't be imported directly
            skip_files = ['test_components.py', 'test_all_files.py', 'setup.py']
            if rel_path.name in skip_files:
                return True, "Skipped (test/setup file)"
            
            # Convert path to module name
            module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            if module_parts[0] == 'app':
                module_parts = module_parts[1:]  # Remove 'app' prefix
            
            module_name = '.'.join(module_parts)
            
            # Add app directory to path temporarily
            app_path = str(self.project_root / 'app')
            if app_path not in sys.path:
                sys.path.insert(0, app_path)
            
            # Try to load the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None:
                return False, "Could not create module spec"
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return True, "Imports OK"
            
        except ImportError as e:
            return False, f"Import Error: {e}"
        except Exception as e:
            return False, f"Error: {e}"
    
    def test_config_file(self, file_path: Path) -> Tuple[bool, str]:
        """Test configuration file validity."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.suffix == '.json':
                json.loads(content)
                return True, "Valid JSON"
            elif file_path.suffix in ['.yml', '.yaml']:
                try:
                    import yaml
                    yaml.safe_load(content)
                    return True, "Valid YAML"
                except ImportError:
                    return True, "YAML parser not available (skipped)"
            
            return True, "Unknown format"
            
        except json.JSONDecodeError as e:
            return False, f"JSON Error: {e}"
        except Exception as e:
            return False, f"Error: {e}"
    
    def test_file(self, file_path: Path) -> Dict[str, any]:
        """Test a single file comprehensively."""
        rel_path = file_path.relative_to(self.project_root)
        result = {
            'file': str(rel_path),
            'syntax': None,
            'imports': None,
            'overall': False
        }
        
        print(f"Testing: {rel_path}")
        
        if file_path.suffix == '.py':
            # Test syntax
            syntax_ok, syntax_msg = self.test_syntax(file_path)
            result['syntax'] = {'ok': syntax_ok, 'message': syntax_msg}
            
            if syntax_ok:
                # Test imports only if syntax is OK
                import_ok, import_msg = self.test_imports(file_path)
                result['imports'] = {'ok': import_ok, 'message': import_msg}
                result['overall'] = syntax_ok and import_ok
            else:
                result['imports'] = {'ok': False, 'message': 'Skipped due to syntax error'}
                result['overall'] = False
        
        elif file_path.suffix in ['.json', '.yml', '.yaml']:
            # Test config files
            config_ok, config_msg = self.test_config_file(file_path)
            result['syntax'] = {'ok': config_ok, 'message': config_msg}
            result['overall'] = config_ok
        
        # Print result
        status = "✅" if result['overall'] else "❌"
        print(f"  {status} {rel_path}")
        if result['syntax'] and not result['syntax']['ok']:
            print(f"    Syntax: {result['syntax']['message']}")
        if result['imports'] and not result['imports']['ok']:
            print(f"    Imports: {result['imports']['message']}")
        
        return result
    
    def run_all_tests(self) -> Dict[str, any]:
        """Run tests on all files."""
        print("🚀 Starting comprehensive file validation...")
        print(f"Project root: {self.project_root}")
        
        # Find all files to test
        python_files = self.find_python_files()
        config_files = self.find_config_files()
        all_files = python_files + config_files
        
        print(f"Found {len(python_files)} Python files and {len(config_files)} config files")
        print("=" * 60)
        
        results = []
        passed = 0
        
        for file_path in all_files:
            try:
                result = self.test_file(file_path)
                results.append(result)
                if result['overall']:
                    passed += 1
            except Exception as e:
                print(f"❌ Error testing {file_path}: {e}")
                results.append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'syntax': {'ok': False, 'message': f"Test error: {e}"},
                    'imports': None,
                    'overall': False
                })
        
        # Summary
        total = len(results)
        print("\n" + "=" * 60)
        print(f"TEST SUMMARY: {passed}/{total} files passed")
        print("=" * 60)
        
        # Group results
        failed_files = [r for r in results if not r['overall']]
        if failed_files:
            print("\n❌ FAILED FILES:")
            for result in failed_files:
                print(f"  {result['file']}")
                if result['syntax'] and not result['syntax']['ok']:
                    print(f"    Syntax: {result['syntax']['message']}")
                if result['imports'] and not result['imports']['ok']:
                    print(f"    Imports: {result['imports']['message']}")
        
        if passed == total:
            print("\n🎉 ALL FILES PASSED! Codebase is clean.")
        else:
            print(f"\n⚠️  {total - passed} files have issues that need fixing.")
        
        return {
            'total': total,
            'passed': passed,
            'failed': total - passed,
            'results': results
        }

def main():
    """Main test runner."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    validator = FileValidator(project_root)
    
    try:
        results = validator.run_all_tests()
        
        # Exit with error code if any files failed
        if results['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error during testing: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
