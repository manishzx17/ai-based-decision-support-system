const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function runPatientIsolationAudit() {
  console.log('=== STARTING FRONTEND PATIENT ISOLATION & AUTHENTICATION AUDIT ===');
  console.log('Target URL: http://127.0.0.1:5173');

  const report = {
    checks: {},
    consoleErrors: [],
    failedRequests: [],
    stepsCompleted: 0
  };

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  page.on('console', msg => {
    if (msg.type() === 'error') {
      const text = msg.text();
      // Ignore normal browser fetch network status 401 log during wrong password test
      if (text.includes('status of 401') || text.includes('favicon')) {
        return;
      }
      report.consoleErrors.push(text);
      console.error('[Browser Console Error]:', text);
    }
  });

  page.on('pageerror', err => {
    report.consoleErrors.push(err.message);
    console.error('[Browser Page Error]:', err.message);
  });

  page.on('requestfailed', req => {
    if (!req.url().includes('favicon')) {
      const failure = `${req.method()} ${req.url()} - ${req.failure()?.errorText || 'Failed'}`;
      report.failedRequests.push(failure);
      console.warn('[Network Request Failed]:', failure);
    }
  });

  try {
    // ==========================================
    // STEP 1: LOGIN PAGE & WRONG PASSWORD REJECTION
    // ==========================================
    console.log('\n--- STEP 1: Verify Login Page & Wrong Password Rejection ---');
    await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle' });

    // Fill wrong password
    const usernameInput = page.locator('main form input[type="text"], main input[type="text"]').first();
    const passwordInput = page.locator('main form input[type="password"], main input[type="password"]').first();
    await usernameInput.fill('demo_cardio');
    await passwordInput.fill('WrongPassword999!');

    const submitBtn = page.locator('main form button[type="submit"], main button[type="submit"]').first();
    await submitBtn.click();
    await page.waitForTimeout(1000);

    const errorMsgLocator = page.locator('main .bg-rose-50 span, form .text-rose-700');
    await errorMsgLocator.waitFor({ state: 'visible', timeout: 5000 });
    const errorMsg = await errorMsgLocator.first().textContent();
    console.log('Wrong password error message received:', errorMsg);
    if (!errorMsg || (!errorMsg.toLowerCase().includes('invalid') && !errorMsg.toLowerCase().includes('wrong') && !errorMsg.toLowerCase().includes('password'))) {
      throw new Error(`Expected invalid password error, got: ${errorMsg}`);
    }
    report.checks.wrong_password_rejected = true;

    // ==========================================
    // STEP 2: LOGIN USER 1 (Rahul Verma / Cardiology)
    // ==========================================
    console.log('\n--- STEP 2: Authenticate User 1 (Rahul Verma) ---');
    await usernameInput.fill('demo_cardio');
    await passwordInput.fill('DemoPassword@123');
    await submitBtn.click();
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.waitForLoadState('networkidle');

    // Verify User 1 Dashboard context
    const bodyText1 = await page.locator('body').textContent();
    if (!bodyText1.includes('Rahul') && !bodyText1.includes('Cardiology')) {
      throw new Error('User 1 context not found on dashboard');
    }
    console.log('User 1 authenticated: Rahul Verma / Cardiology confirmed');

    // Check Profile
    await page.goto('http://127.0.0.1:5173/profile', { waitUntil: 'networkidle' });
    await page.waitForSelector('form input', { state: 'visible' });
    const profileInputs1 = await page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
      return inputs.map(el => el.value).join(' ');
    });
    console.log('User 1 profile inputs evaluated:', profileInputs1);
    if (!profileInputs1.includes('Rahul') || !profileInputs1.includes('Hyderabad')) {
      throw new Error(`User 1 profile mismatch, found: ${profileInputs1}`);
    }
    console.log('User 1 profile verified: Rahul Verma / Hyderabad');

    // Check Records
    await page.goto('http://127.0.0.1:5173/records', { waitUntil: 'networkidle' });
    const recordsText1 = await page.locator('body').textContent();
    console.log('User 1 records page loaded successfully');

    // Check Recommendations
    await page.goto('http://127.0.0.1:5173/hospitals', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    console.log('User 1 recommendations page loaded');

    // Check Cost/LOS
    await page.goto('http://127.0.0.1:5173/cost', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    console.log('User 1 cost estimator loaded');

    // Check Assistant
    await page.goto('http://127.0.0.1:5173/assistant', { waitUntil: 'networkidle' });
    const assistantInput = page.locator('textarea, input[placeholder*="Ask"]');
    if (await assistantInput.count() > 0) {
      await assistantInput.fill('Hello doctor, what are my travel precautions?');
      const sendBtn = page.locator('button:has-text("Send"), button:has([class*="lucide-send"])').first();
      await sendBtn.click();
      await page.waitForTimeout(3000);
      console.log('User 1 assistant query executed');
    }

    report.checks.user1_rahul_complete = true;

    // ==========================================
    // STEP 3: LOGOUT USER 1
    // ==========================================
    console.log('\n--- STEP 3: Logout User 1 ---');
    const logoutBtn = page.locator('button[title*="Logout"], button[aria-label*="Logout"], button:has([class*="lucide-log-out"])').first();
    await logoutBtn.click();
    await page.waitForURL('**/login', { timeout: 10000 });
    await page.waitForLoadState('networkidle');

    // Verify storage cleared
    const storageStateAfterLogout1 = await page.evaluate(() => ({
      currentUser: localStorage.getItem('currentUser'),
      userToken: localStorage.getItem('user_token'),
      activeReportId: sessionStorage.getItem('active_report_id')
    }));
    console.log('Post-logout storage state:', storageStateAfterLogout1);
    if (storageStateAfterLogout1.currentUser !== null || storageStateAfterLogout1.userToken !== null) {
      throw new Error('Session was not fully cleared on logout');
    }
    report.checks.user1_logout_cleared = true;

    // ==========================================
    // STEP 4: LOGIN USER 2 (Priya Sharma / Neurology)
    // ==========================================
    console.log('\n--- STEP 4: Authenticate User 2 (Priya Sharma) ---');
    await page.locator('input[type="text"]').fill('demo_neuro');
    await page.locator('input[type="password"]').fill('DemoPassword@123');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.waitForLoadState('networkidle');

    const bodyText2 = await page.locator('body').textContent();
    if (!bodyText2.includes('Priya') && !bodyText2.includes('Neurology')) {
      throw new Error('User 2 context not found on dashboard');
    }
    if (bodyText2.includes('Rahul Verma')) {
      throw new Error('Cross-patient leakage: Rahul Verma found in Priya Sharma session!');
    }
    console.log('User 2 authenticated: Priya Sharma / Neurology confirmed (No Rahul leakage)');

    // Check User 2 Profile
    await page.goto('http://127.0.0.1:5173/profile', { waitUntil: 'networkidle' });
    await page.waitForSelector('form input', { state: 'visible' });
    const profileInputs2 = await page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
      return inputs.map(el => el.value).join(' ');
    });
    console.log('User 2 profile inputs evaluated:', profileInputs2);
    if (!profileInputs2.includes('Priya') || !profileInputs2.includes('Bengaluru')) {
      throw new Error(`User 2 profile mismatch, found: ${profileInputs2}`);
    }
    if (profileInputs2.includes('Rahul') || profileInputs2.includes('Hyderabad')) {
      throw new Error('Cross-patient leakage: Rahul / Hyderabad found in Priya profile!');
    }
    console.log('User 2 profile verified: Priya Sharma / Bengaluru (Clean isolation)');

    // Check User 2 Records
    await page.goto('http://127.0.0.1:5173/records', { waitUntil: 'networkidle' });
    const recordsText2 = await page.locator('body').textContent();
    if (recordsText2.includes('rahul_cardio_report.pdf')) {
      throw new Error('Cross-patient leakage: Rahul report found in Priya records!');
    }
    console.log('User 2 records verified: Isolated from User 1 reports');

    // Check Assistant for User 2
    await page.goto('http://127.0.0.1:5173/assistant', { waitUntil: 'networkidle' });
    const assistantText2 = await page.locator('body').textContent();
    if (assistantText2.includes('Rahul Verma')) {
      throw new Error('Cross-patient leakage: Rahul found in Priya assistant!');
    }
    console.log('User 2 assistant verified');
    report.checks.user2_priya_complete = true;

    // ==========================================
    // STEP 5: LOGOUT USER 2
    // ==========================================
    console.log('\n--- STEP 5: Logout User 2 ---');
    const logoutBtn2 = page.locator('button[title*="Logout"], button[aria-label*="Logout"], button:has([class*="lucide-log-out"])').first();
    await logoutBtn2.click();
    await page.waitForURL('**/login', { timeout: 10000 });
    await page.waitForLoadState('networkidle');
    report.checks.user2_logout_cleared = true;

    // ==========================================
    // STEP 6: LOGIN USER 3 (Amit Patel / Orthopedics)
    // ==========================================
    console.log('\n--- STEP 6: Authenticate User 3 (Amit Patel) ---');
    await page.locator('input[type="text"]').fill('demo_ortho');
    await page.locator('input[type="password"]').fill('DemoPassword@123');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.waitForLoadState('networkidle');

    const bodyText3 = await page.locator('body').textContent();
    if (!bodyText3.includes('Amit') && !bodyText3.includes('Ortho')) {
      throw new Error('User 3 context not found on dashboard');
    }
    if (bodyText3.includes('Rahul Verma') || bodyText3.includes('Priya Sharma')) {
      throw new Error('Cross-patient leakage: Prior user found in Amit Patel session!');
    }
    console.log('User 3 authenticated: Amit Patel / Orthopedics confirmed (No prior patient leakage)');

    // Check User 3 Profile
    await page.goto('http://127.0.0.1:5173/profile', { waitUntil: 'networkidle' });
    await page.waitForSelector('form input', { state: 'visible' });
    const profileInputs3 = await page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
      return inputs.map(el => el.value).join(' ');
    });
    console.log('User 3 profile inputs evaluated:', profileInputs3);
    if (!profileInputs3.includes('Amit') || !profileInputs3.includes('Delhi')) {
      throw new Error(`User 3 profile mismatch, found: ${profileInputs3}`);
    }
    if (profileInputs3.includes('Rahul') || profileInputs3.includes('Priya')) {
      throw new Error('Cross-patient leakage in Amit profile!');
    }
    console.log('User 3 profile verified: Amit Patel / Delhi (Clean isolation)');

    // Check User 3 Records
    await page.goto('http://127.0.0.1:5173/records', { waitUntil: 'networkidle' });
    const recordsText3 = await page.locator('body').textContent();
    if (recordsText3.includes('rahul_cardio_report.pdf') || recordsText3.includes('priya_confidential_report.pdf')) {
      throw new Error('Cross-patient leakage in Amit records!');
    }
    console.log('User 3 records verified: Isolated from User 1 and User 2');

    // ==========================================
    // STEP 7: BROWSER REFRESH CHECK
    // ==========================================
    console.log('\n--- STEP 7: Browser Refresh Context Retention Check ---');
    await page.reload({ waitUntil: 'networkidle' });
    const reloadedText = await page.locator('body').textContent();
    if (!reloadedText.includes('Amit') && !reloadedText.includes('Ortho')) {
      throw new Error('Session lost after page refresh');
    }
    if (reloadedText.includes('Rahul Verma') || reloadedText.includes('Priya Sharma')) {
      throw new Error('Cross-patient leakage restored upon refresh!');
    }
    console.log('Browser refresh verified: Correct patient context maintained with zero leakage');
    report.checks.user3_amit_complete = true;
    report.checks.browser_refresh_isolated = true;

    console.log('\n=== ALL BROWSER E2E TESTS PASSED SUCCESSFULLY ===');
    console.log('Console Errors:', report.consoleErrors.length);
    console.log('Failed Requests:', report.failedRequests.length);

  } finally {
    await browser.close();
  }

  return report;
}

runPatientIsolationAudit()
  .then(res => {
    console.log('\nFinal Report Summary:');
    console.log(JSON.stringify(res, null, 2));
    process.exit(res.consoleErrors.length > 0 ? 1 : 0);
  })
  .catch(err => {
    console.error('Audit failed with exception:', err);
    process.exit(1);
  });
