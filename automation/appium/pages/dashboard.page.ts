import BasePage from './base.page';

export default class DashboardPage extends BasePage {
  private get uploadTab() { return '~nav_upload'; }
  private get historyTab() { return '~nav_history'; }
  private get settingsTab() { return '~nav_settings'; }
  private get profileTab() { return '~nav_profile'; }
  private get searchInput() { return '~search_input'; }

  public async navigateToUpload() {
    if (await this.isDisplayed(this.uploadTab)) {
      await this.click(this.uploadTab);
    }
  }

  public async navigateToHistory() {
    if (await this.isDisplayed(this.historyTab)) {
      await this.click(this.historyTab);
    }
  }

  public async navigateToSettings() {
    if (await this.isDisplayed(this.settingsTab)) {
      await this.click(this.settingsTab);
    }
  }

  public async search(query: string) {
    if (await this.isDisplayed(this.searchInput)) {
      await this.setValue(this.searchInput, query);
    }
  }
}
