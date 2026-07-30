import BasePage from './base.page';

export default class SettingsPage extends BasePage {
  private get profileNameInput() { return '~profile_name_input'; }
  private get themeToggle() { return '~theme_toggle_switch'; }
  private get notificationsToggle() { return '~notifications_toggle_switch'; }
  private get logoutButton() { return '~logout_button'; }

  public async toggleDarkMode() {
    if (await this.isDisplayed(this.themeToggle)) {
      await this.click(this.themeToggle);
    }
  }

  public async logout() {
    if (await this.isDisplayed(this.logoutButton)) {
      await this.click(this.logoutButton);
    }
  }
}
