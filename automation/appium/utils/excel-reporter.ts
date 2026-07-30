import ExcelJS from 'exceljs';
import path from 'path';
import fs from 'fs-extra';
import { logger } from './logger';

export interface TestResultRecord {
  testId: string;
  module: string;
  testName: string;
  status: 'PASS' | 'FAIL' | 'SKIP';
  priority: 'P0' | 'P1' | 'P2';
  durationMs: number;
  screenshot?: string;
  errorMessage?: string;
}

export class ExcelReporter {
  private static records: TestResultRecord[] = [];

  static addResult(record: TestResultRecord) {
    this.records.push(record);
  }

  static async generateExcelReports() {
    const excelDir = path.join(__dirname, '../reports/Excel');
    fs.ensureDirSync(excelDir);

    // 1. Full Report
    const mainPath = path.join(excelDir, 'Automation_Test_Report.xlsx');
    const workbook = new ExcelJS.Workbook();
    const sheet = workbook.addWorksheet('Executed Tests');

    sheet.columns = [
      { header: 'Test ID', key: 'testId', width: 15 },
      { header: 'Module', key: 'module', width: 20 },
      { header: 'Test Name', key: 'testName', width: 40 },
      { header: 'Status', key: 'status', width: 12 },
      { header: 'Priority', key: 'priority', width: 10 },
      { header: 'Duration (ms)', key: 'durationMs', width: 15 },
      { header: 'Screenshot', key: 'screenshot', width: 30 },
      { header: 'Error Message', key: 'errorMessage', width: 40 }
    ];

    sheet.getRow(1).font = { bold: true, color: { argb: 'FFFFFF' } };
    sheet.getRow(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: '1E293B' } };

    this.records.forEach((rec) => {
      const row = sheet.addRow(rec);
      const statusCell = row.getCell('status');
      if (rec.status === 'PASS') {
        statusCell.font = { bold: true, color: { argb: '10B981' } };
      } else if (rec.status === 'FAIL') {
        statusCell.font = { bold: true, color: { argb: 'EF4444' } };
      }
    });

    await workbook.xlsx.writeFile(mainPath);

    // 2. Passed Tests Report
    const passedPath = path.join(excelDir, 'Passed_Test_Cases.xlsx');
    const passedWb = new ExcelJS.Workbook();
    const passedSheet = passedWb.addWorksheet('Passed Tests');
    passedSheet.columns = sheet.columns;
    this.records.filter((r) => r.status === 'PASS').forEach((r) => passedSheet.addRow(r));
    await passedWb.xlsx.writeFile(passedPath);

    // 3. Failed Tests Report
    const failedPath = path.join(excelDir, 'Failed_Test_Cases.xlsx');
    const failedWb = new ExcelJS.Workbook();
    const failedSheet = failedWb.addWorksheet('Failed Tests');
    failedSheet.columns = sheet.columns;
    this.records.filter((r) => r.status === 'FAIL').forEach((r) => failedSheet.addRow(r));
    await failedWb.xlsx.writeFile(failedPath);

    // 4. Execution Summary Report
    const summaryPath = path.join(excelDir, 'Execution_Summary.xlsx');
    const sumWb = new ExcelJS.Workbook();
    const sumSheet = sumWb.addWorksheet('Metrics');
    sumSheet.columns = [
      { header: 'Metric', key: 'metric', width: 30 },
      { header: 'Value', key: 'value', width: 20 }
    ];
    const total = this.records.length;
    const passed = this.records.filter((r) => r.status === 'PASS').length;
    const failed = this.records.filter((r) => r.status === 'FAIL').length;
    sumSheet.addRows([
      { metric: 'Total Executed Tests', value: total },
      { metric: 'Passed Tests', value: passed },
      { metric: 'Failed Tests', value: failed },
      { metric: 'Pass Rate (%)', value: total > 0 ? ((passed / total) * 100).toFixed(2) + '%' : '0%' }
    ]);
    await sumWb.xlsx.writeFile(summaryPath);

    logger.info(`Enterprise Excel Reports generated in: ${excelDir}`);
  }
}
