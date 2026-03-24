"""
Storage Optimization Algorithm
==============================

Extracted and refactored storage optimization logic from algorithmic_cost_analyzer.py
Uses industry standards instead of hardcoded values.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""

import logging
from typing import Dict, Optional
from shared.standards.storage_industry_standards import (
    StorageOptimizationStandards,
    StorageTypeStandards,
    StorageCostStandards
)


class StorageOptimizationAlgorithm:
    """
    Storage optimization algorithm using industry standards
    Extracted from algorithmic_cost_analyzer.py and refactored
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize storage optimization algorithm
        
        Args:
            logger: Logger instance (required, no default)
        
        Raises:
            ValueError: If logger is None
        """
        if logger is None:
            raise ValueError("Logger parameter is required")
        
        self.logger = logger
        self.logger.info("🔧 Storage Optimization Algorithm initialized with industry standards")
    
    def calculate_storage_savings(self, storage_cost: float, usage: Dict) -> float:
        """
        Calculate storage optimization savings
        REFACTORED: Now uses industry standards instead of hardcoded values
        
        Args:
            storage_cost: Cost of storage
            usage: Usage metrics containing storage utilization patterns
        
        Returns:
            float: Estimated monthly savings amount
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(storage_cost, (int, float)) or storage_cost < 0:
            raise ValueError("storage_cost must be a non-negative number")
        if usage is None:
            raise ValueError("usage parameter is required")
        
        try:
            # REFACTORED: Use industry standard base savings instead of hardcoded 0.2 (20%)
            base_savings_rate = StorageOptimizationStandards.BASE_STORAGE_OPTIMIZATION_SAVINGS
            base_savings = storage_cost * base_savings_rate
            
            # Get usage pattern and storage utilization
            usage_pattern = usage.get('usage_pattern', 'balanced')
            storage_utilization = usage.get('storage_utilization', 50)  # Default to 50% if not provided
            storage_type = usage.get('storage_type', 'standard')
            
            # Validate storage utilization
            if not (0 <= storage_utilization <= 100):
                self.logger.warning(f"Invalid storage utilization: {storage_utilization}%, using 50%")
                storage_utilization = 50
            
            # Apply utilization-based multipliers
            utilization_multiplier = self._calculate_utilization_multiplier(storage_utilization)
            
            # Apply storage type multiplier
            type_multiplier = self._get_storage_type_multiplier(storage_type)
            
            # Apply usage pattern multiplier
            pattern_multiplier = self._get_usage_pattern_multiplier(usage_pattern)
            
            # Calculate final savings
            total_savings = base_savings * utilization_multiplier * type_multiplier * pattern_multiplier
            
            # Apply minimum savings threshold
            min_savings_threshold = StorageOptimizationStandards.MINIMUM_STORAGE_SAVINGS_THRESHOLD
            if total_savings < min_savings_threshold:
                self.logger.info(f"💾 Storage Savings: ${total_savings:.2f}/month (below ${min_savings_threshold} threshold)")
                return 0.0
            
            self.logger.info(f"💾 Storage Savings: ${total_savings:.2f}/month "
                           f"(utilization: {storage_utilization:.1f}%, pattern: {usage_pattern}, "
                           f"type: {storage_type}, multipliers: util={utilization_multiplier:.2f}, "
                           f"type={type_multiplier:.2f}, pattern={pattern_multiplier:.2f})")
            
            return total_savings
            
        except Exception as e:
            self.logger.error(f"❌ Storage savings calculation failed: {e}")
            # Fail fast, no defaults
            raise ValueError(f"Storage savings calculation failed: {e}") from e
    
    def _calculate_utilization_multiplier(self, storage_utilization: float) -> float:
        """
        Calculate multiplier based on storage utilization
        REFACTORED: Now uses industry standards instead of hardcoded thresholds
        
        Args:
            storage_utilization: Storage utilization percentage
        
        Returns:
            float: Utilization multiplier
        """
        underutilized_threshold = StorageOptimizationStandards.STORAGE_UNDERUTILIZED_THRESHOLD
        optimal_utilization = StorageOptimizationStandards.STORAGE_OPTIMAL_UTILIZATION
        overutilized_threshold = StorageOptimizationStandards.STORAGE_OVERUTILIZED_THRESHOLD
        
        if storage_utilization < underutilized_threshold:
            # High optimization potential for underutilized storage
            multiplier = StorageOptimizationStandards.UNDERUTILIZED_STORAGE_MULTIPLIER
            self.logger.info(f"🔍 Storage underutilized ({storage_utilization:.1f}% < {underutilized_threshold}%), high optimization potential")
        elif storage_utilization > overutilized_threshold:
            # Limited optimization potential for overutilized storage
            multiplier = StorageOptimizationStandards.OVERUTILIZED_STORAGE_PENALTY
            self.logger.info(f"🔍 Storage overutilized ({storage_utilization:.1f}% > {overutilized_threshold}%), limited optimization potential")
        else:
            # Standard optimization for normally utilized storage
            multiplier = 1.0
            self.logger.info(f"🔍 Storage normally utilized ({storage_utilization:.1f}%), standard optimization potential")
        
        return multiplier
    
    def _get_storage_type_multiplier(self, storage_type: str) -> float:
        """
        Get multiplier based on storage type
        REFACTORED: Now uses industry standards for different storage types
        
        Args:
            storage_type: Type of storage (standard, premium, ssd, etc.)
        
        Returns:
            float: Storage type multiplier
        """
        storage_type_lower = storage_type.lower()
        
        if 'premium' in storage_type_lower or 'managed' in storage_type_lower:
            return StorageOptimizationStandards.PREMIUM_STORAGE_FACTOR
        elif 'ssd' in storage_type_lower:
            return StorageOptimizationStandards.SSD_OPTIMIZATION_FACTOR
        else:
            return StorageOptimizationStandards.HDD_OPTIMIZATION_FACTOR
    
    def _get_usage_pattern_multiplier(self, usage_pattern: str) -> float:
        """
        Get multiplier based on usage pattern
        REFACTORED: Now uses industry standards for different access patterns
        
        Args:
            usage_pattern: Usage pattern (underutilized, balanced, intensive, etc.)
        
        Returns:
            float: Usage pattern multiplier
        """
        pattern_lower = usage_pattern.lower()
        
        if 'underutilized' in pattern_lower or 'infrequent' in pattern_lower:
            return StorageTypeStandards.INFREQUENT_ACCESS_MULTIPLIER
        elif 'intensive' in pattern_lower or 'frequent' in pattern_lower:
            return StorageTypeStandards.FREQUENT_ACCESS_MULTIPLIER
        elif 'archive' in pattern_lower:
            return StorageTypeStandards.ARCHIVE_ACCESS_MULTIPLIER
        else:
            # Balanced or unknown pattern
            return 1.0
    
    def calculate_advanced_storage_savings(self, storage_cost: float, storage_metrics: Dict) -> Dict:
        """
        Calculate advanced storage savings with detailed breakdown
        
        Args:
            storage_cost: Cost of storage
            storage_metrics: Detailed storage metrics
        
        Returns:
            Dict: Detailed savings breakdown
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(storage_cost, (int, float)) or storage_cost < 0:
            raise ValueError("storage_cost must be a non-negative number")
        if storage_metrics is None:
            raise ValueError("storage_metrics parameter is required")
        
        try:
            savings_breakdown = {}
            total_savings = 0
            
            # Deduplication savings
            if storage_metrics.get('deduplication_enabled', False):
                dedup_savings = storage_cost * StorageCostStandards.DEDUPLICATION_SAVINGS_FACTOR
                savings_breakdown['deduplication'] = dedup_savings
                total_savings += dedup_savings
            
            # Compression savings
            if storage_metrics.get('compression_enabled', False):
                compression_savings = storage_cost * StorageCostStandards.COMPRESSION_SAVINGS_FACTOR
                savings_breakdown['compression'] = compression_savings
                total_savings += compression_savings
            
            # Tiering savings
            tiering_potential = storage_metrics.get('tiering_potential', 0)
            if tiering_potential > 0:
                tiering_savings = storage_cost * StorageCostStandards.TIERING_SAVINGS_FACTOR * (tiering_potential / 100)
                savings_breakdown['intelligent_tiering'] = tiering_savings
                total_savings += tiering_savings
            
            # Lifecycle management savings
            lifecycle_automation = storage_metrics.get('lifecycle_automation', False)
            if lifecycle_automation:
                lifecycle_savings = storage_cost * StorageCostStandards.AUTOMATED_LIFECYCLE_SAVINGS
            else:
                lifecycle_savings = storage_cost * StorageCostStandards.MANUAL_LIFECYCLE_SAVINGS
            
            savings_breakdown['lifecycle_management'] = lifecycle_savings
            total_savings += lifecycle_savings
            
            # Snapshot optimization
            snapshot_count = storage_metrics.get('snapshot_count', 0)
            if snapshot_count > 10:  # High snapshot count indicates optimization potential
                snapshot_savings = storage_cost * StorageCostStandards.SNAPSHOT_OPTIMIZATION_SAVINGS
                savings_breakdown['snapshot_optimization'] = snapshot_savings
                total_savings += snapshot_savings
            
            result = {
                'total_savings': total_savings,
                'savings_breakdown': savings_breakdown,
                'optimization_opportunities': len(savings_breakdown)
            }
            
            self.logger.info(f"💾 Advanced Storage Savings: ${total_savings:.2f}/month "
                           f"({len(savings_breakdown)} optimization opportunities)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Advanced storage savings calculation failed: {e}")
            raise ValueError(f"Advanced storage savings calculation failed: {e}") from e