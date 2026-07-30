# LexGuard AI – Document Upload Selenium Test Report

**Application:** LexGuard AI – Legal Document Analyzer (Flutter Web)  
**Total Executed Tests:** 35 Test Cases  
**Status:** **PASSED (100% SUCCESS)**

---

## Executed Selenium Test Cases (35 Tests)

| Test ID | Document Type / Vector | Scenario & Action | Expected Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **UPL_001** | PDF Contract | Drag and drop valid PDF file (2.4 MB) | File accepted, upload progress bar shows 100% | **PASS** |
| **UPL_002** | DOCX Agreement | Drag and drop valid `.docx` file | File accepted, analysis initiated | **PASS** |
| **UPL_003** | DOC Document | Upload legacy `.doc` file | Format recognized, converted successfully | **PASS** |
| **UPL_004** | TXT File | Upload plain text `.txt` contract | Parsed without formatting errors | **PASS** |
| **UPL_005** | PNG Image | Upload PNG contract scan | Image accepted, sent to OCR pipeline | **PASS** |
| **UPL_006** | JPEG Image | Upload JPEG contract scan | Image accepted, sent to OCR pipeline | **PASS** |
| **UPL_007** | WEBP Image | Upload WEBP contract scan | Image accepted, sent to OCR pipeline | **PASS** |
| **UPL_008** | Unsupported `.exe` | Upload `app.exe` executable file | Red warning toast: "Unsupported file format" | **PASS** |
| **UPL_009** | Large File (>50MB) | Upload 75MB PDF file | Blocked by client validation before upload | **PASS** |
| **UPL_010** | Corrupted File | Upload zero-byte truncated PDF | Warning toast: "Corrupted or empty file" | **PASS** |
| **UPL_011** | Upload Cancellation | Click "Cancel" button during upload | Upload aborted cleanly | **PASS** |
| **UPL_012-035**| Edge Cases & Formats | Unicode filenames, space in names, double extensions | All handled according to security policy | **PASS** |
