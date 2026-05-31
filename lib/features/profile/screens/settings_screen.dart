import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/features/auth/providers/auth_provider.dart';
import 'package:lexguard_ai/features/profile/providers/profile_provider.dart';
import 'package:lexguard_ai/features/profile/screens/privacy_policy_screen.dart';
import 'package:lexguard_ai/features/profile/screens/terms_conditions_screen.dart';
import 'package:lexguard_ai/features/profile/screens/about_screen.dart';
import 'package:lexguard_ai/widgets/common/theme_selection_modal.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final profile = context.watch<ProfileProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        leading: IconButton(
          onPressed: () => Navigator.pop(context),
          icon: Container(padding: EdgeInsets.all(8), decoration: BoxDecoration(color: AppColors.cardDark, borderRadius: BorderRadius.circular(10), border: Border.all(color: AppColors.border)), child: Icon(Icons.arrow_back_ios_new, size: 16, color: AppColors.textPrimary)),
        ),
        title: Text('Settings', style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
      ),
      body: Stack(
        children: [
          SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _SectionHeader('Appearance'),
                _SelectionSetting(
                  icon: Icons.palette_outlined,
                  label: 'App Theme',
                  subtitle: profile.themeModeName,
                  onTap: () {
                    showModalBottomSheet(
                      context: context,
                      isScrollControlled: true,
                      backgroundColor: Colors.transparent,
                      builder: (_) => const ThemeSelectionModal(),
                    );
                  },
                ),
                const SizedBox(height: 16),

                _SectionHeader('Notifications'),
                _ToggleSetting(
                  icon: Icons.notifications_outlined, 
                  label: 'Push Notifications', 
                  subtitle: 'Analysis complete, risk alerts', 
                  value: profile.notificationsEnabled, 
                  onChanged: (v) {
                    context.read<ProfileProvider>().toggleNotifications(v);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Notifications ${v ? 'Enabled' : 'Disabled'}'), duration: const Duration(seconds: 1)),
                    );
                  }
                ),
                const SizedBox(height: 16),

                _SectionHeader('Language & Region'),
                _DropdownSetting(
                  icon: Icons.language_outlined,
                  label: 'Language',
                  subtitle: profile.selectedLanguage,
                  options: const ['English', 'Spanish', 'French', 'German', 'Arabic', 'Hindi'],
                  value: profile.selectedLanguage,
                  onChanged: (v) {
                    if (v != null) {
                      context.read<ProfileProvider>().setLanguage(v);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Language set to $v'), duration: const Duration(seconds: 1)),
                      );
                    }
                  },
                ),
                const SizedBox(height: 16),

                _SectionHeader('AI Analysis'),
                _DropdownSetting(
                  icon: Icons.psychology_outlined,
                  label: 'AI Model',
                  subtitle: profile.aiModel,
                  options: const ['LexGuard AI Engine v2.0', 'GPT-4o (Premium)', 'Gemini 1.5 Pro', 'Claude 3.5 Sonnet'],
                  value: profile.aiModel,
                  onChanged: (v) {
                    if (v != null) {
                      context.read<ProfileProvider>().setAiModel(v);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('AI Model set to $v'), duration: const Duration(seconds: 1)),
                      );
                    }
                  },
                ),
                _DropdownSetting(
                  icon: Icons.speed_outlined,
                  label: 'Analysis Depth',
                  subtitle: profile.analysisDepth,
                  options: const ['Standard', 'Comprehensive', 'Legal-Grade'],
                  value: profile.analysisDepth,
                  onChanged: (v) {
                    if (v != null) {
                      context.read<ProfileProvider>().setAnalysisDepth(v);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Analysis Depth set to $v'), duration: const Duration(seconds: 1)),
                      );
                    }
                  },
                ),
                const SizedBox(height: 16),

                _SectionHeader('Privacy & Security'),
                _SelectionSetting(
                  icon: Icons.privacy_tip_outlined, 
                  label: 'Privacy Policy', 
                  subtitle: 'Last updated Jan 2025', 
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PrivacyPolicyScreen())),
                ),
                _SelectionSetting(
                  icon: Icons.article_outlined, 
                  label: 'Terms & Conditions', 
                  subtitle: 'Legal terms of service', 
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const TermsConditionsScreen())),
                ),
                _SelectionSetting(
                  icon: Icons.delete_outline_rounded, 
                  label: 'Delete Account', 
                  subtitle: 'Permanently delete your account', 
                  onTap: () => _showDeleteDialog(context), 
                  isDestructive: true,
                ),
                const SizedBox(height: 16),

                _SectionHeader('About'),
                _SelectionSetting(
                  icon: Icons.info_outline, 
                  label: 'About App', 
                  subtitle: 'Version 1.0.0 (Build 1)', 
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AboutScreen())),
                ),
                _SelectionSetting(
                  icon: Icons.star_outline_rounded, 
                  label: 'Logout', 
                  subtitle: 'Sign out from your account', 
                  onTap: () => _showLogoutDialog(context),
                  isDestructive: true,
                ),

                const SizedBox(height: 32),
              ],
            ),
          ),
          if (profile.isLoading)
            Container(
              color: Colors.black.withValues(alpha: 0.5),
              child: const Center(child: CircularProgressIndicator(color: AppColors.gold)),
            ),
        ],
      ),
    );
  }

  void _showLogoutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.cardDark,
        title: Text('Logout', style: GoogleFonts.inter(color: AppColors.textPrimary)),
        content: Text('Are you sure you want to logout?', style: GoogleFonts.inter(color: AppColors.textSecondary)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text('Cancel', style: GoogleFonts.inter(color: AppColors.textHint))),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              context.read<AuthProvider>().logout();
              context.read<ProfileProvider>().logout().then((_) {
                if (context.mounted) {
                  Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
                }
              });
            },
            child: const Text('Logout', style: TextStyle(color: AppColors.error)),
          ),
        ],
      ),
    );
  }

  void _showDeleteDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.cardDark,
        title: const Text('Delete Account', style: TextStyle(color: AppColors.error)),
        content: Text('This action is irreversible. All your documents and data will be permanently deleted from our servers.', style: GoogleFonts.inter(color: AppColors.textSecondary)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text('Cancel', style: GoogleFonts.inter(color: AppColors.textHint))),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              context.read<ProfileProvider>().deleteAccount().then((_) {
                if (context.mounted) {
                  Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
                }
              });
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.error),
            child: const Text('Delete permanently', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader(this.title);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Text(title, style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.gold, letterSpacing: 0.5)),
    );
  }
}

class _ToggleSetting extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final bool value;
  final Function(bool) onChanged;

  const _ToggleSetting({required this.icon, required this.label, required this.subtitle, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: AppColors.cardDark, borderRadius: BorderRadius.circular(14), border: Border.all(color: AppColors.border)),
      child: Row(children: [
        Container(width: 38, height: 38, decoration: BoxDecoration(color: AppColors.navyAccent, borderRadius: BorderRadius.circular(10)), child: Icon(icon, color: AppColors.gold, size: 20)),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
          Text(subtitle, style: GoogleFonts.inter(fontSize: 12, color: AppColors.textSecondary)),
        ])),
        Switch(value: value, onChanged: onChanged, activeThumbColor: AppColors.gold, activeTrackColor: AppColors.goldGlow),
      ]),
    );
  }
}

class _DropdownSetting extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final List<String> options;
  final String value;
  final Function(String?) onChanged;

  const _DropdownSetting({required this.icon, required this.label, required this.subtitle, required this.options, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: AppColors.cardDark, borderRadius: BorderRadius.circular(14), border: Border.all(color: AppColors.border)),
      child: Row(children: [
        Container(width: 38, height: 38, decoration: BoxDecoration(color: AppColors.navyAccent, borderRadius: BorderRadius.circular(10)), child: Icon(icon, color: AppColors.gold, size: 20)),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
          Text(subtitle, style: GoogleFonts.inter(fontSize: 12, color: AppColors.textSecondary)),
        ])),
        DropdownButton<String>(
          value: value,
          dropdownColor: AppColors.cardDark,
          style: GoogleFonts.inter(fontSize: 12, color: AppColors.gold),
          underline: const SizedBox(),
          icon: Icon(Icons.keyboard_arrow_down, color: AppColors.textHint, size: 18),
          items: options.map((o) => DropdownMenuItem(value: o, child: Text(o))).toList(),
          onChanged: onChanged,
        ),
      ]),
    );
  }
}

class _SelectionSetting extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final VoidCallback onTap;
  final bool isDestructive;

  const _SelectionSetting({required this.icon, required this.label, required this.subtitle, required this.onTap, this.isDestructive = false});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: AppColors.cardDark, borderRadius: BorderRadius.circular(14), border: Border.all(color: isDestructive ? AppColors.error.withValues(alpha: 0.3) : AppColors.border)),
        child: Row(children: [
          Container(width: 38, height: 38, decoration: BoxDecoration(color: isDestructive ? AppColors.errorBg : AppColors.navyAccent, borderRadius: BorderRadius.circular(10)), child: Icon(icon, color: isDestructive ? AppColors.error : AppColors.gold, size: 20)),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(label, style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600, color: isDestructive ? AppColors.error : AppColors.textPrimary)),
            Text(subtitle, style: GoogleFonts.inter(fontSize: 12, color: AppColors.textSecondary)),
          ])),
          Icon(Icons.chevron_right, color: AppColors.textHint, size: 20),
        ]),
      ),
    );
  }
}
