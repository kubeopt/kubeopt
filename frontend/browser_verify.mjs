/**
 * Browser rendering check for null-cost display.
 *
 * Loads the KubeOpt dev server, mocks the API responses for three cost scenarios,
 * and asserts the rendered text via Playwright.
 *
 * Cases:
 *   1. total_monthly_cost = null  → renders "Unavailable"
 *   2. total_monthly_cost = 0.0   → renders "$0.00"
 *   3. Fresh overview (null) replaces stale cluster row (999.99) → "Unavailable"
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

// Build a minimal mock token (the app just checks existence for routing)
const MOCK_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjo5OTk5OTk5OTk5fQ.mock';

async function mockAndLoad(page, overviewCost, clusterCost) {
  // Intercept all API calls and return controlled responses
  await page.route('**/api/auth/login', r => r.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ token: MOCK_TOKEN }),
  }));

  await page.route('**/api/clusters**', r => {
    const url = r.request().url();
    if (url.includes('/analyze') || url.includes('/analysis')) return r.continue();
    r.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        clusters: [{
          cluster_id: 'test-cluster-001',
          cluster_name: 'Test Cluster',
          cloud_provider: 'azure',
          region: 'eastus',
          optimization_score: 72,
          total_cost: clusterCost,       // stale cluster-row value
          potential_savings: null,
          node_count: 3,
          status: 'active',
        }],
        total: 1,
      }),
    });
  });

  await page.route('**/api/v2/analysis/*/dashboard-overview', r => r.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      total_monthly_cost: overviewCost,  // fresh overview value
      potential_savings: null,
      optimization_score: 72,
      node_count: 3,
      pod_count: 12,
      health_score: 85,
      analysis_status: 'completed',
      top_recommendations: [],
    }),
  }));

  await page.route('**/api/v2/analysis/*/analyze**', r => r.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ status: 'completed', source: 'collector' }),
  }));

  // Catch-all for everything else
  await page.route('**/api/**', r => r.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({}),
  }));

  // Set auth token in localStorage before navigation
  await page.addInitScript((token) => {
    window.localStorage.setItem('kubeopt_token', token);
    window.localStorage.setItem('token', token);
    window.localStorage.setItem('auth_token', token);
  }, MOCK_TOKEN);

  await page.goto(`${DEV_URL}/cluster/test-cluster-001`);
  await page.waitForTimeout(2000);
}

async function main() {
  const browser = await chromium.launch({ headless: true });

  // ── Case 1: Unknown cost (null) → "Unavailable" ──────────────────────────
  {
    const page = await browser.newPage();
    await mockAndLoad(page, null, null);
    const text = await page.textContent('body');
    check('Case 1 — null renders Unavailable (Overview tab)',
      text.includes('Unavailable'), true);
    await page.screenshot({ path: '/tmp/case1_null.png' });
    await page.close();
  }

  // ── Case 2: Explicit zero → "$0.00" not "Unavailable" ────────────────────
  {
    const page = await browser.newPage();
    await mockAndLoad(page, 0, 0);
    await page.waitForTimeout(1500);
    const text = await page.textContent('body');
    const hasZero = text.includes('$0.00') || text.includes('$0');
    const hasUnavailable = text.includes('Unavailable');
    check('Case 2 — zero renders $0.00 (Overview tab)', hasZero, true);
    check('Case 2 — zero does NOT render Unavailable', hasUnavailable, false);
    await page.screenshot({ path: '/tmp/case2_zero.png' });
    await page.close();
  }

  // ── Case 3: Fresh overview (null) over stale cluster row ($999.99) ────────
  {
    const page = await browser.newPage();
    // clusterCost = 999.99 (stale row), overviewCost = null (fresh collector)
    await mockAndLoad(page, null, 999.99);
    await page.waitForTimeout(1500);
    const text = await page.textContent('body');
    const hasUnavailable = text.includes('Unavailable');
    const hasStaleCost = text.includes('999') || text.includes('$1,000');
    check('Case 3 — fresh null overview renders Unavailable', hasUnavailable, true);
    check('Case 3 — stale $999.99 does NOT show', hasStaleCost, false);
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
