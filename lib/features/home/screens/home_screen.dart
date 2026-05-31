import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/features/home/providers/home_provider.dart';
import 'package:lexguard_ai/features/auth/providers/auth_provider.dart';
import 'package:lexguard_ai/features/profile/providers/profile_provider.dart';
import 'package:lexguard_ai/widgets/common/theme_selection_modal.dart';

import 'package:lexguard_ai/widgets/cards/document_card.dart';
import 'package:lexguard_ai/widgets/cards/stat_card.dart';
import 'package:lexguard_ai/features/upload/screens/upload_screen.dart';
import 'package:lexguard_ai/features/analysis/screens/analysis_screen.dart';
import 'package:lexguard_ai/features/chat/screens/chat_screen.dart';
import 'package:lexguard_ai/features/summary/screens/summary_screen.dart';
import 'package:lexguard_ai/features/profile/screens/profile_screen.dart';
import 'package:lexguard_ai/features/profile/screens/notification_settings_modal.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<HomeProvider>().loadDashboard();
    });
  }

  @override
  Widget build(BuildContext context) {
    final home = context.watch<HomeProvider>();
    final auth = context.watch<AuthProvider>();
    final profile = context.watch<ProfileProvider>();
    final user = auth.user;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: RefreshIndicator(
        color: AppColors.gold,
        backgroundColor: AppColors.cardDark,
        onRefresh: () => context.read<HomeProvider>().loadDashboard(),
        child: CustomScrollView(
          slivers: [
            // Header
            SliverToBoxAdapter(
              child: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [Color(0xFF0A1628), Color(0xFF080F1E)],
                  ),
                ),
                child: SafeArea(
                  bottom: false,
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Good morning,',
                                style: GoogleFonts.inter(
                                  fontSize: 13,
                                  color: AppColors.textHint,
                                ),
                              ),
                              Text(
                                user?.firstName ?? 'Alex',
                                style: GoogleFonts.inter(
                                  fontSize: 24,
                                  fontWeight: FontWeight.w800,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                            ],
                          ),
                        ),
                        // Theme Selector Button
                        GestureDetector(
                          onTap: () {
                            showModalBottomSheet(
                              context: context,
                              isScrollControlled: true,
                              backgroundColor: Colors.transparent,
                              builder: (_) => const ThemeSelectionModal(),
                            );
                          },
                          child: Container(
                            width: 44,
                            height: 44,
                            margin: const EdgeInsets.only(right: 12),
                            decoration: BoxDecoration(
                              color: AppColors.cardDark,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: AppColors.border),
                            ),
                            child: Center(
                              child: Icon(
                                profile.themeMode == ThemeMode.system
                                    ? Icons.brightness_auto_outlined
                                    : profile.themeMode == ThemeMode.dark
                                        ? Icons.dark_mode_outlined
                                        : Icons.light_mode_outlined,
                                color: AppColors.textPrimary,
                                size: 22,
                              ),
                            ),
                          ),
                        ),
                        // Notification Bell
                        GestureDetector(
                          onTap: () {
                            showModalBottomSheet(
                              context: context,
                              isScrollControlled: true,
                              backgroundColor: Colors.transparent,
                              builder: (_) => const NotificationSettingsModal(),
                            );
                          },
                          child: Container(
                            width: 44,
                            height: 44,
                            margin: const EdgeInsets.only(right: 12),
                            decoration: BoxDecoration(
                              color: AppColors.cardDark,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: AppColors.border),
                            ),
                            child: Stack(
                              children: [
                                Center(
                                  child: Icon(Icons.notifications_outlined,
                                      color: AppColors.textPrimary, size: 22),
                                ),
                                Positioned(
                                  top: 8,
                                  right: 8,
                                  child: Container(
                                    width: 8,
                                    height: 8,
                                    decoration: const BoxDecoration(
                                      color: AppColors.gold,
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        // Avatar
                        GestureDetector(
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (_) => const ProfileScreen()),
                            );
                          },
                          child: Container(
                            width: 44,
                            height: 44,
                            decoration: const BoxDecoration(
                              gradient: LinearGradient(colors: AppColors.goldGradient),
                              shape: BoxShape.circle,
                            ),
                            child: Center(
                              child: Text(
                                user?.initials ?? 'AJ',
                                style: GoogleFonts.inter(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w800,
                                  color: AppColors.navy,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ).animate().fadeIn(duration: 500.ms),
            ),

            // Hero Card
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                child: _HeroCard(),
              ).animate(delay: 100.ms).fadeIn().slideY(begin: 0.2, end: 0),
            ),

            // Stats Row
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
                child: home.isLoading
                    ? _StatsShimmer()
                    : GridView.count(
                        crossAxisCount: 2,
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        crossAxisSpacing: 12,
                        mainAxisSpacing: 12,
                        childAspectRatio: 1.7,
                        children: [
                          StatCard(
                            label: 'Total Documents',
                            value: '${home.totalDocuments}',
                            icon: Icons.description_outlined,
                            color: AppColors.gold,
                          ),
                          StatCard(
                            label: 'High Risk',
                            value: '${home.highRiskContracts}',
                            icon: Icons.warning_amber_rounded,
                            color: AppColors.highRisk,
                          ),
                          StatCard(
                            label: 'Pending Reviews',
                            value: '${home.pendingReviews}',
                            icon: Icons.pending_actions_outlined,
                            color: AppColors.info,
                          ),
                          StatCard(
                            label: 'AI Accuracy',
                            value: '${home.aiAccuracy}%',
                            icon: Icons.psychology_outlined,
                            color: AppColors.success,
                          ),
                        ],
                      ),
              ).animate(delay: 200.ms).fadeIn().slideY(begin: 0.2, end: 0),
            ),

            // Quick Actions
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Quick Actions',
                      style: GoogleFonts.inter(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 14),
                    SizedBox(
                      height: 100,
                      child: ListView(
                        scrollDirection: Axis.horizontal,
                        children: [
                          _QuickActionItem(
                            icon: Icons.upload_file_outlined,
                            label: 'Upload\nDocument',
                            color: AppColors.gold,
                            onTap: () => showModalBottomSheet(
                              context: context,
                              isScrollControlled: true,
                              backgroundColor: Colors.transparent,
                              builder: (_) => const UploadScreen(),
                            ),
                          ),
                          _QuickActionItem(
                            icon: Icons.psychology_outlined,
                            label: 'AI\nAnalyze',
                            color: const Color(0xFF3498DB),
                            onTap: () => Navigator.push(context,
                                MaterialPageRoute(builder: (_) => const AnalysisScreen())),
                          ),
                          _QuickActionItem(
                            icon: Icons.chat_bubble_outline_rounded,
                            label: 'Chat with\nDocument',
                            color: const Color(0xFF2ECC71),
                            onTap: () => Navigator.push(context,
                                MaterialPageRoute(builder: (_) => const ChatScreen())),
                          ),
                          _QuickActionItem(
                            icon: Icons.summarize_outlined,
                            label: 'Generate\nSummary',
                            color: const Color(0xFF9B59B6),
                            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SummaryScreen())),
                          ),
                          _QuickActionItem(
                            icon: Icons.shield_outlined,
                            label: 'Risk\nDetection',
                            color: AppColors.highRisk,
                            onTap: () {},
                          ),
                          _QuickActionItem(
                            icon: Icons.compare_outlined,
                            label: 'Compare\nContracts',
                            color: const Color(0xFFF39C12),
                            onTap: () {},
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ).animate(delay: 300.ms).fadeIn().slideY(begin: 0.2, end: 0),
            ),

            // Recent Documents Header
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 28, 20, 14),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Recent Documents',
                      style: GoogleFonts.inter(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    TextButton(
                      onPressed: () {},
                      child: Text(
                        'See All',
                        style: GoogleFonts.inter(
                          color: AppColors.gold,
                          fontWeight: FontWeight.w600,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
              ).animate(delay: 350.ms).fadeIn(),
            ),

            // Document List
            if (home.isLoading)
              SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, i) => const _DocumentShimmer(),
                  childCount: 3,
                ),
              )
            else if (home.errorMessage != null)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(color: AppColors.cardDark, borderRadius: BorderRadius.circular(16), border: Border.all(color: AppColors.error)),
                    child: Column(
                      children: [
                        const Icon(Icons.error_outline, color: AppColors.error, size: 32),
                        const SizedBox(height: 12),
                        Text(home.errorMessage!, textAlign: TextAlign.center, style: GoogleFonts.inter(color: AppColors.textPrimary)),
                        const SizedBox(height: 12),
                        ElevatedButton(
                          onPressed: () => context.read<HomeProvider>().loadDashboard(),
                          style: ElevatedButton.styleFrom(backgroundColor: AppColors.error.withValues(alpha: 0.1), foregroundColor: AppColors.error),
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                ),
              )
            else if (home.recentDocuments.isEmpty)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 40),
                  child: Column(
                    children: [
                      Container(
                        width: 80, height: 80,
                        decoration: BoxDecoration(color: AppColors.cardDark, shape: BoxShape.circle, border: Border.all(color: AppColors.border)),
                        child: Icon(Icons.folder_open_outlined, color: AppColors.textSecondary, size: 32),
                      ),
                      const SizedBox(height: 16),
                      Text('No documents yet', style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
                      const SizedBox(height: 8),
                      Text('Upload a document to get started with AI analysis.', textAlign: TextAlign.center, style: GoogleFonts.inter(fontSize: 13, color: AppColors.textSecondary)),
                    ],
                  ),
                ).animate().fadeIn(),
              )
            else
              SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, i) => Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
                    child: DocumentCard(
                      document: home.recentDocuments[i],
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const AnalysisScreen()),
                      ),
                    ),
                  ).animate(delay: Duration(milliseconds: 400 + i * 80)).fadeIn().slideX(begin: 0.1, end: 0),
                  childCount: home.recentDocuments.take(4).length,
                ),
              ),

            const SliverToBoxAdapter(child: SizedBox(height: 100)),
          ],
        ),
      ),
    );
  }
}

class _HeroCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF1E3A6E), Color(0xFF0D1F3C)],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
        boxShadow: [
          BoxShadow(
            color: AppColors.gold.withValues(alpha: 0.08),
            blurRadius: 24,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.goldGlow,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    '⚡ AI-Powered',
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: AppColors.gold,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  'Intelligent Legal\nDocument Review',
                  style: GoogleFonts.inter(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: AppColors.textPrimary,
                    height: 1.2,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Analyze contracts, detect risks\nand extract key clauses instantly.',
                  style: GoogleFonts.inter(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => showModalBottomSheet(
                    context: context,
                    isScrollControlled: true,
                    backgroundColor: Colors.transparent,
                    builder: (_) => const UploadScreen(),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.gold,
                    foregroundColor: AppColors.navy,
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                    elevation: 0,
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.bolt, size: 16),
                      const SizedBox(width: 6),
                      Text(
                        'Quick Analyze',
                        style: GoogleFonts.inter(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Container(
            width: 90,
            height: 90,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.gold.withValues(alpha: 0.1),
              border: Border.all(color: AppColors.gold.withValues(alpha: 0.2), width: 2),
            ),
            child: const Icon(Icons.shield_outlined, size: 48, color: AppColors.gold),
          ),
        ],
      ),
    );
  }
}

class _QuickActionItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _QuickActionItem({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 88,
        margin: const EdgeInsets.only(right: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withValues(alpha: 0.2)),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 26),
            const SizedBox(height: 6),
            Text(
              label,
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: AppColors.textSecondary,
                height: 1.3,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatsShimmer extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.7,
      children: List.generate(4, (_) => Container(
        decoration: BoxDecoration(
          color: AppColors.cardDark,
          borderRadius: BorderRadius.circular(16),
        ),
      )),
    );
  }
}

class _DocumentShimmer extends StatelessWidget {
  const _DocumentShimmer();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
      child: Container(
        height: 80,
        decoration: BoxDecoration(
          color: AppColors.cardDark,
          borderRadius: BorderRadius.circular(16),
        ),
      ),
    );
  }
}
