# LexGuard AI – Flutter Web Google Sign-In Selenium Test Report

**Application:** LexGuard AI – Legal Document Analyzer (Flutter Web)  
**Target URL:** `https://username.github.io/LexGuard-AI/` / `http://localhost:3000`  
**Total Executed Tests:** 20 Test Cases  
**Status:** **PASSED (100% SUCCESS)**

---

## Executive Summary

This report validates the **Google Sign-In (Web)** integration for LexGuard AI using Selenium WebDriver. The tests simulate Google OAuth popup windows, credential selection, token exchange with FastAPI backend, session token caching in browser local storage, and browser refresh/back navigation scenarios.

---

## Executed Selenium Test Cases (20 Tests)

| Test ID | Test Title & Scenario | Expected Result | Status |
| :--- | :--- | :--- | :---: |
| **GGL_001** | Verify Google Sign-In Button Display on Login Screen | Button visible with Google icon and standard text | **PASS** |
| **GGL_002** | Verify Google OAuth Popup Window Trigger | Popup window opens to `accounts.google.com` | **PASS** |
| **GGL_003** | Verify User Account Selection in Google Popup | Selects valid test Google account successfully | **PASS** |
| **GGL_004** | Verify ID Token Exchange with FastAPI Backend | `POST /auth/google-auth` returns LexGuard JWT | **PASS** |
| **GGL_005** | Verify Automatic Navigation to Dashboard post-Auth | Redirects user to `/dashboard` route | **PASS** |
| **GGL_006** | Verify Google OAuth Popup Cancellation | Closing popup window leaves user safely on Login | **PASS** |
| **GGL_007** | Verify Popup Blocked Browser Handling | Notification toast alerts user to allow popups | **PASS** |
| **GGL_008** | Verify Existing User Google Login | Existing profile loaded with saved documents | **PASS** |
| **GGL_009** | Verify New User Automatic Account Creation | New user profile registered in Supabase DB | **PASS** |
| **GGL_010** | Verify Session Persistence on Browser Refresh (F5) | User remains logged in post page refresh | **PASS** |
| **GGL_011** | Verify Session Persistence across New Browser Tab | New tab retains active authentication state | **PASS** |
| **GGL_012** | Verify Google Logout Action | Token cleared from storage, redirects to Login | **PASS** |
| **GGL_013** | Verify Expired Google Credential Handling | Invalid token triggers re-authentication prompt | **PASS** |
| **GGL_014-020**| Edge Cases & Network Interruptions | Slow network, token expiry, multi-account switch | **PASS** |
