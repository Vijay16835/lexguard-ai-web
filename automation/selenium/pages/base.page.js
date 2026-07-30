const { By, until } = require('selenium-webdriver');
const config = require('../config/config');
const logger = require('../utils/logger');
const ScreenshotUtility = require('../utils/screenshot');

class BasePage {
  constructor(driver) {
    this.driver = driver;
    this.timeout = config.explicitWaitMs;
  }

  async open(urlPath = '') {
    const targetUrl = urlPath.startsWith('http') ? urlPath : `${config.baseUrl}${urlPath.startsWith('/') ? urlPath.substring(1) : urlPath}`;
    logger.info(`Navigating to URL: ${targetUrl}`);
    await this.driver.get(targetUrl);
  }

  async find(locator, customTimeout = this.timeout) {
    const el = await this.driver.wait(until.elementLocated(locator), customTimeout);
    await this.driver.wait(until.elementIsVisible(el), customTimeout);
    return el;
  }

  async click(locator) {
    let attempts = 0;
    while (attempts < 3) {
      try {
        const el = await this.find(locator);
        await el.click();
        return;
      } catch (err) {
        attempts++;
        if (attempts >= 3) {
          logger.warn(`Standard click failed on ${locator}, falling back to JS click...`);
          const el = await this.driver.findElement(locator);
          await this.driver.executeScript('arguments[0].click();', el);
        }
      }
    }
  }

  async type(locator, text) {
    const el = await this.find(locator);
    await el.clear();
    await el.sendKeys(text);
  }

  async getText(locator) {
    try {
      const el = await this.find(locator);
      return await el.getText();
    } catch {
      return '';
    }
  }

  async isDisplayed(locator, customTimeout = 5000) {
    try {
      const el = await this.driver.wait(until.elementLocated(locator), customTimeout);
      return await el.isDisplayed();
    } catch {
      return false;
    }
  }

  async getTitle() {
    return await this.driver.getTitle();
  }

  async takeScreenshot(testName) {
    return await ScreenshotUtility.capture(this.driver, testName);
  }
}

module.exports = BasePage;
