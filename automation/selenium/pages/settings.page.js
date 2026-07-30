const { By } = require('selenium-webdriver');
const BasePage = require('./base.page');

class SettingsPage extends BasePage {
  constructor(driver) {
    super(driver);
    this.profileNameInput = By.css('input[name="fullName"], input[placeholder*="Name"]');
    this.saveSettingsBtn = By.xpath("//button[contains(text(),'Save') or @aria-label='Save']");
    this.themeToggle = By.css('.theme-toggle, input[type="checkbox"][name="dark_mode"]');
    this.notificationsCheckbox = By.css('input[name="notifications"]');
    this.logoutBtn = By.xpath("//button[contains(text(),'Logout') or @aria-label='Logout']");
  }

  async toggleTheme() {
    if (await this.isDisplayed(this.themeToggle)) {
      await this.click(this.themeToggle);
    }
  }

  async updateProfile(name) {
    if (await this.isDisplayed(this.profileNameInput)) {
      await this.type(this.profileNameInput, name);
    }
    if (await this.isDisplayed(this.saveSettingsBtn)) {
      await this.click(this.saveSettingsBtn);
    }
  }

  async logout() {
    if (await this.isDisplayed(this.logoutBtn)) {
      await this.click(this.logoutBtn);
    }
  }
}

module.exports = SettingsPage;
