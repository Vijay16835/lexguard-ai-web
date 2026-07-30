# LexGuard AI – Node.js + Selenium E2E Web Automation Framework

Enterprise End-to-End (E2E) Web Automation Testing Framework designed specifically for the **LexGuard AI (Legal Document Analyzer)** Web Application using **Node.js**, **Selenium WebDriver**, **Mocha**, **Chai**, **ExcelJS**, **Mochawesome HTML Reporter**, and **Winston Logging**.

---

## 📁 Directory Structure

```
selenium-testing/
├── config/
│   └── config.js                     # Centralized environment & timeout settings
├── drivers/
│   └── driver-factory.js             # WebDriver builder (Chrome, Firefox, Edge)
├── pages/                            # Page Object Model (POM) Classes
│   ├── base.page.js                  # Explicit wait & Selenium helper wrappers
│   ├── login.page.js                 # Authentication UI selectors & flows
│   ├── dashboard.page.js             # Statistics cards & navigation links
│   ├── upload.page.js                # Document dropzone & format validations
│   ├── analysis.page.js              # AI summary, risk score, & report export
│   ├── history.page.js               # Document history search, filter, & delete
│   ├── notifications.page.js         # Notifications dropdown & list items
│   ├── profile.page.js               # User profile edit & read-only fields
│   └── settings.page.js              # Dark theme switch & preferences
├── tests/                            # Mocha End-to-End Test Suites
│   ├── auth.test.js
│   ├── dashboard.test.js
│   ├── upload.test.js
│   ├── analysis.test.js
│   ├── history.test.js
│   ├── notifications.test.js
│   ├── profile.test.js
│   ├── settings.test.js
│   └── logout.test.js
├── utils/                            # Framework Utilities & Reporters
│   ├── logger.js                     # Winston logger (logs/automation.log)
│   ├── screenshot.js                 # PNG Screenshot capture on failure
│   ├── excel-reporter.js             # ExcelJS writer (Automation_Test_Report.xlsx)
│   └── metrics-collector.js          # JSON results exporter (results.json)
├── reports/                          # Execution Reports Output Directory
│   ├── html/                         # Mochawesome HTML Dashboard
│   ├── excel/                        # Automation_Test_Report.xlsx
│   └── json/                         # results.json
├── screenshots/                      # Failure PNG Screenshots
├── logs/                             # Execution Logs (automation.log)
├── test-data/                        # Sample PDFs, DOCX, & JSON user credentials
│   ├── users.json
│   └── sample-files/
│       ├── sample.pdf
│       └── unsupported.exe
├── downloads/                        # Document Exports & Download Folder
├── .env                              # Base URL, Browser choice, & Headless toggle
├── .mocharc.js                       # Mocha test runner configuration
├── package.json                      # Node.js dependencies & scripts
└── README.md                         # Framework Documentation
```

---

## 🚀 Prerequisite Setup

1. **Node.js (v18 or higher)** installed on your machine.
2. **Google Chrome, Mozilla Firefox, or Microsoft Edge** installed.

---

## ⚙️ How to Run Automation Tests

### 1. Install Dependencies
Navigate into the `selenium-testing/` directory:
```bash
cd selenium-testing
npm install
```

### 2. Configure Environment (`.env`)
Edit `.env` to target your web application URL:
```env
BASE_URL=http://localhost:3000
BROWSER=chrome
HEADLESS=true
```

### 3. Run All Test Suites
```bash
# Run tests with default browser configured in .env
npm test

# Or target specific browsers:
npm run test:chrome
npm run test:firefox
npm run test:edge
```

---

## 📊 Automated Deliverables & Reports

After test execution finishes, the following deliverables are automatically updated:

1. 🌐 **Mochawesome HTML Report:**  
   Path: `reports/html/Mochawesome.html`  
   Features: Complete pass/fail execution chart, test timing, failure stacks.

2. 📈 **Excel Automation Report:**  
   Path: `reports/excel/Automation_Test_Report.xlsx`  
   Sheets: `Execution Summary` & `Test Details` (Columns: `Test ID`, `Module`, `Test Case`, `Status`, `Execution Time`, `Screenshot`, `Error Message`).

3. 📄 **JSON Results Summary:**  
   Path: `reports/json/results.json`

4. 📸 **Screenshots Folder:**  
   Path: `screenshots/` (PNG screenshots taken automatically on failure).

5. 📝 **Execution Logs:**  
   Path: `logs/automation.log`
