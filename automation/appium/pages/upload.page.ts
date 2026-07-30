import BasePage from './base.page';

export default class UploadPage extends BasePage {
  private get chooseFileBtn() { return '~choose_file_btn'; }
  private get cameraBtn() { return '~camera_option_btn'; }
  private get galleryBtn() { return '~gallery_option_btn'; }
  private get analyzeBtn() { return '~analyze_btn'; }

  public async pickDocument() {
    if (await this.isDisplayed(this.chooseFileBtn)) {
      await this.click(this.chooseFileBtn);
    }
  }

  public async clickAnalyze() {
    if (await this.isDisplayed(this.analyzeBtn)) {
      await this.click(this.analyzeBtn);
    }
  }
}
