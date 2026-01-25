"""
Storage Industry Standards
==========================

Industry-standard values for Kubernetes storage optimization.
Based on CNCF FinOps best practices and cloud provider recommendations.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""


class StorageOptimizationStandards:
    """Industry standards for storage optimization"""
    
    # Base Storage Optimization Rates
    BASE_STORAGE_OPTIMIZATION_SAVINGS = 0.2  # 20% base savings through optimization
    UNDERUTILIZED_STORAGE_MULTIPLIER = 1.5  # 1.5x savings for underutilized storage
    OVERUTILIZED_STORAGE_PENALTY = 0.7  # Reduce savings by 30% if overutilized
    
    # Storage Utilization Thresholds (percentages)
    STORAGE_UNDERUTILIZED_THRESHOLD = 30  # Below 30% is underutilized
    STORAGE_OPTIMAL_UTILIZATION = 75  # Target storage utilization
    STORAGE_OVERUTILIZED_THRESHOLD = 90  # Above 90% is overutilized
    
    # Storage Type Optimization Factors
    SSD_OPTIMIZATION_FACTOR = 1.2  # Premium storage has higher optimization potential
    HDD_OPTIMIZATION_FACTOR = 1.0  # Standard HDD optimization
    PREMIUM_STORAGE_FACTOR = 1.3  # Premium/managed storage optimization
    
    # Minimum Savings Thresholds
    MINIMUM_STORAGE_SAVINGS_THRESHOLD = 5.0  # Don't recommend changes < $5/month
    MINIMUM_STORAGE_PERCENTAGE_THRESHOLD = 0.03  # Don't recommend changes < 3%


class StorageTypeStandards:
    """Standards for different storage types and their optimization potential"""
    
    # Storage Class Optimization Rates
    STANDARD_STORAGE_OPTIMIZATION_RATE = 0.15  # 15% optimization for standard storage
    PREMIUM_SSD_OPTIMIZATION_RATE = 0.25  # 25% optimization for premium SSD
    MANAGED_DISK_OPTIMIZATION_RATE = 0.20  # 20% optimization for managed disks
    PERSISTENT_VOLUME_OPTIMIZATION_RATE = 0.18  # 18% optimization for PVs
    
    # Storage Access Pattern Multipliers
    FREQUENT_ACCESS_MULTIPLIER = 0.8  # Less optimization for frequently accessed
    INFREQUENT_ACCESS_MULTIPLIER = 1.2  # More optimization for infrequent access
    ARCHIVE_ACCESS_MULTIPLIER = 1.5  # Highest optimization for archive storage


class StorageCostStandards:
    """Cost calculation standards for storage optimization"""
    
    # Cost Optimization Factors
    DEDUPLICATION_SAVINGS_FACTOR = 0.3  # 30% potential savings from deduplication
    COMPRESSION_SAVINGS_FACTOR = 0.25  # 25% potential savings from compression
    TIERING_SAVINGS_FACTOR = 0.4  # 40% potential savings from intelligent tiering
    
    # Lifecycle Management Savings
    AUTOMATED_LIFECYCLE_SAVINGS = 0.35  # 35% savings from automated lifecycle management
    MANUAL_LIFECYCLE_SAVINGS = 0.20  # 20% savings from manual lifecycle management
    
    # Backup and Snapshot Optimization
    SNAPSHOT_OPTIMIZATION_SAVINGS = 0.3  # 30% savings from snapshot optimization
    BACKUP_DEDUPLICATION_SAVINGS = 0.4  # 40% savings from backup deduplication