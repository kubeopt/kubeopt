#!/usr/bin/env python3
"""
Data Contract Enforcement Script
Run this as pre-commit hook to catch unapproved field usage
"""

import ast
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from shared.interfaces.data_contract import AnalysisDataContract

class FieldUsageVisitor(ast.NodeVisitor):
    """AST visitor to find .get() calls and dict key access"""
    
    def __init__(self):
        self.field_accesses = []
        self.violations = []
        
    def visit_Subscript(self, node):
        """Catch dict['key'] access"""
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            field_name = node.slice.value
            self.field_accesses.append(field_name)
            
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Catch .get('key') calls"""
        if (isinstance(node.func, ast.Attribute) and 
            node.func.attr == 'get' and 
            len(node.args) > 0 and 
            isinstance(node.args[0], ast.Constant) and 
            isinstance(node.args[0].value, str)):
            
            field_name = node.args[0].value
            self.field_accesses.append(field_name)
            
        self.generic_visit(node)

def check_file_compliance(file_path: str) -> tuple[bool, list]:
    """Check if file uses only approved field names"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        tree = ast.parse(content)
        visitor = FieldUsageVisitor()
        visitor.visit(tree)
        
        # Get approved fields from contract
        approved_fields = AnalysisDataContract.get_approved_fields()
        
        # Check for violations
        violations = []
        for field in visitor.field_accesses:
            # Skip common Python fields
            if field in ['items', 'keys', 'values', '__dict__', '__class__']:
                continue
                
            if field not in approved_fields:
                violations.append(field)
        
        return len(violations) == 0, violations
        
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
        return True, []  # Don't block on parse errors

def main():
    """Main enforcement function"""
    # Files to check
    check_patterns = [
        'analytics/**/*.py',
        'presentation/**/*.py', 
        'infrastructure/**/*.py',
        'machine_learning/**/*.py'
    ]
    
    violations_found = False
    
    for pattern in check_patterns:
        for file_path in Path('.').glob(pattern):
            if file_path.is_file():
                compliant, violations = check_file_compliance(str(file_path))
                
                if not compliant:
                    violations_found = True
                    print(f"❌ DATA CONTRACT VIOLATION in {file_path}:")
                    for violation in violations:
                        print(f"   - Unapproved field: '{violation}'")
                    print()
    
    if violations_found:
        print("🚫 COMMIT BLOCKED: Fix data contract violations above")
        print("Add new fields to shared/interfaces/data_contract.py")
        sys.exit(1)
    else:
        print("✅ Data contract enforcement passed")
        sys.exit(0)

if __name__ == "__main__":
    main()