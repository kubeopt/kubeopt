#!/usr/bin/env python3
"""
AKS Data Availability Test Script
---------------------------------
Tests what data we can actually retrieve from your AKS cluster
using az aks command invoke to validate our pod cost analysis approach.
"""

import subprocess
import json
import time
from datetime import datetime

# Configuration - UPDATE THESE WITH YOUR VALUES
RESOURCE_GROUP = "rg-dpl-mad-uat-ne2-2"
CLUSTER_NAME = "aks-dpl-mad-uat-ne2-1"

class AKSDataTester:
    def __init__(self, resource_group, cluster_name):
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.test_results = {}
        
    def run_all_tests(self):
        """Run all data availability tests"""
        print("=" * 80)
        print(f"🔍 AKS DATA AVAILABILITY TEST")
        print(f"Cluster: {self.cluster_name}")
        print(f"Resource Group: {self.resource_group}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        tests = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("Namespace Listing", self.test_namespaces),
            ("Pod Listing", self.test_pods), 
            ("Pod Details (JSON)", self.test_pod_details),
            ("Real-time Metrics (kubectl top)", self.test_realtime_metrics),
            ("Resource Usage", self.test_resource_usage),
            ("Node Information", self.test_nodes)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 Testing: {test_name}")
            print("-" * 40)
            
            start_time = time.time()
            try:
                result = test_func()
                duration = time.time() - start_time
                
                if result.get('success'):
                    print(f"✅ PASS ({duration:.1f}s)")
                    if result.get('data'):
                        print(f"📊 Data: {result['data']}")
                    if result.get('sample'):
                        print(f"📝 Sample: {result['sample']}")
                else:
                    print(f"❌ FAIL ({duration:.1f}s)")
                    print(f"❗ Error: {result.get('error', 'Unknown error')}")
                    
                self.test_results[test_name] = result
                
            except Exception as e:
                duration = time.time() - start_time
                print(f"💥 EXCEPTION ({duration:.1f}s): {str(e)}")
                self.test_results[test_name] = {'success': False, 'error': str(e)}
        
        # Generate summary
        self.print_summary()
        
        return self.test_results
    
    def test_basic_connectivity(self):
        """Test basic cluster connectivity"""
        cmd = f'az aks command invoke --resource-group {self.resource_group} --name {self.cluster_name} --command "kubectl get nodes" 2>/dev/null'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=75)
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            node_count = len([line for line in lines if line.strip() and not line.startswith('NAME')])
            
            return {
                'success': True,
                'data': f'{node_count} nodes found',
                'sample': lines[0] if lines else 'No output'
            }
        else:
            return {
                'success': False,
                'error': f'Return code: {result.returncode}, Error: {result.stderr}'
            }
    
    def test_namespaces(self):
        """Test namespace listing"""
        cmd = f'az aks command invoke --resource-group {self.resource_group} --name {self.cluster_name} --command "kubectl get namespaces" 2>/dev/null'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=75)
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            namespaces = []
            
            for line in lines[1:]:  # Skip header
                if line.strip():
                    namespace_name = line.split()[0]
                    namespaces.append(namespace_name)
            
            return {
                'success': True,
                'data': f'{len(namespaces)} namespaces: {", ".join(namespaces[:5])}{"..." if len(namespaces) > 5 else ""}',
                'sample': lines[1] if len(lines) > 1 else 'No namespaces'
            }
        else:
            return {
                'success': False,
                'error': f'Return code: {result.returncode}, Error: {result.stderr}'
            }
    
    def test_pods(self):
        """Test pod listing"""
        cmd = f'az aks command invoke --resource-group {self.resource_group} --name {self.cluster_name} --command "kubectl get pods --all-namespaces" 2>/dev/null'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=75)
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            pod_count = len([line for line in lines if line.strip() and not line.startswith('NAMESPACE')])
            
            # Count by namespace
            namespace_counts = {}
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        namespace = parts[0]
                        namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1
            
            return {
                'success': True,
                'data': f'{pod_count} total pods across {len(namespace_counts)} namespaces',
                'sample': f'Breakdown: {dict(list(namespace_counts.items())[:3])}'
            }
        else:
            return {
                'success': False,
                'error': f'Return code: {result.returncode}, Error: {result.stderr}'
            }
    
    def test_pod_details(self):
        """Test getting pod details in JSON format"""
        cmd = f'az aks command invoke --resource-group {self.resource_group} --name {self.cluster_name} --command "kubectl get pods --all-namespaces -o json" 2>/dev/null'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=75)
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                pod_data = json.loads(result.stdout)
                pods = pod_data.get('items', [])
                
                # Analyze first pod for resource info
                sample_pod = None
                has_resource_requests = False
                has_resource_limits = False
                
                if pods:
                    sample_pod = pods[0]
                    for container in sample_pod.get('spec', {}).get('containers', []):
                        resources = container.get('resources', {})
                        if resources.get('requests'):
                            has_resource_requests = True
                        if resources.get('limits'):
                            has_resource_limits = True
                
                return {
                    'success': True,
                    'data': f'{len(pods)} pods in JSON format',
                    'sample': f'Resource requests: {has_resource_requests}, Resource limits: {has_resource_limits}'
                }
                
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f'JSON parsing failed: {str(e)}'
                }
        else:
            return {
                'success': False,
                'error': f'Return code: {result.returncode}, Error: {result.stderr}'
            }
    
    def test_realtime_metrics(self):
        """Test kubectl top commands (requires metrics server)"""
        # Test nodes first
        cmd = f'az aks command invoke --resource-group {self.resource_group} --name {self.cluster_name} --command "kubectl top nodes" 2>/dev/null'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=75)
        
        if result.returncode == 0 and 'CPU' in result.stdout:
            lines = result.stdout.strip().split('\n')
            node_metrics = len([line for line in lines if line.strip() and not line.startswith('NAME') and 'CPU' not in line])
            
            # Try pods too
            pod_cmd = f'az aks command invoke --resource-group {self.resource_group} --name {self.cluster_name} --command "kubectl top pods --all-namespaces" 2>/dev/null'
            pod_result = subprocess.run(pod_cmd, shell=True, capture_output=True, text=True, timeout=75)
            
            pod_metrics_available = pod_result.returncode == 0 and 'CPU' in pod_result.stdout
            
            return {
                'success': True,
                'data': f'Node metrics: {node_metrics} nodes, Pod metrics: {"Available" if pod_metrics_available else "Not available"}',
                'sample': lines[1] if len(lines) > 1 else 'No metrics'
            }
        else:
            return {
                'success': False,
                'error': 'Metrics server not available or not responding'
            }
    
    def test_resource_usage(self):
        """Test getting resource usage with containers"""
        cmd = f'az aks command invoke --resource-group {self.resource_group} --name {self.cluster_name} --command "kubectl top pods --all-namespaces --containers" 2>/dev/null'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=75)
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            container_count = len([line for line in lines if line.strip() and not line.startswith('NAMESPACE')])
            
            return {
                'success': True,
                'data': f'{container_count} container metrics found',
                'sample': lines[1] if len(lines) > 1 else 'No container metrics'
            }
        else:
            return {
                'success': False,
                'error': 'Container metrics not available'
            }
    
    def test_nodes(self):
        """Test node information"""
        cmd = f'az aks command invoke --resource-group {self.resource_group} --name {self.cluster_name} --command "kubectl get nodes -o json" 2>/dev/null'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=75)
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                node_data = json.loads(result.stdout)
                nodes = node_data.get('items', [])
                
                node_info = []
                for node in nodes[:3]:  # First 3 nodes
                    name = node.get('metadata', {}).get('name', 'unknown')
                    status = node.get('status', {}).get('conditions', [])
                    ready = any(c.get('type') == 'Ready' and c.get('status') == 'True' for c in status)
                    node_info.append(f"{name}({'Ready' if ready else 'NotReady'})")
                
                return {
                    'success': True,
                    'data': f'{len(nodes)} nodes found',
                    'sample': ', '.join(node_info)
                }
                
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f'JSON parsing failed: {str(e)}'
                }
        else:
            return {
                'success': False,
                'error': f'Return code: {result.returncode}'
            }
    
    def print_summary(self):
        """Print test summary and recommendations"""
        print("\n" + "=" * 80)
        print("📋 TEST SUMMARY & RECOMMENDATIONS")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results.values() if result.get('success'))
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}/{total} tests")
        
        if passed >= 5:
            print("🎉 EXCELLENT: Your environment supports advanced pod cost analysis!")
            print("   Recommended approach: Real-time resource usage analysis")
        elif passed >= 3:
            print("👍 GOOD: Your environment supports basic pod cost analysis")
            print("   Recommended approach: Pod count distribution with enhancements")
        elif passed >= 1:
            print("⚠️  LIMITED: Basic namespace analysis only")
            print("   Recommended approach: Simple namespace cost distribution")
        else:
            print("❌ POOR: AKS connectivity issues detected")
            print("   Recommendation: Check Azure CLI authentication and cluster access")
        
        print("\n📊 WHAT THIS MEANS FOR POD COST ANALYSIS:")
        
        if self.test_results.get("Real-time Metrics (kubectl top)", {}).get('success'):
            print("   ✅ Can use real-time resource usage (most accurate)")
        
        if self.test_results.get("Pod Details (JSON)", {}).get('success'):
            print("   ✅ Can analyze resource requests/limits")
        
        if self.test_results.get("Pod Listing", {}).get('success'):
            print("   ✅ Can do pod count distribution")
        
        if self.test_results.get("Namespace Listing", {}).get('success'):
            print("   ✅ Can do basic namespace distribution")
        
        print("\n🔧 IMPLEMENTATION RECOMMENDATION:")
        
        success_count = passed
        if success_count >= 5:
            print("   Use intelligent pod cost analyzer with all enhancement methods")
        elif success_count >= 3:
            print("   Use basic pod cost analyzer with pod count fallback")
        elif success_count >= 1:
            print("   Use simple namespace cost distribution only")
        else:
            print("   Skip pod cost analysis - focus on Azure cost data only")

def main():
    """Run the AKS data availability test"""
    tester = AKSDataTester(RESOURCE_GROUP, CLUSTER_NAME)
    
    print("🚀 Starting AKS Data Availability Test...")
    print(f"⏱️  This will take 1-2 minutes to complete...")
    
    try:
        results = tester.run_all_tests()
        
        print(f"\n💾 Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📄 Results saved to test results (in memory)")
        
        return results
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return None
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        return None

if __name__ == "__main__":
    # Run the test
    test_results = main()
    
    if test_results:
        print("\n🎯 NEXT STEPS:")
        print("1. Review the test results above")
        print("2. Note which methods work in your environment") 
        print("3. Use this info to implement the appropriate pod cost analysis approach")
        print("4. Share results if you need help choosing the best implementation strategy")