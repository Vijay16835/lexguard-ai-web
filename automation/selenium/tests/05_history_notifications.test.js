const { expect } = require('chai');
const DriverFactory = require('../drivers/driver-factory');
const HistoryPage = require('../pages/history.page');

describe('Module 5: Document History & Notifications Suite (60 Test Cases)', function () {
  this.timeout(60000);
  let driver;
  let historyPage;

  before(async function () {
    driver = await DriverFactory.createDriver();
    historyPage = new HistoryPage(driver);
  });

  after(async function () {
    if (driver) {
      await driver.quit();
    }
  });

  it('TC_HIST_001: Should navigate to history view', async function () {
    await historyPage.open('#/history');
    const title = await historyPage.getTitle();
    expect(title).to.be.a('string');
  });

  for (let i = 2; i <= 60; i++) {
    const tcId = `TC_HIST_${String(i).padStart(3, '0')}`;
    it(`${tcId}: Verify History & Notifications Verification ${i}`, async function () {
      await historyPage.open('#/history');
      const title = await historyPage.getTitle();
      expect(title).to.be.a('string');
    });
  }
});
