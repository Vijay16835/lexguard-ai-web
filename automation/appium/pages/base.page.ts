export default class BasePage {
  protected async find(selector: string) {
    const el = await $(selector);
    await el.waitForDisplayed({ timeout: 20000 });
    return el;
  }

  protected async click(selector: string) {
    const el = await this.find(selector);
    await el.click();
  }

  protected async setValue(selector: string, value: string) {
    const el = await this.find(selector);
    await el.setValue(value);
  }

  protected async getText(selector: string): Promise<string> {
    try {
      const el = await this.find(selector);
      return await el.getText();
    } catch {
      return '';
    }
  }

  protected async isDisplayed(selector: string): Promise<boolean> {
    try {
      const el = await $(selector);
      return await el.isDisplayed();
    } catch {
      return false;
    }
  }

  protected async swipeUp() {
    await browser.execute('mobile: scroll', { direction: 'down' });
  }

  protected async swipeDown() {
    await browser.execute('mobile: scroll', { direction: 'up' });
  }
}
