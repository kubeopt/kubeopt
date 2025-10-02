#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

#!/usr/bin/env python3
"""
Check how implementation plan is being saved in analysis_data
"""

import sqlite3
import json
import sys
from datetime import datetime

def check_implementation_plan_saving_process():
    """Analyze how implementation plans are being saved"""
    
    print("🔍 CHECKING IMPLEMENTATION PLAN SAVING PROCESS")
    print("=" * 60)
    
    # From your cluster_database.py, here's the relevant code analysis:
    
    print("\n📋 CODE ANALYSIS FROM cluster_database.py:")
    print("-" * 40)
    
    print("✅ In update_cluster_analysis() method:")
    print("   1. Enhanced analysis data is created")
    print("   2. Node data flags are set")
    print("   3. CRITICAL: Implementation plan generation happens HERE:")
    print("      ```python")
    print("      if 'implementation_plan' not in enhanced_analysis_data:")
    print("          try:")
    print("              from machine_learning.implementation_generator import AKSImplementationGenerator")
    print("              implementation_generator = AKSImplementationGenerator()")
    print("              implementation_plan = implementation_generator.generate_implementation_plan(enhanced_analysis_data)")
    print("              enhanced_analysis_data['implementation_plan'] = implementation_plan")
    print("      ```")
    print("   4. Data is serialized using serialize_implementation_plan()")
    print("   5. Saved to database in analysis_data field")
    
    print("\n✅ In get_latest_analysis() method:")
    print("   1. Retrieves analysis_data from database")
    print("   2. Uses deserialize_implementation_plan() to reconstruct")
    print("   3. Validates implementation plan structure")
    
    print("\n🚨 POTENTIAL ISSUES IDENTIFIED:")
    print("-" * 40)
    print("1. IMPORT FAILURE:")
    print("   - If 'app.ml.implementation_generator' import fails")
    print("   - Implementation plan generation is skipped silently")
    print("   - Empty or template plan might be created")
    
    print("\n2. GENERATOR EXCEPTION:")
    print("   - If generate_implementation_plan() raises exception")
    print("   - Error is logged but process continues")
    print("   - Partial or broken plan might be saved")
    
    print("\n3. SERIALIZATION ISSUES:")
    print("   - Complex objects might not serialize properly")
    print("   - Implementation plan structure could be corrupted")
    
    print("\n4. DATA QUALITY ISSUES:")
    print("   - If enhanced_analysis_data lacks required fields")
    print("   - Generator might create template/empty plan")

def check_actual_saving_in_database(db_path='app/data/database/clusters.db'):
    """Check what's actually being saved in the database"""
    
    print(f"\n📊 CHECKING ACTUAL DATABASE CONTENT:")
    print("-" * 40)
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get recent clusters with analysis data
            cursor = conn.execute('''
                SELECT id, name, last_analyzed, last_cost, last_savings,
                       length(analysis_data) as data_size
                FROM clusters 
                WHERE analysis_data IS NOT NULL 
                ORDER BY last_analyzed DESC 
                LIMIT 3
            ''')
            
            clusters = cursor.fetchall()
            
            for cluster in clusters:
                print(f"\n🏗️ CLUSTER: {cluster['name']}")
                print(f"   ID: {cluster['id']}")
                print(f"   Last Analyzed: {cluster['last_analyzed']}")
                print(f"   Data Size: {cluster['data_size']:,} bytes")
                print(f"   Cost: ${cluster['last_cost']:.2f}, Savings: ${cluster['last_savings']:.2f}")
                
                # Get the actual analysis data
                detail_cursor = conn.execute('''
                    SELECT analysis_data FROM clusters WHERE id = ?
                ''', (cluster['id'],))
                
                row = detail_cursor.fetchone()
                if row and row['analysis_data']:
                    try:
                        analysis_data = json.loads(row['analysis_data'])
                        
                        print(f"   📋 Analysis Data Keys: {len(analysis_data)} total")
                        
                        # Check implementation plan specifically
                        if 'implementation_plan' in analysis_data:
                            impl_plan = analysis_data['implementation_plan']
                            print(f"   ✅ Implementation Plan: EXISTS")
                            print(f"      Type: {type(impl_plan).__name__}")
                            
                            if isinstance(impl_plan, dict):
                                print(f"      Keys: {list(impl_plan.keys())}")
                                print(f"      Size: {len(json.dumps(impl_plan)):,} bytes")
                                
                                # Check critical sections
                                critical_sections = [
                                    'executive_summary', 'implementation_phases', 
                                    'resource_recommendations', 'risk_assessment'
                                ]
                                
                                for section in critical_sections:
                                    if section in impl_plan:
                                        data = impl_plan[section]
                                        if isinstance(data, dict):
                                            print(f"      ✅ {section}: {len(data)} fields")
                                        elif isinstance(data, list):
                                            print(f"      ✅ {section}: {len(data)} items")
                                        else:
                                            print(f"      ⚠️ {section}: {type(data).__name__}")
                                    else:
                                        print(f"      ❌ {section}: MISSING")
                                
                                # Check if it's a template/empty plan
                                exec_summary = impl_plan.get('executive_summary', {})
                                if isinstance(exec_summary, dict):
                                    has_cost_data = any(key in exec_summary for key in 
                                                      ['current_monthly_cost', 'total_monthly_savings', 'optimized_monthly_cost'])
                                    print(f"      💰 Has Cost Data: {has_cost_data}")
                                    
                                    if not has_cost_data:
                                        print(f"      🚨 ISSUE: Executive summary missing cost fields")
                                        print(f"         Available keys: {list(exec_summary.keys())}")
                                
                                # Check phases
                                phases = impl_plan.get('implementation_phases', [])
                                if isinstance(phases, list) and len(phases) > 0:
                                    first_phase = phases[0]
                                    if isinstance(first_phase, dict):
                                        has_name = 'phase_name' in first_phase or 'title' in first_phase
                                        has_actions = 'actions' in first_phase or 'tasks' in first_phase
                                        print(f"      📋 Phase Structure: Name={has_name}, Actions={has_actions}")
                                        
                                        if not has_name:
                                            print(f"      🚨 ISSUE: Phases missing proper names")
                                            print(f"         First phase keys: {list(first_phase.keys())}")
                            else:
                                print(f"      🚨 ISSUE: Implementation plan is not a dict")
                        else:
                            print(f"   ❌ Implementation Plan: MISSING")
                            
                            # Check if generation failed
                            error_indicators = ['errors', 'implementation_errors', 'generator_errors']
                            for indicator in error_indicators:
                                if indicator in analysis_data:
                                    print(f"      🚨 Found {indicator}: {analysis_data[indicator]}")
                        
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON Decode Error: {e}")
                    except Exception as e:
                        print(f"   ❌ Analysis Error: {e}")
                else:
                    print(f"   ❌ No analysis data found")
    
    except Exception as e:
        print(f"❌ Database error: {e}")

def check_implementation_generator_availability():
    """Check if the implementation generator is available and working"""
    
    print(f"\n🔧 CHECKING IMPLEMENTATION GENERATOR:")
    print("-" * 40)
    
    try:
        from machine_learning.implementation_generator import AKSImplementationGenerator
        print("✅ Implementation generator import: SUCCESS")
        
        try:
            generator = AKSImplementationGenerator()
            print("✅ Implementation generator instantiation: SUCCESS")
            
            # Test with minimal data
            test_data = {
                'total_cost': 1000.0,
                'total_savings': 100.0,
                'nodes': [{'name': 'test-node', 'cpu_usage_pct': 50}],
                'hpa_recommendations': {'optimization_recommendation': {'min_replicas': 2}}
            }
            
            try:
                test_plan = generator.generate_implementation_plan(test_data)
                print("✅ Implementation plan generation: SUCCESS")
                print(f"   Generated plan type: {type(test_plan).__name__}")
                
                if isinstance(test_plan, dict):
                    print(f"   Plan keys: {list(test_plan.keys())}")
                    
                    # Check if it has proper structure
                    if 'executive_summary' in test_plan:
                        exec_sum = test_plan['executive_summary']
                        if isinstance(exec_sum, dict):
                            has_costs = any(key in exec_sum for key in 
                                          ['current_monthly_cost', 'total_monthly_savings'])
                            print(f"   Executive summary has costs: {has_costs}")
                        
            except Exception as gen_error:
                print(f"❌ Implementation plan generation: FAILED")
                print(f"   Error: {gen_error}")
                import traceback
                traceback.print_exc()
        
        except Exception as init_error:
            print(f"❌ Implementation generator instantiation: FAILED")
            print(f"   Error: {init_error}")
    
    except ImportError as import_error:
        print(f"❌ Implementation generator import: FAILED")
        print(f"   Error: {import_error}")
        print(f"   🚨 This is likely the root cause!")
        print(f"   The implementation generator is not being imported successfully")

def provide_recommendations():
    """Provide specific recommendations based on findings"""
    
    print(f"\n💡 RECOMMENDATIONS:")
    print("=" * 60)
    
    print("1. CHECK IMPLEMENTATION GENERATOR:")
    print("   cd app/ml/")
    print("   python -c \"from implementation_generator import AKSImplementationGenerator; print('Import works')\"")
    
    print("\n2. TEST PLAN GENERATION:")
    print("   python -c \"")
    print("   from machine_learning.implementation_generator import AKSImplementationGenerator")
    print("   gen = AKSImplementationGenerator()")
    print("   plan = gen.generate_implementation_plan({'total_cost': 1000, 'total_savings': 100})")
    print("   print('Plan keys:', list(plan.keys()) if isinstance(plan, dict) else 'Not a dict')")
    print("   \"")
    
    print("\n3. CHECK ANALYSIS LOGS:")
    print("   Look for error messages during analysis, especially:")
    print("   - Import errors for implementation_generator")
    print("   - Exceptions during generate_implementation_plan()")
    print("   - Serialization errors")
    
    print("\n4. MANUAL FIX:")
    print("   If generator is broken, use the fix script I provided earlier:")
    print("   python fix_implementation_plan.py --cluster <cluster_id>")

if __name__ == "__main__":
    check_implementation_plan_saving_process()
    check_actual_saving_in_database()
    check_implementation_generator_availability()
    provide_recommendations()