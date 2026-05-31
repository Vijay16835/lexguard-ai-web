import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';

class TermsConditionsScreen extends StatelessWidget {
  const TermsConditionsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        title: Text('Terms & Conditions', style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSection('1. Acceptance of Terms', 'By accessing or using LexGuard AI, you agree to be bound by these Terms and Conditions and all applicable laws and regulations.'),
            _buildSection('2. AI Disclaimer', 'LexGuard AI provides automated legal document analysis powered by artificial intelligence. This is NOT a substitute for professional legal advice from a qualified attorney.'),
            _buildSection('3. User Responsibilities', 'You are responsible for the documents you upload and the decisions you make based on the AI analysis. We recommend verifying any critical findings with legal counsel.'),
            _buildSection('4. Prohibited Uses', 'You may not use LexGuard AI for any illegal purposes or to analyze documents that you do not have the right to process.'),
            _buildSection('5. Termination', 'We reserve the right to terminate or suspend your access to the service at our sole discretion, without notice, for conduct that we believe violates these Terms.'),
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
