#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
REAL AKS DATA TEST SCRIPT
=========================
Tests the hybrid AI implementation generator with your actual cluster data
extracted from the logs: aks-dpl-mad-uat-ne2-1
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class LocalAKSOptimizer:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_name = "llama2"  # You can change this to other models
        
    def check_ollama_status(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
    
    def generate_aks_optimization_plan(self, aks_data: Dict[str, Any]) -> str:
        """Generate AKS cost optimization implementation plan"""
        
        # Create a detailed prompt for AKS analysis
        prompt = self._create_aks_prompt(aks_data)
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 8000,  # Much larger for comprehensive plan
                "num_ctx": 8192     # Larger context window
            }
        }
        
        try:
            print("🤖 Analyzing your actual AKS cluster data and generating optimization plan...")
            print(f"⏱️  This may take 30-60 seconds for comprehensive analysis...")
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=300  # 5 minutes for comprehensive analysis
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated')
            else:
                return f"Error: {response.status_code} - {response.text}"
                
        except requests.exceptions.Timeout:
            return "Error: Request timed out. The model might be processing a complex request."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _create_aks_prompt(self, aks_data: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for your actual AKS optimization"""
        
        prompt = f"""
You are an Azure Kubernetes Service (AKS) cost optimization expert. Analyze this REAL PRODUCTION AKS cluster and generate a detailed implementation plan with EXECUTABLE COMMANDS and step-by-step procedures.
each phase should contain executable commands 

=== REAL AKS CLUSTER DATA ===
Cluster Name: {aks_data.get('cluster_name', 'Unknown')}
Resource Group: {aks_data.get('resource_group', 'Unknown')}
Current Monthly Cost: ${aks_data.get('total_cost', 'Unknown')}
Total Savings Potential: ${aks_data.get('total_savings', 'Unknown')}

DETAILED BREAKDOWN:
- HPA Optimization Savings: ${aks_data.get('hpa_savings', 'Unknown')}
- Right-sizing Savings: ${aks_data.get('right_sizing_savings', 'Unknown')}
- Storage Optimization: ${aks_data.get('storage_savings', 'Unknown')}
- Current HPA Efficiency: {aks_data.get('hpa_efficiency', 'Unknown')}%

CLUSTER CHARACTERISTICS:
- Total Nodes: {aks_data.get('node_count', 'Unknown')}
- Total Pods: {aks_data.get('pod_count', 'Unknown')}
- Namespaces: {aks_data.get('namespace_count', 'Unknown')}
- ML Classification: {aks_data.get('ml_classification', 'Unknown')}
- High CPU Workloads: {aks_data.get('high_cpu_workloads', 'Unknown')}

HIGH CPU WORKLOADS DETECTED:
{aks_data.get('cpu_workload_details', 'No high CPU workloads specified')}

=== REQUIRED COMPREHENSIVE OUTPUT WITH EXECUTABLE COMMANDS in each PHASE===

1. EXECUTIVE SUMMARY
   - Current cost analysis: ${aks_data.get('total_cost', 0)}
   - Potential monthly savings: ${aks_data.get('total_savings', 0)}
   - ROI calculation and payback period
   - Priority assessment and implementation urgency

2. IMMEDIATE CRITICAL ACTIONS (Week 1)
   Commands to execute

3. PHASE 2 ?
    comamnd sto execute
   

4. PHASE 3: ?
    commands to execute
5. PHASE 4: 
commands to execute
week 2,,,, n
    

This plan provides executable commands, specific timelines, and measurable outcomes to achieve the ${aks_data.get('total_savings', 0)} monthly savings target while maintaining production stability for your {aks_data.get('pod_count', 0)} pod cluster.
"""
        return prompt

def test_with_real_aks_data():
    """Test the optimizer with your actual AKS cluster data"""
    
    print("🚀 TESTING WITH YOUR REAL AKS CLUSTER DATA")
    print("=" * 60)
    
    # Your actual cluster data extracted from the logs
    real_aks_data = {
        'cluster_name': 'aks-dpl-mad-uat-ne2-1',
        'resource_group': 'rg-dpl-mad-uat-ne2-2',
        'total_cost': 1759.87,
        'total_savings': 94.65,
        'hpa_savings': 57.20,
        'right_sizing_savings': 33.45,
        'storage_savings': 4.00,
        'hpa_efficiency': 57.0,
        'node_count': 6,
        'pod_count': 504,
        'namespace_count': 13,
        'ml_classification': 'CPU_INTENSIVE (confidence: 0.34)',
        'high_cpu_workloads': 4,
        'node_cost': 'Not specified in logs',
        'storage_cost': 'Part of total cost analysis',
        'networking_cost': 'Networking dominant cost pattern',
        'cpu_workload_details': '''
        HIGH CPU WORKLOADS IDENTIFIED:
        1. madapi-preprod/advertising-api = 166.0% CPU
        2. madapi-preprod/chenosis-mobile-location-processor = 5813.0% CPU (CRITICAL)
        3. madapi-preprod/customer-datashare-cis-system = 173.0% CPU  
        4. madapi-preprod/madapi-mtn-simswap-processor = 253.0% CPU
        
        Average CPU across high workloads: 1601.2%
        Maximum CPU usage detected: 5813.0% (extremely high)
        '''
    }
    
    print("📊 YOUR ACTUAL CLUSTER ANALYSIS:")
    print(f"   Cluster: {real_aks_data['cluster_name']}")
    print(f"   Resource Group: {real_aks_data['resource_group']}")
    print(f"   Monthly Cost: ${real_aks_data['total_cost']:.2f}")
    print(f"   Potential Savings: ${real_aks_data['total_savings']:.2f}")
    print(f"   Nodes: {real_aks_data['node_count']}")
    print(f"   Pods: {real_aks_data['pod_count']}")
    print(f"   Namespaces: {real_aks_data['namespace_count']}")
    print(f"   ML Classification: {real_aks_data['ml_classification']}")
    print(f"   High CPU Workloads: {real_aks_data['high_cpu_workloads']}")
    print(f"   HPA Efficiency: {real_aks_data['hpa_efficiency']}%")
    print("\n" + "="*60 + "\n")
    
    # Initialize the optimizer
    optimizer = LocalAKSOptimizer()
    
    # Check if Ollama is running
    if not optimizer.check_ollama_status():
        print("❌ Ollama is not running!")
        print("\nTo start Ollama:")
        print("1. Install Ollama: https://ollama.ai/")
        print("2. Run: ollama pull llama2")
        print("3. Start: ollama serve")
        print("4. Re-run this script")
        return None
    
    print("✅ Ollama is running!")
    print("🔄 Generating comprehensive implementation plan for your cluster...")
    
    # Generate the implementation plan
    start_time = time.time()
    result = optimizer.generate_aks_optimization_plan(real_aks_data)
    end_time = time.time()
    
    print(f"\n⏱️  Analysis completed in {end_time - start_time:.1f} seconds")
    print("\n" + "="*80)
    print("📋 IMPLEMENTATION PLAN FOR YOUR AKS CLUSTER")
    print("="*80)
    print(result)
    print("="*80)
    
    # Save the result to a file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"aks_optimization_plan_{real_aks_data['cluster_name']}_{timestamp}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"AKS Cost Optimization Plan\n")
            f.write(f"Cluster: {real_aks_data['cluster_name']}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Cost: ${real_aks_data['total_cost']:.2f}\n")
            f.write(f"Savings: ${real_aks_data['total_savings']:.2f}\n")
            f.write(f"\n{'='*80}\n\n")
            f.write(result)
        
        print(f"\n💾 Plan saved to: {filename}")
        
    except Exception as e:
        print(f"\n⚠️  Could not save to file: {e}")
    
    return result

def test_different_models():
    """Test with different Ollama models for comparison"""
    
    models_to_test = [
        "llama2",
        "llama2:13b",  # Better quality but slower
        "codellama",   # Good for technical content
        "mistral"      # Fast and efficient
    ]
    
    print("🔄 TESTING DIFFERENT MODELS FOR COMPARISON")
    print("=" * 50)
    
    # Your actual data
    real_aks_data = {
        'cluster_name': 'aks-dpl-mad-uat-ne2-1',
        'resource_group': 'rg-dpl-mad-uat-ne2-2',
        'total_cost': 1759.87,
        'total_savings': 94.65,
        'hpa_savings': 57.20,
        'right_sizing_savings': 33.45,
        'storage_savings': 4.00,
        'hpa_efficiency': 57.0,
        'node_count': 6,
        'pod_count': 504,
        'namespace_count': 13,
        'high_cpu_workloads': 4
    }
    
    results = {}
    
    for model in models_to_test:
        print(f"\n🤖 Testing model: {model}")
        
        optimizer = LocalAKSOptimizer()
        optimizer.model_name = model
        
        if not optimizer.check_ollama_status():
            print("❌ Ollama not running")
            continue
        
        try:
            start_time = time.time()
            result = optimizer.generate_aks_optimization_plan(real_aks_data)
            end_time = time.time()
            
            results[model] = {
                'result': result,
                'time': end_time - start_time,
                'length': len(result)
            }
            
            print(f"✅ {model}: {end_time - start_time:.1f}s, {len(result)} chars")
            
        except Exception as e:
            print(f"❌ {model} failed: {e}")
    
    # Show comparison
    if results:
        print(f"\n📊 MODEL COMPARISON:")
        for model, data in results.items():
            print(f"   {model}: {data['time']:.1f}s, {data['length']} chars")
        
        # Show best result
        best_model = max(results.keys(), key=lambda x: results[x]['length'])
        print(f"\n🏆 Most detailed result from: {best_model}")
        print("="*60)
        print(results[best_model]['result'])  # Show FULL result, not truncated
    
    return results

def main():
    """Main function to run the tests"""
    
    print("🎯 AKS COST OPTIMIZER - REAL DATA TESTING")
    print("=" * 50)
    
    choice = input("""
Choose testing option:
1. Test with your real cluster data (recommended) - FULL OUTPUT
2. Compare different AI models
3. Both

Enter choice (1/2/3): """).strip()
    
    if choice in ['1', '3']:
        print("\n" + "="*60)
        result = test_with_real_aks_data()
        
        # Always show the full result for option 1
        if choice == '1' and result:
            print("\n" + "="*80)
            print("📋 COMPLETE IMPLEMENTATION PLAN")
            print("="*80)
            print(result)
            print("="*80)
    
    if choice in ['2', '3']:
        print("\n" + "="*60)
        test_different_models()
    
    print(f"\n🎉 Testing completed!")
    print(f"\n💡 Next steps:")
    print(f"   1. Review the generated implementation plan")
    print(f"   2. Adapt recommendations to your environment")
    print(f"   3. Implement high-impact, low-risk optimizations first")
    print(f"   4. Monitor the 4 high CPU workloads specifically")
    print(f"   5. Check the saved file for the complete plan")

def quick_test():
    """Quick test function that just runs the analysis and shows full output"""
    print("🚀 QUICK TEST - YOUR REAL AKS CLUSTER ANALYSIS")
    print("=" * 60)
    
    result = test_with_real_aks_data()
    
    if result:
        print("\n" + "="*80)
        print("📋 COMPLETE IMPLEMENTATION PLAN")
        print("="*80)
        print(result)
        print("="*80)
    
    return result

if __name__ == "__main__":
    # You can also run quick_test() for immediate full output
    # quick_test()
    main()