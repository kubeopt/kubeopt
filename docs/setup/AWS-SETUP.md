# AWS Credentials Setup Guide

Configure KubeOpt to analyze your EKS clusters and retrieve cost data from AWS.

## Prerequisites

- AWS account with EKS clusters
- IAM user or role with appropriate permissions
- AWS CLI installed (optional, for testing)

## Required Environment Variables

```bash
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_DEFAULT_REGION=us-east-1
```

Set these in your `.env` file or as environment variables in your deployment platform.

## IAM Policy

Create an IAM user with the following policy attached. This provides read-only access to EKS, Cost Explorer, and CloudWatch.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EKSReadAccess",
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:ListNodegroups",
        "eks:DescribeNodegroup",
        "eks:ListUpdates",
        "eks:DescribeUpdate"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EC2ReadAccess",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeAddresses",
        "ec2:DescribeLoadBalancers",
        "ec2:DescribeRegions",
        "autoscaling:DescribeAutoScalingGroups"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CostExplorerAccess",
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast",
        "ce:GetReservationUtilization",
        "ce:GetSavingsPlansUtilization"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchMetrics",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    },
    {
      "Sid": "STSIdentity",
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

## Step-by-Step Setup

### 1. Create an IAM User

```bash
aws iam create-user --user-name kubeopt-reader
```

### 2. Create and Attach the Policy

```bash
aws iam create-policy \
  --policy-name KubeOptReadOnly \
  --policy-document file://kubeopt-iam-policy.json

aws iam attach-user-policy \
  --user-name kubeopt-reader \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/KubeOptReadOnly
```

### 3. Generate Access Keys

```bash
aws iam create-access-key --user-name kubeopt-reader
```

Copy the `AccessKeyId` and `SecretAccessKey` from the output into your `.env` file.

### 4. Verify Access

```bash
# Test credentials
aws sts get-caller-identity

# Test EKS access
aws eks list-clusters --region us-east-1
```

## Cost Explorer

AWS Cost Explorer must be enabled in your account for cost data to be available. If you haven't used it before:

1. Go to the AWS Console
2. Navigate to Billing and Cost Management
3. Select Cost Explorer
4. Click "Enable Cost Explorer"

Cost data typically becomes available within 24 hours of enabling.

## Multi-Region Support

KubeOpt uses the `AWS_DEFAULT_REGION` for initial authentication but can analyze EKS clusters across all regions. The region is detected automatically from the cluster ARN.

## Using IAM Roles (Recommended for Production)

Instead of access keys, you can use IAM roles with OIDC for EKS. Attach the policy above to the role and configure:

```bash
AWS_ROLE_ARN=arn:aws:iam::YOUR_ACCOUNT_ID:role/kubeopt-reader
AWS_DEFAULT_REGION=us-east-1
```

This avoids storing long-lived credentials.

## Troubleshooting

**"Access Denied" on Cost Explorer**: Ensure Cost Explorer is enabled and the IAM policy includes `ce:*` permissions. Cost Explorer access can take up to 24 hours to activate.

**"Cluster not found"**: Verify the region. EKS clusters are region-specific. Check `aws eks list-clusters --region <region>` for each region.

**"STS token expired"**: If using temporary credentials, ensure your session hasn't expired. For long-running deployments, use IAM roles instead of access keys.
