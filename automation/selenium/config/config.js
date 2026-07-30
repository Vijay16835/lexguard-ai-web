const path = require('path');
require('dotenv').config();

module.exports = {
  baseUrl: process.env.BASE_URL || 'https://vijay16835.github.io/pdd/',
  browser: process.env.BROWSER || 'chrome',
  headless: process.env.HEADLESS !== 'false', // default to true in CI
  implicitWaitMs: parseInt(process.env.IMPLICIT_WAIT_MS || '10000', 10),
  explicitWaitMs: parseInt(process.env.EXPLICIT_WAIT_MS || '15000', 10),
  retries: parseInt(process.env.TEST_RETRIES || '1', 10),
  credentials: {
    validEmail: process.env.TEST_USER_EMAIL || 'tvijay1098@gmail.com',
    validPassword: process.env.TEST_USER_PASSWORD || 'CorrectPassword123'
  },
  dirs: {
    reports: path.resolve(__dirname, '../reports'),
    excel: path.resolve(__dirname, '../reports/excel'),
    html: path.resolve(__dirname, '../reports/html'),
    json: path.resolve(__dirname, '../reports/json'),
    screenshots: path.resolve(__dirname, '../reports/screenshots'),
    logs: path.resolve(__dirname, '../reports/logs')
  }
};
