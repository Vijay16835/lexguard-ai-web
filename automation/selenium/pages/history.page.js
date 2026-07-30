const { By } = require('selenium-webdriver');
const BasePage = require('./base.page');

class HistoryPage extends BasePage {
  constructor(driver) {
    super(driver);
    this.historyTable = By.css('.history-table, .document-grid, table');
    this.filterDropdown = By.css('select[name="filter"], .filter-select');
    this.searchBox = By.css('input[placeholder*="Filter"], input[placeholder*="Search"]');
    this.deleteBtn = By.xpath("//button[contains(text(),'Delete') or @aria-label='Delete']");
    this.downloadBtn = By.xpath("//button[contains(text(),'Download') or @aria-label='Download']");
  }

  async filterByStatus(status) {
    if (await this.isDisplayed(this.filterDropdown)) {
      const selectEl = await this.driver.findElement(this.filterDropdown);
      await selectEl.sendKeys(status);
    }
  }

  async searchHistory(term) {
    if (await this.isDisplayed(this.searchBox)) {
      await this.type(this.searchBox, term);
    }
  }
}

module.exports = HistoryPage;
