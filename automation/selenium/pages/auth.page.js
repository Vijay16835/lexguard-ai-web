const { By } = require('selenium-webdriver');
const BasePage = require('./base.page');

class AuthPage extends BasePage {
  constructor(driver) {
    super(driver);
    this.emailInput = By.css('input[type="email"], input[name="email"], flt-semantics[aria-label*="Email"]');
    this.passwordInput = By.css('input[type="password"], input[name="password"], flt-semantics[aria-label*="Password"]');
    this.fullNameInput = By.css('input[name="fullName"], input[placeholder*="Full Name"]');
    this.loginBtn = By.xpath("//button[contains(text(),'Sign In') or contains(text(),'Login') or @aria-label='Sign In']");
    this.signupBtn = By.xpath("//button[contains(text(),'Sign Up') or contains(text(),'Register') or @aria-label='Sign Up']");
    this.googleSignInBtn = By.xpath("//button[contains(text(),'Google') or @aria-label='Sign in with Google']");
    this.forgotPasswordLink = By.xpath("//a[contains(text(),'Forgot Password') or contains(text(),'Reset')]");
    this.resetPasswordBtn = By.xpath("//button[contains(text(),'Send OTP') or contains(text(),'Reset Password')]");
    this.logoutBtn = By.xpath("//button[contains(text(),'Logout') or @aria-label='Logout']");
  }

  async login(email, password) {
    if (await this.isDisplayed(this.emailInput)) {
      await this.type(this.emailInput, email);
    }
    if (await this.isDisplayed(this.passwordInput)) {
      await this.type(this.passwordInput, password);
    }
    if (await this.isDisplayed(this.loginBtn)) {
      await this.click(this.loginBtn);
    }
  }

  async register(fullName, email, password) {
    if (await this.isDisplayed(this.fullNameInput)) {
      await this.type(this.fullNameInput, fullName);
    }
    await this.login(email, password);
    if (await this.isDisplayed(this.signupBtn)) {
      await this.click(this.signupBtn);
    }
  }

  async clickGoogleSignIn() {
    if (await this.isDisplayed(this.googleSignInBtn)) {
      await this.click(this.googleSignInBtn);
    }
  }
}

module.exports = AuthPage;
