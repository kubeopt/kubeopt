"""
Track Claude API costs for monitoring and optimization.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

class CostTracker:
    """Track API costs to a JSON log file"""
    
    def __init__(self, log_file: str = "claude_api_costs.jsonl"):
        self.log_file = Path(log_file)
        
    def log_cost(
        self,
        cluster_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        success: bool = True
    ):
        """Log an API call cost"""
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "cluster_id": cluster_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": round(cost, 6),
            "success": success
        }
        
        # Append to JSONL file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_total_cost(self, days: int = 30) -> Dict:
        """Get total costs for last N days"""
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        total_cost = 0
        total_calls = 0
        total_tokens = 0
        
        if not self.log_file.exists():
            return {
                "total_cost": 0,
                "total_calls": 0,
                "average_cost": 0,
                "total_tokens": 0,
                "period_days": days
            }
        
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entry_time = datetime.fromisoformat(entry['timestamp'])
                    
                    if entry_time >= cutoff and entry.get('success', True):
                        total_cost += entry['cost']
                        total_calls += 1
                        total_tokens += entry['total_tokens']
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue  # Skip malformed entries
        
        return {
            "total_cost": round(total_cost, 4),
            "total_calls": total_calls,
            "average_cost": round(total_cost / total_calls, 4) if total_calls > 0 else 0,
            "total_tokens": total_tokens,
            "period_days": days
        }
    
    def get_cost_by_cluster(self, days: int = 30) -> Dict:
        """Get cost breakdown by cluster"""
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        cluster_costs = {}
        
        if not self.log_file.exists():
            return {}
        
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entry_time = datetime.fromisoformat(entry['timestamp'])
                    
                    if entry_time >= cutoff and entry.get('success', True):
                        cluster_id = entry['cluster_id']
                        if cluster_id not in cluster_costs:
                            cluster_costs[cluster_id] = {
                                "cost": 0,
                                "calls": 0,
                                "tokens": 0
                            }
                        
                        cluster_costs[cluster_id]["cost"] += entry['cost']
                        cluster_costs[cluster_id]["calls"] += 1
                        cluster_costs[cluster_id]["tokens"] += entry['total_tokens']
                        
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue
        
        # Round costs
        for cluster_id in cluster_costs:
            cluster_costs[cluster_id]["cost"] = round(cluster_costs[cluster_id]["cost"], 4)
        
        return cluster_costs


# Global instance
_tracker: Optional[CostTracker] = None

def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker