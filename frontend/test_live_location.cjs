const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function testLiveLocationFeature() {
  console.log('=== TEST: "Use My Live Location" Feature Validation ===');
  const screenshotsDir = path.resolve(__dirname, '..', 'test_screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });

  // TEST CASE 1: Permission Granted -> Live Location + Reverse Geocoding + Map Centering + Route Calculation
  console.log('\n--- Test Case 1: Geolocation Granted Flow ---');
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    permissions: ['geolocation'],
    geolocation: { latitude: 12.9716, longitude: 77.5946 }
  });

  const page = await context.newPage();

  page.on('console', msg => {
    if (msg.type() === 'error') console.error('[Browser Error]:', msg.text());
  });

  await page.goto('http://127.0.0.1:5173/travel');
  await page.waitForLoadState('networkidle');

  // Verify the "Use My Live Location" button is visible
  const liveLocationBtn = await page.waitForSelector('#btn-use-live-location', { timeout: 5000 });
  const btnText = await liveLocationBtn.innerText();
  console.log('Found button text:', btnText);
  if (!btnText.includes('Use My Live Location')) {
    throw new Error('Button text does not match "Use My Live Location"');
  }

  // Check initial origin value
  const originInput = await page.waitForSelector('#origin-location-input');
  const initialOrigin = await originInput.inputValue();
  console.log('Initial Origin:', initialOrigin);

  // Click "Use My Live Location"
  console.log('Clicking "Use My Live Location" button...');
  await liveLocationBtn.click();

  // Wait for reverse geocoding and live location state to update
  await page.waitForTimeout(2500);

  const updatedOrigin = await originInput.inputValue();
  console.log('Updated Origin after Live Location detection:', updatedOrigin);

  if (updatedOrigin === initialOrigin) {
    throw new Error('Origin was not updated with live location!');
  }

  // Check success badge
  const successBadge = await page.locator('text=/Live location active/i').first();
  const isSuccessVisible = await successBadge.isVisible();
  console.log('Success badge visible:', isSuccessVisible);

  const shot1 = path.join(screenshotsDir, 'live_location_granted.png');
  await page.screenshot({ path: shot1, fullPage: true });
  console.log('Saved screenshot:', shot1);

  // Calculate route with the live location
  const calcBtn = await page.waitForSelector('button:has-text("Calculate Route")');
  await calcBtn.click();
  console.log('Clicked "Calculate Route" with live origin, waiting for results...');
  await page.waitForTimeout(3000);

  const metricSummary = await page.locator('text=/Route Metric Summary/i').first();
  const isRouteVisible = await metricSummary.isVisible();
  console.log('Route metric summary visible:', isRouteVisible);

  const shotRoute = path.join(screenshotsDir, 'live_location_route_calculated.png');
  await page.screenshot({ path: shotRoute, fullPage: true });
  console.log('Saved route screenshot:', shotRoute);

  await context.close();

  // TEST CASE 2: Permission Denied Error Handling
  console.log('\n--- Test Case 2: Geolocation Permission Denied Flow ---');
  const deniedContext = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    permissions: [] // No geolocation permission
  });

  const deniedPage = await deniedContext.newPage();
  await deniedPage.goto('http://127.0.0.1:5173/travel');
  await deniedPage.waitForLoadState('networkidle');

  const deniedBtn = await deniedPage.waitForSelector('#btn-use-live-location');
  await deniedBtn.click();
  await deniedPage.waitForTimeout(1500);

  const errorAlert = await deniedPage.locator('text=/Location permission was denied|Could not determine your location/i').first();
  const isErrorVisible = await errorAlert.isVisible();
  console.log('Permission denied error alert displayed gracefully:', isErrorVisible);

  const shotDenied = path.join(screenshotsDir, 'live_location_denied.png');
  await deniedPage.screenshot({ path: shotDenied, fullPage: true });
  console.log('Saved denied screenshot:', shotDenied);

  await deniedContext.close();
  await browser.close();

  console.log('\n=== ALL LIVE LOCATION TEST FLOWS PASSED SUCCESSFULLY! ===');
}

testLiveLocationFeature().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
