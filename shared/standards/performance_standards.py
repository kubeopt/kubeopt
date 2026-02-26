"""
Performance Standards for AKS
=============================

Comprehensive performance standards covering application performance,
system performance, scalability, reliability, and performance optimization.
"""

class ApplicationPerformanceStandards:
    """Application-level performance standards and SLAs"""
    
    # =============================================
    # RESPONSE TIME STANDARDS
    # =============================================
    
    # Response Time Thresholds (milliseconds)
    RESPONSE_TIME_EXCELLENT = 100         # <100ms - Excellent
    RESPONSE_TIME_GOOD = 300              # <300ms - Good  
    RESPONSE_TIME_ACCEPTABLE = 1000       # <1000ms - Acceptable
    RESPONSE_TIME_POOR = 3000             # <3000ms - Poor
    RESPONSE_TIME_UNACCEPTABLE = 5000     # >5000ms - Unacceptable
    
    # Percentile-based Response Time Standards
    P50_RESPONSE_TIME_TARGET = 200        # 200ms - 50th percentile target
    P90_RESPONSE_TIME_TARGET = 500        # 500ms - 90th percentile target
    P95_RESPONSE_TIME_TARGET = 800        # 800ms - 95th percentile target
    P99_RESPONSE_TIME_TARGET = 2000       # 2000ms - 99th percentile target
    
    # API-specific Response Time Standards
    API_READ_RESPONSE_TIME_TARGET = 100   # 100ms - Read API target
    API_WRITE_RESPONSE_TIME_TARGET = 500  # 500ms - Write API target
    API_SEARCH_RESPONSE_TIME_TARGET = 300 # 300ms - Search API target
    API_REPORT_RESPONSE_TIME_TARGET = 5000 # 5000ms - Report API target
    
    # =============================================
    # THROUGHPUT STANDARDS
    # =============================================
    
    # Throughput Capacity (requests per second)
    THROUGHPUT_LOW = 100                  # 100 RPS - Low throughput
    THROUGHPUT_MEDIUM = 1000              # 1,000 RPS - Medium throughput
    THROUGHPUT_HIGH = 10000               # 10,000 RPS - High throughput
    THROUGHPUT_VERY_HIGH = 50000          # 50,000 RPS - Very high throughput
    THROUGHPUT_EXTREME = 100000           # 100,000 RPS - Extreme throughput
    
    # Concurrent User Standards
    CONCURRENT_USERS_SMALL = 100          # 100 concurrent users - Small
    CONCURRENT_USERS_MEDIUM = 1000        # 1,000 concurrent users - Medium
    CONCURRENT_USERS_LARGE = 10000        # 10,000 concurrent users - Large
    CONCURRENT_USERS_ENTERPRISE = 50000   # 50,000 concurrent users - Enterprise
    
    # =============================================
    # ERROR RATE STANDARDS
    # =============================================
    
    # Error Rate Thresholds (percentage)
    ERROR_RATE_EXCELLENT = 0.1            # 0.1% - Excellent error rate
    ERROR_RATE_GOOD = 0.5                 # 0.5% - Good error rate
    ERROR_RATE_ACCEPTABLE = 1.0           # 1.0% - Acceptable error rate
    ERROR_RATE_POOR = 5.0                 # 5.0% - Poor error rate
    ERROR_RATE_CRITICAL = 10.0            # 10.0% - Critical error rate
    
    # HTTP Status Code Standards
    HTTP_2XX_TARGET_PERCENTAGE = 99.5     # 99.5% - Success rate target
    HTTP_4XX_MAX_PERCENTAGE = 0.4         # 0.4% - Max client error rate
    HTTP_5XX_MAX_PERCENTAGE = 0.1         # 0.1% - Max server error rate
    
    # =============================================
    # AVAILABILITY STANDARDS
    # =============================================
    
    # Service Level Objectives (SLO)
    SLO_AVAILABILITY_BASIC = 99.0         # 99.0% - Basic availability
    SLO_AVAILABILITY_STANDARD = 99.9      # 99.9% - Standard availability
    SLO_AVAILABILITY_HIGH = 99.95         # 99.95% - High availability
    SLO_AVAILABILITY_PREMIUM = 99.99      # 99.99% - Premium availability
    SLO_AVAILABILITY_ULTRA = 99.999       # 99.999% - Ultra availability
    
    # Downtime Allowances (minutes per month)
    DOWNTIME_BASIC_MINUTES = 432          # 99.0% = 432 minutes downtime
    DOWNTIME_STANDARD_MINUTES = 43.2      # 99.9% = 43.2 minutes downtime  
    DOWNTIME_HIGH_MINUTES = 21.6          # 99.95% = 21.6 minutes downtime
    DOWNTIME_PREMIUM_MINUTES = 4.32       # 99.99% = 4.32 minutes downtime


class SystemPerformanceStandards:
    """System-level performance standards for infrastructure"""
    
    # =============================================
    # CPU PERFORMANCE STANDARDS
    # =============================================
    
    # CPU Utilization Performance Bands
    CPU_UTILIZATION_OPTIMAL = 70          # 70% - Optimal CPU utilization
    CPU_UTILIZATION_HIGH_PERFORMANCE = 80 # 80% - High performance threshold
    CPU_UTILIZATION_STRESS = 90           # 90% - Stress threshold
    CPU_UTILIZATION_CRITICAL = 95         # 95% - Critical threshold
    
    # CPU Performance Targets
    CPU_CONTEXT_SWITCHES_PER_SEC = 10000  # Context switches per second
    CPU_INTERRUPTS_PER_SEC = 5000         # Interrupts per second
    CPU_LOAD_AVERAGE_TARGET = 2.0         # Load average target
    
    # =============================================
    # MEMORY PERFORMANCE STANDARDS
    # =============================================
    
    # Memory Utilization Performance Bands
    MEMORY_UTILIZATION_OPTIMAL = 75       # 75% - Optimal memory utilization
    MEMORY_UTILIZATION_HIGH = 85          # 85% - High utilization threshold
    MEMORY_UTILIZATION_STRESS = 95        # 95% - Stress threshold
    MEMORY_UTILIZATION_CRITICAL = 98      # 98% - Critical threshold
    
    # Memory Performance Metrics
    MEMORY_PAGE_FAULTS_PER_SEC = 1000     # Page faults per second threshold
    MEMORY_SWAP_USAGE_MAX_PERCENT = 10    # Maximum 10% swap usage
    MEMORY_CACHE_HIT_RATIO_TARGET = 95    # 95% cache hit ratio target

    # =============================================
    # ML WORKLOAD CLASSIFICATION THRESHOLDS
    # =============================================
    # Ratios relative to CPU_UTILIZATION_OPTIMAL for workload type classification
    CLASSIFICATION_CPU_INTENSIVE_MEMORY_RATIO = 0.71   # Memory below optimal*0.71 → CPU_INTENSIVE
    CLASSIFICATION_MEMORY_INTENSIVE_CPU_RATIO = 0.57   # CPU below optimal*0.57 → MEMORY_INTENSIVE
    CLASSIFICATION_LOW_UTIL_CPU_RATIO = 0.36           # CPU below optimal*0.36 → LOW_UTILIZATION
    CLASSIFICATION_LOW_UTIL_MEMORY_RATIO = 0.50        # Memory below optimal*0.50 → LOW_UTILIZATION
    CLASSIFICATION_BURSTY_FREQ_THRESHOLD = 0.3         # Burst frequency > 0.3 → BURSTY
    CLASSIFICATION_BURSTY_CV_THRESHOLD = 0.5           # Coefficient of variation > 0.5 → BURSTY
    
    # =============================================
    # DISK PERFORMANCE STANDARDS
    # =============================================
    
    # Disk I/O Performance Standards
    DISK_IOPS_STANDARD_SSD = 500          # 500 IOPS - Standard SSD
    DISK_IOPS_PREMIUM_SSD = 7500          # 7,500 IOPS - Premium SSD
    DISK_IOPS_ULTRA_SSD = 160000          # 160,000 IOPS - Ultra SSD
    
    # Disk Latency Standards (milliseconds)
    DISK_LATENCY_EXCELLENT = 1            # 1ms - Excellent latency
    DISK_LATENCY_GOOD = 5                 # 5ms - Good latency
    DISK_LATENCY_ACCEPTABLE = 10          # 10ms - Acceptable latency
    DISK_LATENCY_POOR = 20                # 20ms - Poor latency
    
    # Disk Throughput Standards (MB/s)
    DISK_THROUGHPUT_STANDARD = 60         # 60 MB/s - Standard SSD
    DISK_THROUGHPUT_PREMIUM = 250         # 250 MB/s - Premium SSD
    DISK_THROUGHPUT_ULTRA = 4000          # 4,000 MB/s - Ultra SSD
    
    # =============================================
    # NETWORK PERFORMANCE STANDARDS
    # =============================================
    
    # Network Latency Standards (milliseconds)
    NETWORK_LATENCY_EXCELLENT = 1         # 1ms - Excellent latency
    NETWORK_LATENCY_GOOD = 5              # 5ms - Good latency
    NETWORK_LATENCY_ACCEPTABLE = 20       # 20ms - Acceptable latency
    NETWORK_LATENCY_POOR = 50             # 50ms - Poor latency
    
    # Network Throughput Standards (Mbps)
    NETWORK_BANDWIDTH_BASIC = 100         # 100 Mbps - Basic bandwidth
    NETWORK_BANDWIDTH_STANDARD = 1000     # 1 Gbps - Standard bandwidth
    NETWORK_BANDWIDTH_HIGH = 10000        # 10 Gbps - High bandwidth
    NETWORK_BANDWIDTH_PREMIUM = 25000     # 25 Gbps - Premium bandwidth
    
    # Network Quality Standards
    NETWORK_PACKET_LOSS_MAX = 0.1         # 0.1% - Maximum packet loss
    NETWORK_JITTER_MAX_MS = 10            # 10ms - Maximum jitter
    NETWORK_UTILIZATION_TARGET = 70       # 70% - Target utilization


class ScalabilityStandards:
    """Scalability and elasticity performance standards"""
    
    # =============================================
    # HORIZONTAL SCALING STANDARDS
    # =============================================
    
    # Scaling Performance Targets
    SCALE_UP_TIME_TARGET_SECONDS = 30     # 30 seconds - Scale up time
    SCALE_DOWN_TIME_TARGET_SECONDS = 60   # 60 seconds - Scale down time
    SCALE_OUT_TIME_TARGET_SECONDS = 90    # 90 seconds - Scale out time
    SCALE_IN_TIME_TARGET_SECONDS = 120    # 120 seconds - Scale in time
    
    # Scaling Efficiency Standards
    SCALING_EFFICIENCY_TARGET = 90        # 90% - Scaling efficiency
    SCALING_OVERHEAD_MAX_PERCENT = 10     # 10% - Maximum scaling overhead
    SCALING_SUCCESS_RATE_TARGET = 99      # 99% - Scaling success rate
    
    # Auto-scaling Performance
    AUTOSCALING_DECISION_TIME_SECONDS = 15 # 15 seconds - Decision time
    AUTOSCALING_REACTION_TIME_SECONDS = 45 # 45 seconds - Reaction time
    AUTOSCALING_STABILIZATION_SECONDS = 300 # 300 seconds - Stabilization
    
    # =============================================
    # VERTICAL SCALING STANDARDS
    # =============================================
    
    # Vertical Scaling Performance
    VERTICAL_SCALE_TIME_SECONDS = 60      # 60 seconds - Vertical scale time
    VERTICAL_SCALE_DOWNTIME_SECONDS = 10  # 10 seconds - Downtime during scale
    VERTICAL_SCALE_SUCCESS_RATE = 95      # 95% - Success rate
    
    # Resource Adjustment Performance
    CPU_ADJUSTMENT_TIME_SECONDS = 30      # 30 seconds - CPU adjustment
    MEMORY_ADJUSTMENT_TIME_SECONDS = 45   # 45 seconds - Memory adjustment
    STORAGE_ADJUSTMENT_TIME_SECONDS = 120 # 120 seconds - Storage adjustment
    
    # =============================================
    # ELASTICITY STANDARDS
    # =============================================
    
    # Elasticity Performance Metrics
    ELASTICITY_RESPONSE_TIME_SECONDS = 120 # 120 seconds - Elasticity response
    ELASTICITY_ACCURACY_PERCENT = 85      # 85% - Elasticity accuracy
    ELASTICITY_STABILITY_PERCENT = 95     # 95% - Elasticity stability
    
    # Load Handling Standards
    BURST_CAPACITY_MULTIPLIER = 3         # 3x - Burst capacity multiplier
    SUSTAINED_LOAD_MULTIPLIER = 2         # 2x - Sustained load multiplier
    PEAK_LOAD_DURATION_MINUTES = 15       # 15 minutes - Peak load duration


class KubernetesPerformanceStandards:
    """Kubernetes-specific performance standards"""
    
    # =============================================
    # POD PERFORMANCE STANDARDS
    # =============================================
    
    # Pod Startup Performance
    POD_STARTUP_TIME_TARGET_SECONDS = 30  # 30 seconds - Pod startup time
    POD_READY_TIME_TARGET_SECONDS = 45    # 45 seconds - Pod ready time
    POD_TERMINATION_TIME_SECONDS = 30     # 30 seconds - Pod termination
    
    # Pod Lifecycle Performance
    POD_RESTART_TIME_SECONDS = 60         # 60 seconds - Pod restart time
    POD_SCHEDULING_TIME_SECONDS = 5       # 5 seconds - Pod scheduling time
    POD_IMAGE_PULL_TIME_SECONDS = 120     # 120 seconds - Image pull time
    
    # Container Performance
    CONTAINER_STARTUP_TIME_SECONDS = 15   # 15 seconds - Container startup
    CONTAINER_HEALTH_CHECK_INTERVAL = 10  # 10 seconds - Health check interval
    CONTAINER_LIVENESS_PROBE_TIMEOUT = 5  # 5 seconds - Liveness probe timeout
    
    # =============================================
    # CLUSTER PERFORMANCE STANDARDS
    # =============================================
    
    # API Server Performance
    API_SERVER_RESPONSE_TIME_MS = 100     # 100ms - API server response
    API_SERVER_THROUGHPUT_QPS = 1000      # 1000 QPS - API server throughput
    API_SERVER_AVAILABILITY_PERCENT = 99.9 # 99.9% - API server availability
    
    # etcd Performance Standards
    ETCD_RESPONSE_TIME_MS = 10            # 10ms - etcd response time
    ETCD_THROUGHPUT_QPS = 10000           # 10,000 QPS - etcd throughput
    ETCD_DISK_LATENCY_MS = 5              # 5ms - etcd disk latency
    
    # Scheduler Performance
    SCHEDULER_THROUGHPUT_PODS_SEC = 100   # 100 pods/sec - Scheduler throughput
    SCHEDULER_LATENCY_MS = 50             # 50ms - Scheduler latency
    SCHEDULER_SUCCESS_RATE_PERCENT = 99   # 99% - Scheduler success rate
    
    # =============================================
    # SERVICE MESH PERFORMANCE
    # =============================================
    
    # Istio Performance Standards
    ISTIO_PROXY_LATENCY_OVERHEAD_MS = 1   # 1ms - Proxy latency overhead
    ISTIO_PROXY_THROUGHPUT_RPS = 10000    # 10,000 RPS - Proxy throughput
    ISTIO_CONTROL_PLANE_CPU_PERCENT = 5   # 5% - Control plane CPU usage
    
    # Service Discovery Performance
    SERVICE_DISCOVERY_TIME_MS = 100       # 100ms - Service discovery time
    DNS_RESOLUTION_TIME_MS = 10           # 10ms - DNS resolution time
    ENDPOINT_UPDATE_TIME_MS = 500         # 500ms - Endpoint update time


class DatabasePerformanceStandards:
    """Database performance standards for AKS workloads"""
    
    # =============================================
    # DATABASE RESPONSE TIME STANDARDS
    # =============================================
    
    # Query Response Time Thresholds (milliseconds)
    DB_QUERY_EXCELLENT = 10               # 10ms - Excellent query time
    DB_QUERY_GOOD = 50                    # 50ms - Good query time
    DB_QUERY_ACCEPTABLE = 200             # 200ms - Acceptable query time
    DB_QUERY_POOR = 1000                  # 1000ms - Poor query time
    
    # Transaction Performance
    DB_TRANSACTION_TIME_MS = 100          # 100ms - Transaction time target
    DB_COMMIT_TIME_MS = 50                # 50ms - Commit time target
    DB_ROLLBACK_TIME_MS = 25              # 25ms - Rollback time target
    
    # =============================================
    # DATABASE THROUGHPUT STANDARDS
    # =============================================
    
    # Database Throughput (transactions per second)
    DB_TPS_LOW = 100                      # 100 TPS - Low throughput
    DB_TPS_MEDIUM = 1000                  # 1,000 TPS - Medium throughput
    DB_TPS_HIGH = 10000                   # 10,000 TPS - High throughput
    DB_TPS_ENTERPRISE = 50000             # 50,000 TPS - Enterprise throughput
    
    # Connection Pool Performance
    DB_CONNECTION_POOL_SIZE = 20          # 20 - Default pool size
    DB_CONNECTION_TIMEOUT_MS = 5000       # 5000ms - Connection timeout
    DB_CONNECTION_ACQUISITION_MS = 100    # 100ms - Connection acquisition
    
    # =============================================
    # DATABASE RESOURCE STANDARDS
    # =============================================
    
    # Database CPU Standards
    DB_CPU_UTILIZATION_TARGET = 70        # 70% - DB CPU utilization target
    DB_CPU_UTILIZATION_MAX = 85           # 85% - DB CPU utilization max
    
    # Database Memory Standards
    DB_MEMORY_UTILIZATION_TARGET = 80     # 80% - DB memory utilization target
    DB_BUFFER_CACHE_HIT_RATIO = 95        # 95% - Buffer cache hit ratio
    
    # Database Storage Standards
    DB_STORAGE_IOPS_MINIMUM = 1000        # 1000 IOPS - Minimum storage IOPS
    DB_STORAGE_LATENCY_MAX_MS = 5         # 5ms - Maximum storage latency


class MonitoringPerformanceStandards:
    """Performance monitoring and observability standards"""
    
    # =============================================
    # METRICS COLLECTION STANDARDS
    # =============================================
    
    # Metrics Collection Performance
    METRICS_COLLECTION_INTERVAL_SECONDS = 15 # 15 seconds - Collection interval
    METRICS_RETENTION_DAYS = 30           # 30 days - Metrics retention
    METRICS_INGESTION_LATENCY_MS = 100    # 100ms - Ingestion latency
    
    # Monitoring System Performance
    MONITORING_QUERY_RESPONSE_MS = 500    # 500ms - Query response time
    MONITORING_DASHBOARD_LOAD_MS = 2000   # 2000ms - Dashboard load time
    MONITORING_ALERT_DELIVERY_SECONDS = 30 # 30 seconds - Alert delivery
    
    # =============================================
    # LOGGING PERFORMANCE STANDARDS
    # =============================================
    
    # Log Processing Performance
    LOG_INGESTION_RATE_EVENTS_SEC = 10000 # 10,000 events/sec - Ingestion rate
    LOG_SEARCH_RESPONSE_TIME_MS = 1000    # 1000ms - Search response time
    LOG_INDEXING_LATENCY_SECONDS = 60     # 60 seconds - Indexing latency
    
    # Log Storage Performance
    LOG_RETENTION_DAYS = 30               # 30 days - Log retention
    LOG_COMPRESSION_RATIO = 10            # 10:1 - Compression ratio
    LOG_STORAGE_COST_PER_GB = 0.03        # $0.03/GB - Storage cost
    
    # =============================================
    # ALERTING PERFORMANCE STANDARDS
    # =============================================
    
    # Alert Processing Performance
    ALERT_EVALUATION_INTERVAL_SECONDS = 30 # 30 seconds - Evaluation interval
    ALERT_DELIVERY_TIME_SECONDS = 60      # 60 seconds - Alert delivery time
    ALERT_ESCALATION_TIME_MINUTES = 15    # 15 minutes - Escalation time
    
    # Alert Quality Standards
    ALERT_FALSE_POSITIVE_RATE_PERCENT = 5 # 5% - False positive rate
    ALERT_COVERAGE_PERCENT = 95           # 95% - Alert coverage
    ALERT_ACCURACY_PERCENT = 95           # 95% - Alert accuracy


class CachePerformanceStandards:
    """Caching performance standards for improved application performance"""
    
    # =============================================
    # CACHE HIT RATIO STANDARDS
    # =============================================
    
    # Cache Hit Ratio Targets
    CACHE_HIT_RATIO_EXCELLENT = 95        # 95% - Excellent hit ratio
    CACHE_HIT_RATIO_GOOD = 85             # 85% - Good hit ratio
    CACHE_HIT_RATIO_ACCEPTABLE = 70       # 70% - Acceptable hit ratio
    CACHE_HIT_RATIO_POOR = 50             # 50% - Poor hit ratio
    
    # Cache Performance Metrics
    CACHE_RESPONSE_TIME_MS = 1            # 1ms - Cache response time
    CACHE_THROUGHPUT_OPS_SEC = 100000     # 100,000 ops/sec - Throughput
    CACHE_EVICTION_RATE_PERCENT = 5       # 5% - Eviction rate
    
    # =============================================
    # CACHE CONFIGURATION STANDARDS
    # =============================================
    
    # Cache Size Standards
    CACHE_MEMORY_UTILIZATION_TARGET = 80  # 80% - Memory utilization target
    CACHE_TTL_DEFAULT_SECONDS = 3600      # 3600 seconds - Default TTL
    CACHE_MAX_ENTRIES = 1000000           # 1M - Maximum cache entries
    
    # Cache Warming Standards
    CACHE_WARM_UP_TIME_MINUTES = 10       # 10 minutes - Warm-up time
    CACHE_PRELOAD_PERCENTAGE = 20         # 20% - Preload percentage
    CACHE_REFRESH_AHEAD_PERCENTAGE = 10   # 10% - Refresh ahead


# =============================================
# PERFORMANCE TESTING STANDARDS
# =============================================

class PerformanceTestingStandards:
    """Standards for performance testing and benchmarking"""
    
    # Load Testing Standards
    LOAD_TEST_DURATION_MINUTES = 30       # 30 minutes - Load test duration
    LOAD_TEST_RAMP_UP_MINUTES = 5         # 5 minutes - Ramp-up time
    LOAD_TEST_USERS_BASELINE = 100        # 100 users - Baseline load
    
    # Stress Testing Standards
    STRESS_TEST_PEAK_MULTIPLIER = 5       # 5x - Peak load multiplier
    STRESS_TEST_DURATION_MINUTES = 15     # 15 minutes - Stress test duration
    STRESS_TEST_FAILURE_THRESHOLD = 10    # 10% - Failure threshold
    
    # Performance Benchmarking
    BENCHMARK_BASELINE_VARIANCE = 5       # 5% - Acceptable variance
    BENCHMARK_REGRESSION_THRESHOLD = 10   # 10% - Regression threshold
    BENCHMARK_IMPROVEMENT_TARGET = 15     # 15% - Improvement target


# =============================================
# USAGE EXAMPLES
# =============================================
"""
USAGE EXAMPLES:
===============

from standards.performance_standards import ApplicationPerformanceStandards as AppPerf
from standards.performance_standards import SystemPerformanceStandards as SysPerf

# Validate response time
if response_time_ms > AppPerf.RESPONSE_TIME_ACCEPTABLE:
    logger.warning(f"Response time {response_time_ms}ms exceeds acceptable threshold")

# Check CPU utilization
if cpu_utilization > SysPerf.CPU_UTILIZATION_STRESS:
    logger.error(f"CPU utilization {cpu_utilization}% in stress zone")

# Validate scaling performance
if scale_up_time > ScalabilityStandards.SCALE_UP_TIME_TARGET_SECONDS:
    logger.warning(f"Scale up time {scale_up_time}s exceeds target")

PERFORMANCE OPTIMIZATION GUIDELINES:
===================================

1. Monitor all key performance indicators against standards
2. Set up automated alerts for performance threshold breaches
3. Implement performance testing in CI/CD pipelines
4. Regular performance benchmarking and regression testing
5. Optimize based on 95th percentile, not just averages
6. Consider user experience impact of performance changes
7. Balance performance with cost optimization
"""