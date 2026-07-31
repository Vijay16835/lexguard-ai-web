import path from 'path';
import fs from 'fs-extra';

const reportsDir = path.join(__dirname, 'reports');
const screenshotsDir = path.join(reportsDir, 'screenshots');
const logsDir = path.join(reportsDir, 'logs');

fs.ensureDirSync(screenshotsDir);
fs.ensureDirSync(logsDir);

export const config: WebdriverIO.Config = {
  runner: 'local',
  autoCompileOpts: {
    autoCompile: true,
    tsNodeOpts: {
      transpileOnly: true,
      project: path.join(__dirname, 'tsconfig.json')
    }
  },
  specs: [
    './tests/**/*.spec.ts'
  ],
  maxInstances: 1,
  capabilities: [{
    platformName: 'Android',
    'appium:automationName': 'UiAutomator2',
    'appium:deviceName': process.env.ANDROID_DEVICE_NAME || 'Android Emulator',
    'appium:platformVersion': process.env.ANDROID_PLATFORM_VERSION || '13.0',
    'appium:app': process.env.APK_PATH || path.join(__dirname, '../../build/app/outputs/flutter-apk/app-debug.apk'),
    'appium:appPackage': process.env.APP_PACKAGE || 'com.lexguard.lexguard_ai',
    'appium:appActivity': process.env.APP_ACTIVITY || 'com.lexguard.lexguard_ai.MainActivity',
    'appium:autoGrantPermissions': true,
    'appium:noReset': false,
    'appium:newCommandTimeout': 180
  }],
  logLevel: 'info',
  bail: 0,
  baseUrl: 'http://localhost',
  waitforTimeout: 20000,
  connectionRetryTimeout: 120000,
  connectionRetryCount: 3,
  // NOTE: Appium server is managed externally by the CI workflow (android-e2e.yml).
  // The workflow starts Appium on port 4723, probes /status for readiness,
  // and stops it after test execution. Do NOT add @wdio/appium-service here
  // as it would cause a port 4723 conflict.
  services: [],
  framework: 'mocha',
  reporters: [
    'spec',
    ['allure', {
      outputDir: path.join(reportsDir, 'allure-results'),
      disableWebdriverStepsReporting: true,
      disableWebdriverScreenshotsReporting: false
    }]
  ],
  mochaOpts: {
    ui: 'bdd',
    timeout: 90000
  },

  afterTest: async function (test, context, { error, result, duration, passed, retry }) {
    if (!passed) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `${test.title.replace(/[^a-zA-Z0-9_-]/g, '_')}_${timestamp}.png`;
      const filepath = path.join(screenshotsDir, filename);
      try {
        await browser.saveScreenshot(filepath);
      } catch (e) {
        console.warn(`Failed to capture screenshot: ${e}`);
      }
    }
  }
};
