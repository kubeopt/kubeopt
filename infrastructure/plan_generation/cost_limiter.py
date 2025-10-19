"""
from pydantic import BaseModel, Field, validator
Emergency brake to prevent runaway costs.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

class CostLimiter:
    """Prevent cost escalation"""
    
    def __init__(self, max_daily_cost: float = 5.0):
        self.max_daily_cost = max_daily_cost
        self.cost_file = Path("claude_daily_costs.json")
    
    def check_and_record_cost(self, cost: float) -> bool:
        """
        Check if adding this cost exceeds daily limit.
        Returns True if safe to proceed, False if limit exceeded.
        """
        today = datetime.utcnow().date().isoformat()
        
        # Load today's costs
        if self.cost_file.exists():
            with open(self.cost_file, 'r') as f:
                data = json.load(f)
        else:
            data = {}
        
        # Get today's total
        today_total = data.get(today, 0.0)
        
        # Check limit
        if today_total + cost > self.max_daily_cost:
            print(f"🚨 COST LIMIT EXCEEDED!")
            print(f"   Today's spend: ${today_total:.2f}")
            print(f"   Attempted cost: ${cost:.2f}")
            print(f"   Daily limit: ${self.max_daily_cost:.2f}")
            print(f"   BLOCKING THIS REQUEST")
            return False
        
        # Record cost
        data[today] = today_total + cost
        
        with open(self.cost_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💰 Today's Claude costs: ${data[today]:.2f} / ${self.max_daily_cost:.2f}")
        
        return True

# Global limiter
_limiter = CostLimiter(max_daily_cost=5.0)

def check_cost_limit(estimated_cost: float) -> bool:
    """Check if we can proceed with this cost"""
    return _limiter.check_and_record_cost(estimated_cost)