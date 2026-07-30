# LexGuard AI – GitHub Actions CI/CD Guide

## Overview

The repository has **two GitHub Actions workflows** that run all automated tests without modifying any existing test code:

| Workflow | File | Trigger |
|----------|------|---------|
| Full CI Suite (Selenium · API · Security · Performance) | `.github/workflows/ci-tests.yml` | Push / PR to `main` or `master`, or manual |
| Android Appium E2E | `.github/workflows/android-e2e.yml` | Push / PR to `main` or `master`, or manual |

---

## How to Enable GitHub Actions

1. Go to your repository on **GitHub.com**
2. Click the **Actions** tab
3. If prompted, click **"I understand my workflows, go ahead and enable them"**

That's it — workflows run automatically on every push or pull request to `main`/`master`.

---

## How to Trigger a Workflow

### Automatic (Push / PR)
Any push or pull request to `main` or `master` triggers both workflows automatically.

### Manual Trigger
1. Go to **GitHub → Actions**
2. Select the workflow you want to run (e.g., *Full CI Suite* or *Android Appium E2E*)
3. Click **"Run workflow"** → **"Run workflow"**

For the Full CI Suite, you can optionally enable the **performance load test** via the dropdown:

```
run_performance: true
```

> **Note:** The performance test connects to your live backend. Make sure `BACKEND_URL` and `JWT_SECRET_KEY` secrets are set before enabling it.

---

## Required GitHub Secrets

Set these in **GitHub → Settings → Secrets and variables → Actions → New repository secret**:

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `TEST_BASE_URL` | URL of deployed Flutter Web app (e.g., `https://your-app.web.app`) | Optional (defaults to localhost) |
| `BACKEND_URL` | FastAPI backend URL (e.g., `https://lexguard-backend.onrender.com`) | For performance tests |
| `TEST_USER_EMAIL` | Test user email for Selenium/Appium login | Optional (has fallback) |
| `TEST_USER_PASSWORD` | Test user password | Optional (has fallback) |
| `JWT_SECRET_KEY` | Backend JWT secret (for performance test token generation) | For performance tests |
| `SUPABASE_URL` | Supabase project URL | For API tests |
| `SUPABASE_KEY` | Supabase anon key | For API tests |
| `GOOGLE_SERVICES_JSON` | Firebase google-services.json content (for Android APK build) | For Appium tests |

---

## Workflow Jobs Summary

### ci-tests.yml (Full CI Suite)

```
flutter-web-build  →  selenium-tests  →  generate-reports
                   →  api-tests       →
                   →  security-tests  →
                   →  performance-tests (manual only)
```

| Job | Runner | What It Does |
|-----|--------|-------------|
| `flutter-web-build` | ubuntu-latest | `flutter build web --release` |
| `selenium-tests` | ubuntu-latest | Serves built web app · Runs `npm test` (Mocha+Selenium) · Generates Excel |
| `api-tests` | ubuntu-latest | Runs `pytest backend/app/tests/` · Generates JUnit XML + JSON |
| `security-tests` | ubuntu-latest | Runs Bandit · Safety · pip-audit · Copies existing security audit reports |
| `performance-tests` | ubuntu-latest | Runs `backend/run_load_test.py` with 100 VUs (manual trigger only) |
| `generate-reports` | ubuntu-latest | Downloads all job artifacts · Produces consolidated Excel, HTML, JSON |

### android-e2e.yml (Android Appium)

| Step | What It Does |
|------|-------------|
| Build APK | `flutter build apk --debug` |
| Appium WDIO | Runs `automation/appium/tests/*.spec.ts` on Android 13 emulator |
| Java/TestNG | Runs `LexGuard_Appium_Testing` Maven suite via `mvn test` |
| HTML Report | `utils/html-reporter.generateHtmlReport()` |
| Excel Reports | `utils/excel-reporter.generateExcelReports()` |

---

## How to Download Generated Reports

1. Go to **GitHub → Actions**
2. Click the completed workflow run
3. Scroll down to the **Artifacts** section
4. Click any artifact to download a `.zip` file

### Available Artifacts (retained 30 days)

| Artifact Name | Contents |
|---------------|----------|
| `LexGuard-CI-Consolidated-Reports` | **Automation_Test_Report.xlsx**, **Passed_Test_Cases.xlsx**, **Failed_Test_Cases.xlsx**, **Execution_Summary.xlsx**, `ci_report.html`, `ci_summary.json` |
| `LexGuard-Selenium-Reports` | Mochawesome HTML, JSON, Selenium Excel, Screenshots, Logs |
| `LexGuard-API-Test-Reports` | JUnit XML, API JSON summary |
| `LexGuard-Security-Reports` | Bandit JSON, Safety report, pip-audit JSON, existing security-audit-reports/ |
| `LexGuard-Performance-Reports` | `performance_results.json`, `Performance_Report.xlsx`, `performance_dashboard.html` |
| `LexGuard-Appium-Automation-Reports` | WDIO reports, screenshots, logs, Maven Surefire HTML, debug APK |

---

## How to Interpret Results

### GitHub Actions Step Summary

After every run, open the workflow run and click **"Summary"** at the top left. You'll see:

```
📋 LexGuard AI – CI/CD Test Execution Summary

| Pipeline Stage        | Status    |
|-----------------------|-----------|
| 🌐 Flutter Web Build  | ✅ Passed |
| 🖥️ Selenium Web E2E   | ✅ Passed |
| 🔌 Backend API Tests  | ✅ Passed |
| 🔒 Security Audit     | ✅ Passed |

🖥️ Selenium Web E2E Test Results
| Metric    | Value |
|-----------|-------|
| Total     | 2     |
| ✅ Passed | 2     |
| ❌ Failed | 0     |
| Pass %    | 100%  |
```

### Excel Report — `Automation_Test_Report.xlsx`

| Sheet | Contents |
|-------|----------|
| **All Test Results** | Every test case from all frameworks — Test ID, Suite, Name, Status (color-coded), Duration, Framework, Error |
| **Execution Summary** | Total/Passed/Failed/Skipped counts, Pass %, Duration, per-framework breakdown |
| **Passed Tests** | Filter view of all passing test cases |
| **Failed Tests** | Filter view of failing cases with error messages |

**Status colors:**
- 🟢 `PASS` — Green text + light green row
- 🔴 `FAIL` — Red text + light red row  
- 🟡 `SKIP` — Amber text + light amber row

### HTML Report — `ci_report.html`

Open in any browser. Shows:
- KPI cards: Total, Passed, Failed, Skipped, Pass Rate %
- Full test table with all frameworks combined

### Security Reports

| Report | Severity Levels |
|--------|----------------|
| `bandit-report.json` | HIGH / MEDIUM / LOW SAST issues in Python source |
| `safety-report.json` | Known CVEs in `requirements.txt` dependencies |
| `pip-audit-report.json` | CVE database scan of installed packages |
| `security-summary.json` | Consolidated with overall status: `PASSED` / `NEEDS_REVIEW` / `CRITICAL` |

---

## File Structure (CI/CD files only)

```
.github/
├── workflows/
│   ├── ci-tests.yml          ← Full CI suite (Selenium · API · Security · Perf)
│   ├── android-e2e.yml       ← Android Appium E2E (updated)
│   └── deploy.yml            ← Existing Flutter Web deployment (unchanged)
└── scripts/
    ├── generate_ci_reports.py    ← Consolidated Excel + HTML + JSON generator
    └── generate_security_report.py ← Security audit aggregator
```

---

## Troubleshooting

### Selenium tests fail with "Unable to find Chrome binary"
The workflow uses `browser-actions/setup-chrome@v1` to install Chrome automatically. If this fails, check the [browser-actions GitHub repo](https://github.com/browser-actions/setup-chrome) for updates.

### Android Appium tests timeout
The `macos-latest` runner with Android emulator can be slow. The timeout is set to 90 minutes. If tests consistently time out, reduce the test suite or use a paid runner.

### Performance tests not running
Performance tests are **manual-only** and require `run_performance: true` in the manual trigger input. Secrets `BACKEND_URL` and `JWT_SECRET_KEY` must also be set.

### Excel reports show 0 tests
This means no JUnit XML or Mochawesome JSON was found in the downloaded artifacts. Check that the test jobs completed (even with failures) before the `generate-reports` job runs. The `if: always()` condition ensures this.

### `flutter build apk` fails with Firebase error
Set the `GOOGLE_SERVICES_JSON` secret. The workflow will write it to `android/app/google-services.json` before the build.
