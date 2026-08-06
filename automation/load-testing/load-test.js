import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Target URL resolution
const TARGET_URL = __ENV.LEXGUARD_API_URL || __ENV.TARGET_URL || 'https://pdd-uw63.onrender.com';
const CLEAN_BASE_URL = TARGET_URL.replace(/\/+$/, '');

// Custom k6 metrics for detailed report generation
export const status200Counter = new Counter('http_status_200');
export const status4xxCounter = new Counter('http_status_4xx');
export const status5xxCounter = new Counter('http_status_5xx');
export const statusOtherCounter = new Counter('http_status_other');

// Load Test Configuration Options & Stages Profile
export const options = {
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
  stages: [
    { duration: __ENV.STAGE_1_DURATION || '30s', target: parseInt(__ENV.STAGE_1_VUS || '5') },
    { duration: __ENV.STAGE_2_DURATION || '30s', target: parseInt(__ENV.STAGE_2_VUS || '10') },
    { duration: __ENV.STAGE_3_DURATION || '60s', target: parseInt(__ENV.STAGE_3_VUS || '20') },
    { duration: __ENV.STAGE_4_DURATION || '60s', target: parseInt(__ENV.STAGE_4_VUS || '30') },
    { duration: __ENV.STAGE_5_DURATION || '30s', target: parseInt(__ENV.STAGE_5_VUS || '0') }
  ],
  thresholds: {
    http_req_failed: ['rate<0.10'], // HTTP error rate should be below 10%
    http_req_duration: ['p(95)<10000'] // P95 response time below 10000ms (suitable for cloud runners & cold starts)
  }
};

export default function () {
  const endpoints = [
    { path: '/', name: 'Root Welcome Endpoint' },
    { path: '/api/v1/auth/health', name: 'Auth Service Health' },
    { path: '/api/v1/openapi.json', name: 'OpenAPI Specification' }
  ];

  // Select a target endpoint for each iteration
  const target = endpoints[Math.floor(Math.random() * endpoints.length)];
  const fullUrl = `${CLEAN_BASE_URL}${target.path}`;

  const res = http.get(fullUrl, {
    headers: {
      'User-Agent': 'LexGuard-k6-LoadTest/1.0',
      'Accept': 'application/json'
    },
    tags: { name: target.name, endpoint: target.path },
    timeout: '15s'
  });

  // Track status code metrics
  if (res.status === 200) {
    status200Counter.add(1);
  } else if (res.status >= 400 && res.status < 500) {
    status4xxCounter.add(1);
  } else if (res.status >= 500) {
    status5xxCounter.add(1);
  } else {
    statusOtherCounter.add(1);
  }

  // Verification checks
  check(res, {
    'status code is 200': (r) => r.status === 200,
    'response body received': (r) => r.body && r.body.length > 0
  });

  // Pacing delay between requests
  sleep(1);
}

// Generate machine-readable JSON summary output for Excel report generator
export function handleSummary(data) {
  // Inject metadata into raw summary
  data.metadata = {
    target_url: CLEAN_BASE_URL,
    execution_timestamp: new Date().toISOString(),
    stages: options.stages
  };

  return {
    'automation/load-testing/reports/json/k6-summary.json': JSON.stringify(data, null, 2),
    'reports/json/k6-summary.json': JSON.stringify(data, null, 2)
  };
}
