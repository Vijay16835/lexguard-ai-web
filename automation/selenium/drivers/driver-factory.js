const { Builder } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const firefox = require('selenium-webdriver/firefox');
const edge = require('selenium-webdriver/edge');
const config = require('../config/config');
const fs = require('fs-extra');

class DriverFactory {
  static async createDriver(browserName = config.browser) {
    fs.ensureDirSync(config.dirs.screenshots);
    fs.ensureDirSync(config.dirs.logs);

    let builder = new Builder().forBrowser(browserName.toLowerCase());

    switch (browserName.toLowerCase()) {
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
        edgeOptions.addArguments('--window-size=1920,1080');
        builder.setEdgeOptions(edgeOptions);
        break;
      }
      case 'chrome':
      default: {
        const chromeOptions = new chrome.Options();
        if (config.headless) {
          chromeOptions.addArguments('--headless=new');
        }
        chromeOptions.addArguments(
          '--disable-gpu',
          '--no-sandbox',
          '--disable-dev-shm-usage',
          '--window-size=1920,1080',
          '--allow-insecure-localhost',
          '--disable-web-security',
          '--disable-blink-features=AutomationControlled'
        );
        builder.setChromeOptions(chromeOptions);
        break;
      }
    }

    const driver = await builder.build();
    await driver.manage().setTimeouts({ implicit: config.implicitWaitMs });
    return driver;
  }
}

module.exports = DriverFactory;
