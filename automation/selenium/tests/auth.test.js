const { expect } = require('chai');
const DriverFactory = require('../drivers/driver-factory');
const LoginPage = require('../pages/login.page');
const DashboardPage = require('../pages/dashboard.page');
const config = require('../config/config');

describe('1. Authentication Module Tests', function () {
  let driver;
  let loginPage;

  before(async function () {
    driver = await DriverFactory.createDriver();
    loginPage = new LoginPage(driver);
  });

  after(async function () {
    if (driver) {
      await driver.quit();
    }
  });

  it('TC_AUTH_001: Should launch login screen successfully', async function () {
    await loginPage.open('/login');
    const isLoaded = await loginPage.isDisplayed(loginPage.loginBtn);
    expect(isLoaded).to.be.true;
  });

  it('TC_AUTH_002: Should perform successful email login', async function () {
    await loginPage.open('/login');
    await loginPage.login(config.credentials.validEmail, config.credentials.validPassword);
    const dashboardPage = new DashboardPage(driver);
    const loaded = await dashboardPage.isLoaded();
    expect(loaded).to.be.true;
  });
});
