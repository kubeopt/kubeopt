/**
 * Browser rendering check for null-cost display.
 *
 * Loads the KubeOpt dev server, mocks API responses for three cost scenarios,
 * and asserts the Monthly Cost metric in the Overview tab.
 *
 * Cases:
 *   1. total_monthly_cost = null  → Monthly Cost shows "Unavailable"
 *   2. total_monthly_cost = 0.0   → Monthly Cost shows "$0.00" (not "Unavailable")
 *   3. Fresh overview (null) replaces stale cluster row ($999.99) → Monthly Cost shows "Unavailable"
 *
 * Run: node browser_verify.mjs   (dev server must be running on :5174)
 */

import { chromium } from 'playwright';

const DEV_URL = 'http://localhost:5174';
const PASS = [];
const FAIL = [];

function check(label, got, expected) {
  if (typeof expected === 'function' ? expected(got) : got === expected) {
    console.log(`✅  ${label}: ${JSON.stringify(got)}`);
    PASS.push(label);
  } else {
    console.log(`❌  ${label}: got ${JSON.stringify(got)}, expected ${JSON.stringify(expected)}`);
    FAIL.push(label);
  }
}

const MOCK_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjo5OTk5OTk5OTk5fQ.mock';
const MOCK_USER = JSON.stringify({ sub: 'test', username: 'test' });

function overviewBody(cost) {
  return JSON.stringify({
    total_monthly_cost: cost,
    potential_savings: null,
    optimization_score: 72,
    node_count: 3,
    pod_count: 12,
    health_score: 85,
    analysis_status: 'completed',
    top_recommendations: [],
  });
}

function clusterListBody(clusterCost) {
  return JSON.stringify({
    clusters: [{
      cluster_id: 'test-cluster-001',
      cluster_name: 'Test Cluster',
      cloud_provider: 'azure',
      region: 'eastus',
      optimization_score: 72,
      total_cost: clusterCost,
      potential_savings: null,
      node_count: 3,
      status: 'active',
    }],
    total: 1,
  });
}

async function mockAndLoad(page, overviewCost, clusterCost) {
  // Use a URL predicate to scope interception strictly to /api/ paths.
  // Glob patterns like **/api/** can inadvertently match Vite module script
  // requests and break page load with MIME type errors.
  await page.route(
    (url) => url.pathname.startsWith('/api/'),
    (route) => {
      const path = route.request().url().replace(/^https?:\/\/[^/]+/, '').split('?')[0];
      if (path === '/api/clusters') {
        return route.fulfill({ status: 200, contentType: 'application/json', body: clusterListBody(clusterCost) });
      }
      if (path === '/api/dashboard/overview') {
        return route.fulfill({ status: 200, contentType: 'application/json', body: overviewBody(overviewCost) });
      }
      if (path === '/api/auth/login') {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ token: MOCK_TOKEN }) });
      }
      // All other /api/ calls return an empty object (collector status, chart data, etc.)
      return route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    },
  );

  await page.addInitScript(({ token, user }) => {
    localStorage.setItem('kubeopt_token', token);
    localStorage.setItem('kubeopt_user', user);
  }, { token: MOCK_TOKEN, user: MOCK_USER });

  await page.goto(`${DEV_URL}/cluster/test-cluster-001`);
  await page.waitForTimeout(2500);
}

// Extract the value shown under the "MONTHLY COST" label.
// The Overview tab renders: <div>MONTHLY COST</div> immediately followed by <div>{value}</div>
// within the same flex container; innerText preserves newline separation.
async function getMonthlyCostText(page) {
  const body = await page.evaluate(() => document.body.innerText);
  const match = body.match(/MONTHLY COST\n([^\n]+)/);
  return match ? match[1].trim() : null;
}

async function main() {
  const browser = await chromium.launch({ headless: true });

  // ── Case 1: Unknown cost (null) → Monthly Cost shows "Unavailable" ─────────
  {
    const page = await browser.newPage();
    await mockAndLoad(page, null, null);
    const cost = await getMonthlyCostText(page);
    check('Case 1 — null: Monthly Cost shows Unavailable', cost, 'Unavailable');
    await page.screenshot({ path: '/tmp/case1_null.png' });
    await page.close();
  }

  // ── Case 2: Explicit zero → Monthly Cost shows "$0.00", not "Unavailable" ──
  {
    const page = await browser.newPage();
    await mockAndLoad(page, 0, 0);
    const cost = await getMonthlyCostText(page);
    check('Case 2 — zero: Monthly Cost shows $0', cost !== null && cost.includes('$0'), true);
    check('Case 2 — zero: Monthly Cost is not Unavailable', cost !== 'Unavailable', true);
    await page.screenshot({ path: '/tmp/case2_zero.png' });
    await page.close();
  }

  // ── Case 3: Fresh overview (null) over stale cluster row ($999.99) ──────────
  {
    const page = await browser.newPage();
    await mockAndLoad(page, null, 999.99);
    const cost = await getMonthlyCostText(page);
    check('Case 3 — fresh null over stale row: Monthly Cost shows Unavailable', cost, 'Unavailable');
    check('Case 3 — stale $999.99 not shown as cost', cost !== null && !cost.includes('999'), true);
    await page.screenshot({ path: '/tmp/case3_stale.png' });
    await page.close();
  }

  await browser.close();

  console.log(`\nResults: ${PASS.length} passed, ${FAIL.length} failed`);
  if (FAIL.length > 0) {
    FAIL.forEach(f => console.log(`  ❌ ${f}`));
    process.exit(1);
  } else {
    console.log('  All browser rendering cases confirmed.');
  }
}

main().catch(e => { console.error(e); process.exit(1); });
