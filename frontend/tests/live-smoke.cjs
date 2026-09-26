const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || undefined });
  try {
    for (const role of ['ADMIN', 'SOC', 'MALWARE', 'VULN', 'VIEWER']) {
      const password = process.env[`TEST_${role}_PASSWORD`];
      assert.ok(password, `TEST_${role}_PASSWORD is required`);
      const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
      const page = await context.newPage();
      const failures = [];
      page.on('pageerror', error => failures.push(error.message));
      await page.goto(process.env.UI_BASE_URL || 'http://127.0.0.1:5173');
      await page.getByPlaceholder('Email', { exact: true }).fill(`test.${role.toLowerCase()}@cybershield.local`);
      await page.getByPlaceholder('Password', { exact: true }).fill(password);
      await page.getByRole('button', { name: 'Enter SOC' }).click();
      await page.getByRole('heading', { name: 'Security Operations Overview' }).waitFor();
      await page.getByText('Posture score not configured').waitFor();
      await page.getByText('Notifications connected', { exact: true }).waitFor();
      assert.equal(await page.getByText('Unable to load', { exact: false }).count(), 0);
      if (role === 'ADMIN') await page.screenshot({ path: path.resolve(__dirname, '../../.local-run/dashboard-live.png'), fullPage: true, animations: 'disabled' });
      await page.locator('.bell-button').click();
      await page.locator('#notification-popover').waitFor();
      assert.deepEqual(failures, []);
      console.log(`${role}: login, dashboard, authorized notification connection, and bell passed`);
      await context.close();
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
