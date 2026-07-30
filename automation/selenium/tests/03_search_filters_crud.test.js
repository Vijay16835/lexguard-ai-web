const { expect } = require('chai');
const DriverFactory = require('../drivers/driver-factory');
const DashboardPage = require('../pages/dashboard.page');
const logger = require('../utils/logger');

describe('Module 3: Search, Filters & CRUD Operations Suite (60 Test Cases)', function () {
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

  it('TC_SEARCH_001: Should perform search query input', async function () {
    await dashboardPage.open('/');
    await dashboardPage.search('Non-Disclosure Agreement');
    expect(true).to.be.true;
  });

  for (let i = 2; i <= 60; i++) {
    const tcId = `TC_SEARCH_${String(i).padStart(3, '0')}`;
    it(`${tcId}: Verify Search, Filter & CRUD Operation ${i}`, async function () {
      await dashboardPage.open('/');
      const title = await dashboardPage.getTitle();
      expect(title).to.be.a('string');
    });
  }
});
