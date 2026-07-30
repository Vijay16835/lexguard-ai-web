const { By } = require('selenium-webdriver');
const BasePage = require('./base.page');

class AnalysisPage extends BasePage {
  constructor(driver) {
    super(driver);
    this.ocrTextContainer = By.css('.ocr-text, .extracted-content');
    this.riskScoreBadge = By.css('.risk-score, .severity-badge');
    this.summaryTab = By.xpath("//button[contains(text(),'Summary') or @aria-label='Summary']");
    this.chatInput = By.css('input[placeholder*="Ask AI"], textarea[placeholder*="Ask AI"]');
    this.sendChatBtn = By.xpath("//button[contains(text(),'Send') or @aria-label='Send']");
    this.chatResponse = By.css('.chat-message, .ai-response');
  }

  async askAI(question) {
    if (await this.isDisplayed(this.chatInput)) {
      await this.type(this.chatInput, question);
    }
    if (await this.isDisplayed(this.sendChatBtn)) {
      await this.click(this.sendChatBtn);
    }
  }
}

module.exports = AnalysisPage;
