import BasePage from './base.page';

export default class HistoryPage extends BasePage {
  private get filterChip() { return '~filter_chip'; }
  private get searchInput() { return '~history_search_input'; }
  private get deleteButton() { return '~delete_doc_btn'; }

  public async searchHistory(term: string) {
    if (await this.isDisplayed(this.searchInput)) {
      await this.setValue(this.searchInput, term);
    }
  }

  public async deleteDocument() {
    if (await this.isDisplayed(this.deleteButton)) {
      await this.click(this.deleteButton);
    }
  }
}
