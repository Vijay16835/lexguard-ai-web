#!/bin/bash
set -e

echo "════════════════════════════════════════════════"
echo "  LexGuard AI — Android Appium E2E Test Runner  "
echo "════════════════════════════════════════════════"
echo ""

# ── 1. Wait for ADB device readiness ──────────────────────────
echo "🔌 Waiting for ADB device..."
adb wait-for-device

echo "⏳ Waiting for Android boot completion..."
i=0
max_attempts=60
boot_completed="0"
while [ "$i" -lt "$max_attempts" ]; do
  boot_completed=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || echo "0")
  if [ "$boot_completed" = "1" ]; then
    echo "✅ Android emulator boot completed."
    break
  fi
  i=$((i + 1))
  echo "  Waiting for Android boot completion... attempt $i/$max_attempts"
  sleep 2
done

if [ "$boot_completed" != "1" ]; then
  echo "❌ ERROR: Android emulator did not reach sys.boot_completed=1 within $max_attempts attempts"
  exit 1
fi

echo "✅ Device booted. Connected devices:"
adb devices

# ── 2. Disable system animations ─────────────────────────────
echo "🎭 Disabling animations for stable testing..."
adb shell settings put global window_animation_scale 0 || true
adb shell settings put global transition_animation_scale 0 || true
adb shell settings put global animator_duration_scale 0 || true

# ── 3. Install APK ────────────────────────────────────────────
APK_PATH="${APK_PATH:-build/app/outputs/flutter-apk/app-debug.apk}"
echo "📲 Installing APK: ${APK_PATH}"
ADB_INSTALL_RETRIES=3
for i in $(seq 1 ${ADB_INSTALL_RETRIES}); do
  if adb install -r "${APK_PATH}"; then
    echo "✅ APK installed successfully on attempt ${i}"
    break
  fi
  echo "⚠️ Install attempt ${i} failed, retrying..."
  sleep 5
  if [ ${i} -eq ${ADB_INSTALL_RETRIES} ]; then
    echo "❌ APK install failed after ${ADB_INSTALL_RETRIES} attempts"
    exit 1
  fi
done

# Verify APK install
PACKAGE_NAME="com.lexguard.lexguard_ai"
adb shell pm list packages | grep -q "${PACKAGE_NAME}" && \
  echo "✅ Package verified: ${PACKAGE_NAME}" || \
  echo "⚠️ Package not found — tests may fail to launch app"

# ── 4. Start Appium Server ────────────────────────────────────
echo "🚀 Starting Appium 2.x server..."
appium --port 4723 \
       --log-level info \
       --allow-insecure *:chromedriver_autodownload \
       > automation/appium/reports/logs/appium-server.log 2>&1 &
APPIUM_PID=$!
echo "Appium PID: ${APPIUM_PID}"

# Wait for Appium readiness
echo "⏳ Waiting for Appium server to be ready..."
MAX_APPIUM_WAIT=30
for i in $(seq 1 ${MAX_APPIUM_WAIT}); do
  if curl -s http://localhost:4723/status | grep -q '"ready":true'; then
    echo "✅ Appium server ready at attempt ${i}"
    break
  fi
  sleep 2
  if [ ${i} -eq ${MAX_APPIUM_WAIT} ]; then
    echo "❌ Appium server did not become ready in time"
    cat automation/appium/reports/logs/appium-server.log || true
    exit 1
  fi
done

# ── 5. Execute Appium Test Suite ──────────────────────────────
SUITE="${TEST_SUITE:-all}"
echo "🧪 Executing test suite: ${SUITE}"
echo ""

cd automation/appium
set +e
if [[ "${SUITE}" == "all" || "${SUITE}" == "" ]]; then
  npm test
else
  npm run "test:${SUITE}" 2>/dev/null || npm test -- --spec "tests/*${SUITE}*"
fi
TEST_EXIT_CODE=$?
set -e

echo ""
echo "═══════════════════════════════════"
echo "  Appium exit code: ${TEST_EXIT_CODE}"
echo "═══════════════════════════════════"

# Save exit code for downstream jobs
echo "${TEST_EXIT_CODE}" > /tmp/appium_exit_code

# ── 6. Cleanup ────────────────────────────────────────────────
kill ${APPIUM_PID} 2>/dev/null || true
echo "✅ Appium server stopped"

exit ${TEST_EXIT_CODE}
