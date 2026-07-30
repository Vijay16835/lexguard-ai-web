# LexGuard AI – Enterprise Android Appium 2.x WebdriverIO Automation Framework

Enterprise End-to-End (E2E) Mobile Automation Testing Framework engineered for the **LexGuard AI – Legal Document Analyzer** Android application using **Appium 2.x**, **WebdriverIO**, **TypeScript**, **Page Object Model (POM)**, **ExcelJS**, and **GitHub Actions**.

---

## 📁 Directory Architecture

```
automation/appium/
├── config/
│   └── appium.config.ts              # Appium 2.x UiAutomator2 capabilities
├── pages/                            # Page Object Model (POM) Classes
│   ├── base.page.ts
│   ├── splash.page.ts
│   ├── login.page.ts
│   ├── registration.page.ts
│   ├── otp.page.ts
│   ├── forgot-password.page.ts
│   ├── dashboard.page.ts
│   ├── upload.page.ts
│   ├── ai-analysis.page.ts
│   ├── document-viewer.page.ts
│   ├── search.page.ts
│   ├── notifications.page.ts
│   ├── history.page.ts
│   ├── profile.page.ts
│   ├── settings.page.ts
│   └── logout.page.ts
├── tests/                            # 16 Test Spec Modules (400+ Test Cases)
│   ├── auth.spec.ts
│   ├── registration.spec.ts
│   ├── forgot-password.spec.ts
│   ├── dashboard.spec.ts
│   ├── upload.spec.ts
│   ├── ai-analysis.spec.ts
│   ├── history.spec.ts
│   ├── search.spec.ts
│   ├── notifications.spec.ts
│   ├── profile.spec.ts
│   ├── settings.spec.ts
│   ├── session.spec.ts
│   ├── error-handling.spec.ts
│   ├── file-validation.spec.ts
│   ├── performance-smoke.spec.ts
│   └── regression.spec.ts
├── data/
│   ├── test-cases-catalog.json       # Programmatic 400+ Test Case Specifications Catalog
│   └── users.json
├── utils/
│   ├── excel-reporter.ts             # Generates 4 Excel Reports (.xlsx)
│   ├── html-reporter.ts              # Generates HTML Dashboards & Trends
│   ├── logger.ts                     # Winston logger (logs/automation.log)
│   └── screenshot.ts                 # PNG Screenshot capture on failure
├── reports/
│   ├── Excel/
│   │   ├── Automation_Test_Report.xlsx
│   │   ├── Passed_Test_Cases.xlsx
│   │   ├── Failed_Test_Cases.xlsx
│   │   └── Execution_Summary.xlsx
│   ├── HTML/
│   │   ├── execution-report.html
│   │   ├── dashboard.html
│   │   └── trends.html
│   ├── JSON/
│   │   └── execution-results.json
│   ├── Screenshots/
│   ├── Logs/
│   └── Summary/
│       └── summary.md
├── package.json
├── tsconfig.json
├── appium.config.ts
└── README.md
```

---

## 🚀 Local Setup & Execution Guide

### 1. Prerequisites
- **Node.js (v18+)** & **TypeScript**
- **Appium 2.x & UiAutomator2 Driver**:
  ```bash
  npm install -g appium
  appium driver install uiautomator2
  ```
- **Android SDK & Emulator** running API 33 (Android 13)

### 2. Install Dependencies
```bash
cd automation/appium
npm install
```

### 3. Run Automation Test Suites
```bash
# Execute entire 400+ test suite
npm test

# Target specific modules:
npm run test:auth
npm run test:upload
npm run test:analysis
npm run test:regression
```

---

## ⚙️ GitHub Actions CI/CD Pipeline

The framework is configured with `.github/workflows/android-e2e.yml` which automatically:
1. Boots Android Emulator (API 33)
2. Builds `app-debug.apk` (`flutter build apk`)
3. Installs APK & launches Appium 2.x
4. Executes all 400+ test cases
5. Generates Excel & HTML reports
6. Uploads artifacts with **30 Days Retention**
7. Publishes dashboards to **GitHub Pages** (`gh-pages`)
