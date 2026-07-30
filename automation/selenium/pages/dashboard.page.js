const { By } = require('selenium-webdriver');
const BasePage = require('./base.page');

class DashboardPage extends BasePage {
  constructor(driver) {
    super(driver);
    this.dashboardContainer = By.css('.dashboard-container, flt-glass-pane, flt-scene-host, body');
    this.navUpload = By.xpath("//a[contains(text(),'Upload') or @aria-label='Upload']");
    this.navHistory = By.xpath("//a[contains(text(),'History') or @aria-label='History']");
    this.navSettings = By.xpath("//a[contains(text(),'Settings') or @aria-label='Settings']");
    this.navProfile = By.xpath("//a[contains(text(),'Profile') or @aria-label='Profile']");
    this.navNotifications = By.xpath("//a[contains(text(),'Notifications') or @aria-label='Notifications']");
    this.recentUploadsCard = By.css('.recent-uploads, .card-recent');
    this.totalDocumentsStat = By.css('.stat-total-docs, .stat-card');
    this.searchInput = By.css('input[placeholder*="Search"], input[type="search"]');
  }

  async isLoaded() {
    return await this.isDisplayed(this.dashboardContainer);
  }

  async navigateToUpload() {
    if (await this.isDisplayed(this.navUpload)) {
      await this.click(this.navUpload);
    }
  }

  async navigateToHistory() {
    if (await this.isDisplayed(this.navHistory)) {
      await this.click(this.navHistory);
    }
  }

  async navigateToSettings() {
    if (await this.isDisplayed(this.navSettings)) {
      await this.click(this.navSettings);
    }
  }

  async search(query) {
    if (await this.isDisplayed(this.searchInput)) {
      await this.type(this.searchInput, query);
    }
  }
}

module.exports = DashboardPage;
