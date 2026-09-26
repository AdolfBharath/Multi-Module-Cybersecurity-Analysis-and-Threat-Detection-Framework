const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const { mkdir } = require('node:fs/promises');
const path = require('node:path');

let browser;
const base = process.env.UI_BASE_URL || 'http://127.0.0.1:5173';
const output = path.resolve(__dirname, '../../.local-run');
const metrics = { total_logs: 124, critical_alerts: 3, incidents: 1, high_threats: 8, medium_threats: 12, low_threats: 4, network_status: 'Events recorded', cpu: 22, memory: 45, disk: 61, todays_attacks: 4, weekly_trend: Array.from({ length: 7 }, (_, i) => ({ name: `Sep ${19 + i}`, attacks: i })), monthly_trend: Array.from({ length: 30 }, (_, i) => ({ name: `Day ${i + 1}`, alerts: i % 4 })), attack_timeline: [], alert_timeline: [], recent_activity: [{ action: 'Authentication event recorded', time: new Date().toISOString() }], live_feed: [{ id: 1, title: 'Suspicious privileged access', severity: 'critical', source: 'identity', created_at: new Date().toISOString() }], threat_map: [], top_attack_sources: [], mitre_matrix: [{ tactic: 'Credential Access', technique: 'T1110 Brute Force', count: 2 }] };

before(async () => { await mkdir(output, { recursive: true }); browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || undefined }); });
after(async () => { await browser?.close(); });

async function workspace({ viewer = false, failure = false, empty = false } = {}) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  let notices = empty ? [] : [{ id: 1, title: 'Critical security alert', message: 'Suspicious privileged access detected', severity: 'critical', status: 'unread', created_at: new Date().toISOString(), related_entity: 'alert', related_id: 1, required_permission: 'alerts:read' }];
  await page.addInitScript(({ viewer }) => { localStorage.setItem('cybershield_token', 'ui-test-session'); localStorage.setItem('cybershield_user', JSON.stringify({ id: 1, full_name: 'Bharath Murugan', role: viewer ? 'Viewer' : 'Admin', permissions: ['dashboard:read'], email: 'test.admin@cybershield.local' })); }, { viewer });
  let connection;
  await page.routeWebSocket('**/ws/live*', ws => { connection = ws; ws.send(JSON.stringify({ type: 'notification_snapshot', notifications: notices, unread_count: notices.filter(n => n.status === 'unread').length })); });
  await page.route('**/api/v1/**', async route => {
    const url = new URL(route.request().url());
    let data = {};
    if (url.pathname.endsWith('/dashboard')) {
      if (failure) return route.fulfill({ status: 500, json: { detail: 'SQL secret /internal/path/token' } });
      data = empty ? { ...metrics, total_logs: 0, critical_alerts: 0, incidents: 0, high_threats: 0, medium_threats: 0, low_threats: 0, live_feed: [], recent_activity: [], mitre_matrix: [] } : metrics;
    } else if (url.pathname.endsWith('/incidents')) data = empty ? [] : [{ id: 1, title: 'Suspicious privileged access', severity: 'critical', status: 'triage', assignee: 'SOC Queue', created_at: new Date().toISOString() }];
    else if (url.pathname.endsWith('/unread-count')) data = { data: { unread_count: notices.filter(n => n.status === 'unread').length } };
    else if (route.request().method() === 'PUT') { notices = notices.map(n => ({ ...n, status: url.pathname.endsWith('/archive') ? 'archived' : 'read' })); data = { success: true }; }
    else if (url.pathname.endsWith('/notifications')) data = { data: notices };
    await route.fulfill({ json: data });
  });
  await page.goto(base);
  await page.getByRole('heading', { name: 'Security Operations Overview' }).waitFor();
  if (!failure) await page.getByText('Posture score not configured').waitFor();
  return { page, context, push: item => { notices = [...notices, item]; connection.send(JSON.stringify({ type: 'notification_snapshot', notifications: notices, unread_count: notices.filter(n => n.status === 'unread').length })); } };
}

test('Dashboard fits all six requested viewport widths', async () => {
  const { page, context } = await workspace();
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  for (const width of [320, 375, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.screenshot({ path: path.join(output, `dashboard-${width}.png`), fullPage: true, animations: 'disabled' });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, `Overflow at ${width}px`);
    assert.ok(await page.locator('.recharts-surface').isVisible());
  }
  assert.deepEqual(errors, []);
  await context.close();
});

test('Bell, center, and dashboard synchronize reads and live notifications', async () => {
  const { page, context, push } = await workspace();
  await page.getByRole('button', { name: 'Notifications, 1 unread', exact: true }).click();
  await page.locator('#notification-popover').getByRole('button', { name: 'Mark Critical security alert as read', exact: true }).click();
  await page.getByRole('button', { name: 'Notifications, 0 unread', exact: true }).waitFor();
  push({ id: 2, title: 'New detection from server', message: 'Live event', severity: 'high', status: 'unread', created_at: new Date().toISOString(), required_permission: 'dashboard:read' });
  await page.getByRole('button', { name: 'Notifications, 1 unread', exact: true }).waitFor();
  await page.getByRole('link', { name: 'View all notifications', exact: true }).click();
  await page.getByRole('heading', { name: 'Notifications', exact: true }).waitFor();
  await page.getByRole('button', { name: 'Mark all as read' }).click();
  await page.getByRole('button', { name: 'Notifications, 0 unread', exact: true }).waitFor();
  await context.close();
});

test('Mobile drawer and dropdown support keyboard dismissal without overflow', async () => {
  const { page, context } = await workspace();
  await page.setViewportSize({ width: 320, height: 700 });
  await page.getByRole('button', { name: 'Toggle navigation' }).click();
  await page.waitForFunction(() => document.querySelector('.soc-sidebar').getBoundingClientRect().left >= 0);
  assert.equal(await page.locator('.soc-sidebar').evaluate(el => el.getBoundingClientRect().left >= 0), true);
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Notifications, 1 unread' }).click();
  await page.screenshot({ path: path.join(output, 'notifications-mobile.png'), fullPage: true, animations: 'disabled' });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('#notification-popover').count(), 0);
  await context.close();
});

test('Viewer navigation and route guards enforce the permission presentation', async () => {
  const { page, context } = await workspace({ viewer: true });
  assert.equal(await page.locator('.soc-sidebar').getByRole('link', { name: 'Settings', exact: true }).count(), 0);
  assert.equal(await page.locator('.soc-sidebar').getByRole('link', { name: 'Malware analysis', exact: true }).count(), 0);
  await page.goto(`${base}/settings`);
  await page.getByRole('heading', { name: 'Unauthorized', exact: true }).waitFor();
  await context.close();
});

test('Empty states and safe component failures retain the rest of the dashboard', async () => {
  const empty = await workspace({ empty: true });
  await empty.page.getByText('No active incidents', { exact: true }).waitFor();
  await empty.page.getByText('No recent security events', { exact: true }).waitFor();
  await empty.context.close();
  const broken = await workspace({ failure: true });
  await broken.page.getByText('Unable to load the security overview.', { exact: false }).waitFor();
  assert.equal(await broken.page.getByText('SQL secret /internal/path/token', { exact: false }).count(), 0);
  await broken.page.getByRole('heading', { name: 'Recent notifications' }).waitFor();
  await broken.context.close();
});
