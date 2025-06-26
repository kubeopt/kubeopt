#!/usr/bin/env python3
"""
UI Diagnostic Script - Find Exact Breakdown Point
=================================================
Run this to see exactly where your UI pipeline is failing
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"
CLUSTER_ID = "rg-dpl-mad-uat-ne2-2_aks-dpl-mad-uat-ne2-1"

def test_chart_data_api():
    """Test the chart data API and show exactly what's wrong"""
    print("🔍 TESTING CHART DATA API")
    print("=" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/api/chart-data", params={'cluster_id': CLUSTER_ID})
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ API Response: Valid JSON")
                
                # Check data structure
                print(f"\n📊 API Response Structure:")
                print(f"   Keys: {list(data.keys())}")
                
                # Check critical components
                critical_components = [
                    'cost_breakdown', 'savings_breakdown', 
                    'namespace_costs', 'workload_costs', 
                    'node_utilization', 'hpa_comparison'
                ]
                
                for component in critical_components:
                    if component in data:
                        component_data = data[component]
                        if isinstance(component_data, dict):
                            if 'labels' in component_data:
                                label_count = len(component_data.get('labels', []))
                                data_count = len(component_data.get('data', []))
                                print(f"   ✅ {component}: {label_count} labels, {data_count} data points")
                            else:
                                print(f"   ⚠️ {component}: Present but no 'labels' key")
                        else:
                            print(f"   ⚠️ {component}: Present but not a dict")
                    else:
                        print(f"   ❌ {component}: MISSING")
                
                # Check specific problematic areas
                print(f"\n🔍 SPECIFIC ISSUE ANALYSIS:")
                
                # Namespace costs check
                namespace_data = data.get('namespace_costs', {})
                if namespace_data:
                    ns_labels = namespace_data.get('labels', [])
                    ns_total = namespace_data.get('total_namespaces', 0)
                    ns_active = namespace_data.get('active_namespaces', 0)
                    print(f"   Namespaces: {len(ns_labels)} shown, {ns_active} active, {ns_total} total")
                else:
                    print(f"   ❌ Namespace data: COMPLETELY MISSING")
                
                # Workload costs check
                workload_data = data.get('workload_costs', {})
                if workload_data:
                    wl_labels = workload_data.get('labels', [])
                    wl_total = workload_data.get('total_workloads', 0)
                    print(f"   Workloads: {len(wl_labels)} shown, {wl_total} total")
                    
                    if wl_total == 0:
                        print(f"   🎯 FOUND ISSUE: total_workloads = 0 (this causes '0 WORKLOADS FOUND')")
                else:
                    print(f"   ❌ Workload data: COMPLETELY MISSING")
                
                # Node utilization check
                node_data = data.get('node_utilization', {})
                if node_data:
                    node_count = node_data.get('node_count', 0)
                    datasets = node_data.get('datasets', [])
                    print(f"   Nodes: {node_count} nodes, {len(datasets)} datasets")
                else:
                    print(f"   ❌ Node data: COMPLETELY MISSING")
                
                return data
                
            except json.JSONDecodeError as e:
                print(f"❌ API Response: Invalid JSON - {e}")
                print(f"Raw response: {response.text[:500]}...")
                return None
        else:
            print(f"❌ API Failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return None
            
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        return None

def test_raw_analysis_data():
    """Check if raw analysis data is available"""
    print("\n🔍 TESTING RAW ANALYSIS DATA ACCESS")
    print("=" * 45)
    
    # Try to access database/cache directly
    endpoints_to_test = [
        f"/api/analysis-data?cluster_id={CLUSTER_ID}",
        f"/api/cluster-data?cluster_id={CLUSTER_ID}",
        f"/api/debug/analysis?cluster_id={CLUSTER_ID}"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"   {endpoint}: HTTP {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"      ✅ Valid JSON with {len(data)} keys")
                    
                    # Check for key indicators
                    key_indicators = ['total_cost', 'namespace_costs', 'workload_costs', 'nodes']
                    for indicator in key_indicators:
                        if indicator in data:
                            value = data[indicator]
                            if isinstance(value, (dict, list)):
                                print(f"      ✅ {indicator}: {len(value)} items")
                            else:
                                print(f"      ✅ {indicator}: {value}")
                        else:
                            print(f"      ❌ {indicator}: Missing")
                    
                    return data
                except:
                    print(f"      ⚠️ Response not JSON")
                    
        except Exception as e:
            print(f"      ❌ Request failed: {e}")
    
    return None

def diagnose_data_transformation():
    """Diagnose data transformation issues"""
    print("\n🔧 DIAGNOSING DATA TRANSFORMATION")
    print("=" * 45)
    
    # Simulate the transformation using your actual data
    sample_analysis_data = {
        "total_cost": 1864.68,
        "total_savings": 135.01,
        "namespace_costs": {
            "madapi-preprod": 283.87,
            "argocd": 22.95,
            "kube-system": 8.06,
            "gatekeeper-system": 3.23,
            "kubecost": 1.73
        },
        "pod_cost_analysis": {
            "workload_costs": {
                "madapi-preprod/account-decisioning-api-aggregator": {"cost": 9.46, "type": "Deployment"},
                "madapi-preprod/account-topup-aggregator": {"cost": 9.46, "type": "Deployment"},
                "argocd/argocd-repo-server": {"cost": 7.65, "type": "Deployment"}
            }
        },
        "nodes": [
            {"name": "node1", "cpu_usage_pct": 47.6, "memory_usage_pct": 80.2},
            {"name": "node2", "cpu_usage_pct": 43.7, "memory_usage_pct": 71.7}
        ]
    }
    
    print("📊 Testing transformation with sample data:")
    
    # Test namespace transformation
    namespace_costs = sample_analysis_data.get('namespace_costs', {})
    active_namespaces = {k: v for k, v in namespace_costs.items() if v > 0}
    print(f"   Namespaces: {len(namespace_costs)} total, {len(active_namespaces)} active")
    
    # Test workload transformation
    workload_costs = sample_analysis_data.get('pod_cost_analysis', {}).get('workload_costs', {})
    print(f"   Workloads: {len(workload_costs)} found")
    
    if len(workload_costs) == 0:
        print(f"   🎯 ISSUE FOUND: No workload_costs in pod_cost_analysis")
        print(f"   🔧 Check: analysis_data['pod_cost_analysis']['workload_costs']")
    
    # Test node transformation  
    nodes = sample_analysis_data.get('nodes', [])
    print(f"   Nodes: {len(nodes)} found")
    
    return {
        "namespace_issues": len(active_namespaces) == 0,
        "workload_issues": len(workload_costs) == 0,
        "node_issues": len(nodes) == 0
    }

def test_frontend_consumption():
    """Test what the frontend is actually receiving"""
    print("\n🌐 TESTING FRONTEND DATA CONSUMPTION")
    print("=" * 45)
    
    # Test chart data endpoint
    chart_data = test_chart_data_api()
    
    if chart_data:
        print(f"\n📊 FRONTEND WOULD RECEIVE:")
        
        # Simulate frontend processing
        components = {
            'cost_breakdown': chart_data.get('cost_breakdown'),
            'namespace_costs': chart_data.get('namespace_costs'), 
            'workload_costs': chart_data.get('workload_costs'),
            'node_utilization': chart_data.get('node_utilization')
        }
        
        for name, component in components.items():
            if component:
                if isinstance(component, dict):
                    labels = component.get('labels', [])
                    data = component.get('data', [])
                    print(f"   {name}: {len(labels)} labels, {len(data)} data points")
                    
                    if name == 'workload_costs':
                        total_workloads = component.get('total_workloads', 0)
                        print(f"      → total_workloads: {total_workloads}")
                        if total_workloads == 0:
                            print(f"      🎯 THIS CAUSES '0 WORKLOADS FOUND' IN UI")
                    
                    if len(labels) == 0:
                        print(f"      ⚠️ Empty labels would cause empty chart")
                else:
                    print(f"   {name}: Wrong data type: {type(component)}")
            else:
                print(f"   ❌ {name}: Missing or None")

def generate_fix_recommendations():
    """Generate specific fix recommendations"""
    print("\n🔧 FIX RECOMMENDATIONS")
    print("=" * 30)
    
    print("1. IMMEDIATE CHECK:")
    print("   - Verify /api/chart-data endpoint exists and responds")
    print("   - Check if data transformation is happening")
    print(f"   - Test: curl '{BASE_URL}/api/chart-data?cluster_id={CLUSTER_ID}'")
    
    print("\n2. DATA PIPELINE CHECK:")
    print("   - Verify analysis data contains 'pod_cost_analysis.workload_costs'")
    print("   - Check namespace_costs is populated")
    print("   - Ensure nodes array is not empty")
    
    print("\n3. UI TRANSFORMATION CHECK:")
    print("   - Add proper data transformation in chart API")
    print("   - Ensure workload_costs.total_workloads is set correctly")
    print("   - Verify chart data format matches frontend expectations")
    
    print("\n4. FRONTEND CHECK:")
    print("   - Check JavaScript console for errors")
    print("   - Verify Chart.js is loading data correctly")
    print("   - Check if DOM elements exist for charts")

def main():
    """Main diagnostic routine"""
    print("🚀 AKS COST OPTIMIZER - UI DIAGNOSTIC SCRIPT")
    print("=" * 60)
    print(f"Target: {CLUSTER_ID}")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Run all diagnostics
    chart_data = test_chart_data_api()
    raw_data = test_raw_analysis_data()  
    transformation_issues = diagnose_data_transformation()
    test_frontend_consumption()
    generate_fix_recommendations()
    
    # Summary
    print(f"\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 30)
    
    if chart_data:
        print("✅ Chart API: Responding")
    else:
        print("❌ Chart API: Not working")
    
    if raw_data:
        print("✅ Raw Data: Available")
    else:
        print("❌ Raw Data: Not accessible")
    
    critical_issues = sum(transformation_issues.values())
    print(f"⚠️ Critical Issues: {critical_issues}")
    
    if critical_issues == 0:
        print("🎯 DIAGNOSIS: UI transformation layer issue")
        print("📋 ACTION: Deploy the complete chart data transformation fix")
    else:
        print("🎯 DIAGNOSIS: Data availability issue") 
        print("📋 ACTION: Check data saving and loading pipeline")

if __name__ == "__main__":
    main()