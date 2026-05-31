import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:image_picker/image_picker.dart';
import 'package:lexguard_ai/models/document_model.dart';

enum UploadState { idle, picking, uploading, analyzing, success, error }

class UploadProvider extends ChangeNotifier {
  UploadState _uploadState = UploadState.idle;
  DocumentModel? _selectedDocument;
  double _uploadProgress = 0;
  String? _errorMessage;
  File? _selectedFile;

  UploadState get uploadState => _uploadState;
  DocumentModel? get selectedDocument => _selectedDocument;
  double get uploadProgress => _uploadProgress;
  String? get errorMessage => _errorMessage;
  bool get hasDocument => _selectedDocument != null;

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  Future<bool> pickFileFromDevice() async {
    try {
      _uploadState = UploadState.picking;
      _errorMessage = null;
      notifyListeners();

      FilePickerResult? result = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png'],
      );

      if (result != null && result.files.single.path != null) {
        File file = File(result.files.single.path!);
        await _processSelectedFile(file, result.files.single.name);
        return true;
      } else {
        _uploadState = UploadState.idle;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _errorMessage = 'Error picking file: $e';
      _uploadState = UploadState.error;
      notifyListeners();
      return false;
    }
  }

  Future<bool> scanFromCamera() async {
    try {
      _uploadState = UploadState.picking;
      _errorMessage = null;
      notifyListeners();

      final ImagePicker picker = ImagePicker();
      final XFile? photo = await picker.pickImage(source: ImageSource.camera);

      if (photo != null) {
        File file = File(photo.path);
        // Placeholder for OCR Architecture
        // TODO: Send file to backend FastAPI endpoint for text extraction
        await Future.delayed(const Duration(seconds: 1));
        
        await _processSelectedFile(file, photo.name);
        return true;
      } else {
        _uploadState = UploadState.idle;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _errorMessage = 'Error scanning from camera: $e';
      _uploadState = UploadState.error;
      notifyListeners();
      return false;
    }
  }

  Future<void> _processSelectedFile(File file, String fileName) async {
    int fileSizeInBytes = await file.length();
    double fileSizeInMB = fileSizeInBytes / (1024 * 1024);

    if (fileSizeInMB > 50) {
      _errorMessage = 'File size exceeds 50MB limit.';
      _uploadState = UploadState.error;
      notifyListeners();
      return;
    }

    String extension = fileName.split('.').last.toLowerCase();
    DocumentType type = DocumentType.unknown;
    if (extension == 'pdf') {
      type = DocumentType.pdf;
    } else if (extension == 'docx' || extension == 'doc') {
      type = DocumentType.docx;
    } else if (['jpg', 'jpeg', 'png'].contains(extension)) {
      type = DocumentType.image;
    }

    _selectedFile = file;
    _selectedDocument = DocumentModel(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      name: fileName,
      path: file.path,
      type: type,
      sizeInMB: double.parse(fileSizeInMB.toStringAsFixed(2)),
      uploadedAt: DateTime.now(),
      status: DocumentStatus.pending,
    );

    _uploadState = UploadState.idle;
    notifyListeners();
  }

  Future<bool> uploadAndAnalyze() async {
    if (_selectedDocument == null || _selectedFile == null) return false;

    try {
      // Upload phase
      _uploadState = UploadState.uploading;
      _uploadProgress = 0;
      notifyListeners();

      // Placeholder for FastAPI + PostgreSQL backend upload integration
      for (int i = 0; i <= 100; i += 10) {
        await Future.delayed(const Duration(milliseconds: 100));
        _uploadProgress = i / 100;
        notifyListeners();
      }

      // Analyzing phase
      _uploadState = UploadState.analyzing;
      notifyListeners();
      
      // Placeholder for AI analysis processing integration
      await Future.delayed(const Duration(seconds: 3));

      // Success
      _selectedDocument = _selectedDocument!.copyWith(
        status: DocumentStatus.completed,
        riskLevel: RiskLevel.high,
        riskScore: 78,
      );
      _uploadState = UploadState.success;
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = 'Upload failed: $e';
      _uploadState = UploadState.error;
      notifyListeners();
      return false;
    }
  }

  void reset() {
    _uploadState = UploadState.idle;
    _selectedDocument = null;
    _selectedFile = null;
    _uploadProgress = 0;
    _errorMessage = null;
    notifyListeners();
  }
}
