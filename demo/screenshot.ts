import {test, expect} from '@playwright/test';

import * as fs from 'fs';
import * as path from 'path';

// Single-file demos: root-level .py files
const pythonDemoFiles = fs
  .readdirSync(__dirname)
  .filter((file) => path.extname(file) === '.py');

// Multi-file demos: subdirectories that contain an app.py entry point
const multiFileDemoDirs = fs
  .readdirSync(__dirname, {withFileTypes: true})
  .filter(
    (entry) =>
      entry.isDirectory() &&
      fs.existsSync(path.join(__dirname, entry.name, 'app.py')),
  )
  .map((entry) => entry.name);

console.log('Single-file demos:', pythonDemoFiles);
console.log('Multi-file demos:', multiFileDemoDirs);

// Remove the skip if you want to re-generate the screenshots.
test.skip('screenshot each demo', async ({page}) => {
  // This will take a while.
  test.setTimeout(0);

  await page.setViewportSize({width: 400, height: 300});

  // Screenshot single-file demos
  for (const demoFile of pythonDemoFiles) {
    const demo = demoFile.slice(0, -3);
    await page.goto('/' + demo);
    await new Promise((resolve) => setTimeout(resolve, 3000));
    await page.screenshot({
      path: `demo/screenshots/${demo}.png`,
      fullPage: true,
    });
  }

  // Screenshot multi-file demos (entry point is app.py, URL is /dirname)
  for (const demoDir of multiFileDemoDirs) {
    await page.goto('/' + demoDir);
    await new Promise((resolve) => setTimeout(resolve, 3000));
    await page.screenshot({
      path: `demo/screenshots/${demoDir}.png`,
      fullPage: true,
    });
  }
});
