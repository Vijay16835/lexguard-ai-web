import BasePage from './base.page';

export default class LoginPage extends BasePage {
  private get emailInput() { return '~email_input'; }
  private get passwordInput() { return '~password_input'; }
  private get loginButton() { return '~login_button'; }
  private get signupButton() { return '~signup_button'; }
  private get forgotPasswordLink() { return '~forgot_password_link'; }

  public async login(email: string, pass: string) {
    if (await this.isDisplayed(this.emailInput)) {
      await this.setValue(this.emailInput, email);
    }
    if (await this.isDisplayed(this.passwordInput)) {
      await this.setValue(this.passwordInput, pass);
    }
    if (await this.isDisplayed(this.loginButton)) {
      await this.click(this.loginButton);
    }
  }

  public async register(email: string, pass: string) {
    await this.login(email, pass);
    if (await this.isDisplayed(this.signupButton)) {
      await this.click(this.signupButton);
    }
  }
}
