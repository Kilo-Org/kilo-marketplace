import { addCheck, isMain, loadBrowser, loadContract, parseArgs, reportFor, safeURL, writeReport } from './lib/common.mjs';

// Playwright throws for a navigation that opens a new page, before its frame exists.
function isTopLevel(request) {
  try { return !request.frame().parentFrame(); } catch { return true; }
}

export async function testFormFlow(contract, { url, browserModule, executablePath, allowRemote = false, browser: suppliedBrowser } = {}) {
  const report = reportFor(contract, 'test-form-flow', 'browser-with-intercepted-responses');
  report.limitations.push('All configured form responses are intercepted. Backend acceptance, storage, delivery, full accessibility, and privacy behavior need separate checks.');
  report.limitations.push('Cross-origin reads and requests with query strings are blocked, so test a self-contained build. WebSockets are blocked; WebRTC is not intercepted.');
  const target = safeURL(url ?? contract.verification.target);
  if (!['localhost', '127.0.0.1', '[::1]'].includes(target.hostname) && !allowRemote) throw new Error('Remote browsing requires --allow-remote; submissions remain intercepted');
  report.target = `${target.origin}${target.pathname}`;
  report.viewport = { width: 390, height: 844 };
  if (contract.form.mode === 'unconnected' || !contract.verification.browser || !contract.form.fields.length) {
    addCheck(report, 'form-flow', 'not-tested', 'Connected test adapter', 'Form is unconnected, absent, or lacks a browser adapter');
    return report;
  }
  let browser = suppliedBrowser;
  try {
    if (!browser) {
      const library = await loadBrowser(browserModule);
      browser = await library.chromium.launch({ headless: true, executablePath });
    }
  } catch {
    addCheck(report, 'browser-available', 'not-tested', 'Existing Playwright and Chromium installation', 'Browser module or browser could not be launched');
    return report;
  }
  try {
    report.browserVersion = browser.version();
    const adapter = contract.verification.browser;
    const endpoint = safeURL(contract.form.destination.endpoint, target);
    // Values this short could match an unrelated request body by chance.
    const formValues = Object.values(adapter.values).filter(value => typeof value === 'string' && value.length > 3).flatMap(value => [value, encodeURIComponent(value), new URLSearchParams({ value }).toString().slice(6)]);
    for (const scenario of ['invalid', 'accepted', 'rejected', 'duplicate', 'timeout', 'retry']) {
      if (scenario === 'invalid' && !contract.form.fields.some(field => field.required && field.type !== 'hidden')) {
        addCheck(report, scenario, 'not-applicable', 'Required fields prevent empty submission', 'No required visible fields'); continue;
      }
      if (scenario === 'retry' && !contract.form.responses.retrySafe) {
        addCheck(report, scenario, 'not-applicable', 'Safe retry preserves identity', 'Retry safety is not supported by this contract'); continue;
      }
      const context = await browser.newContext({ viewport: report.viewport, serviceWorkers: 'block' });
      let calls = 0;
      let blockedMutations = 0;
      let unrelatedMutations = 0;
      let blockedReads = 0;
      let nativeSubmission = false;
      const identities = [];
      try {
        if (!context.routeWebSocket) {
          addCheck(report, 'browser-available', 'not-tested', 'Playwright 1.48 or later, which can block WebSockets', 'This Playwright cannot block WebSockets, so no scenario ran');
          return report;
        }
        await context.routeWebSocket(/.*/, socket => socket.close());
        await context.route('**/*', async route => {
          const request = route.request();
          const requestURL = new URL(request.url());
          if (requestURL.href === endpoint.href && request.method() === contract.form.destination.method) {
            calls++;
            if (request.isNavigationRequest() && isTopLevel(request)) nativeSubmission = true;
            if (contract.form.responses.idempotencyHeader) identities.push(request.headers()[contract.form.responses.idempotencyHeader.toLowerCase()] ?? null);
            if (scenario === 'timeout' || scenario === 'retry' && calls === 1) return route.abort('timedout');
            const response = contract.form.responses[scenario === 'retry' || scenario === 'invalid' ? 'accepted' : scenario];
            return route.fulfill({ status: response.status, contentType: 'application/json', body: JSON.stringify(response.body), headers: { 'access-control-allow-origin': target.origin } });
          }
          if (!['GET', 'HEAD'].includes(request.method())) {
            // Playwright answers CORS preflights itself while routing, so OPTIONS never reaches this branch.
            // Analytics and similar posts stay blocked; only the form's own data counts against the flow.
            const body = request.postData() ?? '';
            if (requestURL.origin === endpoint.origin && requestURL.pathname === endpoint.pathname || formValues.some(value => body.includes(value))) blockedMutations++;
            else unrelatedMutations++;
            return route.abort();
          }
          if (requestURL.origin !== target.origin) { blockedReads++; return route.abort(); }
          // Do not forward query strings from accidental native GET submissions.
          if (requestURL.search) return route.abort();
          return route.continue();
        });
        const page = await context.newPage();
        page.setDefaultTimeout(adapter.timeoutMs);
        await page.goto(target.href, { waitUntil: 'domcontentloaded' });
        const form = page.locator(adapter.formSelector);
        const button = form.locator(adapter.submitSelector);
        if (scenario !== 'invalid') {
          for (const field of contract.form.fields) {
            if (!Object.hasOwn(adapter.values, field.name)) continue;
            const input = form.locator(`[name="${field.name}"]`);
            if (field.type === 'checkbox') await input.setChecked(Boolean(adapter.values[field.name]));
            else if (field.type === 'select') await input.selectOption(String(adapter.values[field.name]));
            else if (field.type !== 'hidden') await input.fill(String(adapter.values[field.name]));
          }
        }
        await button.click();
        if (scenario === 'invalid') {
          await page.waitForTimeout(150);
          const invalid = await form.evaluate(element => !element.checkValidity());
          addCheck(report, scenario, invalid && calls === 0 && blockedMutations === 0, 'Empty required fields block submission', `${calls} intercepted requests; native validation ${invalid ? 'blocked' : 'did not block'}; undeclared form mutations=${blockedMutations}; unrelated mutations blocked=${unrelatedMutations}`);
        } else {
          const failed = ['rejected', 'timeout', 'retry'].includes(scenario);
          const selector = failed ? adapter.errorSelector : adapter.statusSelector;
          const expectedText = failed ? adapter.errorText : scenario === 'duplicate' ? adapter.duplicateText : adapter.successText;
          if (scenario === 'accepted' && contract.form.success.mode === 'redirect') {
            await page.waitForURL(safeURL(contract.form.success.redirectPath, target).href);
          }
          await page.waitForFunction(({ selector, expectedText }) => document.querySelector(selector)?.textContent.toLowerCase().includes(expectedText.toLowerCase()), { selector, expectedText });
          const status = page.locator(selector);
          const visible = await status.isVisible();
          const announced = await status.evaluate(element => Boolean(element.closest('[role="status"], [role="alert"], [aria-live="polite"], [aria-live="assertive"]')));
          let retained = true;
          if (failed) {
            for (const field of contract.form.fields) {
              if (!Object.hasOwn(adapter.values, field.name) || field.type === 'hidden') continue;
              const input = form.locator(`[name="${field.name}"]`);
              const value = field.type === 'checkbox' ? await input.isChecked() : await input.inputValue();
              if (value !== adapter.values[field.name]) retained = false;
            }
            retained = retained && await button.isEnabled();
          }
          if (scenario === 'retry') {
            await button.click();
            if (contract.form.success.mode === 'redirect') await page.waitForURL(safeURL(contract.form.success.redirectPath, target).href);
            await page.waitForFunction(({ selector, text }) => document.querySelector(selector)?.textContent.toLowerCase().includes(text.toLowerCase()), { selector: adapter.statusSelector, text: adapter.successText });
          }
          const expectedCalls = scenario === 'retry' ? 2 : 1;
          const identityOK = scenario !== 'retry' || identities.length === 2 && Boolean(identities[0]) && identities[0] === identities[1];
          addCheck(report, scenario, calls === expectedCalls && blockedMutations === 0 && visible && announced && retained && identityOK, 'Expected response state, announced feedback, retained input on failure, and safe retry identity', `${calls} intercepted requests; visible=${visible}; live-region=${announced}; retained=${retained}; retry-identity=${identityOK}; undeclared form mutations=${blockedMutations}; unrelated mutations blocked=${unrelatedMutations}`);
        }
      } catch {
        if (nativeSubmission && scenario !== 'invalid') addCheck(report, scenario, 'not-tested', 'A submission handled by page script', 'The form navigated on submit, which this helper cannot simulate. Raw page text and values omitted.');
        else addCheck(report, scenario, false, 'The declared browser flow completes', `Flow did not meet its contract; ${calls} intercepted requests; ${blockedReads} cross-origin reads blocked. Raw page text and values omitted.`);
      } finally { await context.close(); }
    }
  } finally { if (!suppliedBrowser) await browser.close(); }
  for (const stage of ['backend-acceptance', 'lead-storage', 'notification', 'recipient-receipt']) addCheck(report, stage, 'not-tested', 'Separate authorized destination evidence', 'Intercepted browser checks do not observe this stage');
  return report;
}

async function main() {
  const args = parseArgs(process.argv.slice(2), { '--help': 'boolean', '--contract': 'value', '--url': 'value', '--output': 'value', '--browser-module': 'value', '--allow-remote': 'boolean' });
  if (args.help) {
    console.log('Usage: node test-form-flow.mjs --contract contract.json [--url http://127.0.0.1:4173/page/] [--browser-module /path/to/playwright/index.mjs] [--output report.json] [--allow-remote]\nRequires Node 22+ and existing Playwright 1.48+ with Chromium. Runs isolated mobile contexts with all form responses intercepted and WebSockets blocked. No real submissions. Remote reads need --allow-remote.\nScope: single POST form handled by page script, native required validation, in-place or redirect success, rejection, duplicate feedback, simulated transport timeout, header-based retry identity. A form that navigates on submit reports not-tested. Other POSTs stay blocked and fail a check only if they target the destination or carry form values. Cross-origin reads and requests with query strings are blocked, so test a self-contained build. WebRTC is not intercepted. Does not test slow pending responses or the real backend.\nExit: 0 complete within scope, 1 failed check, 2 untested checks remain (including backend/delivery), 3 invalid input.');
    return;
  }
  if (!args.contract) throw new Error('Required: --contract');
  const contract = await loadContract(args.contract);
  const report = await testFormFlow(contract, { url: args.url, browserModule: args['browser-module'] ?? process.env.GURU_PLAYWRIGHT_MODULE, executablePath: process.env.GURU_CHROMIUM_EXECUTABLE, allowRemote: args['allow-remote'] });
  process.exitCode = await writeReport(report, args.output);
}

if (isMain(import.meta.url)) main().catch(() => { console.error('Form check could not start. Check paths, contract, browser adapter, URL policy, and --help. No input values were logged.'); process.exitCode = 3; });
