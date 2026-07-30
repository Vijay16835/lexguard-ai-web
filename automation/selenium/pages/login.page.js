const { By } = require('selenium-webdriver');
const BasePage = require('./base.page');

class LoginPage extends BasePage {
  constructor(driver) {
    super(driver);
    this.emailInput = By.css('input[type="email"], input[name="email"]');
    this.passwordInput = By.css('input[type="password"], input[name="password"]');
    this.loginBtn = By.css('button[type="submit"], button.login-btn');
    this.googleBtn = By.css('button.google-signin-btn, button[aria-label="Google Sign-In"]');
    this.forgotPassLink = By.css('a[href*="forgot"], a.forgot-password');
  }

  async login(email, password) {
    await this.type(this.emailInput, email);
    await this.type(this.passwordInput, password);
    await this.click(this.loginBtn);
  }

  async clickGoogleSignIn() {
    await this.click(this.googleBtn);
  }
}

module.exports = LoginPage;
