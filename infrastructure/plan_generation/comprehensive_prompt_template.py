"""
Comprehensive Implementation Plan Prompt Template
This generates detailed 900+ line implementation plans with multiple phases and actions
"""

def build_comprehensive_prompt(cluster_name: str, cluster_id: str, current_cost: float, resource_group: str = "rg") -> str:
    """
    Generate a comprehensive prompt that produces detailed multi-phase implementation plans
    """
    
    potential_savings = current_cost * 0.35  # Target 35% cost reduction
    
    prompt = f"""Generate an EXTREMELY DETAILED implementation plan for AKS cluster '{cluster_name}'.

REQUIREMENTS:
- Generate 6 phases with 8-10 actions per phase (minimum 50 total actions)
- Each action must have 5-10 implementation steps with real commands
- Include validation, rollback, monitoring, and success criteria for EVERY action
- Target 35% cost reduction (${potential_savings:.2f}/month from current ${current_cost:.2f})
- Provide cluster-specific commands using actual resource names

Return ONLY this complete JSON structure:

{{
  "metadata": {{
    "plan_id": "KUBEOPT-{cluster_id}-2025",
    "cluster_name": "{cluster_name}",
    "generated_date": "2025-12-22T20:00:00Z",
    "estimated_duration_days": 45
  }},
  "executive_summary": {{
    "current_monthly_cost": {current_cost},
    "potential_monthly_savings": {potential_savings:.2f},
    "savings_percentage": 35
  }},
  "phases": [
    {{
      "phase_number": 1,
      "name": "Immediate Cost Reduction - Quick Wins",
      "duration_days": 5,
      "estimated_savings": {potential_savings * 0.25:.2f},
      "actions": [
        {{
          "action_id": "1.1",
          "name": "Right-size over-provisioned deployments",
          "estimated_savings": {potential_savings * 0.08:.2f},
          "commands": {{
            "backup": [
              "kubectl get deployments -A -o yaml > all-deployments-backup.yaml",
              "kubectl get pods -A -o wide > pods-state-backup.txt",
              "kubectl top nodes > nodes-utilization-backup.txt"
            ],
            "implement": [
              "# Step 1: Analyze current resource usage",
              "kubectl top pods -A --sort-by=cpu | head -50 > high-cpu-pods.txt",
              "kubectl top pods -A --sort-by=memory | head -50 > high-memory-pods.txt",
              
              "# Step 2: Identify over-provisioned workloads",
              "for deployment in $(kubectl get deployments -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name --no-headers); do",
              "  ns=$(echo $deployment | awk '{{print $1}}')",
              "  name=$(echo $deployment | awk '{{print $2}}')",
              "  kubectl describe deployment $name -n $ns | grep -E 'Replicas:|cpu:|memory:'",
              "done > deployment-resources.txt",
              
              "# Step 3: Apply optimized resource limits for production workloads",
              "kubectl set resources deployment webapp -n production --requests=cpu=250m,memory=512Mi --limits=cpu=500m,memory=1Gi",
              "kubectl set resources deployment api-gateway -n production --requests=cpu=200m,memory=256Mi --limits=cpu=400m,memory=512Mi",
              "kubectl set resources deployment background-worker -n production --requests=cpu=100m,memory=256Mi --limits=cpu=200m,memory=512Mi",
              
              "# Step 4: Apply optimized resources for staging workloads",
              "kubectl set resources deployment webapp -n staging --requests=cpu=100m,memory=256Mi --limits=cpu=200m,memory=512Mi",
              "kubectl set resources deployment api-gateway -n staging --requests=cpu=100m,memory=128Mi --limits=cpu=200m,memory=256Mi",
              
              "# Step 5: Apply optimized resources for development workloads",
              "kubectl set resources deployment webapp -n development --requests=cpu=50m,memory=128Mi --limits=cpu=100m,memory=256Mi"
            ],
            "validate": [
              "kubectl get pods -A --field-selector=status.phase!=Running",
              "kubectl top pods -A --sort-by=cpu | head -20",
              "kubectl describe nodes | grep -A 5 'Allocated resources'"
            ],
            "rollback": [
              "kubectl apply -f all-deployments-backup.yaml",
              "kubectl rollout restart deployment -A"
            ]
          }},
          "success_criteria": [
            "All pods are running without OOMKilled errors",
            "CPU utilization per pod < 80%",
            "Memory utilization per pod < 85%",
            "No performance degradation in application metrics"
          ]
        }},
        {{
          "action_id": "1.2",
          "name": "Remove unused resources and idle workloads",
          "estimated_savings": {potential_savings * 0.05:.2f},
          "commands": {{
            "backup": [
              "kubectl get all -A -o yaml > all-resources-backup.yaml",
              "kubectl get pvc -A -o yaml > pvc-backup.yaml",
              "kubectl get configmaps,secrets -A -o yaml > configs-backup.yaml"
            ],
            "implement": [
              "# Step 1: Identify unused ConfigMaps",
              "kubectl get configmaps -A -o json | jq -r '.items[] | select(.metadata.annotations.\"kubectl.kubernetes.io/last-applied-configuration\" == null) | .metadata.namespace + \"/\" + .metadata.name' > unused-configmaps.txt",
              
              "# Step 2: Identify unused Secrets",
              "kubectl get secrets -A -o json | jq -r '.items[] | select(.type != \"kubernetes.io/service-account-token\") | select(.metadata.annotations.\"kubectl.kubernetes.io/last-applied-configuration\" == null) | .metadata.namespace + \"/\" + .metadata.name' > unused-secrets.txt",
              
              "# Step 3: Identify completed Jobs older than 7 days",
              "kubectl get jobs -A -o json | jq -r '.items[] | select(.status.succeeded == 1) | select(now - (.status.completionTime | fromdate) > 604800) | .metadata.namespace + \"/\" + .metadata.name' > old-completed-jobs.txt",
              
              "# Step 4: Clean up evicted pods",
              "kubectl get pods -A --field-selector=status.phase=Failed -o json | jq -r '.items[] | select(.status.reason == \"Evicted\") | \"kubectl delete pod \" + .metadata.name + \" -n \" + .metadata.namespace' | sh",
              
              "# Step 5: Remove unused PVCs",
              "kubectl get pvc -A -o json | jq -r '.items[] | select(.status.phase == \"Bound\" and .status.accessModes[] == \"ReadWriteOnce\") | select(.metadata.annotations.\"volume.beta.kubernetes.io/storage-class\" != null) | .metadata.namespace + \"/\" + .metadata.name' > check-pvc-usage.txt"
            ],
            "validate": [
              "kubectl get configmaps -A | wc -l",
              "kubectl get secrets -A | wc -l",
              "kubectl get jobs -A --field-selector=status.successful=1",
              "kubectl get pvc -A"
            ],
            "rollback": [
              "kubectl apply -f all-resources-backup.yaml",
              "kubectl apply -f pvc-backup.yaml",
              "kubectl apply -f configs-backup.yaml"
            ]
          }},
          "success_criteria": [
            "No critical resources accidentally deleted",
            "All active applications remain functional",
            "Storage usage reduced by at least 10%",
            "Kubernetes object count reduced"
          ]
        }},
        {{
          "action_id": "1.3",
          "name": "Optimize pod replica counts",
          "estimated_savings": {potential_savings * 0.06:.2f},
          "commands": {{
            "backup": [
              "kubectl get deployments -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,REPLICAS:.spec.replicas > replica-counts-backup.txt"
            ],
            "implement": [
              "# Step 1: Analyze current replica usage",
              "for deployment in $(kubectl get deployments -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name --no-headers); do",
              "  ns=$(echo $deployment | awk '{{print $1}}')",
              "  name=$(echo $deployment | awk '{{print $2}}')",
              "  kubectl top pods -n $ns -l app=$name --no-headers | awk '{{sum+=$2}} END {{print \"Average CPU for \" name \": \" sum/NR \"m\"}}'",
              "done",
              
              "# Step 2: Reduce over-provisioned replicas in non-production",
              "kubectl scale deployment webapp -n staging --replicas=2",
              "kubectl scale deployment api-gateway -n staging --replicas=2",
              "kubectl scale deployment webapp -n development --replicas=1",
              "kubectl scale deployment api-gateway -n development --replicas=1",
              
              "# Step 3: Optimize production replicas based on actual load",
              "kubectl scale deployment background-worker -n production --replicas=3",
              "kubectl scale deployment cache-service -n production --replicas=2"
            ],
            "validate": [
              "kubectl get deployments -A",
              "kubectl top pods -A --sort-by=cpu",
              "kubectl get hpa -A"
            ],
            "rollback": [
              "while read line; do",
              "  ns=$(echo $line | awk '{{print $1}}')",
              "  name=$(echo $line | awk '{{print $2}}')",
              "  replicas=$(echo $line | awk '{{print $3}}')",
              "  kubectl scale deployment $name -n $ns --replicas=$replicas",
              "done < replica-counts-backup.txt"
            ]
          }},
          "success_criteria": [
            "Application availability maintained at 99.9%",
            "Response times within acceptable limits",
            "Pod CPU utilization between 50-80%",
            "Successful handling of peak traffic"
          ]
        }},
        {{
          "action_id": "1.4",
          "name": "Implement resource quotas",
          "estimated_savings": {potential_savings * 0.03:.2f},
          "commands": {{
            "backup": [
              "kubectl get resourcequotas -A -o yaml > quotas-backup.yaml",
              "kubectl get limitranges -A -o yaml > limitranges-backup.yaml"
            ],
            "implement": [
              "# Create namespace resource quotas",
              "for ns in production staging development; do",
              "kubectl apply -f - <<EOF",
              "apiVersion: v1",
              "kind: ResourceQuota",
              "metadata:",
              "  name: compute-resources",
              "  namespace: $ns",
              "spec:",
              "  hard:",
              "    requests.cpu: '20'",
              "    requests.memory: '40Gi'",
              "    limits.cpu: '40'",
              "    limits.memory: '80Gi'",
              "    persistentvolumeclaims: '20'",
              "EOF",
              "done",
              
              "# Create limit ranges",
              "for ns in production staging development; do",
              "kubectl apply -f - <<EOF",
              "apiVersion: v1",
              "kind: LimitRange",
              "metadata:",
              "  name: default-limits",
              "  namespace: $ns",
              "spec:",
              "  limits:",
              "  - default:",
              "      cpu: '1'",
              "      memory: '1Gi'",
              "    defaultRequest:",
              "      cpu: '100m'",
              "      memory: '128Mi'",
              "    type: Container",
              "EOF",
              "done"
            ],
            "validate": [
              "kubectl describe resourcequotas -A",
              "kubectl describe limitranges -A",
              "kubectl get resourcequotas -A --output=custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,CPU-REQUEST:.status.used.'requests.cpu',MEMORY-REQUEST:.status.used.'requests.memory'"
            ],
            "rollback": [
              "kubectl delete resourcequotas --all -A",
              "kubectl delete limitranges --all -A",
              "kubectl apply -f quotas-backup.yaml",
              "kubectl apply -f limitranges-backup.yaml"
            ]
          }},
          "success_criteria": [
            "Resource quotas enforced in all namespaces",
            "No pods stuck in pending due to quotas",
            "Resource consumption within defined limits",
            "Automatic resource request injection working"
          ]
        }},
        {{
          "action_id": "1.5",
          "name": "Enable spot instances for non-critical workloads",
          "estimated_savings": {potential_savings * 0.03:.2f},
          "commands": {{
            "backup": [
              "az aks nodepool list --resource-group {resource_group} --cluster-name {cluster_name} -o json > nodepools-backup.json"
            ],
            "implement": [
              "# Create spot instance node pool",
              "az aks nodepool add --resource-group {resource_group} --cluster-name {cluster_name} --name spotnp01 --priority Spot --eviction-policy Delete --spot-max-price -1 --enable-cluster-autoscaler --min-count 1 --max-count 5 --node-vm-size Standard_D2s_v3",
              
              "# Label nodes for workload placement",
              "kubectl label nodes -l agentpool=spotnp01 workload-type=non-critical",
              
              "# Add node selectors to non-critical workloads",
              "kubectl patch deployment background-worker -n production -p '{{\"spec\":{{\"template\":{{\"spec\":{{\"nodeSelector\":{{\"workload-type\":\"non-critical\"}}}}}}}}}}'",
              "kubectl patch deployment data-processor -n production -p '{{\"spec\":{{\"template\":{{\"spec\":{{\"nodeSelector\":{{\"workload-type\":\"non-critical\"}}}}}}}}}}'"
            ],
            "validate": [
              "az aks nodepool show --resource-group {resource_group} --cluster-name {cluster_name} --name spotnp01 --query scaleSetPriority",
              "kubectl get nodes -l agentpool=spotnp01",
              "kubectl get pods -o wide | grep spotnp01"
            ],
            "rollback": [
              "az aks nodepool delete --resource-group {resource_group} --cluster-name {cluster_name} --name spotnp01 --no-wait",
              "kubectl patch deployment background-worker -n production --type json -p '[{{\"op\": \"remove\", \"path\": \"/spec/template/spec/nodeSelector\"}}]'"
            ]
          }},
          "success_criteria": [
            "Spot instance node pool created successfully",
            "Non-critical workloads running on spot nodes",
            "Cost savings of 60-90% on spot node compute",
            "Graceful handling of spot evictions"
          ]
        }}
      ]
    }},
    {{
      "phase_number": 2,
      "name": "Advanced Autoscaling and Performance Optimization",
      "duration_days": 7,
      "estimated_savings": {potential_savings * 0.20:.2f},
      "actions": [
        {{
          "action_id": "2.1",
          "name": "Implement Horizontal Pod Autoscaling (HPA)",
          "estimated_savings": {potential_savings * 0.08:.2f},
          "commands": {{
            "backup": [
              "kubectl get hpa -A -o yaml > hpa-backup.yaml"
            ],
            "implement": [
              "# Install metrics server",
              "kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml",
              
              "# Create HPA for production workloads",
              "kubectl autoscale deployment webapp -n production --cpu-percent=70 --min=3 --max=20",
              "kubectl autoscale deployment api-gateway -n production --cpu-percent=70 --min=2 --max=15",
              "kubectl autoscale deployment background-worker -n production --cpu-percent=80 --min=2 --max=10",
              
              "# Create HPA for staging workloads",
              "kubectl autoscale deployment webapp -n staging --cpu-percent=75 --min=1 --max=5",
              "kubectl autoscale deployment api-gateway -n staging --cpu-percent=75 --min=1 --max=3",
              
              "# Advanced HPA with custom metrics",
              "kubectl apply -f - <<EOF",
              "apiVersion: autoscaling/v2",
              "kind: HorizontalPodAutoscaler",
              "metadata:",
              "  name: webapp-advanced",
              "  namespace: production",
              "spec:",
              "  scaleTargetRef:",
              "    apiVersion: apps/v1",
              "    kind: Deployment",
              "    name: webapp",
              "  minReplicas: 3",
              "  maxReplicas: 30",
              "  metrics:",
              "  - type: Resource",
              "    resource:",
              "      name: cpu",
              "      target:",
              "        type: Utilization",
              "        averageUtilization: 70",
              "  - type: Resource",
              "    resource:",
              "      name: memory",
              "      target:",
              "        type: Utilization",
              "        averageUtilization: 80",
              "  behavior:",
              "    scaleDown:",
              "      stabilizationWindowSeconds: 300",
              "      policies:",
              "      - type: Percent",
              "        value: 50",
              "        periodSeconds: 60",
              "    scaleUp:",
              "      stabilizationWindowSeconds: 60",
              "      policies:",
              "      - type: Percent",
              "        value: 100",
              "        periodSeconds: 30",
              "EOF"
            ],
            "validate": [
              "kubectl get hpa -A",
              "kubectl describe hpa -A",
              "kubectl get events -A | grep HorizontalPodAutoscaler"
            ],
            "rollback": [
              "kubectl delete hpa --all -A",
              "kubectl apply -f hpa-backup.yaml"
            ]
          }},
          "success_criteria": [
            "HPA actively scaling based on metrics",
            "Pods scaling between min and max replicas",
            "Average CPU utilization maintained at target",
            "No thrashing or flapping in scaling decisions"
          ]
        }},
        {{
          "action_id": "2.2",
          "name": "Implement Vertical Pod Autoscaling (VPA)",
          "estimated_savings": {potential_savings * 0.06:.2f},
          "commands": {{
            "backup": [
              "kubectl get vpa -A -o yaml > vpa-backup.yaml"
            ],
            "implement": [
              "# Install VPA",
              "git clone https://github.com/kubernetes/autoscaler.git",
              "cd autoscaler/vertical-pod-autoscaler",
              "./hack/vpa-up.sh",
              
              "# Create VPA for key workloads",
              "kubectl apply -f - <<EOF",
              "apiVersion: autoscaling.k8s.io/v1",
              "kind: VerticalPodAutoscaler",
              "metadata:",
              "  name: webapp-vpa",
              "  namespace: production",
              "spec:",
              "  targetRef:",
              "    apiVersion: apps/v1",
              "    kind: Deployment",
              "    name: webapp",
              "  updatePolicy:",
              "    updateMode: Auto",
              "  resourcePolicy:",
              "    containerPolicies:",
              "    - containerName: webapp",
              "      minAllowed:",
              "        cpu: 100m",
              "        memory: 128Mi",
              "      maxAllowed:",
              "        cpu: 2",
              "        memory: 2Gi",
              "EOF",
              
              "# Create VPA for other workloads",
              "for deployment in api-gateway background-worker cache-service; do",
              "kubectl apply -f - <<EOF",
              "apiVersion: autoscaling.k8s.io/v1",
              "kind: VerticalPodAutoscaler",
              "metadata:",
              "  name: $deployment-vpa",
              "  namespace: production",
              "spec:",
              "  targetRef:",
              "    apiVersion: apps/v1",
              "    kind: Deployment",
              "    name: $deployment",
              "  updatePolicy:",
              "    updateMode: Recreate",
              "EOF",
              "done"
            ],
            "validate": [
              "kubectl get vpa -A",
              "kubectl describe vpa -A",
              "kubectl get vpa -A -o custom-columns=NAME:.metadata.name,MODE:.spec.updatePolicy.updateMode,CPU:.status.recommendation.containerRecommendations[0].target.cpu,MEMORY:.status.recommendation.containerRecommendations[0].target.memory"
            ],
            "rollback": [
              "kubectl delete vpa --all -A",
              "kubectl apply -f vpa-backup.yaml"
            ]
          }},
          "success_criteria": [
            "VPA providing recommendations for all workloads",
            "Resource requests automatically adjusted",
            "Improved resource utilization efficiency",
            "No OOMKilled pods after VPA adjustments"
          ]
        }},
        {{
          "action_id": "2.3",
          "name": "Enable cluster autoscaling with optimization",
          "estimated_savings": {potential_savings * 0.06:.2f},
          "commands": {{
            "backup": [
              "az aks show --resource-group {resource_group} --name {cluster_name} -o json > cluster-autoscaler-backup.json"
            ],
            "implement": [
              "# Enable cluster autoscaler on system node pool",
              "az aks update --resource-group {resource_group} --name {cluster_name} --enable-cluster-autoscaler --min-count 2 --max-count 10",
              
              "# Configure cluster autoscaler for aggressive scale-down",
              "kubectl apply -f - <<EOF",
              "apiVersion: v1",
              "kind: ConfigMap",
              "metadata:",
              "  name: cluster-autoscaler-status",
              "  namespace: kube-system",
              "data:",
              "  nodes.max-node-provision-time: '15m0s'",
              "  scale-down-delay-after-add: '5m0s'",
              "  scale-down-delay-after-delete: '10s'",
              "  scale-down-unneeded-time: '5m0s'",
              "  scale-down-utilization-threshold: '0.65'",
              "  skip-nodes-with-local-storage: 'false'",
              "  skip-nodes-with-system-pods: 'false'",
              "  max-graceful-termination-sec: '600'",
              "  max-node-provision-time: '15m'",
              "  max-nodes-total: '50'",
              "EOF",
              
              "# Restart cluster autoscaler to apply settings",
              "kubectl rollout restart deployment cluster-autoscaler -n kube-system"
            ],
            "validate": [
              "kubectl get nodes",
              "kubectl logs -n kube-system -l app=cluster-autoscaler --tail=50",
              "kubectl get events -n kube-system | grep cluster-autoscaler"
            ],
            "rollback": [
              "az aks update --resource-group {resource_group} --name {cluster_name} --disable-cluster-autoscaler"
            ]
          }},
          "success_criteria": [
            "Nodes scaling based on demand",
            "Scale-down happening within 5 minutes of low utilization",
            "No pods stuck in pending due to insufficient resources",
            "Node utilization maintained above 65%"
          ]
        }}
      ]
    }},
    {{
      "phase_number": 3,
      "name": "Storage and Network Optimization",
      "duration_days": 7,
      "estimated_savings": {potential_savings * 0.15:.2f},
      "actions": [
        {{
          "action_id": "3.1",
          "name": "Optimize persistent volume usage",
          "estimated_savings": {potential_savings * 0.08:.2f},
          "commands": {{
            "backup": [
              "kubectl get pv -o yaml > pv-backup.yaml",
              "kubectl get pvc -A -o yaml > pvc-backup.yaml"
            ],
            "implement": [
              "# Identify and resize over-provisioned PVCs",
              "kubectl get pvc -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,SIZE:.spec.resources.requests.storage,USED:.status.capacity.storage",
              
              "# Convert Premium to Standard storage where appropriate",
              "kubectl apply -f - <<EOF",
              "apiVersion: storage.k8s.io/v1",
              "kind: StorageClass",
              "metadata:",
              "  name: managed-standard-retain",
              "provisioner: kubernetes.io/azure-disk",
              "parameters:",
              "  storageaccounttype: Standard_LRS",
              "  kind: Managed",
              "reclaimPolicy: Retain",
              "allowVolumeExpansion: true",
              "volumeBindingMode: WaitForFirstConsumer",
              "EOF",
              
              "# Migrate non-critical workloads to standard storage",
              "# This requires creating new PVCs and migrating data",
              "kubectl apply -f - <<EOF",
              "apiVersion: v1",
              "kind: PersistentVolumeClaim",
              "metadata:",
              "  name: data-volume-standard",
              "  namespace: production",
              "spec:",
              "  accessModes:",
              "    - ReadWriteOnce",
              "  storageClassName: managed-standard-retain",
              "  resources:",
              "    requests:",
              "      storage: 10Gi",
              "EOF"
            ],
            "validate": [
              "kubectl get pvc -A",
              "kubectl get storageclass",
              "kubectl describe pvc -A | grep -E 'Name:|StorageClass:|Capacity:'"
            ],
            "rollback": [
              "kubectl apply -f pv-backup.yaml",
              "kubectl apply -f pvc-backup.yaml"
            ]
          }},
          "success_criteria": [
            "PVC utilization above 70%",
            "Appropriate storage tiers for workload requirements",
            "No data loss during migration",
            "Cost reduction in storage billing"
          ]
        }},
        {{
          "action_id": "3.2",
          "name": "Implement network policies for cost control",
          "estimated_savings": {potential_savings * 0.04:.2f},
          "commands": {{
            "backup": [
              "kubectl get networkpolicy -A -o yaml > netpol-backup.yaml"
            ],
            "implement": [
              "# Install network policy controller if not present",
              "kubectl apply -f https://raw.githubusercontent.com/Azure/azure-container-networking/master/npm/azure-npm.yaml",
              
              "# Default deny all traffic",
              "for ns in production staging development; do",
              "kubectl apply -f - <<EOF",
              "apiVersion: networking.k8s.io/v1",
              "kind: NetworkPolicy",
              "metadata:",
              "  name: default-deny",
              "  namespace: $ns",
              "spec:",
              "  podSelector: {{}}",
              "  policyTypes:",
              "  - Ingress",
              "  - Egress",
              "EOF",
              "done",
              
              "# Allow necessary ingress",
              "kubectl apply -f - <<EOF",
              "apiVersion: networking.k8s.io/v1",
              "kind: NetworkPolicy",
              "metadata:",
              "  name: allow-webapp-ingress",
              "  namespace: production",
              "spec:",
              "  podSelector:",
              "    matchLabels:",
              "      app: webapp",
              "  policyTypes:",
              "  - Ingress",
              "  ingress:",
              "  - from:",
              "    - namespaceSelector:",
              "        matchLabels:",
              "          name: ingress-nginx",
              "    ports:",
              "    - protocol: TCP",
              "      port: 8080",
              "EOF"
            ],
            "validate": [
              "kubectl get networkpolicy -A",
              "kubectl describe networkpolicy -A"
            ],
            "rollback": [
              "kubectl delete networkpolicy --all -A",
              "kubectl apply -f netpol-backup.yaml"
            ]
          }},
          "success_criteria": [
            "Network policies enforced",
            "Reduced cross-AZ traffic",
            "Lower data transfer costs",
            "No connectivity issues for legitimate traffic"
          ]
        }},
        {{
          "action_id": "3.3",
          "name": "Optimize load balancer configuration",
          "estimated_savings": {potential_savings * 0.03:.2f},
          "commands": {{
            "backup": [
              "kubectl get svc -A -o yaml > services-backup.yaml"
            ],
            "implement": [
              "# Convert multiple LoadBalancers to single Ingress",
              "kubectl apply -f - <<EOF",
              "apiVersion: networking.k8s.io/v1",
              "kind: Ingress",
              "metadata:",
              "  name: main-ingress",
              "  namespace: production",
              "  annotations:",
              "    kubernetes.io/ingress.class: nginx",
              "    cert-manager.io/cluster-issuer: letsencrypt-prod",
              "spec:",
              "  tls:",
              "  - hosts:",
              "    - app.example.com",
              "    - api.example.com",
              "    secretName: tls-secret",
              "  rules:",
              "  - host: app.example.com",
              "    http:",
              "      paths:",
              "      - path: /",
              "        pathType: Prefix",
              "        backend:",
              "          service:",
              "            name: webapp",
              "            port:",
              "              number: 80",
              "  - host: api.example.com",
              "    http:",
              "      paths:",
              "      - path: /",
              "        pathType: Prefix",
              "        backend:",
              "          service:",
              "            name: api-gateway",
              "            port:",
              "              number: 80",
              "EOF",
              
              "# Convert LoadBalancer services to ClusterIP",
              "kubectl patch svc webapp -n production -p '{{\"spec\":{{\"type\":\"ClusterIP\"}}}}'",
              "kubectl patch svc api-gateway -n production -p '{{\"spec\":{{\"type\":\"ClusterIP\"}}}}'"
            ],
            "validate": [
              "kubectl get ingress -A",
              "kubectl get svc -A | grep LoadBalancer",
              "curl -I https://app.example.com"
            ],
            "rollback": [
              "kubectl apply -f services-backup.yaml"
            ]
          }},
          "success_criteria": [
            "Single ingress handling multiple services",
            "Reduced number of LoadBalancer services",
            "All endpoints accessible via ingress",
            "SSL/TLS properly configured"
          ]
        }}
      ]
    }},
    {{
      "phase_number": 4,
      "name": "Monitoring and Observability Optimization",
      "duration_days": 6,
      "estimated_savings": {potential_savings * 0.10:.2f},
      "actions": [
        {{
          "action_id": "4.1",
          "name": "Optimize monitoring and logging",
          "estimated_savings": {potential_savings * 0.05:.2f},
          "commands": {{
            "backup": [
              "kubectl get cm -n monitoring -o yaml > monitoring-config-backup.yaml"
            ],
            "implement": [
              "# Reduce Prometheus retention and scraping frequency",
              "kubectl apply -f - <<EOF",
              "apiVersion: v1",
              "kind: ConfigMap",
              "metadata:",
              "  name: prometheus-config",
              "  namespace: monitoring",
              "data:",
              "  prometheus.yml: |",
              "    global:",
              "      scrape_interval: 30s",
              "      evaluation_interval: 30s",
              "      external_labels:",
              "        cluster: '{cluster_name}'",
              "    scrape_configs:",
              "    - job_name: 'kubernetes-pods'",
              "      kubernetes_sd_configs:",
              "      - role: pod",
              "      relabel_configs:",
              "      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]",
              "        action: keep",
              "        regex: true",
              "EOF",
              
              "# Configure log aggregation with filtering",
              "kubectl apply -f - <<EOF",
              "apiVersion: v1",
              "kind: ConfigMap",
              "metadata:",
              "  name: fluentd-config",
              "  namespace: kube-system",
              "data:",
              "  fluent.conf: |",
              "    <match kubernetes.**>",
              "      @type forward",
              "      <buffer>",
              "        @type file",
              "        path /var/log/fluentd-buffers/kubernetes.buffer",
              "        flush_interval 5s",
              "        chunk_limit_size 2M",
              "        queue_limit_length 32",
              "        overflow_action drop_oldest_chunk",
              "      </buffer>",
              "    </match>",
              "EOF"
            ],
            "validate": [
              "kubectl get cm -n monitoring",
              "kubectl logs -n monitoring -l app=prometheus --tail=20"
            ],
            "rollback": [
              "kubectl apply -f monitoring-config-backup.yaml"
            ]
          }},
          "success_criteria": [
            "Reduced metrics storage by 30%",
            "Lower network traffic from monitoring",
            "Critical metrics still captured",
            "Alert latency under 2 minutes"
          ]
        }},
        {{
          "action_id": "4.2",
          "name": "Implement cost allocation tags",
          "estimated_savings": {potential_savings * 0.05:.2f},
          "commands": {{
            "backup": [
              "kubectl get nodes -o json | jq '.items[].metadata.labels' > node-labels-backup.json"
            ],
            "implement": [
              "# Add cost allocation labels to nodes",
              "for node in $(kubectl get nodes -o name); do",
              "  kubectl label $node cost-center=engineering",
              "  kubectl label $node environment=production",
              "  kubectl label $node team=platform",
              "done",
              
              "# Add labels to all workloads",
              "for ns in production staging development; do",
              "  kubectl label namespace $ns cost-center=engineering",
              "  kubectl label namespace $ns environment=$ns",
              "  ",
              "  for deployment in $(kubectl get deployments -n $ns -o name); do",
              "    kubectl label $deployment cost-center=engineering",
              "    kubectl label $deployment billing-team=platform",
              "  done",
              "done",
              
              "# Configure Azure tags for cost tracking",
              "az aks update --resource-group {resource_group} --name {cluster_name} --tags Environment=Production CostCenter=Engineering Team=Platform"
            ],
            "validate": [
              "kubectl get nodes --show-labels",
              "kubectl get namespaces --show-labels",
              "az aks show --resource-group {resource_group} --name {cluster_name} --query tags"
            ],
            "rollback": [
              "# Remove labels if needed",
              "kubectl label nodes --all cost-center-",
              "kubectl label nodes --all environment-",
              "kubectl label nodes --all team-"
            ]
          }},
          "success_criteria": [
            "All resources properly tagged",
            "Cost allocation reports available",
            "Chargeback/showback implemented",
            "Budget alerts configured per team"
          ]
        }}
      ]
    }},
    {{
      "phase_number": 5,
      "name": "Security and Compliance Optimization",
      "duration_days": 8,
      "estimated_savings": {potential_savings * 0.08:.2f},
      "actions": [
        {{
          "action_id": "5.1",
          "name": "Implement pod security policies",
          "estimated_savings": {potential_savings * 0.04:.2f},
          "commands": {{
            "backup": [
              "kubectl get psp -o yaml > psp-backup.yaml",
              "kubectl get clusterrole,clusterrolebinding -o yaml | grep -E 'psp|security' > security-rbac-backup.yaml"
            ],
            "implement": [
              "# Create restricted PSP",
              "kubectl apply -f - <<EOF",
              "apiVersion: policy/v1beta1",
              "kind: PodSecurityPolicy",
              "metadata:",
              "  name: restricted",
              "spec:",
              "  privileged: false",
              "  allowPrivilegeEscalation: false",
              "  requiredDropCapabilities:",
              "    - ALL",
              "  volumes:",
              "    - 'configMap'",
              "    - 'emptyDir'",
              "    - 'projected'",
              "    - 'secret'",
              "    - 'downwardAPI'",
              "    - 'persistentVolumeClaim'",
              "  hostNetwork: false",
              "  hostIPC: false",
              "  hostPID: false",
              "  runAsUser:",
              "    rule: 'MustRunAsNonRoot'",
              "  seLinux:",
              "    rule: 'RunAsAny'",
              "  supplementalGroups:",
              "    rule: 'RunAsAny'",
              "  fsGroup:",
              "    rule: 'RunAsAny'",
              "  readOnlyRootFilesystem: true",
              "EOF",
              
              "# Apply RBAC for PSP",
              "kubectl apply -f - <<EOF",
              "apiVersion: rbac.authorization.k8s.io/v1",
              "kind: ClusterRole",
              "metadata:",
              "  name: restricted-psp-user",
              "rules:",
              "- apiGroups:",
              "  - policy",
              "  resources:",
              "  - podsecuritypolicies",
              "  resourceNames:",
              "  - restricted",
              "  verbs:",
              "  - use",
              "EOF"
            ],
            "validate": [
              "kubectl get psp",
              "kubectl get clusterrole | grep psp",
              "kubectl auth can-i use podsecuritypolicy/restricted"
            ],
            "rollback": [
              "kubectl delete psp restricted",
              "kubectl delete clusterrole restricted-psp-user"
            ]
          }},
          "success_criteria": [
            "PSPs enforced for all workloads",
            "No privileged containers running",
            "Security compliance improved",
            "No legitimate workloads blocked"
          ]
        }},
        {{
          "action_id": "5.2",
          "name": "Implement RBAC optimization",
          "estimated_savings": {potential_savings * 0.04:.2f},
          "commands": {{
            "backup": [
              "kubectl get clusterrole,clusterrolebinding,role,rolebinding -A -o yaml > rbac-backup.yaml"
            ],
            "implement": [
              "# Remove overly permissive roles",
              "kubectl delete clusterrolebinding permissive-binding --ignore-not-found=true",
              
              "# Create least privilege roles",
              "kubectl apply -f - <<EOF",
              "apiVersion: rbac.authorization.k8s.io/v1",
              "kind: Role",
              "metadata:",
              "  name: developer",
              "  namespace: development",
              "rules:",
              "- apiGroups: ['', 'apps']",
              "  resources: ['pods', 'services', 'deployments']",
              "  verbs: ['get', 'list', 'watch']",
              "- apiGroups: ['']",
              "  resources: ['pods/log', 'pods/exec']",
              "  verbs: ['get', 'create']",
              "EOF",
              
              "# Bind roles appropriately",
              "kubectl apply -f - <<EOF",
              "apiVersion: rbac.authorization.k8s.io/v1",
              "kind: RoleBinding",
              "metadata:",
              "  name: developer-binding",
              "  namespace: development",
              "subjects:",
              "- kind: Group",
              "  name: developers",
              "  apiGroup: rbac.authorization.k8s.io",
              "roleRef:",
              "  kind: Role",
              "  name: developer",
              "  apiGroup: rbac.authorization.k8s.io",
              "EOF"
            ],
            "validate": [
              "kubectl auth can-i --list",
              "kubectl get roles,rolebindings -A",
              "kubectl describe role developer -n development"
            ],
            "rollback": [
              "kubectl apply -f rbac-backup.yaml"
            ]
          }},
          "success_criteria": [
            "Least privilege access implemented",
            "No overly permissive roles",
            "Audit logs showing proper access patterns",
            "Compliance requirements met"
          ]
        }}
      ]
    }},
    {{
      "phase_number": 6,
      "name": "Advanced Cost Optimization and FinOps",
      "duration_days": 10,
      "estimated_savings": {potential_savings * 0.12:.2f},
      "actions": [
        {{
          "action_id": "6.1",
          "name": "Implement Azure Reservations and Savings Plans",
          "estimated_savings": {potential_savings * 0.06:.2f},
          "commands": {{
            "backup": [
              "az reservations reservation list -o json > reservations-backup.json"
            ],
            "implement": [
              "# Analyze usage for reservation recommendations",
              "az consumption usage list --start-date 2025-01-01 --end-date 2025-12-31 --query \"[?contains(instanceId, '{cluster_name}')]\" -o table",
              
              "# Calculate reservation requirements",
              "echo 'Based on usage analysis, recommending reservations for:'",
              "echo '- 10 x Standard_D4s_v3 instances (1-year term)'",
              "echo '- 5 x Standard_D8s_v3 instances (1-year term)'",
              
              "# Purchase reservations (requires appropriate permissions)",
              "# az reservations reservation-order purchase --reserved-resource-type VirtualMachines --billing-scope-id /subscriptions/xxx --term P1Y --billing-plan Monthly --quantity 10 --sku Standard_D4s_v3 --location eastus",
              
              "# Apply Azure Hybrid Benefit",
              "az aks update --resource-group {resource_group} --name {cluster_name} --enable-ahub"
            ],
            "validate": [
              "az reservations reservation list",
              "az aks show --resource-group {resource_group} --name {cluster_name} --query windowsProfile.licenseType"
            ],
            "rollback": [
              "echo 'Reservations cannot be rolled back, but can be exchanged or refunded per Azure policy'"
            ]
          }},
          "success_criteria": [
            "Reservations purchased for steady-state workloads",
            "15-30% discount achieved on compute costs",
            "Azure Hybrid Benefit applied where applicable",
            "Reserved capacity utilization above 90%"
          ]
        }},
        {{
          "action_id": "6.2",
          "name": "Implement showback and chargeback",
          "estimated_savings": {potential_savings * 0.06:.2f},
          "commands": {{
            "backup": [
              "kubectl get configmap -n kube-system cost-model -o yaml > cost-model-backup.yaml"
            ],
            "implement": [
              "# Deploy OpenCost for cost visibility",
              "kubectl apply -f https://raw.githubusercontent.com/opencost/opencost/develop/kubernetes/opencost.yaml",
              
              "# Configure cost allocation",
              "kubectl apply -f - <<EOF",
              "apiVersion: v1",
              "kind: ConfigMap",
              "metadata:",
              "  name: cost-model",
              "  namespace: opencost",
              "data:",
              "  CPU_PRICE_PER_HOUR: '0.031611'",
              "  RAM_PRICE_PER_GB_HOUR: '0.003968'",
              "  STORAGE_PRICE_PER_GB_HOUR: '0.00005479'",
              "  NETWORK_PRICE_PER_GB: '0.01'",
              "EOF",
              
              "# Create namespace budgets",
              "for ns in production staging development; do",
              "kubectl apply -f - <<EOF",
              "apiVersion: v1",
              "kind: ConfigMap",
              "metadata:",
              "  name: budget-config",
              "  namespace: $ns",
              "data:",
              "  monthly_budget: '5000'",
              "  alert_threshold: '80'",
              "  enforcement: 'soft'",
              "EOF",
              "done"
            ],
            "validate": [
              "kubectl get pods -n opencost",
              "kubectl get cm -n opencost cost-model",
              "curl http://opencost.opencost.svc.cluster.local:9090/allocation/compute"
            ],
            "rollback": [
              "kubectl delete namespace opencost",
              "kubectl delete cm budget-config -A"
            ]
          }},
          "success_criteria": [
            "Cost visibility per namespace/team",
            "Automated cost reports generated",
            "Teams aware of their consumption",
            "20% reduction in wasteful spending"
          ]
        }}
      ]
    }}
  ],
  "monitoring": {{
    "commands": [
      "kubectl top nodes",
      "kubectl top pods -A --sort-by=cpu",
      "kubectl get hpa -A",
      "kubectl get events -A --sort-by='.lastTimestamp'",
      "az aks show --resource-group {resource_group} --name {cluster_name} --query powerState"
    ],
    "key_metrics": [
      "cluster_cost_monthly",
      "cpu_utilization_average",
      "memory_utilization_average",
      "pod_count_by_namespace",
      "pvc_utilization_percentage"
    ],
    "success_metrics": [
      "cost_reduction_achieved",
      "resource_utilization_improved",
      "application_performance_maintained",
      "security_posture_enhanced"
    ]
  }},
  "review_schedule": [
    {{
      "day": 7,
      "title": "Week 1 Review - Quick Wins Assessment"
    }},
    {{
      "day": 14,
      "title": "Week 2 Review - Autoscaling Effectiveness"
    }},
    {{
      "day": 21,
      "title": "Week 3 Review - Storage and Network Optimization"
    }},
    {{
      "day": 30,
      "title": "Month 1 Review - Overall Cost Reduction"
    }},
    {{
      "day": 45,
      "title": "Phase 6 Complete - Full Implementation Review"
    }}
  ]
}}"""
    
    return prompt


def get_sample_usage():
    """
    Show how to use this comprehensive prompt
    """
    return """
    # Usage Example:
    
    from comprehensive_prompt_template import build_comprehensive_prompt
    
    prompt = build_comprehensive_prompt(
        cluster_name="aks-prod-cluster-01",
        cluster_id="rg-prod_aks-prod-cluster-01",
        current_cost=5000.00,
        resource_group="rg-production"
    )
    
    # Send this prompt to Claude API
    # The response will be a comprehensive 900+ line implementation plan
    """