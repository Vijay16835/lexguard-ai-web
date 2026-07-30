const { By } = require('selenium-webdriver');
const BasePage = require('./base.page');

class UploadPage extends BasePage {
  constructor(driver) {
    super(driver);
    this.fileInput = By.css('input[type="file"]');
    this.dropzone = By.css('.dropzone, .upload-box, [aria-label*="Upload File"]');
    this.submitUploadBtn = By.xpath("//button[contains(text(),'Analyze Document') or contains(text(),'Upload') or @aria-label='Analyze']");
    this.progressBar = By.css('.progress-bar, .upload-progress');
    this.successAlert = By.css('.alert-success, .success-banner');
  }

  async uploadFile(filePath) {
    if (await this.isDisplayed(this.fileInput)) {
      const el = await this.driver.findElement(this.fileInput);
      await el.sendKeys(filePath);
    }
  }

  async clickAnalyze() {
    if (await this.isDisplayed(this.submitUploadBtn)) {
      await this.click(this.submitUploadBtn);
    }
  }
}

module.exports = UploadPage;
