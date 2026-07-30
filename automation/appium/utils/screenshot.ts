import path from 'path';
import fs from 'fs-extra';

export class ScreenshotUtils {
  static async capture(name: string): Promise<string> {
    try {
      const screenshotDir = path.join(__dirname, '../screenshots');
      fs.ensureDirSync(screenshotDir);

      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `${name.replace(/[^a-zA-Z0-9_-]/g, '_')}_${timestamp}.png`;
      const fullPath = path.join(screenshotDir, filename);

      await browser.saveScreenshot(fullPath);
      return path.relative(process.cwd(), fullPath);
    } catch {
      return '';
    }
  }
}
