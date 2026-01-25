#!/usr/bin/env python3
"""
Check for field violations in warning mode
Run analysis and collect all field violations without failing
"""

import sys
import logging
from shared.interfaces.data_contract import DataContractDict

def main():
    """Enable warning mode and report violations after analysis"""
    
    # Setup logging to see warnings
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Enable warning mode
    print("📋 Enabling warning mode for field violations...")
    DataContractDict.set_enforcement_mode("warning")
    DataContractDict.clear_violations()
    
    print("⚠️  Field violations will be logged but not cause failures")
    print("🔍 Run your analysis now to collect all violations")
    print("\n" + "="*60)
    print("After analysis completes, run this script again with --report")
    print("to see all collected violations")
    print("="*60 + "\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        violations = DataContractDict.get_collected_violations()
        if violations:
            print(f"\n🚨 Found {len(violations)} field violations:")
            print("="*60)
            for field in violations:
                print(f"  - {field}")
            print("="*60)
            print("\n📝 Add these fields to data_contract.py:")
            for field in violations:
                field_upper = field.upper()
                print(f"    {field_upper} = '{field}'")
            print("\n✅ Then switch back to strict mode:")
            print("    DataContractDict.set_enforcement_mode('strict')")
        else:
            print("✅ No field violations found!")

if __name__ == "__main__":
    main()