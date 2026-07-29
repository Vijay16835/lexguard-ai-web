import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:file_picker/file_picker.dart';
import 'package:lexguard_ai/core/constants/api_constants.dart';
import 'package:lexguard_ai/core/utils/file_download_helper.dart';
import 'package:lexguard_ai/services/api_service.dart';

class DownloadResult {
  final String? path;
  final String? error;

  const DownloadResult({this.path, this.error});

  bool get success => path != null;
}

class DocumentService {
  late final Dio _dio;

  DocumentService() {
    _dio = ApiService().dio;
  }

  /// Get the base URL for constructing download URLs
  String getBaseUrl() => ApiConstants.baseUrl;

  /// Upload a document file
  Future<Map<String, dynamic>> uploadDocument(PlatformFile file) async {
    // ── Step 1: File selection audit ─────────────────────────────────────────
    debugPrint('[Upload] STEP 1 — File audit:');
    debugPrint('[Upload]   name     = ${file.name}');
    debugPrint('[Upload]   size     = ${file.size} bytes');
    debugPrint('[Upload]   path     = ${file.path ?? "NULL"}');
    debugPrint('[Upload]   bytes    = ${file.bytes != null ? "${file.bytes!.length} bytes loaded" : "NULL (withData not set?)"}');
    debugPrint('[Upload]   kIsWeb   = $kIsWeb');

    // ── Step 2: Build MultipartFile ──────────────────────────────────────────
    // Strategy: prefer in-memory bytes (works on Web AND Android content:// URIs).
    // Fall back to file path only on desktop where real filesystem paths exist.
    debugPrint('[Upload] STEP 2 — Building MultipartFile...');
    MultipartFile multipartFile;
    try {
      final bytes = file.bytes;
      if (bytes != null && bytes.isNotEmpty) {
        // Bytes already loaded (withData: true) — works on every platform.
        debugPrint('[Upload]   Using in-memory bytes (${bytes.length} bytes).');
        multipartFile = MultipartFile.fromBytes(bytes, filename: file.name);
      } else if (!kIsWeb && file.path != null) {
        // Desktop/mobile fallback: only if path is a real filesystem path.
        // NOTE: On Android 13+ file_picker returns content:// URIs.
        // If bytes are null and path is a content URI, this WILL throw.
        final pathStr = file.path!;
        final isContentUri = pathStr.startsWith('content://');
        debugPrint('[Upload]   Using file path: $pathStr');
        debugPrint('[Upload]   Is content URI: $isContentUri');
        if (isContentUri) {
          debugPrint('[Upload]   ERROR: content:// URI detected but bytes are null.');
          debugPrint('[Upload]   FIX: ensure withData: true is passed to FilePicker.pickFiles()');
          return {
            'success': false,
            'message': 'Upload failed: File bytes could not be loaded. '
                'This is an Android content URI — ensure withData: true in FilePicker.',
          };
        }
        final dartFile = File(pathStr);
        final exists = dartFile.existsSync();
        final length = exists ? dartFile.lengthSync() : 0;
        debugPrint('[Upload]   File.existsSync() = $exists');
        debugPrint('[Upload]   File.lengthSync()  = $length bytes');
        if (!exists) {
          return {'success': false, 'message': 'Upload failed: File not found at path: $pathStr'};
        }
        multipartFile = await MultipartFile.fromFile(pathStr, filename: file.name);
      } else {
        // No bytes and no valid path.
        final reason = kIsWeb
            ? 'on Flutter Web, withData: true must be passed to FilePicker'
            : 'file.path is null and file.bytes is null';
        debugPrint('[Upload]   ERROR: Cannot build MultipartFile — $reason');
        return {'success': false, 'message': 'Upload failed: No file data available ($reason)'};
      }
    } catch (e, stack) {
      debugPrint('[Upload]   EXCEPTION building MultipartFile: ${e.runtimeType}: $e');
      debugPrint('[Upload]   Stack:\n$stack');
      return {'success': false, 'message': 'Upload failed (MultipartFile): ${e.runtimeType}: $e'};
    }

    // ── Step 3: Build FormData ───────────────────────────────────────────────
    debugPrint('[Upload] STEP 3 — Building FormData...');
    final FormData formData = FormData.fromMap({'file': multipartFile});

    // ── Step 4: HTTP POST ────────────────────────────────────────────────────
    final uploadUrl = ApiConstants.uploadDocument;
    debugPrint('[Upload] STEP 4 — Posting to: $uploadUrl');
    try {
      final response = await _dio.post(uploadUrl, data: formData);
      debugPrint('[Upload] STEP 4 — HTTP ${response.statusCode} received.');
      return {'success': true, 'data': response.data};
    } on DioException catch (e) {
      final statusCode = e.response?.statusCode;
      final body = e.response?.data;
      final detail = body is Map ? body['detail'] : body?.toString();
      debugPrint('[Upload] STEP 4 — DioException: ${e.type} | HTTP $statusCode');
      debugPrint('[Upload]   response body: $body');
      debugPrint('[Upload]   error message: ${e.message}');
      debugPrint('[Upload]   stack: ${e.stackTrace}');
      return {
        'success': false,
        'message': detail ?? e.message ?? 'Upload failed (HTTP $statusCode)',
      };
    } catch (e, stack) {
      debugPrint('[Upload] STEP 4 — Unexpected exception: ${e.runtimeType}: $e');
      debugPrint('[Upload]   Stack:\n$stack');
      return {'success': false, 'message': 'Upload failed: ${e.runtimeType}: $e'};
    }
  }

  /// Get all documents for current user
  Future<Map<String, dynamic>> getDocuments() async {
    try {
      final response = await _dio.get(ApiConstants.documentHistory);
      return {'success': true, 'data': response.data};
    } on DioException catch (e) {
      return {
        'success': false,
        'message': e.response?.data?['detail'] ?? 'Failed to fetch documents',
      };
    }
  }

  /// Get document details with analysis
  Future<Map<String, dynamic>> getDocumentDetail(String documentId) async {
    try {
      final response = await _dio.get(ApiConstants.documentDetail(documentId));
      return {'success': true, 'data': response.data};
    } on DioException catch (e) {
      return {
        'success': false,
        'message': e.response?.data?['detail'] ?? 'Failed to fetch document',
      };
    }
  }

  /// Poll document analysis status
  Future<Map<String, dynamic>> getDocumentStatus(String documentId) async {
    try {
      final response = await _dio.get(ApiConstants.documentStatus(documentId));
      return {'success': true, 'data': response.data};
    } on DioException catch (e) {
      return {
        'success': false,
        'message': e.response?.data?['detail'] ?? 'Status check failed',
      };
    }
  }

  /// Delete a document
  Future<Map<String, dynamic>> deleteDocument(String documentId) async {
    try {
      final response = await _dio.delete(ApiConstants.documentDetail(documentId));
      return {'success': true, 'data': response.data};
    } on DioException catch (e) {
      return {
        'success': false,
        'message': e.response?.data?['detail'] ?? 'Delete failed',
      };
    }
  }

  /// Chat with a document
  Future<Map<String, dynamic>> chatWithDocument(String documentId, String query) async {
    try {
      final response = await _dio.post(
        ApiConstants.aiChat,
        data: {'document_id': documentId, 'message': query},
      );
      return {'success': true, 'data': response.data};
    } on DioException catch (e) {
      return {
        'success': false,
        'message': e.response?.data?['detail'] ?? 'Chat failed',
      };
    }
  }

  /// Get chat history for a document
  Future<Map<String, dynamic>> getChatHistory(String documentId) async {
    try {
      final response = await _dio.get(ApiConstants.chatHistory(documentId));
      return {'success': true, 'data': response.data};
    } on DioException catch (e) {
      return {
        'success': false,
        'message': e.response?.data?['detail'] ?? 'Failed to fetch chat history',
      };
    }
  }

  /// Generate AI summary
  Future<Map<String, dynamic>> getSummary(String documentId) async {
    try {
      final response = await _dio.post(ApiConstants.documentSummary(documentId));
      return {'success': true, 'data': response.data};
    } on DioException catch (e) {
      return {
        'success': false,
        'message': e.response?.data?['detail'] ?? 'Summary failed',
      };
    }
  }

  /// Get risk analysis
  Future<Map<String, dynamic>> getRiskAnalysis(String documentId) async {
    try {
      final response = await _dio.post(ApiConstants.riskAnalysis(documentId));
      return {'success': true, 'data': response.data};
    } on DioException catch (e) {
      return {
        'success': false,
        'message': e.response?.data?['detail'] ?? 'Risk analysis failed',
      };
    }
  }

  Future<bool> _requestAndroidStoragePermission() async {
    if (kIsWeb) return true;
    if (!Platform.isAndroid) return true;

    if (await Permission.storage.isGranted) {
      return true;
    }

    if (await Permission.manageExternalStorage.isGranted) {
      return true;
    }

    final storageResult = await Permission.storage.request();
    if (storageResult.isGranted) {
      return true;
    }

    final manageResult = await Permission.manageExternalStorage.request();
    return manageResult.isGranted;
  }

  Future<Directory> _getDownloadDirectory() async {
    if (kIsWeb) {
      throw UnsupportedError('Download directory not available on Web');
    }
    if (!kIsWeb && (Platform.isWindows || Platform.isLinux || Platform.isMacOS)) {
      final downloads = await getDownloadsDirectory();
      if (downloads != null) {
        return downloads;
      }
    }

    if (!kIsWeb && Platform.isAndroid) {
      final externalDirs = await getExternalStorageDirectories(type: StorageDirectory.downloads);
      if (externalDirs != null && externalDirs.isNotEmpty) {
        return externalDirs.first;
      }
    }

    return await getApplicationDocumentsDirectory();
  }

  /// Download a file at the provided URL into a temporary cache.
  Future<String?> downloadFile(String url, String fileName) async {
    try {
      if (kIsWeb) {
        return url;
      }
      final dir = await getTemporaryDirectory();
      final savePath = '${dir.path}${Platform.pathSeparator}$fileName';
      final response = await _dio.get(
        url,
        options: Options(responseType: ResponseType.bytes),
      );

      final file = File(savePath);
      await file.create(recursive: true);
      await file.writeAsBytes(response.data as List<int>);
      return file.path;
    } on DioException catch (_) {
      return null;
    } catch (_) {
      return null;
    }
  }

  Future<DownloadResult> downloadFileToDownloads(
    String url,
    String fileName, {
    ProgressCallback? onReceiveProgress,
    String expectedFormat = 'pdf',
  }) async {
    try {
      if (kIsWeb) {
        final response = await _dio.get(
          url,
          options: Options(responseType: ResponseType.bytes, validateStatus: (status) => status != null && status < 400),
          onReceiveProgress: onReceiveProgress,
        );
        final bytes = response.data as List<int>?;
        if (bytes == null || bytes.isEmpty) {
          return const DownloadResult(error: 'Received empty file response from server.');
        }
        await saveAndLaunchFile(bytes, fileName);
        return const DownloadResult(path: 'Browser downloads folder');
      }

      if (!await _requestAndroidStoragePermission()) {
        return const DownloadResult(error: 'Permission denied to save files.');
      }

      final dir = await _getDownloadDirectory();
      final savePath = '${dir.path}${Platform.pathSeparator}$fileName';
      final response = await _dio.get(
        url,
        options: Options(responseType: ResponseType.bytes, validateStatus: (status) => status != null && status < 400),
        onReceiveProgress: onReceiveProgress,
      );

      final mimeType = response.headers.value('content-type');
      if (mimeType != null && mimeType.toLowerCase().contains('application/json')) {
        final errorMessage = response.data is String
            ? response.data
            : response.data is Map
                ? response.data['detail'] ?? response.data['message'] ?? response.statusMessage
                : response.statusMessage;
        return DownloadResult(error: 'Export failed: ${errorMessage ?? 'Unexpected JSON response'}');
      }

      if (!_isAllowedMimeType(mimeType, expectedFormat)) {
        if (mimeType != null) {
          return DownloadResult(error: 'Unexpected MIME type: $mimeType');
        }
      }

      final bytes = response.data as List<int>?;
      if (bytes == null || bytes.isEmpty) {
        return const DownloadResult(error: 'Received empty file response from server.');
      }

      final file = File(savePath);
      await file.create(recursive: true);
      await file.writeAsBytes(bytes);
      return DownloadResult(path: file.path);
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      final serverMessage = e.response?.data is Map ? e.response?.data['detail'] ?? e.response?.data['message'] : e.response?.statusMessage;
      return DownloadResult(error: 'Network error${status != null ? ' ($status)' : ''}: ${serverMessage ?? e.message}');
    } catch (e) {
      return DownloadResult(error: 'Download failed: $e');
    }
  }

  bool _isAllowedMimeType(String? mimeType, String format) {
    if (mimeType == null) return false;
    final normalized = mimeType.toLowerCase();

    if (normalized.contains('application/octet-stream')) {
      return true;
    }

    switch (format.toLowerCase()) {
      case 'pdf':
        return normalized.contains('application/pdf');
      case 'docx':
      case 'doc':
        return normalized.contains('application/vnd.openxmlformats-officedocument.wordprocessingml.document') ||
            normalized.contains('application/msword');
      case 'txt':
        return normalized.contains('text/plain');
      case 'md':
      case 'markdown':
        return normalized.contains('text/markdown') || normalized.contains('text/plain');
      default:
        return true;
    }
  }

  /// Get export report URL
  String getExportUrl(String documentId, [String format = 'pdf']) {
    return ApiConstants.exportReport(documentId, format);
  }
}
