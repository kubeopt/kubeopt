#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

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
        self._results_store = {}  # cluster_id -> security_results (memory cache)
        self._cache_duration = timedelta(hours=1)
        
        # Import unified database managers
        try:
            from app.data.operational_data_db import operational_data_db
            from app.data.security_analytics_db import security_analytics_db
            self.operational_db = operational_data_db
            self.security_db = security_analytics_db
            logger.info("🔒 Security Results Manager initialized with unified database")
        except ImportError as e:
            logger.warning(f"⚠️ Failed to import unified databases, falling back to file storage: {e}")
            self.operational_db = None
            self.security_db = None
            # Fallback: Create persistence directory
            self._persistence_dir = Path("security_results")
            self._persistence_dir.mkdir(exist_ok=True)
    
    def store_security_results(self, cluster_id: str, resource_group: str, 
                              cluster_name: str, security_analysis: Dict) -> str:
        """
        Store security analysis results for a cluster in unified database
        
        Returns: Result ID for reference
        """
        try:
            result_id = f"sec_{cluster_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            timestamp = datetime.now().isoformat()
            
            # Structure the results
            security_results = {
                'result_id': result_id,
                'cluster_id': cluster_id,
                'resource_group': resource_group,
                'cluster_name': cluster_name,
                'timestamp': timestamp,
                'analysis': security_analysis,
                'metadata': {
                    'version': '1.0.0',
                    'complete': True,
                    'cached_until': (datetime.now() + self._cache_duration).isoformat()
                }
            }
            
            # Store in memory cache
            self._results_store[cluster_id] = security_results
            
            # Store in unified database if available
            if self.operational_db and self.security_db:
                try:
                    # Store in operational database (main storage)
                    self.operational_db.store_security_scan_result(
                        result_id=result_id,
                        cluster_id=cluster_id,
                        resource_group=resource_group,
                        cluster_name=cluster_name,
                        scan_timestamp=timestamp,
                        analysis_data=security_analysis,
                        confidence=security_analysis.get('confidence', 0.0),
                        frameworks_analyzed=security_analysis.get('frameworks_analyzed', []),
                        based_on_real_data=security_analysis.get('based_on_real_data', False)
                    )
                    
                    # Also store security assessment if available
                    if 'security_posture' in security_analysis:
                        posture = security_analysis['security_posture']
                        self.security_db.store_security_assessment(
                            cluster_id=cluster_id,
                            assessment_id=result_id,
                            overall_score=posture.get('overall_score', 0),
                            grade=posture.get('grade', 'N/A'),
                            framework=security_analysis.get('frameworks_analyzed', ['CIS'])[0] if security_analysis.get('frameworks_analyzed') else 'CIS',
                            score_breakdown=posture.get('breakdown', {}),
                            confidence=security_analysis.get('confidence', 0.0),
                            based_on_real_data=security_analysis.get('based_on_real_data', False),
                            trends_data=posture.get('trends', {})
                        )
                    
                    logger.info(f"✅ Stored security results in unified database for {cluster_name} (ID: {result_id})")
                    
                except Exception as db_error:
                    logger.warning(f"⚠️ Failed to store in unified database: {db_error}, falling back to file storage")
                    self._persist_results(cluster_id, security_results)
            else:
                # Fallback to file storage
                self._persist_results(cluster_id, security_results)
            
            return result_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store security results: {e}")
            raise
    
    def get_latest_results(self, cluster_id: str) -> Optional[Dict]:
        """Get the latest security results for a cluster from unified database"""
        
        # Check memory cache first
        if cluster_id in self._results_store:
            results = self._results_store[cluster_id]
            
            # Check if cache is still valid
            cached_until = datetime.fromisoformat(results['metadata']['cached_until'])
            if datetime.now() < cached_until:
                logger.info(f"✅ Returning cached security results for cluster {cluster_id}")
                return results
            else:
                logger.info(f"⚠️ Cache expired for cluster {cluster_id}")
        
        # Try to load from unified database
        if self.operational_db:
            try:
                scan_results = self.operational_db.get_security_scan_results(cluster_id, limit=1)
                
                if scan_results:
                    latest_result = scan_results[0]
                    
                    # Convert database format to expected format
                    security_results = {
                        'result_id': latest_result.get('result_id'),
                        'cluster_id': cluster_id,
                        'resource_group': latest_result.get('resource_group'),
                        'cluster_name': latest_result.get('cluster_name'),
                        'timestamp': latest_result.get('scan_timestamp'),
                        'analysis': latest_result.get('analysis_data'),
                        'metadata': {
                            'version': '1.0.0',
                            'complete': True,
                            'cached_until': (datetime.now() + self._cache_duration).isoformat(),
                            'confidence': latest_result.get('confidence'),
                            'frameworks_analyzed': latest_result.get('frameworks_analyzed'),
                            'based_on_real_data': latest_result.get('based_on_real_data'),
                            'data_source': 'unified_database'
                        }
                    }
                    
                    # Cache the results
                    self._results_store[cluster_id] = security_results
                    
                    logger.info(f"✅ Retrieved security results from unified database for cluster {cluster_id}")
                    return security_results
                    
            except Exception as db_error:
                logger.warning(f"⚠️ Failed to load from unified database: {db_error}, trying fallback")
        
        # Fallback: Try to load from disk if unified database fails
        if hasattr(self, '_persistence_dir'):
            persisted = self._load_persisted_results(cluster_id)
            if persisted:
                self._results_store[cluster_id] = persisted
                return persisted
        
        logger.info(f"ℹ️ No security results found for cluster {cluster_id}")
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
        """Get historical security results summary for a cluster from unified database"""
        
        # Try to get from unified database
        if self.operational_db:
            try:
                scan_results = self.operational_db.get_security_scan_results(cluster_id, limit=limit)
                
                history = []
                for result in scan_results:
                    summary = {
                        'result_id': result.get('result_id'),
                        'timestamp': result.get('scan_timestamp'),
                        'summary': self._create_summary(result.get('analysis_data', {}))
                    }
                    history.append(summary)
                
                logger.info(f"✅ Retrieved {len(history)} historical security results from unified database")
                return history
                
            except Exception as db_error:
                logger.warning(f"⚠️ Failed to get history from unified database: {db_error}")
        
        # Fallback: check memory cache
        if hasattr(self, '_results_history') and cluster_id in self._results_history:
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