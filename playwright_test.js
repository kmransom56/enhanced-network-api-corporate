const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({
    headless: false,
    args: [
      '--enable-webgl',
      '--use-gl=desktop', // enable hardware GL; fallback to swiftshader if needed
      '--disable-features=VizDisplayCompositor'
    ]
  });
  const page = await browser.newPage();
  await page.goto('http://127.0.0.1:11111/static/babylon_lab_view.html');
  // wait for scene to load (adjust if needed)
  await page.waitForTimeout(8000);
  await page.screenshot({ path: 'babylon_playwright.png' });
  console.log('Screenshot saved as babylon_playwright.png');
  await browser.close();
})();
