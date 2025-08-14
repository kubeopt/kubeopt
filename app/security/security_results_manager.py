"""
Security Results Manager
========================
Manages storage and retrieval of security analysis results
Keeps security data separate from implementation plans
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

class SecurityResultsManager:
    """
    Singleton manager for security analysis results
    Stores results in memory with optional persistence
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._results_store = {}  # cluster_id -> security_results
        self._results_history = {}  # cluster_id -> list of historical results
        self._cache_duration = timedelta(hours=1)
        
        # Optional: Create persistence directory
        self._persistence_dir = Path("security_results")
        self._persistence_dir.mkdir(exist_ok=True)
        
        logger.info("🔒 Security Results Manager initialized")
    
    def store_security_results(self, cluster_id: str, resource_group: str, 
                              cluster_name: str, security_analysis: Dict) -> str:
        """
        Store security analysis results for a cluster
        
        Returns: Result ID for reference
        """
        try:
            result_id = f"sec_{cluster_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Structure the results
            security_results = {
                'result_id': result_id,
                'cluster_id': cluster_id,
                'resource_group': resource_group,
                'cluster_name': cluster_name,
                'timestamp': datetime.now().isoformat(),
                'analysis': security_analysis,
                'metadata': {
                    'version': '1.0.0',
                    'complete': True,
                    'cached_until': (datetime.now() + self._cache_duration).isoformat()
                }
            }
            
            # Store in memory
            self._results_store[cluster_id] = security_results
            
            # Add to history
            if cluster_id not in self._results_history:
                self._results_history[cluster_id] = []
            self._results_history[cluster_id].append({
                'result_id': result_id,
                'timestamp': security_results['timestamp'],
                'summary': self._create_summary(security_analysis)
            })
            
            # Optional: Persist to disk
            self._persist_results(cluster_id, security_results)
            
            logger.info(f"✅ Stored security results for {cluster_name} (ID: {result_id})")
            return result_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store security results: {e}")
            raise
    
    def get_latest_results(self, cluster_id: str) -> Optional[Dict]:
        """Get the latest security results for a cluster"""
        
        # Check memory cache
        if cluster_id in self._results_store:
            results = self._results_store[cluster_id]
            
            # Check if cache is still valid
            cached_until = datetime.fromisoformat(results['metadata']['cached_until'])
            if datetime.now() < cached_until:
                logger.info(f"✅ Returning cached security results for cluster {cluster_id}")
                return results
            else:
                logger.info(f"⚠️ Cache expired for cluster {cluster_id}")
        
        # Try to load from disk if not in memory
        persisted = self._load_persisted_results(cluster_id)
        if persisted:
            self._results_store[cluster_id] = persisted
            return persisted
        
        return None
    
    def get_results_by_id(self, result_id: str) -> Optional[Dict]:
        """Get specific security results by result ID"""
        
        # Search in memory
        for cluster_id, results in self._results_store.items():
            if results.get('result_id') == result_id:
                return results
        
        # Search in persisted files
        for file_path in self._persistence_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get('result_id') == result_id:
                        return data
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
        
        return None
    
    def get_history(self, cluster_id: str, limit: int = 10) -> List[Dict]:
        """Get historical security results summary for a cluster"""
        
        if cluster_id in self._results_history:
            history = self._results_history[cluster_id]
            return sorted(history, key=lambda x: x['timestamp'], reverse=True)[:limit]
        
        return []
    
    def clear_results(self, cluster_id: str):
        """Clear security results for a cluster"""
        
        if cluster_id in self._results_store:
            del self._results_store[cluster_id]
        
        if cluster_id in self._results_history:
            del self._results_history[cluster_id]
        
        # Remove persisted file
        file_path = self._persistence_dir / f"{cluster_id}_latest.json"
        if file_path.exists():
            file_path.unlink()
        
        logger.info(f"🗑️ Cleared security results for cluster {cluster_id}")
    
    def _create_summary(self, security_analysis: Dict) -> Dict:
        """Create a summary of security analysis results"""
        
        return {
            'security_score': security_analysis.get('security_posture', {}).get('overall_score', 0),
            'grade': security_analysis.get('security_posture', {}).get('grade', 'N/A'),
            'critical_vulnerabilities': security_analysis.get('vulnerability_assessment', {}).get('critical_vulnerabilities', 0),
            'policy_violations': security_analysis.get('policy_compliance', {}).get('violations_count', 0),
            'compliance_score': security_analysis.get('compliance_assessment', {}).get('overall_compliance', 0),
            'frameworks_analyzed': security_analysis.get('frameworks_analyzed', [])
        }
    
    def _persist_results(self, cluster_id: str, results: Dict):
        """Persist results to disk for recovery"""
        
        try:
            file_path = self._persistence_dir / f"{cluster_id}_latest.json"
            with open(file_path, 'w') as f:
                json.dump(results, f, indent=2)
            logger.debug(f"💾 Persisted security results to {file_path}")
        except Exception as e:
            logger.warning(f"Failed to persist results: {e}")
    
    def _load_persisted_results(self, cluster_id: str) -> Optional[Dict]:
        """Load persisted results from disk"""
        
        try:
            file_path = self._persistence_dir / f"{cluster_id}_latest.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load persisted results: {e}")
        
        return None

# Global singleton instance
security_results_manager = SecurityResultsManager()