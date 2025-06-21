#!/usr/bin/env python3
"""
🔍 DEBUG PLAN GENERATION
======================
Diagnoses why the revolutionary system isn't generating implementation plans
"""

import json
import traceback
from datetime import datetime

def debug_plan_generation():
    """Debug the plan generation process step by step"""
    
    print("🔍 DEBUGGING REVOLUTIONARY PLAN GENERATION")
    print("=" * 50)
    print(f"⏰ Debug started: {datetime.now()}")
    print()
    
    # Step 1: Test basic import
    print("📦 Step 1: Testing Implementation Generator Import")
    print("-" * 45)
    
    try:
        from implementation_generator import AKSImplementationGenerator
        print("✅ AKSImplementationGenerator imported successfully")
        
        generator = AKSImplementationGenerator()
        print("✅ Generator instance created")
        
        # Check if it's revolutionary or standard
        if hasattr(generator, 'dna_analyzer'):
            print("🚀 REVOLUTIONARY version detected")
            
            # Check each component
            components = [
                ('dna_analyzer', 'DNA Analyzer'),
                ('strategy_generator', 'Strategy Generator'),
                ('command_center', 'Command Center'),
                ('learning_engine', 'Learning Engine'),
                ('plan_generator', 'Plan Generator')
            ]
            
            for attr, name in components:
                if hasattr(generator, attr):
                    component = getattr(generator, attr)
                    print(f"   ✅ {name}: {type(component).__name__}")
                else:
                    print(f"   ❌ {name}: Missing")
        else:
            print("⚠️  STANDARD version detected - revolutionary components missing")
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print(f"📝 Details: {traceback.format_exc()}")
        return False
    
    print()
    
    # Step 2: Test with sample data
    print("🧪 Step 2: Testing Plan Generation with Sample Data")
    print("-" * 48)
    
    # Create sample data that matches your real structure
    sample_analysis = {
        'total_cost': 1864.43,
        'total_savings': 71.11,
        'hpa_savings': 45.50,
        'right_sizing_savings': 18.25,
        'storage_savings': 7.36,
        'node_cost': 1500.00,
        'storage_cost': 200.00,
        'networking_cost': 100.00,
        'control_plane_cost': 50.00,
        'registry_cost': 14.43,
        'other_cost': 0.00,
        'cpu_gap': 35.0,
        'memory_gap': 28.0,
        'hpa_reduction': 25.0,
        'resource_group': 'test-rg',
        'cluster_name': 'test-cluster',
        'has_pod_costs': True,
        'analysis_confidence': 0.85,
        'confidence_level': 'High'
    }
    
    print("📊 Sample analysis data created")
    print(f"   💰 Total Cost: ${sample_analysis['total_cost']}")
    print(f"   💡 Total Savings: ${sample_analysis['total_savings']}")
    print()
    
    try:
        print("🎯 Calling generate_implementation_plan()...")
        plan = generator.generate_implementation_plan(sample_analysis)
        
        print("✅ Plan generation completed!")
        print(f"📋 Plan type: {type(plan)}")
        
        if isinstance(plan, dict):
            print(f"🔧 Plan keys: {list(plan.keys())}")
            
            # Check critical sections
            sections_to_check = [
                'metadata',
                'executive_summary', 
                'implementation_phases',
                'timeline_optimization',
                'intelligence_insights'
            ]
            
            print("\n📋 Section Analysis:")
            for section in sections_to_check:
                if section in plan:
                    section_data = plan[section]
                    if isinstance(section_data, list):
                        print(f"   ✅ {section}: {len(section_data)} items")
                    elif isinstance(section_data, dict):
                        print(f"   ✅ {section}: {len(section_data)} fields")
                    else:
                        print(f"   ✅ {section}: {type(section_data).__name__}")
                else:
                    print(f"   ❌ {section}: Missing")
            
            # Deep dive into implementation_phases
            phases = plan.get('implementation_phases', [])
            print(f"\n🔍 Implementation Phases Deep Dive:")
            print(f"   📊 Number of phases: {len(phases)}")
            
            if len(phases) == 0:
                print("   ❌ NO PHASES GENERATED - This is the problem!")
                
                # Check if there's an error message
                if 'message' in plan:
                    print(f"   📝 Error message: {plan['message']}")
                
                if 'error' in plan:
                    print(f"   ⚠️  Error details: {plan['error']}")
                
                # Check metadata for clues
                metadata = plan.get('metadata', {})
                generation_method = metadata.get('generation_method', 'unknown')
                print(f"   🔧 Generation method: {generation_method}")
                
                if generation_method == 'fallback_mode':
                    print("   🚨 SYSTEM IS IN FALLBACK MODE!")
                    print("   💡 This means the revolutionary components failed to generate phases")
                
            else:
                print("   ✅ Phases found! Let's examine them...")
                for i, phase in enumerate(phases[:3]):  # Check first 3 phases
                    print(f"   📋 Phase {i+1}:")
                    print(f"      Title: {phase.get('title', 'No title')}")
                    print(f"      Duration: {phase.get('duration_weeks', 'Unknown')} weeks")
                    print(f"      Savings: ${phase.get('projected_savings', 0)}")
                    print(f"      Tasks: {len(phase.get('tasks', []))}")
            
            # Check revolutionary features
            print(f"\n🚀 Revolutionary Features Check:")
            
            intelligence = plan.get('intelligence_insights', {})
            if intelligence:
                print("   ✅ Intelligence insights present")
                
                dna = intelligence.get('cluster_dna_analysis', {})
                if dna:
                    personality = dna.get('personality_type', 'unknown')
                    print(f"      🧬 Cluster DNA: {personality}")
                
                strategy = intelligence.get('dynamic_strategy_insights', {})
                if strategy:
                    strategy_type = strategy.get('strategy_type', 'unknown')
                    print(f"      🎯 Strategy: {strategy_type}")
                
                learning = intelligence.get('learning_engine_insights', {})
                if learning:
                    confidence = learning.get('confidence_boost', 0)
                    print(f"      🎓 Learning boost: {confidence}%")
                    
            else:
                print("   ❌ No intelligence insights - revolutionary features not working")
            
        else:
            print(f"❌ Plan is not a dictionary: {plan}")
            
    except Exception as e:
        print(f"❌ Plan Generation Error: {e}")
        print(f"📝 Full traceback:")
        print(traceback.format_exc())
        return False
    
    print()
    
    # Step 3: Check specific components
    print("🔧 Step 3: Testing Individual Revolutionary Components")
    print("-" * 52)
    
    if hasattr(generator, 'dna_analyzer'):
        try:
            print("🧬 Testing DNA Analyzer...")
            dna_result = generator.dna_analyzer.analyze_cluster_dna(sample_analysis)
            print(f"   ✅ DNA Analysis: {dna_result.personality_type} cluster")
        except Exception as e:
            print(f"   ❌ DNA Analyzer Error: {e}")
    
    if hasattr(generator, 'strategy_generator'):
        try:
            print("🎯 Testing Strategy Generator...")
            # This might fail if DNA analyzer failed, but we'll try
            print("   (Skipping - requires DNA analysis)")
        except Exception as e:
            print(f"   ❌ Strategy Generator Error: {e}")
    
    print()
    
    # Step 4: Test JSON serialization
    print("📤 Step 4: Testing JSON Serialization (for API)")
    print("-" * 44)
    
    try:
        json_str = json.dumps(plan, default=str, indent=2)
        print("✅ Plan is JSON serializable")
        
        # Save to file for inspection
        with open('debug_plan_output.json', 'w') as f:
            f.write(json_str)
        print("📁 Plan saved to debug_plan_output.json for inspection")
        
    except Exception as e:
        print(f"❌ JSON Serialization Error: {e}")
    
    print()
    print("🏁 DEBUG SUMMARY")
    print("=" * 20)
    
    phases_count = len(plan.get('implementation_phases', [])) if isinstance(plan, dict) else 0
    
    if phases_count > 0:
        print(f"✅ SUCCESS: {phases_count} phases generated")
        print("🎉 Your revolutionary system is working!")
    else:
        print("❌ ISSUE: No phases generated")
        print("🔧 This is why your UI shows 'No phases found to display'")
        
        # Provide specific fixes
        print("\n💡 LIKELY FIXES:")
        
        if isinstance(plan, dict):
            generation_method = plan.get('metadata', {}).get('generation_method', 'unknown')
            
            if generation_method == 'fallback_mode':
                print("   1. Revolutionary components have errors - check individual component files")
                print("   2. Missing dependencies in revolutionary component imports")
                print("   3. Data validation failing in revolutionary components")
            else:
                print("   1. Check implementation_phases generation logic")
                print("   2. Verify phase creation in revolutionary components")
                print("   3. Check if phases are being filtered out")
        else:
            print("   1. Plan generation returning wrong data type")
            print("   2. Check for exceptions in generate_implementation_plan method")
    
    print(f"\n⏰ Debug completed: {datetime.now()}")
    return phases_count > 0

def test_strategy_generator_properly(analysis_data):
    """Test strategy generator with proper DNA input"""
    try:
        from dna_analyzer import ClusterDNAAnalyzer
        from dynamic_strategy import DynamicStrategyEngine
        
        # Step 1: Get cluster DNA
        dna_analyzer = ClusterDNAAnalyzer()
        cluster_dna = dna_analyzer.analyze_cluster_dna(analysis_data)
        print(f"   🧬 DNA for strategy: {cluster_dna.cluster_personality}")
        
        # Step 2: Test strategy generation
        strategy_engine = DynamicStrategyEngine()
        strategy = strategy_engine.generate_dynamic_strategy(cluster_dna, analysis_data)
        print(f"   ✅ Strategy generated: {strategy.strategy_type}")
        
        return True
    except Exception as e:
        print(f"   ❌ Strategy generation failed: {e}")
        return False

# Use this instead of skipping

if __name__ == "__main__":
    success = debug_plan_generation()
    
    if not success:
        print("\n🚑 IMMEDIATE FIXES TO TRY:")
        print("1. Run this debug script and check the error messages")
        print("2. Verify all 5 revolutionary component files are present and error-free")
        print("3. Check the debug_plan_output.json file for clues")
        print("4. Consider using the simplified fallback version below")