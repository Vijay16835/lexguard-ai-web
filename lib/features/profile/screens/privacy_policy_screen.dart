import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';

class PrivacyPolicyScreen extends StatelessWidget {
  const PrivacyPolicyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        title: Text('Privacy Policy', style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSection('1. Introduction', 'LexGuard AI ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and share your personal information.'),
            _buildSection('2. Information We Collect', 'We collect information you provide directly to us, such as when you create an account, upload legal documents for analysis, or contact us for support.'),
            _buildSection('3. How We Use Information', 'We use the information we collect to provide, maintain, and improve our services, including our AI-powered document analysis and legal explainers.'),
            _buildSection('4. Data Security', 'We implement industry-standard security measures to protect your documents and personal data. All documents are processed securely and encrypted at rest.'),
            _buildSection('5. Your Rights', 'You have the right to access, correct, or delete your personal information. You can manage your data settings directly within the app profile.'),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(String title, String content) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.gold)),
          const SizedBox(height: 8),
          Text(content, style: GoogleFonts.inter(fontSize: 14, color: AppColors.textSecondary, height: 1.6)),
        ],
      ),
    );
  }
}
