import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/features/home/screens/home_screen.dart';
import 'package:lexguard_ai/features/history/screens/history_screen.dart';
import 'package:lexguard_ai/features/chat/screens/chat_screen.dart';
import 'package:lexguard_ai/features/profile/screens/profile_screen.dart';
import 'package:lexguard_ai/features/upload/screens/upload_screen.dart';
import 'package:provider/provider.dart';
import 'package:lexguard_ai/features/profile/providers/profile_provider.dart';

class MainShell extends StatefulWidget {
  final Widget child;
  const MainShell({super.key, required this.child});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  final _screens = const [
    HomeScreen(),
    HistoryScreen(),
    ChatScreen(),
    ProfileScreen(),
  ];

  void _onNavTap(int index) {
    if (index == 1) {
      // Upload tap — navigate to full upload screen
      Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => const UploadScreen()),
      );
      return;
    }
    final screenIndex = index < 2 ? index : index - 1;
    setState(() => _currentIndex = screenIndex);
  }

  @override
  Widget build(BuildContext context) {
    context.watch<ProfileProvider>();
    // Map screen index back to nav index for active indicator
    final navIndex = _currentIndex < 1 ? _currentIndex : _currentIndex + 1;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: _BottomNav(
        currentIndex: navIndex,
        onTap: _onNavTap,
      ),
    );
  }
}

class _BottomNav extends StatelessWidget {
  final int currentIndex;
  final Function(int) onTap;
  const _BottomNav({required this.currentIndex, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.navBar,
        border: Border(top: BorderSide(color: AppColors.border, width: 0.5)),
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.4), blurRadius: 20, offset: const Offset(0, -5)),
        ],
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _NavItem(icon: Icons.home_outlined, activeIcon: Icons.home_rounded, label: 'Home', index: 0, currentIndex: currentIndex, onTap: onTap),
              _NavItem(icon: Icons.add_circle_outline, activeIcon: Icons.add_circle_rounded, label: 'Upload', index: 1, currentIndex: currentIndex, onTap: onTap, isUpload: true),
              _NavItem(icon: Icons.history_outlined, activeIcon: Icons.history, label: 'History', index: 2, currentIndex: currentIndex, onTap: onTap),
              _NavItem(icon: Icons.chat_bubble_outline, activeIcon: Icons.chat_bubble_rounded, label: 'Chat', index: 3, currentIndex: currentIndex, onTap: onTap),
              _NavItem(icon: Icons.person_outline, activeIcon: Icons.person_rounded, label: 'Profile', index: 4, currentIndex: currentIndex, onTap: onTap),
            ],
          ),
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final IconData activeIcon;
  final String label;
  final int index;
  final int currentIndex;
  final Function(int) onTap;
  final bool isUpload;

  const _NavItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
    required this.index,
    required this.currentIndex,
    required this.onTap,
    this.isUpload = false,
  });

  @override
  Widget build(BuildContext context) {
    final isActive = currentIndex == index;

    if (isUpload) {
      return GestureDetector(
        onTap: () => onTap(index),
        child: Container(
          width: 56, height: 56,
          decoration: BoxDecoration(
            gradient: const LinearGradient(colors: AppColors.goldGradient),
            shape: BoxShape.circle,
            boxShadow: [BoxShadow(color: AppColors.gold.withValues(alpha: 0.4), blurRadius: 16, spreadRadius: 2)],
          ),
          child: const Icon(Icons.add, color: AppColors.navy, size: 28),
        ),
      );
    }

    return GestureDetector(
      onTap: () => onTap(index),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isActive ? AppColors.goldGlow : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(isActive ? activeIcon : icon, color: isActive ? AppColors.gold : AppColors.textHint, size: 24),
            const SizedBox(height: 4),
            Text(label, style: GoogleFonts.inter(fontSize: 10, fontWeight: isActive ? FontWeight.w600 : FontWeight.w400, color: isActive ? AppColors.gold : AppColors.textHint)),
          ],
        ),
      ),
    );
  }
}
