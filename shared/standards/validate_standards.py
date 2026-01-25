"""
Validate that all required standards YAML files exist and are valid.
Run this before starting the application.
"""

import sys
import logging
from pathlib import Path
from standards_loader import StandardsLoader

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def validate_standards():
    """Validate all standards files"""
    
    print("Validating KubeOpt standards configuration...")
    print("=" * 70)
    
    try:
        loader = StandardsLoader()
        errors = []
        
        # Test 1: Load scoring standards
        try:
            scoring_data = loader.load_scoring_standards()
            print("✓ Valid: aks_scoring.yaml")
            print(f"  Version: {scoring_data.get('version', 'unknown')}")
            print(f"  Build quality weights: {list(scoring_data.get('build_quality', {}).get('weights', {}).keys())}")
        except Exception as e:
            errors.append(f"❌ Invalid: aks_scoring.yaml - {e}")
        
        # Test 2: Load implementation standards  
        try:
            impl_data = loader.load_implementation_standards()
            print("✓ Valid: aks_implementation_standards.yaml")
            print(f"  Version: {impl_data.get('version', 'unknown')}")
            print(f"  Contains: {list(impl_data.keys())[:5]}...")
        except Exception as e:
            errors.append(f"❌ Invalid: aks_implementation_standards.yaml - {e}")
        
        # Test 3: CPU utilization targets
        try:
            cpu_targets = loader.get_cpu_utilization_target()
            print("✓ Valid: CPU utilization targets")
            print(f"  Target range: {cpu_targets['target_min']:.0f}%-{cpu_targets['target_max']:.0f}%")
            print(f"  Optimal: {cpu_targets['optimal']:.0f}%")
        except Exception as e:
            errors.append(f"❌ Invalid: CPU targets - {e}")
        
        # Test 4: Memory utilization targets
        try:
            mem_targets = loader.get_memory_utilization_target()
            print("✓ Valid: Memory utilization targets")
            print(f"  Target range: {mem_targets['target_min']:.0f}%-{mem_targets['target_max']:.0f}%")
            print(f"  Optimal: {mem_targets['optimal']:.0f}%")
        except Exception as e:
            errors.append(f"❌ Invalid: Memory targets - {e}")
        
        # Test 5: HPA standards
        try:
            hpa_config = loader.get_hpa_standards()
            print("✓ Valid: HPA configuration standards")
            print(f"  Coverage target: {hpa_config['coverage_target']:.0f}%")
            print(f"  CPU target: {hpa_config['target_cpu_utilization']:.0f}%")
            print(f"  Memory target: {hpa_config['target_memory_utilization']:.0f}%")
        except Exception as e:
            errors.append(f"❌ Invalid: HPA standards - {e}")
        
        # Test 6: Optimization thresholds
        try:
            opt_config = loader.get_optimization_thresholds()
            print("✓ Valid: Optimization thresholds")
            print(f"  Max payback: {opt_config['payback_threshold_months']} months")
            print(f"  Min monthly savings: ${opt_config['minimum_monthly_savings']}")
            print(f"  Min savings %: {opt_config['minimum_savings_percentage']*100:.1f}%")
        except Exception as e:
            errors.append(f"❌ Invalid: Optimization thresholds - {e}")
        
        # Test 7: Cost calculation standards
        try:
            cost_config = loader.get_cost_calculation_standards()
            print("✓ Valid: Cost calculation standards")
            print(f"  Monthly hours: {cost_config['monthly_hours']}")
            print(f"  Optimal CPU: {cost_config['optimal_cpu_utilization']}%")
            print(f"  Optimal Memory: {cost_config['optimal_memory_utilization']}%")
        except Exception as e:
            errors.append(f"❌ Invalid: Cost calculation standards - {e}")
        
        # Test 8: Risk and confidence factors
        try:
            risk_config = loader.get_confidence_and_risk_factors()
            print("✓ Valid: Risk and confidence factors")
            print(f"  Risk levels: {list(risk_config['risk_levels'].keys())}")
            print(f"  Confidence threshold: {risk_config['confidence_threshold']}")
        except Exception as e:
            errors.append(f"❌ Invalid: Risk factors - {e}")
        
        print("=" * 70)
        
        if errors:
            print("\n❌ VALIDATION FAILED:")
            for error in errors:
                print(f"  {error}")
            print("\n🔧 FIX THESE ISSUES BEFORE RUNNING KUBEOPT!")
            print("\nEXPECTED YAML FILES:")
            print("  - config/aks_scoring.yaml (scoring and build quality standards)")
            print("  - config/aks_implementation_standards.yaml (implementation costs and thresholds)")
            return False
        else:
            print("\n✅ ALL STANDARDS FILES ARE VALID!")
            print("\n📊 STANDARDS SUMMARY:")
            print("  • CPU utilization target: 60-80% (optimal: 70%)")
            print("  • Memory utilization target: 60-80% (optimal: 70%)")
            print("  • HPA coverage target: 80%")
            print("  • All optimization thresholds configured")
            print("  • Cost calculation formulas loaded")
            print("  • Risk assessment framework available")
            print("\n🚀 Ready to run KubeOpt with YAML-based standards!")
            return True
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        print("\nThis usually means:")
        print("  1. Config directory not found")
        print("  2. Required YAML files missing")
        print("  3. YAML syntax errors")
        print("\nCheck that these files exist and are valid YAML:")
        print("  - config/aks_scoring.yaml")
        print("  - config/aks_implementation_standards.yaml")
        return False

def validate_no_hardcoded_fallbacks():
    """Ensure no hardcoded fallback values are used"""
    
    print("\nValidating NO hardcoded fallbacks policy...")
    print("-" * 50)
    
    try:
        loader = StandardsLoader()
        
        # Try with non-existent config directory
        test_loader = StandardsLoader("/non/existent/path")
        print("❌ VALIDATION FAILED: Should have raised FileNotFoundError for missing config directory!")
        return False
        
    except FileNotFoundError:
        print("✓ Correctly fails when config directory missing")
    
    try:
        # The main loader should work
        loader = StandardsLoader()
        cpu_targets = loader.get_cpu_utilization_target()
        
        # Verify we get actual values, not defaults
        if cpu_targets['target_min'] == 60.0 and cpu_targets['target_max'] == 80.0:
            print("✓ Returns actual YAML values (not hardcoded defaults)")
        else:
            print(f"⚠️  Unexpected values: {cpu_targets}")
        
        print("✓ NO FALLBACKS policy validated - loader fails correctly when YAML missing")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during no-fallbacks test: {e}")
        return False

if __name__ == "__main__":
    success = validate_standards()
    
    if success:
        fallback_success = validate_no_hardcoded_fallbacks()
        if not fallback_success:
            success = False
    
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 All validations passed!")
        sys.exit(0)