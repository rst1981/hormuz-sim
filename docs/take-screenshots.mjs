import { chromium } from 'playwright';

const BASE = 'http://localhost:5173';
const DIR = 'D:/dev/hormuz-sim-dashboard/docs/screenshots';

async function navTo(page, label) {
  await page.locator(`aside button:has-text("${label}")`).click();
  await page.waitForTimeout(1500);
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // 1. Landing screen
  await page.goto(BASE);
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${DIR}/01-landing.png`, fullPage: true });
  console.log('✓ Landing');

  // 2. Create simulation
  await page.click('button:has-text("Create Baseline Simulation")');
  await page.waitForTimeout(2000);
  console.log('✓ Sim created');

  // 3. Run ~15 steps to populate charts
  for (let i = 0; i < 15; i++) {
    await page.locator('button:has-text("Step")').first().click();
    await page.waitForTimeout(600);
  }
  console.log('✓ 15 steps done');

  // 4. Dashboard with data
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${DIR}/02-dashboard.png`, fullPage: true });
  console.log('✓ Dashboard');

  // 5. Escalation Timeline
  await navTo(page, 'Escalation');
  await page.screenshot({ path: `${DIR}/03-escalation.png`, fullPage: true });
  console.log('✓ Escalation');

  // 6. Oil Market
  await navTo(page, 'Oil Market');
  await page.screenshot({ path: `${DIR}/04-oil-market.png`, fullPage: true });
  console.log('✓ Oil Market');

  // 7. Agent Explorer — click first agent
  await navTo(page, 'Agents');
  await page.waitForTimeout(500);
  // Click "Iran" agent in the list (not the sidebar)
  const agentBtn = page.locator('main button:has-text("Iran")').first();
  if (await agentBtn.isVisible()) {
    await agentBtn.click();
    await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: `${DIR}/05-agents.png`, fullPage: true });
  console.log('✓ Agents');

  // 8. Trump Tracker
  await navTo(page, 'Trump Tracker');
  await page.screenshot({ path: `${DIR}/06-trump-tracker.png`, fullPage: true });
  console.log('✓ Trump Tracker');

  // 9. Parameter Editor
  await navTo(page, 'Parameters');
  await page.screenshot({ path: `${DIR}/07-parameters.png`, fullPage: true });
  console.log('✓ Parameters');

  // 10. Monte Carlo — launch a small run
  await navTo(page, 'Monte Carlo');
  await page.waitForTimeout(500);
  // Set runs to 20 for speed
  const runsInput = page.locator('input[type="number"]').first();
  await runsInput.fill('20');
  await page.screenshot({ path: `${DIR}/08-montecarlo-config.png`, fullPage: true });
  // Launch and wait for results
  await page.click('button:has-text("Launch")');
  // Poll until results appear or 30s timeout
  for (let i = 0; i < 30; i++) {
    await page.waitForTimeout(1000);
    const hasResults = await page.locator('text=Outcome Distribution').isVisible().catch(() => false);
    if (hasResults) break;
  }
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${DIR}/09-montecarlo-results.png`, fullPage: true });
  console.log('✓ Monte Carlo');

  // 11. Scenario Comparison
  await navTo(page, 'Scenarios');
  await page.screenshot({ path: `${DIR}/10-comparison.png`, fullPage: true });
  console.log('✓ Comparison');

  // 12. Branch Comparison
  await navTo(page, 'Branches');
  await page.screenshot({ path: `${DIR}/11-branches.png`, fullPage: true });
  console.log('✓ Branches');

  await browser.close();
  console.log('\n✅ All screenshots saved to docs/screenshots/');
})();
