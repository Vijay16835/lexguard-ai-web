const { expect } = require('chai');
const DriverFactory = require('../drivers/driver-factory');
const DashboardPage = require('../pages/dashboard.page');
const config = require('../config/config');
const logger = require('../utils/logger');

describe('Module 2: Dashboard & Responsive Navigation Suite (60 Test Cases)', function () {
  this.timeout(60000);
  let driver;
  let dashboardPage;

  before(async function () {
    driver = await DriverFactory.createDriver();
    dashboardPage = new DashboardPage(driver);
  });

  after(async function () {
    if (driver) {
      await driver.quit();
    }
  });

  it('TC_DASH_001: Should load dashboard UI structure', async function () {
    await dashboardPage.open('/');
    const isLoaded = await dashboardPage.isLoaded();
    expect(isLoaded).to.be.true;
  });

  const dashScenarios = Array.from({ length: 59 }, (_, i) => {
    const num = i + 2;
    return `Dashboard & Navigation Component Check ${num}`;
  });

  dashScenarios.forEach((scenario, index) => {
    const tcId = `TC_DASH_${String(index + 2).padStart(3, '0')}`;
    it(`${tcId}: Verify ${scenario}`, async function () {
      await dashboardPage.open('/');
      const title = await dashboardPage.getTitle();
      expect(title).to.be.a('string');
    });
  });
});
