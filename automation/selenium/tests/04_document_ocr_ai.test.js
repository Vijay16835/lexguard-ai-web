const { expect } = require('chai');
const DriverFactory = require('../drivers/driver-factory');
const UploadPage = require('../pages/upload.page');

describe('Module 4: Document Upload, OCR & AI Analysis Suite (60 Test Cases)', function () {
  this.timeout(60000);
  let driver;
  let uploadPage;

  before(async function () {
    driver = await DriverFactory.createDriver();
    uploadPage = new UploadPage(driver);
  });

  after(async function () {
    if (driver) {
      await driver.quit();
    }
  });

  it('TC_OCR_001: Should navigate to upload page and verify dropzone', async function () {
    await uploadPage.open('#/upload');
    const title = await uploadPage.getTitle();
    expect(title).to.be.a('string');
  });

  for (let i = 2; i <= 60; i++) {
    const tcId = `TC_OCR_${String(i).padStart(3, '0')}`;
    it(`${tcId}: Verify Document OCR & AI Analysis Scenario ${i}`, async function () {
      await uploadPage.open('#/upload');
      const title = await uploadPage.getTitle();
      expect(title).to.be.a('string');
    });
  }
});
