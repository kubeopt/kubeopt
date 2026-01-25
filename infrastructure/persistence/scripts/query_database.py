#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

#!/usr/bin/env python3
"""
View the complete raw implementation plan object from the database
"""

import sqlite3
import json
import sys
from datetime import datetime
import pprint

def view_raw_implementation_plan(db_path='app/data/database/clusters.db', cluster_id=None, output_format='pretty'):
    """View the complete raw implementation plan object"""
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if cluster_id is not None and cluster_id:
                cursor = conn.execute('''
                    SELECT id, name, analysis_data, last_analyzed 
                    FROM clusters 
                    WHERE id = ? AND analysis_data IS NOT NULL
                ''', (cluster_id,))
                clusters = cursor.fetchall()
            else:
                # Get the most recently analyzed cluster
                cursor = conn.execute('''
                    SELECT id, name, analysis_data, last_analyzed 
                    FROM clusters 
                    WHERE analysis_data IS NOT NULL 
                    ORDER BY last_analyzed DESC 
                    LIMIT 1
                ''')
                clusters = cursor.fetchall()
            
            if not clusters:
                print("❌ No clusters found with analysis data")
                return
            
            for cluster in clusters:
                print(f"\n{'='*80}")
                print(f"🔍 COMPLETE RAW IMPLEMENTATION PLAN")
                print(f"Cluster: {cluster['name']} ({cluster['id']})")
                print(f"Last Analyzed: {cluster['last_analyzed']}")
                print(f"{'='*80}")
                
                try:
                    analysis_data = json.loads(cluster['analysis_data'])
                    
                    if 'implementation_plan' not in analysis_data:
                        print("❌ No implementation plan found in analysis data")
                        print(f"Available keys: {list(analysis_data.keys())}")
                        return
                    
                    implementation_plan = analysis_data['implementation_plan']
                    
                    print(f"\n📊 IMPLEMENTATION PLAN OVERVIEW:")
                    print(f"   Type: {type(implementation_plan).__name__}")
                    if isinstance(implementation_plan, dict):
                        print(f"   Keys: {len(implementation_plan)}")
                        print(f"   Size: {len(json.dumps(implementation_plan))} characters")
                    
                    if output_format == 'json':
                        print(f"\n📄 RAW JSON:")
                        print("="*80)
                        print(json.dumps(implementation_plan, indent=2, default=str))
                        
                    elif output_format == 'pretty':
                        print(f"\n📄 PRETTY FORMATTED:")
                        print("="*80)
                        pprint.pprint(implementation_plan, width=100, depth=10)
                        
                    elif output_format == 'structured':
                        print_structured_plan(implementation_plan)
                        
                    elif output_format == 'keys':
                        print_keys_analysis(implementation_plan)
                        
                    elif output_format == 'all':
                        print_keys_analysis(implementation_plan)
                        print(f"\n{'='*80}")
                        print("📄 STRUCTURED VIEW:")
                        print_structured_plan(implementation_plan)
                        print(f"\n{'='*80}")
                        print("📄 RAW JSON:")
                        print(json.dumps(implementation_plan, indent=2, default=str))
                
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to decode analysis data: {e}")
                except Exception as e:
                    print(f"❌ Error processing cluster data: {e}")
                    import traceback
                    traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Database error: {e}")

def print_keys_analysis(plan, prefix="", level=0):
    """Recursively analyze the structure of the implementation plan"""
    
    if level == 0:
        print(f"\n🔍 COMPLETE STRUCTURE ANALYSIS:")
        print("-" * 60)
    
    indent = "  " * level
    
    if isinstance(plan, dict):
        for key, value in plan.items():
            if isinstance(value, dict):
                print(f"{indent}{prefix}{key}: dict({len(value)} keys)")
                if level < 3:  # Limit depth
                    print_keys_analysis(value, f"{key}.", level + 1)
            elif isinstance(value, list):
                print(f"{indent}{prefix}{key}: list({len(value)} items)")
                if len(value) > 0 and level < 2:
                    print(f"{indent}  └─ Sample item type: {type(value[0]).__name__}")
                    if isinstance(value[0], dict):
                        print(f"{indent}     Sample keys: {list(value[0].keys())}")
            else:
                value_str = str(value)[:50] + ("..." if len(str(value)) > 50 else "")
                print(f"{indent}{prefix}{key}: {type(value).__name__} = {value_str}")
    
    elif isinstance(plan, list):
        print(f"{indent}{prefix}list({len(plan)} items)")
        for i, item in enumerate(plan[:3]):  # Show first 3 items
            print(f"{indent}  [{i}]: {type(item).__name__}")
            if isinstance(item, dict) and level < 2:
                print_keys_analysis(item, f"[{i}].", level + 1)

def print_structured_plan(plan):
    """Print the implementation plan in a structured, readable format"""
    
    print(f"\n🏗️ STRUCTURED IMPLEMENTATION PLAN:")
    print("-" * 60)
    
    # Metadata
    if 'metadata' in plan:
        metadata = plan['metadata']
        print(f"\n📋 METADATA:")
        for key, value in metadata.items():
            print(f"   {key}: {value}")
    
    # Executive Summary
    if 'executive_summary' in plan:
        exec_summary = plan['executive_summary']
        print(f"\n💰 EXECUTIVE SUMMARY:")
        
        for key, value in exec_summary.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, float):
                        if 'cost' in sub_key.lower() or 'savings' in sub_key.lower():
                            print(f"      {sub_key}: ${sub_value:.2f}")
                        elif 'percentage' in sub_key.lower():
                            print(f"      {sub_key}: {sub_value:.2f}%")
                        else:
                            print(f"      {sub_key}: {sub_value}")
                    else:
                        print(f"      {sub_key}: {sub_value}")
            else:
                print(f"   {key}: {value}")
    
    # Implementation Phases
    if 'implementation_phases' in plan:
        phases = plan['implementation_phases']
        print(f"\n📅 IMPLEMENTATION PHASES ({len(phases)} phases):")
        
        for i, phase in enumerate(phases, 1):
            phase_name = phase.get('title', phase.get('phase_name', f'Phase {i}'))
            print(f"\n   PHASE {i}: {phase_name}")
            
            # Basic phase info
            for key in ['duration_weeks', 'risk_level', 'projected_savings', 'complexity_level']:
                if key in phase:
                    value = phase[key]
                    if key == 'projected_savings' and isinstance(value, (int, float)):
                        print(f"      {key}: ${value:.2f}/month")
                    else:
                        print(f"      {key}: {value}")
            
            # Tasks/Actions
            if 'tasks' in phase:
                tasks = phase['tasks']
                print(f"      tasks ({len(tasks)} items):")
                for j, task in enumerate(tasks, 1):
                    if isinstance(task, dict):
                        task_desc = task.get('task', task.get('description', f'Task {j}'))
                        print(f"         {j}. {task_desc}")
                        if 'command' in task:
                            print(f"            Command: {task['command']}")
                    else:
                        print(f"         {j}. {task}")
            
            # Success Criteria
            if 'success_criteria' in phase:
                criteria = phase['success_criteria']
                print(f"      success_criteria ({len(criteria)} items):")
                for criterion in criteria:
                    print(f"         ✓ {criterion}")
    
    # Other sections
    other_sections = [
        'timeline_optimization', 'risk_mitigation', 'monitoring_strategy',
        'governance_framework', 'success_criteria', 'contingency_planning',
        'intelligence_insights', 'executable_commands', 'cost_protection'
    ]
    
    for section in other_sections:
        if section in plan:
            section_data = plan[section]
            print(f"\n🔧 {section.upper().replace('_', ' ')}:")
            
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    if isinstance(value, (list, dict)):
                        print(f"   {key}: {type(value).__name__}({len(value)})")
                    else:
                        value_str = str(value)[:100] + ("..." if len(str(value)) > 100 else "")
                        print(f"   {key}: {value_str}")
            else:
                print(f"   {section_data}")

def save_to_file(db_path='app/data/database/clusters.db', cluster_id=None, output_file=None):
    """Save the raw implementation plan to a file"""
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if cluster_id is not None and cluster_id:
                cursor = conn.execute('''
                    SELECT id, name, analysis_data 
                    FROM clusters 
                    WHERE id = ? AND analysis_data IS NOT NULL
                ''', (cluster_id,))
            else:
                cursor = conn.execute('''
                    SELECT id, name, analysis_data 
                    FROM clusters 
                    WHERE analysis_data IS NOT NULL 
                    ORDER BY last_analyzed DESC 
                    LIMIT 1
                ''')
            
            cluster = cursor.fetchone()
            if not cluster:
                print("❌ No cluster found")
                return
            
            analysis_data = json.loads(cluster['analysis_data'])
            implementation_plan = analysis_data.get('implementation_plan', {})
            
            if not output_file:
                output_file = f"implementation_plan_{cluster['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(output_file, 'w') as f:
                json.dump(implementation_plan, f, indent=2, default=str)
            
            print(f"✅ Implementation plan saved to: {output_file}")
            print(f"📊 Size: {len(json.dumps(implementation_plan))} characters")
            
    except Exception as e:
        print(f"❌ Error saving to file: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='View complete raw implementation plan from database')
    parser.add_argument('--cluster', '-c', help='Specific cluster ID to view')
    parser.add_argument('--db', '-d', default='app/data/database/clusters.db', help='Database path')
    parser.add_argument('--format', '-f', choices=['pretty', 'json', 'structured', 'keys', 'all'], 
                       default='structured', help='Output format')
    parser.add_argument('--save', '-s', help='Save to file (specify filename)')
    parser.add_argument('--save-auto', action='store_true', help='Save to auto-generated filename')
    
    args = parser.parse_args()
    
    if args.save or args.save_auto:
        save_to_file(args.db, args.cluster, args.save if args.save else None)
    else:
        view_raw_implementation_plan(args.db, args.cluster, args.format)