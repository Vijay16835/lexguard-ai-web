import BasePage from './base.page';

export default class AiAnalysisPage extends BasePage {
  private get riskScoreCard() { return '~risk_score_card'; }
  private get summaryTab() { return '~summary_tab'; }
  private get chatInput() { return '~ai_chat_input'; }
  private get sendChatBtn() { return '~send_chat_btn'; }

  public async askAssistant(question: string) {
    if (await this.isDisplayed(this.chatInput)) {
      await this.setValue(this.chatInput, question);
    }
    if (await this.isDisplayed(this.sendChatBtn)) {
      await this.click(this.sendChatBtn);
    }
  }
}
