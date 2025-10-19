from typing import Dict
from pydantic import BaseModel, Field, validator

class HPAAnalyzer:
    """Unified HPA analysis utility - SINGLE SOURCE OF TRUTH"""
    
    @staticmethod
    def calculate_optimization_score(hpa: Dict, analysis_type: str = 'enhanced') -> float:
        """Calculate HPA optimization score (consolidated implementation)"""
        score_factors = []
        
        # Analyze metrics configuration
        metrics = hpa.get('spec', {}).get('metrics', [])
        if len(metrics) >= 2:  # CPU and memory
            score_factors.append(0.8)
        elif len(metrics) == 1:
            score_factors.append(0.6)
        else:
            score_factors.append(0.3)
        
        # Analyze replica configuration
        min_replicas = hpa.get('spec', {}).get('minReplicas', 1)
        max_replicas = hpa.get('spec', {}).get('maxReplicas', 10)
        
        if min_replicas >= 2 and max_replicas >= min_replicas * 3:
            score_factors.append(0.9)
        elif min_replicas >= 1 and max_replicas >= min_replicas * 2:
            score_factors.append(0.7)
        else:
            score_factors.append(0.4)
        
        # Enhanced analysis includes behavior configuration
        if analysis_type == 'enhanced':
            behavior = hpa.get('spec', {}).get('behavior')
            score_factors.append(0.9 if behavior else 0.5)
        
        # CPU target analysis
        cpu_target = HPAAnalyzer.extract_cpu_target(hpa)
        if 60 <= cpu_target <= 80:
            score_factors.append(1.0)
        elif 50 <= cpu_target <= 90:
            score_factors.append(0.8)
        else:
            score_factors.append(0.4)
        
        return sum(score_factors) / len(score_factors)
    
    @staticmethod
    def extract_cpu_target(hpa: Dict) -> int:
        """Extract CPU target from HPA metrics"""
        metrics = hpa.get('spec', {}).get('metrics', [])
        for metric in metrics:
            if (metric.get('type') == 'Resource' and 
                metric.get('resource', {}).get('name') == 'cpu'):
                return metric.get('resource', {}).get('target', {}).get('averageUtilization', 70)
        return 70

    @staticmethod
    def extract_memory_target(hpa: Dict) -> int:
        """Extract memory target from HPA metrics"""
        metrics = hpa.get('spec', {}).get('metrics', [])
        for metric in metrics:
            if (metric.get('type') == 'Resource' and 
                metric.get('resource', {}).get('name') == 'memory'):
                return metric.get('resource', {}).get('target', {}).get('averageUtilization', 70)
        return 70

    @staticmethod
    def calculate_candidate_score(deployment: Dict) -> float:
        """Calculate HPA candidate score for deployment"""
        score = 0.5  # Base score
        
        # Replica analysis
        replicas = deployment.get('spec', {}).get('replicas', 1)
        if replicas > 1:
            score += 0.2
        
        # Resource requests analysis
        containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
        has_requests = any(c.get('resources', {}).get('requests') for c in containers)
        if has_requests is not None and has_requests:
            score += 0.3
        
        # Application type analysis
        name = deployment.get('metadata', {}).get('name', '').lower()
        if any(keyword in name for keyword in ['web', 'api', 'frontend', 'app', 'service']):
            score += 0.2
        
        # Label analysis
        labels = deployment.get('metadata', {}).get('labels', {})
        if labels.get('app.kubernetes.io/component') in ['frontend', 'backend', 'api']:
            score += 0.1
        
        return min(1.0, score)

    @staticmethod
    def generate_optimization_recommendations(hpa: Dict) -> Dict:
        """Generate HPA optimization recommendations"""
        optimizations = {}
        
        # CPU target improvements
        current_cpu = HPAAnalyzer.extract_cpu_target(hpa)
        if current_cpu < 60:
            optimizations['cpu_target'] = 70
            optimizations['cpu_rationale'] = 'Increase target for better resource utilization'
        elif current_cpu > 80:
            optimizations['cpu_target'] = 75
            optimizations['cpu_rationale'] = 'Decrease target to prevent over-scaling'
        
        # Memory target improvements
        current_memory = HPAAnalyzer.extract_memory_target(hpa)
        if current_memory < 60:
            optimizations['memory_target'] = 70
            optimizations['memory_rationale'] = 'Increase target for better memory utilization'
        elif current_memory > 80:
            optimizations['memory_target'] = 75
            optimizations['memory_rationale'] = 'Decrease target to prevent memory pressure'
        
        # Replica improvements
        current_max = hpa.get('spec', {}).get('maxReplicas', 10)
        current_min = hpa.get('spec', {}).get('minReplicas', 1)
        
        if current_max < current_min * 3:
            optimizations['max_replicas'] = current_min * 3
            optimizations['replica_rationale'] = 'Increase max replicas for better scaling headroom'
        
        if current_min < 2:
            optimizations['min_replicas'] = 2
            optimizations['min_replica_rationale'] = 'Increase min replicas for better availability'
        
        return optimizations