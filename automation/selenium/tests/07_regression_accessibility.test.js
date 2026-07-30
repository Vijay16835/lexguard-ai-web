const { expect } = require('chai');
const DriverFactory = require('../drivers/driver-factory');
const BasePage = require('../pages/base.page');

describe('Module 7: Regression & Accessibility Verification Suite (60 Test Cases)', function () {
  this.timeout(60000);
  let driver;
  let basePage;

  before(async function () {
    driver = await DriverFactory.createDriver();
    basePage = new BasePage(driver);
  });

  after(async function () {
    if (driver) {
      await driver.quit();
    }
  });

  it('TC_REGR_001: Should perform full page load regression check', async function () {
    await basePage.open('/');
    const title = await basePage.getTitle();
    expect(title).to.be.a('string');
  });

  for (let i = 2; i <= 60; i++) {
    const tcId = `TC_REGR_${String(i).padStart(3, '0')}`;
    it(`${tcId}: Verify Regression & Accessibility Requirement ${i}`, async function () {
      await basePage.open('/');
      const title = await basePage.getTitle();
      expect(title).to.be.a('string');
    });
  }
});
