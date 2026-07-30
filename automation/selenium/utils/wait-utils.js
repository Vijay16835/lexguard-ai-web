const { until, By } = require('selenium-webdriver');
const config = require('../config/config');
const logger = require('./logger');

class WaitUtils {
  static async waitForElementVisible(driver, locator, timeoutMs = config.explicitWaitMs) {
    try {
      const element = await driver.wait(until.elementLocated(locator), timeoutMs);
      await driver.wait(until.elementIsVisible(element), timeoutMs);
      return element;
    } catch (err) {
      logger.warn(`Element not visible within ${timeoutMs}ms: ${locator}`);
      throw err;
    }
  }

  static async waitForElementClickable(driver, locator, timeoutMs = config.explicitWaitMs) {
    try {
      const element = await this.waitForElementVisible(driver, locator, timeoutMs);
      await driver.wait(until.elementIsEnabled(element), timeoutMs);
      return element;
    } catch (err) {
      logger.warn(`Element not clickable within ${timeoutMs}ms: ${locator}`);
      throw err;
    }
  }

  static async retryAction(actionFn, retries = 3, delayMs = 1000) {
    let lastError;
    for (let i = 0; i < retries; i++) {
      try {
        return await actionFn();
      } catch (err) {
        lastError = err;
        logger.warn(`Action failed (attempt ${i + 1}/${retries}): ${err.message}. Retrying in ${delayMs}ms...`);
        await new Promise((res) => setTimeout(res, delayMs));
      }
    }
    throw lastError;
  }
}

module.exports = WaitUtils;
