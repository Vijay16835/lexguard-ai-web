module.exports = {
  timeout: 60000,
  retries: 1,
  slow: 5000,
  ui: 'bdd',
  reporter: 'mochawesome',
  'reporter-option': [
    'reportDir=reports/html',
    'reportFilename=Mochawesome',
    'quiet=false',
    'overwrite=true',
    'html=true',
    'json=true',
    'charts=true'
  ],
  spec: ['tests/*.test.js']
};
