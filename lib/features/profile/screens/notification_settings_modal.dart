import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/features/profile/providers/profile_provider.dart';

class NotificationSettingsModal extends StatelessWidget {
  const NotificationSettingsModal({super.key});

  @override
  Widget build(BuildContext context) {
    final profile = context.watch<ProfileProvider>();

    return Container(
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 24,
        bottom: MediaQuery.of(context).padding.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Drag handle
          Center(
            child: Container(
              width: 40, height: 4,
              decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(2)),
            ),
          ),
          const SizedBox(height: 24),
          
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Notifications', style: GoogleFonts.inter(fontSize: 20, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
              if (profile.isLoading)
                const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: AppColors.gold, strokeWidth: 2)),
            ],
          ),
          const SizedBox(height: 24),
          
          // Master Toggle
          _ToggleRow(
            title: 'Push Notifications',
            subtitle: 'Enable or disable all push notifications',
            value: profile.pushNotifications,
            onChanged: (val) => context.read<ProfileProvider>().togglePushNotifications(val),
            isMaster: true,
          ),
          
          if (profile.pushNotifications) ...[
            Padding(padding: EdgeInsets.symmetric(vertical: 16), child: Divider(color: AppColors.border, height: 1)),
            
            Text('Alert Modes', style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.textSecondary)),
            const SizedBox(height: 12),
            
            // Mode Selectors
            Row(
              children: [
                _ModeButton(
                  icon: Icons.notifications_off_outlined,
                  label: 'Silent',
                  isSelected: profile.notificationMode == NotificationMode.silent,
                  onTap: () => context.read<ProfileProvider>().updateNotificationMode(NotificationMode.silent),
                ),
                const SizedBox(width: 12),
                _ModeButton(
                  icon: Icons.vibration,
                  label: 'Vibrate',
                  isSelected: profile.notificationMode == NotificationMode.vibrate,
                  onTap: () => context.read<ProfileProvider>().updateNotificationMode(NotificationMode.vibrate),
                ),
                const SizedBox(width: 12),
                _ModeButton(
                  icon: Icons.notifications_active_outlined,
                  label: 'Ring',
                  isSelected: profile.notificationMode == NotificationMode.ring,
                  onTap: () => context.read<ProfileProvider>().updateNotificationMode(NotificationMode.ring),
                ),
              ],
            ),
            
            Padding(padding: EdgeInsets.symmetric(vertical: 16), child: Divider(color: AppColors.border, height: 1)),
            
            Text('Alert Types', style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.textSecondary)),
            const SizedBox(height: 12),
            
            _ToggleRow(
              title: 'AI Analysis Completed',
              subtitle: 'Notify when document processing is done',
              value: profile.aiAnalysisAlerts,
              onChanged: (val) => context.read<ProfileProvider>().toggleAiAnalysisAlerts(val),
            ),
            const SizedBox(height: 16),
            
            _ToggleRow(
              title: 'High Risk Alerts',
              subtitle: 'Notify when high-risk clauses are detected',
              value: profile.highRiskAlerts,
              onChanged: (val) => context.read<ProfileProvider>().toggleHighRiskAlerts(val),
            ),
            const SizedBox(height: 16),
            
            _ToggleRow(
              title: 'Upload Success Alerts',
              subtitle: 'Notify when files are successfully uploaded',
              value: profile.uploadSuccessAlerts,
              onChanged: (val) => context.read<ProfileProvider>().toggleUploadSuccessAlerts(val),
            ),
          ],
        ],
      ),
    );
  }
}

class _ToggleRow extends StatelessWidget {
  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;
  final bool isMaster;

  const _ToggleRow({
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
    this.isMaster = false,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: GoogleFonts.inter(fontSize: isMaster ? 16 : 14, fontWeight: isMaster ? FontWeight.w700 : FontWeight.w600, color: AppColors.textPrimary)),
              const SizedBox(height: 4),
              Text(subtitle, style: GoogleFonts.inter(fontSize: 12, color: AppColors.textSecondary)),
            ],
          ),
        ),
        CupertinoSwitch(
          value: value,
          onChanged: onChanged,
          activeTrackColor: AppColors.gold,
          inactiveTrackColor: AppColors.cardMid,
        ),
      ],
    );
  }
}

class _ModeButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _ModeButton({
    required this.icon,
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected ? AppColors.gold.withValues(alpha: 0.15) : AppColors.cardDark,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: isSelected ? AppColors.gold : AppColors.border),
          ),
          child: Column(
            children: [
              Icon(icon, color: isSelected ? AppColors.gold : AppColors.textSecondary, size: 22),
              const SizedBox(height: 6),
              Text(
                label,
                style: GoogleFonts.inter(
                  fontSize: 12,
                  fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                  color: isSelected ? AppColors.gold : AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
