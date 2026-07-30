const fs = require('fs-extra');
const path = require('path');
const config = require('../config/config');
const logger = require('./logger');

class ScreenshotUtility {
  static async capture(driver, testName) {
    try {
      fs.ensureDirSync(config.dirs.screenshots);
      const sanitizedName = testName.replace(/[^a-zA-Z0-9_-]/g, '_');
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const fileName = `${sanitizedName}_${timestamp}.png`;
      const filePath = path.join(config.dirs.screenshots, fileName);

      const image = await driver.takeScreenshot();
      await fs.writeFile(filePath, image, 'base64');
      logger.info(`Screenshot captured: ${filePath}`);
      return filePath;
    } catch (err) {
      logger.error(`Failed to capture screenshot for test '${testName}': ${err.message}`);
      return null;
    }
  }
}

module.exports = ScreenshotUtility;
