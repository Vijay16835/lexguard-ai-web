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
    'appium:appPackage': 'com.lexguard.ai',
    'appium:appActivity': 'com.lexguard.ai.MainActivity',
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
  services: [
    ['appium', {
      args: {
        address: '127.0.0.1',
        port: 4723,
        relaxedSecurity: true
      },
      logPath: logsDir
    }]
  ],
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
