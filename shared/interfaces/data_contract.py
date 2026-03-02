#!/usr/bin/env python3
"""
Data Contract Interface for AKS Cost Optimizer
Defines standardized field names and data structures across the entire pipeline
"""

class DataContractDict(dict):
    """
    Enforced dictionary that only allows approved field names
    Replaces regular dict to prevent unapproved field usage
    """
    
    # Class-level enforcement mode and violation tracking
    ENFORCEMENT_MODE = "warning"  # "strict" or "warning"
    _violations_collected = set()  # Track unique violations across all instances
    
    @classmethod
    def set_enforcement_mode(cls, mode):
        """Set enforcement mode to 'strict' or 'warning'"""
        if mode not in ["strict", "warning"]:
            raise ValueError("Mode must be 'strict' or 'warning'")
        cls.ENFORCEMENT_MODE = mode
        if mode == "strict":
            # Clear violations when switching to strict mode
            cls._violations_collected.clear()
    
    @classmethod
    def get_collected_violations(cls):
        """Get all collected field violations"""
        return sorted(list(cls._violations_collected))
    
    @classmethod  
    def clear_violations(cls):
        """Clear collected violations"""
        cls._violations_collected.clear()
    
    def __init__(self, data=None, context=""):
        self._context = context
        self._approved_fields = AnalysisDataContract.get_approved_fields()
        super().__init__()
        
        if data:
            for key, value in data.items():
                self[key] = value
    
    def __setitem__(self, key, value):
        """Enforce approved fields on assignment"""
        if key not in self._approved_fields:
            # Check if it's a mapped field that should be normalized
            normalized_key = AnalysisDataContract.normalize_field_name(key)
            if normalized_key != key and normalized_key in self._approved_fields:
                # Auto-normalize the field name and preserve nested structure
                processed_value = self._preserve_nested_structure(value, f"{self._context}.{normalized_key}")
                super().__setitem__(normalized_key, processed_value)
                return
            
            # Record violation
            violation_msg = f"'{key}' not in approved fields (context: {self._context})"
            DataContractDict._violations_collected.add(key)
            
            if DataContractDict.ENFORCEMENT_MODE == "strict":
                raise ValueError(f"❌ FIELD VIOLATION in {self._context}: "
                               f"'{key}' not in approved fields. "
                               f"Add to data_contract.py or use approved field.")
            else:
                # Warning mode - log but don't fail
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ FIELD VIOLATION WARNING in {self._context}: {violation_msg}")
                # Allow the field to be set in warning mode, preserving nested structure
                processed_value = self._preserve_nested_structure(value, f"{self._context}.{key}")
                super().__setitem__(key, processed_value)
                return
        
        # Preserve nested structure for approved fields too
        processed_value = self._preserve_nested_structure(value, f"{self._context}.{key}")
        super().__setitem__(key, processed_value)
    
    def _preserve_nested_structure(self, value, context):
        """Preserve nested dictionaries and lists while maintaining data contract enforcement"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 PRESERVE DEBUG: _preserve_nested_structure() called with context='{context}', value_type={type(value)}")
        
        if isinstance(value, dict):
            logger.info(f"🔍 PRESERVE DEBUG: Processing dict with {len(value)} keys: {list(value.keys())}")
            # Log sample data for node dicts
            if 'name' in value or 'cpu_usage_pct' in value:
                logger.info(f"🔍 PRESERVE DEBUG: Node data BEFORE conversion - name: '{value.get('name')}', cpu_usage_pct: {value.get('cpu_usage_pct')}")
            
            # Convert nested dict to DataContractDict to preserve structure
            result = DataContractDict(value, context)
            
            # Log sample data after conversion
            if 'name' in value or 'cpu_usage_pct' in value:
                try:
                    result_name = result.get('name', 'UNKNOWN')
                    result_cpu = result.get('cpu_usage_pct', 'MISSING')
                    logger.info(f"🔍 PRESERVE DEBUG: Node data AFTER conversion - name: '{result_name}', cpu_usage_pct: {result_cpu}")
                except Exception as e:
                    logger.info(f"🔍 PRESERVE DEBUG: Error accessing converted data: {e}")
            
            return result
            
        elif isinstance(value, list):
            logger.info(f"🔍 PRESERVE DEBUG: Processing list with {len(value)} items")
            # Process each item in the list
            processed_list = []
            for i, item in enumerate(value):
                logger.info(f"🔍 PRESERVE DEBUG: Processing list item {i}, type={type(item)}")
                if isinstance(item, dict):
                    logger.info(f"🔍 PRESERVE DEBUG: List item {i} is dict with keys: {list(item.keys())}")
                    # Log node data if present
                    if 'name' in item or 'cpu_usage_pct' in item:
                        logger.info(f"🔍 PRESERVE DEBUG: List item {i} node data BEFORE - name: '{item.get('name')}', cpu_usage_pct: {item.get('cpu_usage_pct')}")
                    
                    # Convert dict items to DataContractDict
                    converted_item = DataContractDict(item, f"{context}[{i}]")
                    
                    # Log node data after conversion
                    if 'name' in item or 'cpu_usage_pct' in item:
                        try:
                            converted_name = converted_item.get('name', 'UNKNOWN')
                            converted_cpu = converted_item.get('cpu_usage_pct', 'MISSING')
                            logger.info(f"🔍 PRESERVE DEBUG: List item {i} node data AFTER - name: '{converted_name}', cpu_usage_pct: {converted_cpu}")
                        except Exception as e:
                            logger.info(f"🔍 PRESERVE DEBUG: Error accessing list item {i} converted data: {e}")
                    
                    processed_list.append(converted_item)
                else:
                    logger.info(f"🔍 PRESERVE DEBUG: List item {i} is primitive, keeping as-is: {item}")
                    # Keep primitive values as-is
                    processed_list.append(item)
            
            logger.info(f"🔍 PRESERVE DEBUG: Processed list complete, returning {len(processed_list)} items")
            return processed_list
        else:
            logger.info(f"🔍 PRESERVE DEBUG: Value is primitive type {type(value)}, returning unchanged: {value}")
            # Return primitive values unchanged
            return value
    
    def get(self, key, default=None):
        """Override get() to enforce contract"""
        if key in self:
            return super().get(key, default)
        
        # Try normalized field name
        normalized_key = AnalysisDataContract.normalize_field_name(key)
        if normalized_key in self:
            return super().get(normalized_key, default)
            
        # Respect enforcement mode for field access violations
        if default is None:
            if DataContractDict.ENFORCEMENT_MODE == "strict":
                raise KeyError(f"❌ FIELD ACCESS VIOLATION: '{key}' not found. "
                             f"Use only approved fields from data contract.")
            else:
                # Warning mode - log but return None
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ FIELD ACCESS WARNING in {self._context}: '{key}' not found in approved fields")
                DataContractDict._violations_collected.add(key)
                return None
        
        return default


class ValidationOnlyDataContract:
    """
    NEW: Validation-only data contract that checks data integrity without modifying data
    Provides field validation, type checking, and consistency verification
    WITHOUT corrupting or modifying the original data structures
    """
    
    @staticmethod
    def validate_without_modification(data: dict, context: str = "", enforce_strict: bool = False) -> dict:
        """
        Validate data integrity without modifying the original data
        Returns the original data unchanged but logs validation issues
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not isinstance(data, dict):
            logger.warning(f"⚠️ VALIDATION: {context} - Expected dict, got {type(data)}")
            return data
        
        approved_fields = AnalysisDataContract.get_approved_fields()
        violations = []
        suggestions = []
        
        # Check each field in the data
        for field_name, field_value in data.items():
            # Check if field is approved
            if field_name not in approved_fields:
                # Check if it has a normalized equivalent
                normalized_name = AnalysisDataContract.normalize_field_name(field_name)
                if normalized_name != field_name and normalized_name in approved_fields:
                    suggestions.append(f"Field '{field_name}' could be normalized to '{normalized_name}'")
                else:
                    violations.append(field_name)
            
            # Validate nested structures recursively
            if isinstance(field_value, dict):
                ValidationOnlyDataContract.validate_without_modification(
                    field_value, 
                    f"{context}.{field_name}",
                    enforce_strict
                )
            elif isinstance(field_value, list):
                for i, item in enumerate(field_value):
                    if isinstance(item, dict):
                        ValidationOnlyDataContract.validate_without_modification(
                            item,
                            f"{context}.{field_name}[{i}]",
                            enforce_strict
                        )
        
        # Log validation results
        if violations:
            violation_msg = f"Field violations in {context}: {violations}"
            if enforce_strict:
                raise ValueError(f"❌ STRICT VALIDATION FAILED: {violation_msg}")
            else:
                logger.warning(f"⚠️ VALIDATION WARNING: {violation_msg}")
        
        if suggestions:
            logger.info(f"💡 VALIDATION SUGGESTIONS for {context}: {suggestions}")
        
        if not violations and not suggestions:
            logger.debug(f"✅ VALIDATION PASSED: {context} - All fields approved")
        
        # Return original data unchanged
        return data
    
    @staticmethod
    def check_critical_fields(data: dict, required_fields: list, context: str = "") -> bool:
        """
        Check that critical fields are present and not None/empty
        """
        import logging
        logger = logging.getLogger(__name__)
        
        missing_fields = []
        empty_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            elif data[field] is None or data[field] == "MISSING":
                empty_fields.append(field)
        
        if missing_fields:
            logger.error(f"❌ CRITICAL FIELD CHECK FAILED in {context}: Missing fields {missing_fields}")
            return False
        
        if empty_fields:
            logger.error(f"❌ CRITICAL FIELD CHECK FAILED in {context}: Empty/corrupted fields {empty_fields}")
            return False
        
        logger.debug(f"✅ CRITICAL FIELD CHECK PASSED: {context}")
        return True
    
    @staticmethod
    def suggest_field_mappings(data: dict, context: str = "") -> dict:
        """
        Analyze data and suggest field mappings without modifying the data
        Returns a mapping dictionary of suggested changes
        """
        import logging
        logger = logging.getLogger(__name__)
        
        suggested_mappings = {}
        approved_fields = AnalysisDataContract.get_approved_fields()
        
        for field_name in data.keys():
            if field_name not in approved_fields:
                normalized_name = AnalysisDataContract.normalize_field_name(field_name)
                if normalized_name != field_name and normalized_name in approved_fields:
                    suggested_mappings[field_name] = normalized_name
        
        if suggested_mappings:
            logger.info(f"💡 FIELD MAPPING SUGGESTIONS for {context}: {suggested_mappings}")
        
        return suggested_mappings
    
    @staticmethod
    def apply_safe_field_normalization(data: dict, context: str = "") -> dict:
        """
        Safely apply field normalization to a copy of the data
        Does NOT modify the original data - creates a new normalized copy
        """
        import copy
        import logging
        logger = logging.getLogger(__name__)
        
        # Create a deep copy to avoid modifying original
        normalized_data = copy.deepcopy(data)
        
        # Apply field mappings from AnalysisDataContract.normalize_analysis_data
        # But do it safely on the copy
        try:
            normalized_result = AnalysisDataContract.normalize_analysis_data(normalized_data)
            logger.info(f"✅ SAFE NORMALIZATION: Successfully normalized {context}")
            return normalized_result
        except Exception as e:
            logger.warning(f"⚠️ SAFE NORMALIZATION FAILED for {context}: {e} - returning original data")
            return data


class DataContractUtils:
    """
    Utility class for common DataContract operations
    Provides easy-to-use methods for validation and normalization
    """
    
    @staticmethod
    def validate_and_normalize(data: dict, context: str = "", strict: bool = False) -> dict:
        """
        One-stop method: validate data integrity and optionally normalize field names
        Returns either normalized data (if successful) or original data (if validation fails in non-strict mode)
        """
        # First validate without modification
        validated_data = ValidationOnlyDataContract.validate_without_modification(data, context, strict)
        
        # If validation passed, optionally apply safe normalization
        if not strict:  # Only normalize in non-strict mode to avoid data corruption
            normalized_data = ValidationOnlyDataContract.apply_safe_field_normalization(validated_data, context)
            return normalized_data
        
        return validated_data
    
    @staticmethod
    def check_data_integrity(data: dict, critical_fields: list = None, context: str = ""):
        """
        Quick integrity check for critical data fields
        """
        if critical_fields is None:
            critical_fields = ['name', 'cpu_usage_pct']  # Default node fields
        
        return ValidationOnlyDataContract.check_critical_fields(data, critical_fields, context)


class AnalysisDataContract:
    """
    Standard data contract for analysis results flowing through the pipeline
    COMPLETE MAPPING based on comprehensive scan of ALL files
    FROM: algorithmic_cost_analyzer.py + aks_realtime_metrics.py
    TO: chart_generator.py, api_routes.py
    """
    
    # COST FIELDS (standardized names)
    TOTAL_COST = 'total_cost'
    NODE_COST = 'node_cost'  # UI field name - analyzer outputs 'compute_cost' but mapped to 'node_cost'
    COMPUTE_COST = 'compute_cost'  # Analyzer field name - mapped to node_cost in UI
    STORAGE_COST = 'storage_cost'
    NETWORKING_COST = 'networking_cost'
    CONTROL_PLANE_COST = 'control_plane_cost'
    REGISTRY_COST = 'registry_cost'
    LOAD_BALANCER_COST = 'load_balancer_cost'
    PUBLIC_IP_COST = 'public_ip_cost'
    DATA_TRANSFER_COST = 'data_transfer_cost'
    OTHER_NETWORKING_COST = 'other_networking_cost'
    MONITORING_COST = 'monitoring_cost'
    KEYVAULT_COST = 'keyvault_cost'
    BACKUP_RECOVERY_COST = 'backup_recovery_cost'
    SECURITY_COST = 'security_cost'
    GOVERNANCE_COST = 'governance_cost'
    SUPPORT_MANAGEMENT_COST = 'support_management_cost'
    IDLE_COST = 'idle_cost'
    SYSTEM_COST = 'system_cost'
    OTHER_COST = 'other_cost'
    DEVOPS_COST = 'devops_cost'
    APPLICATION_SERVICES_COST = 'application_services_cost'
    DATA_SERVICES_COST = 'data_services_cost'
    INTEGRATION_SERVICES_COST = 'integration_services_cost'
    MONTHLY_COST = 'monthly_cost'
    COST_OPTIMIZATION_INSIGHTS = 'cost_optimization_insights'
    ENHANCEMENT_LEVEL = 'enhancement_level'
    
    # Cost processing metadata fields
    ALLOCATION_METHOD = 'allocation_method'
    ALLOCATION_METHODS_APPLIED = 'allocation_methods_applied'
    SYSTEM_COSTS_ALLOCATED = 'system_costs_allocated'
    SYSTEM_COST_ALLOCATED = 'system_cost_allocated'
    IDLE_COST_CALCULATED = 'idle_cost_calculated'
    NETWORKING_DETAILED = 'networking_detailed'
    DATA_SOURCE = 'data_source'
    IS_SAMPLE_DATA = 'is_sample_data'
    TIMESTAMP = 'timestamp'
    CATEGORIES = 'categories'
    SUBCATEGORIES = 'subcategories'
    NETWORKING_DETAILED_BREAKDOWN = 'networking_detailed_breakdown'
    SERVICE_CATEGORIZATION_ENHANCED = 'service_categorization_enhanced'
    OPTIMIZATION_INSIGHTS_INCLUDED = 'optimization_insights_included'
    
    # ML and optimization analysis fields
    CONSISTENT_RECOMMENDATION = 'consistent_recommendation'
    WORKLOAD_CHARS = 'workload_chars'
    USAGE_PATTERN = 'usage_pattern'
    CPU_OPTIMIZATION_POTENTIAL = 'cpu_optimization_potential'
    MEMORY_OPTIMIZATION_POTENTIAL = 'memory_optimization_potential'
    HPA_SUITABILITY = 'hpa_suitability'
    SYSTEM_EFFICIENCY = 'system_efficiency'
    HIGH_CPU_WORKLOADS = 'high_cpu_workloads'
    MAX_WORKLOAD_CPU = 'max_workload_cpu'
    OPTIMIZATION_CONFIDENCE = 'optimization_confidence'
    CHART_DATA = 'chart_data'
    OPTIMIZATION_RECOMMENDATION = 'optimization_recommendation'
    VALIDATION_PERFORMED = 'validation_performed'
    HPA_DISCREPANCIES = 'hpa_discrepancies'
    RECOMMENDED_MIN_REPLICAS = 'recommended_min_replicas'
    RECOMMENDED_MAX_REPLICAS = 'recommended_max_replicas'
    TITLE = 'title'
    CONSISTENT = 'consistent'
    ISSUES = 'issues'
    MONTHLY_ACTUAL_TOTAL = 'monthly_actual_total'
    MONTHLY_ACTUAL_STORAGE = 'monthly_actual_storage'
    HPA_MONTHLY_SAVINGS = 'hpa_monthly_savings'
    RIGHTSIZING_MONTHLY_SAVINGS = 'rightsizing_monthly_savings'
    COMPUTE_MONTHLY_SAVINGS = 'compute_monthly_savings'
    
    # CPU/MEMORY UTILIZATION (standardized names - NOW CONSISTENT)
    AVG_CPU_UTILIZATION = 'avg_cpu_utilization'  # All components now use this
    AVG_CPU_USAGE_PCT = 'avg_cpu_usage_pct'  # Alternative CPU field name
    AVG_MEMORY_UTILIZATION = 'avg_memory_utilization'  # All components use this
    MAX_CPU_UTILIZATION = 'max_cpu_utilization'  # All components use this
    MAX_MEMORY_UTILIZATION = 'max_memory_utilization'  # All components use this
    CPU_STD_DEV = 'cpu_std_dev'
    MEMORY_STD_DEV = 'memory_std_dev'
    
    # SAVINGS FIELDS (standardized names)
    TOTAL_SAVINGS = 'total_savings'
    TOTAL_POTENTIAL_SAVINGS = 'total_potential_savings'
    HPA_SAVINGS = 'hpa_savings'
    COMPUTE_SAVINGS = 'compute_savings'
    STORAGE_SAVINGS = 'storage_savings'
    NETWORKING_SAVINGS = 'networking_savings'
    NETWORKING_MONTHLY_SAVINGS = 'networking_monthly_savings'
    CONTROL_PLANE_MONTHLY_SAVINGS = 'control_plane_monthly_savings'
    REGISTRY_MONTHLY_SAVINGS = 'registry_monthly_savings'
    MONITORING_MONTHLY_SAVINGS = 'monitoring_monthly_savings'  # ADDED
    IDLE_MONTHLY_SAVINGS = 'idle_monthly_savings'  # ADDED
    INFRASTRUCTURE_MONTHLY_SAVINGS = 'infrastructure_monthly_savings'  # ADDED
    PERFORMANCE_MONTHLY_SAVINGS = 'performance_monthly_savings'  # ADDED
    STORAGE_MONTHLY_SAVINGS = 'storage_monthly_savings'  # ADDED
    HPA_MONTHLY_SAVINGS = 'hpa_monthly_savings'  # ADDED
    COMPUTE_MONTHLY_SAVINGS = 'compute_monthly_savings'  # ADDED
    RIGHTSIZING_MONTHLY_SAVINGS = 'rightsizing_monthly_savings'  # ADDED
    
    # EFFICIENCY FIELDS
    CURRENT_EFFICIENCY = 'current_efficiency'
    TARGET_EFFICIENCY = 'target_efficiency'
    CURRENT_CPU_EFFICIENCY = 'current_cpu_efficiency'
    CURRENT_MEMORY_EFFICIENCY = 'current_memory_efficiency'
    
    # CONFIDENCE/SCORING FIELDS
    CONFIDENCE_SCORE = 'confidence_score'
    ANALYSIS_CONFIDENCE = 'analysis_confidence'  # Alternative confidence field name
    DATA_QUALITY = 'data_quality'
    CONSISTENCY_SCORE = 'consistency_score'
    FEASIBILITY_SCORE = 'feasibility_score'
    CURRENT_HEALTH_SCORE = 'current_health_score'
    TARGET_HEALTH_SCORE = 'target_health_score'
    OPTIMIZATION_SCORE = 'optimization_score'
    
    # GAP FIELDS (calculated from utilization)
    CPU_GAP = 'cpu_gap'
    MEMORY_GAP = 'memory_gap'
    
    # NODE FIELDS
    NODE_COUNT = 'node_count'
    TOTAL_NODES = 'total_nodes'
    NODES = 'nodes'
    TOTAL_CPU_CORES = 'total_cpu_cores'
    TOTAL_MEMORY_GB = 'total_memory_gb'
    
    # WORKLOAD FIELDS
    ALL_WORKLOADS = 'all_workloads'
    TOTAL_WORKLOADS = 'total_workloads'
    HIGH_CPU_COUNT = 'high_cpu_count'
    TOP_CPU_SUMMARY = 'top_cpu_summary'
    
    # HPA FIELDS
    HPA_EFFICIENCY = 'hpa_efficiency'
    HPA_EFFICIENCY_PERCENTAGE = 'hpa_efficiency_percentage'
    HPA_REDUCTION = 'hpa_reduction'
    HPA_RECOMMENDATIONS = 'hpa_recommendations'
    HPA_IMPLEMENTATION = 'hpa_implementation'
    HPA_CPU_METRICS = 'hpa_cpu_metrics'
    HPA_COUNT = 'hpa_count'
    
    # ML FIELDS
    ML_CONFIDENCE = 'ml_confidence'
    WORKLOAD_CLASSIFICATION = 'workload_classification'
    
    # CATEGORY SAVINGS
    SAVINGS_BY_CATEGORY = 'savings_by_category'
    
    # STANDARDS COMPLIANCE
    STANDARDS_COMPLIANCE = 'standards_compliance'
    
    # ADDITIONAL FIELDS FROM ANALYSIS ENGINE (added to final_results)
    COST_LABEL = 'cost_label'
    ACTUAL_PERIOD_COST = 'actual_period_cost' 
    ANALYSIS_PERIOD_DAYS = 'analysis_period_days'
    NODE_METRICS = 'node_metrics'
    REAL_NODE_DATA = 'real_node_data'
    HAS_REAL_NODE_DATA = 'has_real_node_data'
    
    # POD COST ANALYSIS FIELDS
    HAS_POD_COSTS = 'has_pod_costs'
    POD_COST_ANALYSIS = 'pod_cost_analysis'
    NAMESPACE_COSTS = 'namespace_costs'
    NAMESPACE_SUMMARY = 'namespace_summary'
    NAMESPACE_DATA = 'namespaceData'
    WORKLOAD_COSTS = 'workload_costs'
    WORKLOAD_DATA = 'workloadData'
    
    # COMPREHENSIVE FIELDS FROM ALL FILES ANALYSIS
    # Analysis Engine fields
    CLUSTER_INFO = 'cluster_info'
    SUPPORTS_CLUSTER_CONFIG_FETCH = 'supports_cluster_config_fetch'
    CLUSTER_CONFIG_AVAILABLE = 'cluster_config_available'
    OPTIMIZATION_ANALYSIS = 'optimization_analysis'
    NODE_ANALYSIS = 'node_analysis'
    CONFIDENCE_LEVEL = 'confidence_level'
    MONTHLY_ACTUAL_COMPUTE = 'monthly_actual_compute'
    VM_COST = 'vm_cost'
    NODE_POOL_COST = 'node_pool_cost'
    CLUSTER_VALIDATION = 'cluster_validation'
    
    # Current usage analysis
    CURRENT_USAGE_ANALYSIS = 'current_usage_analysis'
    EFFICIENCY_ANALYSIS = 'efficiency_analysis'
    CURRENT_SYSTEM_EFFICIENCY = 'current_system_efficiency'
    TARGET_SYSTEM_EFFICIENCY = 'target_system_efficiency'
    EFFICIENCY_IMPROVEMENT_POTENTIAL = 'efficiency_improvement_potential'
    
    # Node analysis fields
    CURRENT_NODE_COUNT = 'current_node_count'
    UNDERUTILIZED_NODES = 'underutilized_nodes'
    OPTIMIZATION_TYPE = 'optimization_type'
    POTENTIAL_SAVINGS = 'potential_savings'
    POTENTIAL_NODE_SAVINGS = 'potential_node_savings'
    
    # HPA comprehensive fields
    TOTAL_HPAS = 'total_hpas'
    WORKLOAD_CHARACTERISTICS = 'workload_characteristics'
    ALL_HPA_DETAILS = 'all_hpa_details'
    HIGH_CPU_HPAS = 'high_cpu_hpas'
    HPA_DETECTED = 'hpa_detected'
    
    # Workload comprehensive fields
    ALL_WORKLOADS_PRESERVED = 'all_workloads_preserved'
    TOTAL_WORKLOADS_PRESERVED = 'total_workloads_preserved'
    REPLICAS = 'replicas'
    CURRENT_REPLICAS = 'current_replicas'
    REPLICA_COUNT = 'replica_count'
    WORKLOAD_TYPE = 'workload_type'
    WORKLOAD_NAMESPACE_BREAKDOWN = 'workload_namespace_breakdown'
    CPU_UTILIZATION = 'cpu_utilization'
    MEMORY_UTILIZATION = 'memory_utilization'
    AVG_CPU_USAGE = 'avg_cpu_usage'
    AVG_MEMORY_USAGE = 'avg_memory_usage'
    CURRENT_CPU_USAGE = 'current_cpu_usage'
    CURRENT_MEMORY_USAGE = 'current_memory_usage'
    CPU_USAGE_PERCENT = 'cpu_usage_percent'
    MEMORY_USAGE_PERCENT = 'memory_usage_percent'
    MONTHLY_COST = 'monthly_cost'
    COST_ESTIMATE = 'cost_estimate'
    OPTIMIZATION_POTENTIAL = 'optimization_potential'
    SEVERITY = 'severity'
    TYPE = 'type'
    PRIORITY = 'priority'
    
    # Resource fields
    RESOURCES = 'resources'
    REQUESTS = 'requests'
    LIMITS = 'limits'
    CPU_REQUEST = 'cpu_request'
    MEMORY_REQUEST = 'memory_request'
    CPU_LIMIT = 'cpu_limit'
    MEMORY_LIMIT = 'memory_limit'
    CPU_REQUEST_PCT = 'cpu_request_pct'
    MEMORY_REQUEST_PCT = 'memory_request_pct'
    CPU = 'cpu'
    MEMORY = 'memory'
    
    # Opportunity fields
    OPTIMIZATION_OPPORTUNITIES = 'optimization_opportunities'
    DESCRIPTION = 'description'
    CURRENT_STATE = 'current_state'
    RECOMMENDED_ACTION = 'recommended_action'
    POTENTIAL_MONTHLY_SAVINGS = 'potential_monthly_savings'
    IMPLEMENTATION_DIFFICULTY = 'implementation_difficulty'
    RISK_LEVEL = 'risk_level'
    ESTIMATED_IMPLEMENTATION_TIME = 'estimated_implementation_time'
    CATEGORY = 'category'
    
    # HPA detailed fields
    MIN_REPLICAS = 'min_replicas'
    MAX_REPLICAS = 'max_replicas'
    DESIRED_REPLICAS = 'desired_replicas'
    TARGET_CPU = 'target_cpu'
    HPA_TYPE = 'hpa_type'
    API_VERSION = 'apiVersion'
    SPEC = 'spec'
    
    # Node and metrics analysis fields
    CPU_USAGE_PCT = 'cpu_usage_pct'
    CPU_STATISTICS = 'cpu_statistics'
    RESOURCE_CONCENTRATION = 'resource_concentration'
    ML_FEATURES_READY = 'ml_features_ready'
    FEATURES = 'features'
    ANALYSIS_TYPE = 'analysis_type'
    SUBSCRIPTION_AWARE = 'subscription_aware'
    DYNAMIC_ALLOCATION = 'dynamic_allocation'
    ANALYSIS_METHOD = 'analysis_method'
    ACCURACY_LEVEL = 'accuracy_level'
    TOTAL_NAMESPACES = 'total_namespaces'
    STATUS = 'status'
    METADATA = 'metadata'
    NAME = 'name'
    NAMESPACE = 'namespace'
    METRICS = 'metrics'
    TARGET = 'target'
    RESOURCE = 'resource'
    SCALE_TARGET_REF = 'scaleTargetRef'
    KIND = 'kind'
    
    # Kubernetes object fields
    ITEMS = 'items'
    LABELS = 'labels'
    ANNOTATIONS = 'annotations'
    CONTAINERS = 'containers'
    TEMPLATE = 'template'
    ALLOCATABLE = 'allocatable'
    NODE_INFO = 'nodeInfo'
    KUBELET_VERSION = 'kubeletVersion'
    KUBERNETES_VERSION = 'kubernetesVersion'
    CURRENT_KUBERNETES_VERSION = 'currentKubernetesVersion'
    SERVER_VERSION = 'serverVersion'
    GIT_VERSION = 'gitVersion'
    
    # Cost detailed fields
    TOTAL_COST_ALT = 'total_cost'
    COST = 'cost'
    TOTAL_COST_ALT2 = 'total_cost'
    SIZE_GB = 'size_gb'
    OTHER_COST = 'other_cost'
    MONITORING_COST = 'monitoring_cost'
    
    # Node status and info
    STATUS_FIELD = 'status'
    READY_REPLICAS = 'readyReplicas'
    LOCATION = 'location'
    VERSION = 'version'
    
    # Cache and data fields
    POD_RESOURCES_DETAILED = 'pod_resources_detailed'
    DEPLOYMENTS = 'deployments'
    STATEFULSETS = 'statefulsets'
    HPA_DATA = 'hpa'
    POD_USAGE = 'pod_usage'
    PODS_RUNNING = 'pods_running'
    PVC_TEXT = 'pvc_text'
    SERVICES_TEXT = 'services_text'
    STORAGE_CLASSES = 'storage_classes'
    CLUSTER_VERSION_SDK = 'cluster_version_sdk'
    CLUSTER_INFO = 'cluster_info'
    NAMESPACES_WITH_LABELS = 'namespaces_with_labels'
    NAMESPACES = 'namespaces'
    PODS = 'pods'
    KUBECTL_DATA = 'kubectl_data'
    
    # ML Model fields
    WORKLOAD_TYPE_ML = 'workload_type'
    CONFIDENCE = 'confidence'
    HAS_ANOMALIES = 'has_anomalies'
    ANOMALY_DETAILS = 'anomaly_details'
    FEATURE_INSIGHTS = 'feature_insights'
    EFFICIENCY_METRICS = 'efficiency_metrics'
    OVERALL_EFFICIENCY = 'overall_efficiency'
    CPU_MEAN = 'cpu_mean'
    MEMORY_MEAN = 'memory_mean'
    CPU_MAX = 'cpu_max'
    MEMORY_MAX = 'memory_max'
    CPU_CV = 'cpu_cv'
    MEMORY_CV = 'memory_cv'
    CPU_BURST_FREQUENCY = 'cpu_burst_frequency'
    OVERALL_EFFICIENCY_SCORE = 'overall_efficiency_score'
    AVG_CPU_GAP = 'avg_cpu_gap'
    AVG_MEMORY_GAP = 'avg_memory_gap'
    CPU_STABILITY_SCORE = 'cpu_stability_score'
    MEMORY_STABILITY_SCORE = 'memory_stability_score'
    CPU_USAGE_PCT = 'cpu_usage_pct'
    MEMORY_USAGE_PCT = 'memory_usage_pct'
    CPU_PEAK_PCT = 'cpu_peak_pct'
    MEMORY_PEAK_PCT = 'memory_peak_pct'
    EFFICIENCY_SCORE = 'efficiency_score'
    STABILITY_SCORE = 'stability_score'
    
    # HPA pattern fields
    CURRENT_HPA_PATTERN = 'current_hpa_pattern'
    
    # Pod Cost Analyzer fields
    POD_METRICS = 'pod_metrics'
    PODS_TEXT = 'pods_text'
    NODES_DATA = 'nodes'
    INSTANCE_TYPE = 'node.kubernetes.io/instance-type'
    TOTAL_PODS_ANALYZED = 'total_pods_analyzed'
    FEATURES_USED = 'features_used'
    ALLOCATION_METADATA = 'allocation_metadata'
    
    # Additional missing fields that appear in .get() calls
    SUCCESS = 'success'
    ERROR = 'error'
    SHOULD_HAVE_HPA = 'should_have_hpa'
    CPU_MILLICORES = 'cpu_millicores'
    MEMORY_MB = 'memory_mb'
    PEAK_CPU_LAST_7D = 'peak_cpu_last_7d'
    PEAK_MEMORY_LAST_7D = 'peak_memory_last_7d'
    LAST_SCALE_TIME = 'lastScaleTime'
    CONDITIONS = 'conditions'
    POD_COUNT = 'pod_count'
    TEAM = 'team'
    
    # SAVINGS BREAKDOWN (from analysis_engine)
    ANNUAL_SAVINGS = 'annual_savings'
    SAVINGS_PERCENTAGE = 'savings_percentage'
    SAVINGS_BREAKDOWN = 'savings_breakdown'
    HPA_OPTIMIZATION_SAVINGS = 'hpa_optimization_savings'
    RIGHT_SIZING_SAVINGS = 'right_sizing_savings'
    STORAGE_OPTIMIZATION_SAVINGS = 'storage_optimization_savings'
    NETWORKING_OPTIMIZATION_SAVINGS = 'networking_optimization_savings'
    NODE_OPTIMIZATION_SAVINGS = 'node_optimization_savings'
    CORE_OPTIMIZATION_SAVINGS = 'core_optimization_savings'
    COMPUTE_OPTIMIZATION_SAVINGS = 'compute_optimization_savings'
    INFRASTRUCTURE_SAVINGS = 'infrastructure_savings'
    CONTROL_PLANE_SAVINGS = 'control_plane_savings'
    REGISTRY_SAVINGS = 'registry_savings'
    
    # METADATA FIELDS
    RESOURCE_GROUP = 'resource_group'
    CLUSTER_NAME = 'cluster_name'
    SUBSCRIPTION_ID = 'subscription_id'
    COST_PERIOD = 'cost_period'
    COST_DATA_SOURCE = 'cost_data_source'
    METRICS_DATA_SOURCE = 'metrics_data_source'
    ANALYSIS_TIMESTAMP = 'analysis_timestamp'
    SESSION_ID = 'session_id'
    ML_ENHANCED = 'ml_enhanced'
    
    # DATA FIELDS  
    COST_DATA = 'cost_data'
    COST_DATA_COLUMNS = 'cost_data_columns'
    COST_DATA_SHAPE = 'cost_data_shape'
    METRICS_DATA = 'metrics_data'
    NODE_USAGE = 'node_usage'
    
    # METADATA FIELDS EXTENDED
    MULTI_SUBSCRIPTION = 'multi_subscription'
    SUBSCRIPTION_METADATA = 'subscription_metadata'
    CLUSTER_METADATA = 'cluster_metadata'
    ENHANCED_ANALYSIS_INPUT = 'enhanced_analysis_input'
    DATABASE_SAVE_METADATA = 'database_save_metadata'
    IMPLEMENTATION_PLAN = 'implementation_plan'
    WORKLOAD_SEVERITY_BREAKDOWN = 'workload_severity_breakdown'
    
    # CLUSTER CONTEXT
    CLUSTER_CONTEXT = 'cluster_context'
    ML_ANALYSIS_METADATA = 'ml_analysis_metadata'
    
    @staticmethod
    def validate_field_usage(data: dict, allowed_fields: list, context: str = ""):
        """
        Enforce that only approved field names are used
        Raises error if unknown fields found
        """
        unknown_fields = []
        for field_name in data.keys():
            if field_name not in allowed_fields:
                unknown_fields.append(field_name)
        
        if unknown_fields:
            raise ValueError(f"FIELD CONTRACT VIOLATION in {context}: "
                           f"Unknown fields {unknown_fields}. "
                           f"Only approved fields allowed: {allowed_fields[:10]}...")
    
    @staticmethod
    def get_approved_fields() -> list:
        """
        Return list of all approved field names from the contract
        """
        # Get all constants that represent field names
        approved = []
        for attr_name in dir(AnalysisDataContract):
            if not attr_name.startswith('_') and attr_name.isupper():
                approved.append(getattr(AnalysisDataContract, attr_name))
        
        # Add common variations that are acceptable
        approved.extend([
            'nodes', 'workloads', 'total_cost', 'savings', 'efficiency',
            'timestamp', 'cluster_name', 'namespace', 'name', 'replicas',
            # Node-specific fields that must be preserved
            'cpu_usage_pct', 'memory_usage_pct', 'cpu_cores', 'memory_gb',
            'node_name', 'node_type', 'availability_zone'
        ])
        
        return approved
    
    @staticmethod
    def enforce_strict_mode(data: dict, context: str = "") -> dict:
        """
        STRICT MODE: Only allow data contract approved fields
        """
        approved_fields = AnalysisDataContract.get_approved_fields()
        AnalysisDataContract.validate_field_usage(data, approved_fields, context)
        return data
    
    @staticmethod
    def normalize_analysis_data(analysis_data: dict) -> dict:
        """
        Transform analyzer output to standardized field names for UI consumption
        This is the SINGLE point of field name transformation
        """
        normalized = analysis_data.copy()
        
        # Map analyzer field names to UI expected names (COMPLETE MAPPING)
        # Based on exhaustive scan of ALL .get() calls across entire pipeline
        field_mappings = {
            # Cost mappings
            'compute_cost': 'node_cost',  # UI expects 'node_cost'
            'monthly_actual_compute': 'node_cost',  # Alternative field name
            'vm_cost': 'node_cost',  # Alternative field name
            'node_pool_cost': 'node_cost',  # Alternative field name
            
            # Total cost normalization
            'monthly_actual_total': 'total_cost',
            
            # Critical savings field mappings (analyzer → UI) 
            'compute_savings': 'right_sizing_savings',  # UI expects right_sizing_savings
            'hpa_savings': 'core_optimization_savings',  # UI expects core_optimization_savings  
            'storage_savings': 'infrastructure_savings',  # UI expects infrastructure_savings
            'networking_savings': 'networking_optimization_savings',  # UI expects networking_optimization_savings
            
            # Additional missing field mappings
            'total_savings': 'total_potential_savings',  # UI also expects total_potential_savings
            'hpa_efficiency_percentage': 'hpa_efficiency',  # UI sometimes expects both variants
            
            # Cost breakdown mappings (if savings_breakdown exists)
            'hpa_savings': 'hpa_optimization_savings',  # For savings breakdown
            'compute_savings': 'compute_optimization_savings',  # For savings breakdown
            'storage_savings': 'storage_optimization_savings',  # For savings breakdown
            
            # CPU/Memory utilization field mappings (CRITICAL)
            'avg_cpu_usage_pct': 'avg_cpu_utilization',  # Standardize CPU field
            'cpu_usage_pct': 'cpu_utilization',  # Individual workload CPU
            'memory_usage_pct': 'memory_utilization',  # Individual workload memory
            'cpu_usage_percent': 'cpu_utilization',  # Alternative CPU field
            'memory_usage_percent': 'memory_utilization',  # Alternative memory field
            'current_cpu_usage': 'cpu_utilization',  # Current usage field
            'current_memory_usage': 'memory_utilization',  # Current usage field
            'avg_cpu_usage': 'avg_cpu_utilization',  # Average CPU usage
            'avg_memory_usage': 'avg_memory_utilization',  # Average memory usage
            
            # Workload field mappings
            'replicas': 'current_replicas',  # Standardize replica field
            'replica_count': 'current_replicas',  # Alternative replica field
            'workload_type': 'type',  # Standardize type field
            'all_workloads': 'workloads',  # Alternative workload list field
            'all_workloads_preserved': 'workloads',  # Preserved workload list
            
            # Node field mappings
            'nodes': 'node_metrics',  # Alternative node data field
            'original_nodes': 'nodes',  # Original node data
            'current_node_count': 'node_count',  # Current nodes
            
            # Efficiency mappings
            'current_efficiency': 'current_cpu_efficiency',  # Default efficiency
            'system_efficiency': 'current_system_efficiency',  # System efficiency
            'overall_efficiency_score': 'efficiency_score',  # ML efficiency score
            'overall_efficiency': 'efficiency_score',  # Alternative efficiency
            
            # Confidence and scoring mappings
            'analysis_confidence': 'confidence_score',  # Analysis confidence
            'ml_confidence': 'confidence_score',  # ML confidence
            'data_quality_score': 'data_quality',  # Data quality mapping
            
            # Gap field mappings
            'avg_cpu_gap': 'cpu_gap',  # CPU gap field
            'avg_memory_gap': 'memory_gap',  # Memory gap field
            
            # Resource mappings
            'cpu_request': 'cpu_requests',  # Resource request mapping
            'memory_request': 'memory_requests',  # Memory request mapping
            'cpu_limit': 'cpu_limits',  # CPU limit mapping
            'memory_limit': 'memory_limits',  # Memory limit mapping
            
            # HPA detailed mappings
            'min_replicas': 'minReplicas',  # HPA min replicas
            'max_replicas': 'maxReplicas',  # HPA max replicas
            'current_replicas': 'currentReplicas',  # HPA current replicas
            'desired_replicas': 'desiredReplicas',  # HPA desired replicas
            'hpa_detected': 'has_hpa',  # HPA detection flag
            'total_hpas': 'hpa_count',  # Total HPA count
            
            # Feature mappings from ML model
            'cpu_mean': 'avg_cpu_utilization',  # ML CPU mean to avg
            'memory_mean': 'avg_memory_utilization',  # ML memory mean to avg
            'cpu_max': 'max_cpu_utilization',  # ML CPU max to max
            'memory_max': 'max_memory_utilization',  # ML memory max to max
            'efficiency_metrics': 'efficiency_analysis',  # ML efficiency
            'feature_insights': 'ml_insights',  # ML feature insights
        }
        
        # Apply mappings to top-level fields
        for analyzer_field, ui_field in field_mappings.items():
            if analyzer_field in analysis_data and ui_field not in analysis_data:
                normalized[ui_field] = analysis_data[analyzer_field]
        
        # Also normalize top_cpu_summary fields if they exist
        if 'top_cpu_summary' in normalized:
            top_cpu = normalized['top_cpu_summary']
            if isinstance(top_cpu, dict):
                for analyzer_field, ui_field in field_mappings.items():
                    if analyzer_field in top_cpu and ui_field not in top_cpu:
                        top_cpu[ui_field] = top_cpu[analyzer_field]
        
        # Calculate gaps if missing
        if 'cpu_gap' not in normalized:
            from shared.standards.performance_standards import SystemPerformanceStandards
            avg_cpu = normalized.get('avg_cpu_utilization', 0)
            if avg_cpu > 0:
                normalized['cpu_gap'] = max(0, SystemPerformanceStandards.CPU_UTILIZATION_OPTIMAL - avg_cpu)
        
        if 'memory_gap' not in normalized:
            from shared.standards.performance_standards import SystemPerformanceStandards
            avg_memory = normalized.get('avg_memory_utilization', 0)
            if avg_memory > 0:
                normalized['memory_gap'] = max(0, SystemPerformanceStandards.MEMORY_UTILIZATION_OPTIMAL - avg_memory)
        
        return normalized
    
    @staticmethod
    def create_enforced_data(context: str = "") -> 'DataContractDict':
        """
        Create a new enforced dictionary for analysis data
        MANDATORY: Use this instead of {} or dict() for analysis data
        """
        return DataContractDict(context=context)
    
    @staticmethod
    def enforce_data(data: dict, context: str = "") -> 'DataContractDict':
        """
        Convert existing dict to enforced contract dict
        MANDATORY: Use this for all incoming data
        """
        return DataContractDict(data, context=context)
    
    @staticmethod
    def normalize_field_name(field_name: str) -> str:
        """
        Normalize field names using the standardized mappings
        Returns the normalized field name or original if no mapping exists
        """
        # Use the same field mappings from normalize_analysis_data
        field_mappings = {
            # Cost mappings
            'compute_cost': 'node_cost',
            'monthly_actual_compute': 'node_cost',
            'vm_cost': 'node_cost',
            'node_pool_cost': 'node_cost',
            'monthly_actual_total': 'total_cost',
            
            # Critical savings field mappings
            'compute_savings': 'right_sizing_savings',
            'hpa_savings': 'core_optimization_savings',
            'storage_savings': 'infrastructure_savings',
            'networking_savings': 'networking_optimization_savings',
            'total_savings': 'total_potential_savings',
            'hpa_efficiency_percentage': 'hpa_efficiency',
            
            # CPU/Memory utilization field mappings
            'avg_cpu_usage_pct': 'avg_cpu_utilization',
            'cpu_usage_pct': 'cpu_utilization',
            'memory_usage_pct': 'memory_utilization',
            'cpu_usage_percent': 'cpu_utilization',
            'memory_usage_percent': 'memory_utilization',
            'current_cpu_usage': 'cpu_utilization',
            'current_memory_usage': 'memory_utilization',
            'avg_cpu_usage': 'avg_cpu_utilization',
            'avg_memory_usage': 'avg_memory_utilization',
            
            # Workload field mappings
            'replicas': 'current_replicas',
            'replica_count': 'current_replicas',
            'workload_type': 'type',
            'all_workloads': 'workloads',
            'all_workloads_preserved': 'workloads',
            
            # Node field mappings
            'nodes': 'node_metrics',
            'original_nodes': 'nodes',
            'current_node_count': 'node_count',
            
            # Efficiency mappings
            'current_efficiency': 'current_cpu_efficiency',
            'system_efficiency': 'current_system_efficiency',
            'overall_efficiency_score': 'efficiency_score',
            'overall_efficiency': 'efficiency_score',
            
            # Confidence and scoring mappings
            'analysis_confidence': 'confidence_score',
            'ml_confidence': 'confidence_score',
            'data_quality_score': 'data_quality',
            
            # Gap field mappings
            'avg_cpu_gap': 'cpu_gap',
            'avg_memory_gap': 'memory_gap',
            
            # HPA detailed mappings
            'min_replicas': 'minReplicas',
            'max_replicas': 'maxReplicas',
            'current_replicas': 'currentReplicas',
            'desired_replicas': 'desiredReplicas',
            'hpa_detected': 'has_hpa',
            'total_hpas': 'hpa_count',
            
            # Feature mappings from ML model
            'cpu_mean': 'avg_cpu_utilization',
            'memory_mean': 'avg_memory_utilization',
            'cpu_max': 'max_cpu_utilization',
            'memory_max': 'max_memory_utilization',
            'efficiency_metrics': 'efficiency_analysis',
            'feature_insights': 'ml_insights',
        }
        
        # Return mapped field name if it exists, otherwise return original
        return field_mappings.get(field_name, field_name)


class MetricsDataContract:
    """
    Standard data contract for metrics from collectors
    FROM: aks_realtime_metrics.py  
    TO: algorithmic_cost_analyzer.py
    """
    
    # CORE FIELDS (from collector) - COMPLETE LIST
    TIMESTAMP = 'timestamp'
    CLUSTER_NAME = 'cluster_name'
    SUBSCRIPTION_ID = 'subscription_id'
    
    # NODE FIELDS
    NODES = 'nodes'
    ORIGINAL_NODES = 'original_nodes'
    NODE_COUNT = 'node_count'
    TOTAL_CPU_CORES = 'total_cpu_cores'
    TOTAL_MEMORY_GB = 'total_memory_gb'
    
    # AGGREGATED NODE METRICS
    AVG_CPU_UTILIZATION = 'avg_cpu_utilization'
    AVG_MEMORY_UTILIZATION = 'avg_memory_utilization' 
    MAX_CPU_UTILIZATION = 'max_cpu_utilization'
    MAX_MEMORY_UTILIZATION = 'max_memory_utilization'
    
    # WORKLOAD FIELDS
    ALL_WORKLOADS = 'all_workloads'
    TOTAL_WORKLOADS = 'total_workloads'
    HIGH_CPU_COUNT = 'high_cpu_count'
    
    # HPA FIELDS
    HPA_IMPLEMENTATION = 'hpa_implementation'
    HPA_CPU_METRICS = 'hpa_cpu_metrics'
    CPU_STATISTICS = 'cpu_statistics'
    
    # SUMMARY FIELDS
    TOP_CPU_SUMMARY = 'top_cpu_summary'
    RESOURCE_CONCENTRATION = 'resource_concentration'
    
    # ML FIELDS
    ML_FEATURES_READY = 'ml_features_ready'
    FEATURES = 'features'
    
    @staticmethod
    def validate_metrics_data(metrics_data: dict) -> bool:
        """
        Validate that metrics data contains required fields per .clauderc
        """
        required_fields = [
            MetricsDataContract.NODES,
            MetricsDataContract.TOTAL_WORKLOADS,
            MetricsDataContract.ALL_WORKLOADS,
            MetricsDataContract.TOP_CPU_SUMMARY
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in metrics_data:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required fields in metrics_data: {missing_fields}")
        
        return True