# GCP Billing Export Setup Guide

This guide walks you through enabling BigQuery billing export in Google Cloud so that KubeOpt can query **real billing data** instead of estimated costs for your GKE clusters.

Without this setup, KubeOpt falls back to cost estimates based on node pool machine types and static pricing tables. With BigQuery billing export, you get actual spend broken down by GKE service (Compute Engine, Persistent Disk, Network, etc.).

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Step 1: Find Your Billing Account ID](#step-1-find-your-billing-account-id)
3. [Step 2: Create a BigQuery Dataset](#step-2-create-a-bigquery-dataset)
4. [Step 3: Enable Billing Export to BigQuery](#step-3-enable-billing-export-to-bigquery)
5. [Step 4: Wait for Data to Populate](#step-4-wait-for-data-to-populate)
6. [Step 5: Verify the Export Table Exists](#step-5-verify-the-export-table-exists)
7. [Step 6: Grant BigQuery Access to Your Service Account](#step-6-grant-bigquery-access-to-your-service-account)
8. [Step 7: Configure KubeOpt Environment Variables](#step-7-configure-kubeopt-environment-variables)
9. [Step 8: Verify KubeOpt Reads Real Billing Data](#step-8-verify-kubeopt-reads-real-billing-data)
10. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

Before you begin, make sure you have:

- A Google Cloud project with an active billing account
- At least one GKE cluster running (so there's cost data to export)
- **Billing Account Administrator** role (to enable billing export)
- **BigQuery Admin** role (to create datasets and grant access)
- A service account for KubeOpt (either uploaded via the KubeOpt UI or set via `GOOGLE_APPLICATION_CREDENTIALS`)

---

## Step 1: Find Your Billing Account ID

You'll need your Billing Account ID — it looks like `01A2B3-C4D5E6-F7G8H9`.

1. Go to the Google Cloud Console: https://console.cloud.google.com
2. Click the **Navigation menu** (hamburger icon, top-left)
3. Scroll down and click **Billing**
4. If you have multiple billing accounts, select the one linked to your GKE project
5. On the Billing Overview page, your **Billing Account ID** is displayed near the top, under the billing account name

   It looks like this:
   ```
   Billing account: My Billing Account
   Billing account ID: 01A2B3-C4D5E6-F7G8H9
   ```

6. **Copy this ID** — you'll need it in Step 7

> **Tip:** You can also find it via gcloud CLI:
> ```bash
> gcloud billing accounts list
> ```
> Output:
> ```
> ACCOUNT_ID            NAME                  OPEN   MASTER_ACCOUNT_ID
> 01A2B3-C4D5E6-F7G8H9  My Billing Account    True
> ```

---

## Step 2: Create a BigQuery Dataset

The billing export needs a BigQuery dataset to write to. You can use an existing dataset or create a new one.

1. Go to **BigQuery** in the Cloud Console: https://console.cloud.google.com/bigquery
2. In the **Explorer** panel on the left, click the **three dots** next to your project name
3. Click **Create dataset**
4. Fill in the details:

   | Field | Value | Notes |
   |-------|-------|-------|
   | **Dataset ID** | `billing_export` | You can name it anything, but `billing_export` is conventional |
   | **Data location** | `US` (or your preferred region) | Must match your organization's data residency requirements. **Once set, this cannot be changed.** |
   | **Default table expiration** | Leave blank (Never) | Billing data should be retained |
   | **Encryption** | Google-managed encryption key | Default is fine for most users |

5. Click **Create dataset**

> **Important:** The dataset must be in the **same project** that's linked to the billing account, or in a project where the billing account has export permissions. For simplicity, use the same project where your GKE clusters run.

---

## Step 3: Enable Billing Export to BigQuery

Now connect your billing account to the BigQuery dataset.

1. Go to **Billing** in the Cloud Console: https://console.cloud.google.com/billing
2. Select your billing account (the one from Step 1)
3. In the left sidebar, click **Billing export**
4. You'll see tabs for different export types. Click the **Detailed usage cost** tab

   > **Why "Detailed usage cost"?** This is the export type that includes resource-level labels, which KubeOpt uses to filter costs by GKE cluster name (via the `goog-k8s-cluster-name` label). The "Standard usage cost" export does NOT include resource labels.

5. Click **Edit settings**
6. Configure the export:

   | Field | Value |
   |-------|-------|
   | **Project** | Select the project where you created the BigQuery dataset in Step 2 |
   | **Dataset** | Select `billing_export` (or whatever you named your dataset) |

7. Click **Save**

You should see a confirmation message: "Detailed usage cost export is enabled."

The status will show:
```
Detailed usage cost
Status: Enabled
Project: your-project-id
Dataset: billing_export
```

> **Note:** Google also offers "Standard usage cost" and "Pricing" export types. You can enable those too, but KubeOpt specifically requires **Detailed usage cost** because it contains resource labels needed to filter by cluster.

---

## Step 4: Wait for Data to Populate

After enabling the export, **Google does NOT backfill historical data.** Billing data will start appearing in BigQuery from the moment you enable the export.

- **First data:** Typically appears within **24-48 hours** after enabling
- **Complete day:** A full day's data is usually available by the **next morning** (Pacific Time)
- **Ongoing:** Data is updated multiple times per day (not real-time, but within a few hours)

> **What to do while waiting:** KubeOpt will continue using its estimated costs (based on node pool machine types) until BigQuery data becomes available. Once the data is there, KubeOpt automatically switches to real billing data.

---

## Step 5: Verify the Export Table Exists

After 24-48 hours, verify that the billing export table was created.

1. Go to **BigQuery**: https://console.cloud.google.com/bigquery
2. In the **Explorer** panel, expand your project, then expand the `billing_export` dataset
3. You should see a table named like:
   ```
   gcp_billing_export_resource_v1_01A2B3C4D5E6F7G8H9
   ```

   Notice:
   - The prefix is `gcp_billing_export_resource_v1_` (for Detailed usage cost)
   - The suffix is your billing account ID **with dashes removed**
   - Example: Account `01A2B3-C4D5E6-F7G8H9` becomes `01A2B3C4D5E6F7G8H9`

4. Click on the table to see its schema. Key columns KubeOpt uses:
   - `service.description` — The GCP service name (e.g., "Compute Engine", "Cloud Storage")
   - `cost` — The cost amount
   - `currency` — Currency code (e.g., "USD")
   - `usage_start_time` — When the usage occurred
   - `project.id` — The GCP project ID
   - `labels` — Array of key-value pairs (includes `goog-k8s-cluster-name`)

5. **Quick test query** — Run this in the BigQuery query editor to verify data exists:
   ```sql
   SELECT
       service.description AS service,
       ROUND(SUM(cost), 2) AS total_cost,
       currency
   FROM `your-project-id.billing_export.gcp_billing_export_resource_v1_01A2B3C4D5E6F7G8H9`
   WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
       AND project.id = 'your-project-id'
   GROUP BY service.description, currency
   ORDER BY total_cost DESC
   ```

   Replace:
   - `your-project-id` with your actual project ID
   - `01A2B3C4D5E6F7G8H9` with your billing account ID (dashes removed)

6. **Verify GKE labels exist** — Run this to confirm your GKE clusters have cost labels:
   ```sql
   SELECT DISTINCT l.value AS cluster_name
   FROM `your-project-id.billing_export.gcp_billing_export_resource_v1_01A2B3C4D5E6F7G8H9`,
       UNNEST(labels) AS l
   WHERE l.key = 'goog-k8s-cluster-name'
       AND DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
   ```

   This should list all your GKE cluster names. If it returns no results:
   - The billing export may not have accumulated enough data yet (wait another 24 hours)
   - Your GKE clusters might be very new (labels take time to appear in billing data)

---

## Step 6: Grant BigQuery Access to Your Service Account

KubeOpt's service account needs permission to query the billing dataset.

### Option A: Via Google Cloud Console (Recommended)

1. Go to **IAM & Admin** > **IAM**: https://console.cloud.google.com/iam-admin/iam
2. Make sure you're in the project where the BigQuery dataset lives
3. Click **Grant Access** (top of page)
4. In the **New principals** field, enter your service account email
   - It looks like: `kubeopt@your-project-id.iam.gserviceaccount.com`
   - You can find it in your service account JSON file under the `client_email` field
5. In the **Role** dropdown, search for and select: **BigQuery Data Viewer** (`roles/bigquery.dataViewer`)
6. Click **Add another role** and also add: **BigQuery Job User** (`roles/bigquery.jobUser`)

   > **Why two roles?**
   > - `BigQuery Data Viewer` — Allows reading data from tables
   > - `BigQuery Job User` — Allows running queries (creating query jobs)
   > Without `BigQuery Job User`, the service account can see the data but can't execute queries.

7. Click **Save**

### Option B: Via gcloud CLI

```bash
# Replace with your actual values
PROJECT_ID="your-project-id"
SERVICE_ACCOUNT="kubeopt@your-project-id.iam.gserviceaccount.com"

# Grant BigQuery Data Viewer
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/bigquery.dataViewer"

# Grant BigQuery Job User
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/bigquery.jobUser"
```

### Option C: Dataset-Level Permissions (More Restrictive)

If you want to limit access to just the billing dataset (not all BigQuery data in the project):

1. Go to **BigQuery**: https://console.cloud.google.com/bigquery
2. Click on your `billing_export` dataset in the Explorer panel
3. Click **Sharing** > **Permissions**
4. Click **Add Principal**
5. Enter your service account email
6. Assign the role: **BigQuery Data Viewer**
7. Click **Save**

You still need `BigQuery Job User` at the project level (Step 6, Option A or B) since query jobs are a project-level resource.

---

## Step 7: Configure KubeOpt Environment Variables

Set two environment variables so KubeOpt knows where to find the billing data.

### Required Variables

| Variable | Value | Example |
|----------|-------|---------|
| `GCP_BILLING_DATASET` | The BigQuery dataset name (just the dataset, not the full table path) | `billing_export` |
| `GCP_BILLING_ACCOUNT_ID` | Your billing account ID (with or without dashes — KubeOpt strips them automatically) | `01A2B3-C4D5E6-F7G8H9` |

### How to Set Them

**Option A: Add to your `.env` file**

```bash
# In /Users/srini/coderepos/nivaya/kubeopt/.env
# Add these lines:
GCP_BILLING_DATASET=billing_export
GCP_BILLING_ACCOUNT_ID=01A2B3-C4D5E6-F7G8H9
```

**Option B: Export in your shell**

```bash
export GCP_BILLING_DATASET="billing_export"
export GCP_BILLING_ACCOUNT_ID="01A2B3-C4D5E6-F7G8H9"
```

**Option C: Docker**

```bash
docker run -d -p 5001:5001 \
  -e GCP_BILLING_DATASET=billing_export \
  -e GCP_BILLING_ACCOUNT_ID=01A2B3-C4D5E6-F7G8H9 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-key.json \
  -v /path/to/your/service-account-key.json:/app/gcp-key.json \
  kubeopt:latest
```

### How KubeOpt Builds the Table Name

KubeOpt constructs the BigQuery table path as:

```
{project_id}.{GCP_BILLING_DATASET}.gcp_billing_export_resource_v1_{GCP_BILLING_ACCOUNT_ID}
```

For example, with:
- Project: `my-gcp-project`
- Dataset: `billing_export`
- Account ID: `01A2B3-C4D5E6-F7G8H9`

The table path becomes:
```
my-gcp-project.billing_export.gcp_billing_export_resource_v1_01A2B3C4D5E6F7G8H9
```

This must exactly match the table name created by Google's billing export (from Step 5).

---

## Step 8: Verify KubeOpt Reads Real Billing Data

1. **Restart KubeOpt** with the new environment variables:
   ```bash
   cd /Users/srini/coderepos/nivaya/kubeopt
   LOCAL_DEV=true .venv/bin/python main.py
   ```

2. **Trigger a GKE analysis** — either via the dashboard or API:
   ```bash
   curl -X POST http://localhost:5001/api/v2/analysis/analyze \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"cluster_id": "your-cluster-id"}'
   ```

3. **Check the logs** — look for these log messages:

   **With real billing data (success):**
   ```
   GKE costs for 'your-cluster': $142.35 (4 services)
   ```

   **Without billing data (still using estimates):**
   ```
   GCP_BILLING_DATASET not set. Cannot query costs.
   GKE cost estimate for 'your-cluster': $98.08 (30 days, 1 pools, estimated)
   ```

   **BigQuery query failed:**
   ```
   GCP BigQuery cost query failed: <error details>
   GKE cost estimate for 'your-cluster': $98.08 (30 days, 1 pools, estimated)
   ```

   KubeOpt gracefully falls back to estimated costs if BigQuery is unavailable, so your analysis will always complete.

---

## Troubleshooting

### "GCP_BILLING_DATASET not set. Cannot query costs."

The environment variable is not set or not visible to the KubeOpt process. Verify:
```bash
echo $GCP_BILLING_DATASET
```
If using `.env`, make sure KubeOpt loads it (check `python-dotenv` is installed and `.env` is in the working directory).

### "GCP BigQuery cost query failed: 403 Access Denied"

The service account doesn't have BigQuery permissions. Go back to [Step 6](#step-6-grant-bigquery-access-to-your-service-account) and verify both roles are granted:
- `roles/bigquery.dataViewer`
- `roles/bigquery.jobUser`

### "GCP BigQuery cost query failed: 404 Not found: Table"

The table name doesn't match. Common causes:

1. **Wrong dataset name** — Check `GCP_BILLING_DATASET` matches exactly (case-sensitive)
2. **Wrong billing account ID** — Verify `GCP_BILLING_ACCOUNT_ID` matches your billing account. Dashes are stripped automatically, so `01A2B3-C4D5E6-F7G8H9` and `01A2B3C4D5E6F7G8H9` both work
3. **Wrong export type** — You need **Detailed usage cost** export, not "Standard usage cost". The table prefix should be `gcp_billing_export_resource_v1_` (note `resource` in the name). Standard export creates `gcp_billing_export_v1_` (without `resource`)
4. **Data not yet available** — If you just enabled the export, wait 24-48 hours

Verify the actual table name in BigQuery Console and compare it to what KubeOpt constructs.

### "No cost data found for GKE cluster 'xxx'"

BigQuery query succeeded but returned zero rows for your cluster. This means:

1. **Cluster name mismatch** — KubeOpt filters by the `goog-k8s-cluster-name` label. Verify your cluster name in the billing data:
   ```sql
   SELECT DISTINCT l.value
   FROM `project.dataset.gcp_billing_export_resource_v1_XXXXX`,
       UNNEST(labels) AS l
   WHERE l.key = 'goog-k8s-cluster-name'
   ```
2. **Date range issue** — The export only contains data from when it was enabled. If you enabled it today, there's no data for last month.
3. **Wrong project** — The `project.id` filter might not match. Check which project your GKE cluster is billed under.

### "google-auth not installed" or "google.cloud.bigquery not installed"

Install the required Python packages:
```bash
pip install google-auth google-cloud-bigquery
```

Or with the venv:
```bash
cd /Users/srini/coderepos/nivaya/kubeopt
.venv/bin/pip install google-cloud-bigquery
```

### Billing export enabled but no table appears after 48 hours

1. Verify the export is still enabled: **Billing** > **Billing export** > **Detailed usage cost** tab
2. Check that the linked project hasn't changed
3. Ensure there's actual usage — if no GCP resources are running, there's nothing to export
4. Try the "Standard usage cost" tab to see if that table was created (if so, you selected the wrong export type)

### Cost data is much lower than expected

- Billing export only captures data **from the time it's enabled** — no backfill
- If enabled mid-month, the first month will show a partial amount
- Compare the date range in the KubeOpt analysis to when you enabled the export

---

## Summary of What You Need

| Item | Where to Find It | Example |
|------|-------------------|---------|
| Billing Account ID | Billing > Overview | `01A2B3-C4D5E6-F7G8H9` |
| BigQuery Dataset | You create it in Step 2 | `billing_export` |
| Service Account Email | Your SA JSON file, `client_email` field | `kubeopt@project.iam.gserviceaccount.com` |
| IAM Roles | Grant in Step 6 | `bigquery.dataViewer` + `bigquery.jobUser` |
| Env: `GCP_BILLING_DATASET` | Set in `.env` or shell | `billing_export` |
| Env: `GCP_BILLING_ACCOUNT_ID` | Set in `.env` or shell | `01A2B3-C4D5E6-F7G8H9` |

Once configured, KubeOpt automatically uses real billing data for all GKE cost analysis — no code changes required.
