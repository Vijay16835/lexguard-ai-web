/**
 * DriverFactory — Enterprise Selenium WebDriver Factory
 *
 * ChromeDriver Strategy: Selenium Manager (built into selenium-webdriver@4.15+)
 * ─────────────────────────────────────────────────────────────────────────────
 * Selenium Manager automatically detects the installed Chrome version and
 * downloads the exact matching ChromeDriver at runtime. This eliminates
 * SessionNotCreatedError caused by Chrome/ChromeDriver version mismatches.
 *
 * DO NOT:
 *  - Set chromedriver path manually (selenium.chromeBinary / Service)
 *  - Install chromedriver npm package
 *  - Install webdriver-manager
 *  - Pin a ChromeDriver version anywhere
 *
 * The workflow installs Chrome only. Selenium Manager handles the rest.
 */

'use strict';

const { Builder } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const firefox = require('selenium-webdriver/firefox');
const edge = require('selenium-webdriver/edge');
const config = require('../config/config');
const fs = require('fs-extra');

class DriverFactory {
  /**
   * Creates a WebDriver instance using Selenium Manager for auto driver resolution.
   * @param {string} browserName - 'chrome' | 'firefox' | 'edge'
   * @returns {Promise<WebDriver>}
   */
  static async createDriver(browserName = config.browser) {
    fs.ensureDirSync(config.dirs.screenshots);
    fs.ensureDirSync(config.dirs.logs);

    browserName = (browserName || 'chrome').toLowerCase();

    // Selenium Manager is invoked automatically by Builder when no
    // explicit driver service is provided. Never set a manual chromedriver path.
    const builder = new Builder().forBrowser(browserName);

    switch (browserName) {
      case 'firefox': {
        const ffOptions = new firefox.Options();
        if (config.headless) {
          ffOptions.addArguments('-headless');
        }
        ffOptions.addArguments('--width=1920', '--height=1080');
        builder.setFirefoxOptions(ffOptions);
        break;
      }

      case 'edge': {
        const edgeOptions = new edge.Options();
        if (config.headless) {
          edgeOptions.addArguments('--headless=new');
        }
        edgeOptions.addArguments('--window-size=1920,1080', '--no-sandbox');
        builder.setEdgeOptions(edgeOptions);
        break;
      }

      // chrome is the default
      case 'chrome':
      default: {
        const chromeOptions = new chrome.Options();

        // Headless mode (new headless is standard in Chrome 112+)
        if (config.headless) {
          chromeOptions.addArguments('--headless=new');
        }

        chromeOptions.addArguments(
          '--disable-gpu',
          '--no-sandbox',
          '--disable-dev-shm-usage',
          '--window-size=1920,1080',
          '--disable-extensions',
          '--disable-infobars',
          '--disable-blink-features=AutomationControlled',
          '--remote-allow-origins=*'
        );

        // Point to the system Chrome binary if explicitly provided via env
        // (e.g. from browser-actions/setup-chrome output). If not set,
        // Selenium Manager will locate Chrome automatically.
        if (process.env.CHROME_BIN) {
          chromeOptions.setChromeBinaryPath(process.env.CHROME_BIN);
        }

        builder.setChromeOptions(chromeOptions);
        break;
      }
    }

    // Build the driver — Selenium Manager resolves ChromeDriver automatically
    const driver = await builder.build();
    await driver.manage().setTimeouts({ implicit: config.implicitWaitMs });
    return driver;
  }
}

module.exports = DriverFactory;
