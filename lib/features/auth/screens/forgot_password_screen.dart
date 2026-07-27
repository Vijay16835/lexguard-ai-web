import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/features/auth/providers/auth_provider.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  // Step navigation: 1 = Email, 2 = OTP, 3 = New Password, 4 = Success
  int _currentStep = 1;

  final _formKey1 = GlobalKey<FormState>();
  final _formKey3 = GlobalKey<FormState>();

  final _emailCtrl = TextEditingController();
  final _newPasswordCtrl = TextEditingController();
  final _confirmPasswordCtrl = TextEditingController();

  // OTP controller boxes
  final List<TextEditingController> _otpControllers = List.generate(6, (_) => TextEditingController());
  final List<FocusNode> _otpFocusNodes = List.generate(6, (_) => FocusNode());

  bool _isLoading = false;
  bool _isEmailNotRegistered = false;
  bool _obscureNewPass = true;
  bool _obscureConfPass = true;

  // OTP Timer variables
  Timer? _timer;
  int _timerSeconds = 60;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _newPasswordCtrl.dispose();
    _confirmPasswordCtrl.dispose();
    for (var c in _otpControllers) {
      c.dispose();
    }
    for (var f in _otpFocusNodes) {
      f.dispose();
    }
    _timer?.cancel();
    super.dispose();
  }

  void _startTimer() {
    _timer?.cancel();
    setState(() {
      _timerSeconds = 60;
    });
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) return;
      setState(() {
        if (_timerSeconds > 0) {
          _timerSeconds--;
        } else {
          _timer?.cancel();
        }
      });
    });
  }

  // OTP field logic (focus jumping)
  Widget _buildOtpInputRow() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: List.generate(6, (index) {
        return Container(
          width: 48,
          height: 52,
          decoration: BoxDecoration(
            color: AppColors.cardMid,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: AppColors.border),
          ),
          child: TextField(
            controller: _otpControllers[index],
            focusNode: _otpFocusNodes[index],
            keyboardType: TextInputType.number,
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
            maxLength: 1,
            decoration: const InputDecoration(
              counterText: "",
              border: InputBorder.none,
            ),
            onChanged: (value) {
              if (value.isNotEmpty) {
                if (index < 5) {
                  FocusScope.of(context).requestFocus(_otpFocusNodes[index + 1]);
                } else {
                  _otpFocusNodes[index].unfocus();
                }
              } else {
                if (index > 0) {
                  FocusScope.of(context).requestFocus(_otpFocusNodes[index - 1]);
                }
              }
            },
          ),
        );
      }),
    );
  }

  String _getOtpString() {
    return _otpControllers.map((c) => c.text).join().trim();
  }

  // Password strength checker
  double _getPasswordStrength(String password) {
    if (password.isEmpty) return 0.0;
    double strength = 0.0;
    if (password.length >= 8) strength += 0.2;
    if (password.contains(RegExp(r'[A-Z]'))) strength += 0.2;
    if (password.contains(RegExp(r'[a-z]'))) strength += 0.2;
    if (password.contains(RegExp(r'[0-9]'))) strength += 0.2;
    if (password.contains(RegExp(r'[!@#\$&*~]'))) strength += 0.2;
    return strength;
  }

  Color _getStrengthColor(double strength) {
    if (strength <= 0.4) return AppColors.error;
    if (strength <= 0.8) return AppColors.warning;
    return AppColors.success;
  }

  String _getStrengthText(double strength) {
    if (strength <= 0.4) return "Weak";
    if (strength <= 0.8) return "Medium";
    return "Strong";
  }

  // Step 1: Send OTP request
  Future<void> _sendOtp() async {
    if (!_formKey1.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _isEmailNotRegistered = false;
    });

    final email = _emailCtrl.text.trim();

    try {
      final auth = context.read<AuthProvider>();
      final success = await auth.sendResetOtp(email).timeout(
        const Duration(seconds: 10),
        onTimeout: () => throw TimeoutException('Connection timed out. Please try again.'),
      );

      if (success) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Verification code sent to your email.'),
              backgroundColor: Colors.green,
              behavior: SnackBarBehavior.floating,
            ),
          );
          _startTimer();
          setState(() {
            _currentStep = 2;
          });
        }
      } else {
        if (mounted) {
          final errorMsg = auth.errorMessage ?? '';
          if (errorMsg.toLowerCase().contains('not registered') || errorMsg.toLowerCase().contains('not found')) {
            setState(() {
              _isEmailNotRegistered = true;
            });
          } else {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(auth.errorMessage ?? 'Failed to send OTP.'),
                backgroundColor: AppColors.error,
                behavior: SnackBarBehavior.floating,
              ),
            );
          }
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${e.toString()}'),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  // Step 2: Verify OTP request
  Future<void> _verifyOtp() async {
    final otp = _getOtpString();
    if (otp.length < 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter all 6 digits of the OTP.'),
          backgroundColor: AppColors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final auth = context.read<AuthProvider>();
      final success = await auth.verifyResetOtp(_emailCtrl.text.trim(), otp);

      if (success) {
        if (mounted) {
          setState(() {
            _currentStep = 3;
          });
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(auth.errorMessage ?? 'Invalid or expired OTP.'),
              backgroundColor: AppColors.error,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${e.toString()}'),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  // Step 3: Reset Password request
  Future<void> _resetPassword() async {
    if (!_formKey3.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
    });

    final newPass = _newPasswordCtrl.text;
    final otp = _getOtpString();

    try {
      final auth = context.read<AuthProvider>();
      final success = await auth.resetPassword(_emailCtrl.text.trim(), otp, newPass);

      if (success) {
        if (mounted) {
          setState(() {
            _currentStep = 4;
          });
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(auth.errorMessage ?? 'Failed to reset password.'),
              backgroundColor: AppColors.error,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${e.toString()}'),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isDesktop = screenWidth >= 950;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: isDesktop
          ? Row(
              children: [
                // Left side illustration panel
                Expanded(
                  flex: 5,
                  child: _buildIllustrationPanel(isDark),
                ),
                // Right side forms panel
                Expanded(
                  flex: 6,
                  child: Container(
                    color: AppColors.background,
                    child: Center(
                      child: Container(
                        constraints: const BoxConstraints(maxWidth: 460),
                        padding: const EdgeInsets.all(32),
                        child: _buildActiveFormStep(),
                      ),
                    ),
                  ),
                ),
              ],
            )
          : SafeArea(
              child: Center(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
                  child: Container(
                    constraints: const BoxConstraints(maxWidth: 460),
                    padding: const EdgeInsets.all(28),
                    decoration: BoxDecoration(
                      color: AppColors.cardDark,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: AppColors.border),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.04),
                          blurRadius: 20,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: _buildActiveFormStep(),
                  ),
                ),
              ),
            ),
    );
  }

  // Left-panel premium layout for Desktop
  Widget _buildIllustrationPanel(bool isDark) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: isDark
              ? const [Color(0xFF0F2038), Color(0xFF070E1A)]
              : const [Color(0xFFE6EEFA), Color(0xFFD0DFF2)],
        ),
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Concentric circles graphic
          ...List.generate(3, (index) {
            final double radius = 120.0 + (index * 80.0);
            return Container(
              width: radius * 2,
              height: radius * 2,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: AppColors.gold.withValues(alpha: 0.05),
                  width: 1.5,
                ),
              ),
            );
          }),
          // Main content centered
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Icon shield/lock illustration
              Stack(
                alignment: Alignment.center,
                children: [
                  Container(
                    width: 180,
                    height: 180,
                    decoration: BoxDecoration(
                      color: AppColors.goldGlow,
                      shape: BoxShape.circle,
                    ),
                  ).animate(onPlay: (c) => c.repeat(reverse: true)).scale(
                        begin: const Offset(0.95, 0.95),
                        end: const Offset(1.05, 1.05),
                        duration: 2000.ms,
                        curve: Curves.easeInOut,
                      ),
                  const Icon(
                    Icons.security_rounded,
                    size: 84,
                    color: AppColors.gold,
                  ),
                  Positioned(
                    top: 14,
                    right: 14,
                    child: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: const BoxDecoration(
                        color: AppColors.navy,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.lock_rounded,
                        color: AppColors.goldLight,
                        size: 20,
                      ),
                    ),
                  ),
                  Positioned(
                    bottom: 14,
                    left: 14,
                    child: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: const BoxDecoration(
                        color: AppColors.navy,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.mail_rounded,
                        color: AppColors.goldLight,
                        size: 20,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 48),
              Text(
                'LexGuard Cryptographic Recovery',
                style: GoogleFonts.inter(
                  fontSize: 22,
                  fontWeight: FontWeight.w800,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 12),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 48),
                child: Text(
                  'Restore security access using verified 6-digit OTP codes and automated security protocols.',
                  style: GoogleFonts.inter(
                    fontSize: 13.5,
                    color: AppColors.textSecondary,
                    height: 1.5,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // Active step router
  Widget _buildActiveFormStep() {
    switch (_currentStep) {
      case 1:
        return _buildStep1Email();
      case 2:
        return _buildStep2Otp();
      case 3:
        return _buildStep3NewPassword();
      case 4:
        return _buildStep4Success();
      default:
        return _buildStep1Email();
    }
  }

  // Step 1 Widget: Email Input
  Widget _buildStep1Email() {
    return Form(
      key: _formKey1,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              IconButton(
                onPressed: () => Navigator.pop(context),
                icon: Icon(Icons.arrow_back_ios_new_rounded, color: AppColors.textPrimary, size: 18),
              ),
              const SizedBox(width: 8),
              Text(
                'Reset Password',
                style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
              ),
            ],
          ),
          const SizedBox(height: 36),
          Text(
            'Forgot Password?',
            style: GoogleFonts.inter(fontSize: 28, fontWeight: FontWeight.w800, color: AppColors.textPrimary),
          ),
          const SizedBox(height: 8),
          Text(
            'Enter your registered email below to receive a 6-digit OTP code to verify and reset.',
            style: GoogleFonts.inter(fontSize: 13, color: AppColors.textSecondary, height: 1.5),
          ),
          const SizedBox(height: 36),
          if (_isEmailNotRegistered) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.errorBg,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.error.withValues(alpha: 0.2)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.error_outline_rounded, color: AppColors.error, size: 20),
                      const SizedBox(width: 8),
                      Text(
                        'Email is not registered.',
                        style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.error),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'No account exists for "${_emailCtrl.text.trim()}". Check spelling or register below.',
                    style: GoogleFonts.inter(fontSize: 12.5, color: AppColors.textPrimary, height: 1.4),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => setState(() => _isEmailNotRegistered = false),
                          style: OutlinedButton.styleFrom(
                            side: BorderSide(color: AppColors.border),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          child: Text('Retry', style: GoogleFonts.inter(color: AppColors.textPrimary)),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () {
                            Navigator.pushReplacementNamed(
                              context,
                              '/signup',
                              arguments: {'email': _emailCtrl.text.trim()},
                            );
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.gold,
                            foregroundColor: AppColors.navy,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            elevation: 0,
                          ),
                          child: Text('Register', style: GoogleFonts.inter(fontWeight: FontWeight.w700)),
                        ),
                      ),
                    ],
                  )
                ],
              ),
            ),
          ] else ...[
            // Email Input Box
            Text(
              'Email Address',
              style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
            ),
            const SizedBox(height: 8),
            Container(
              decoration: BoxDecoration(
                color: AppColors.inputBg,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: TextFormField(
                controller: _emailCtrl,
                style: GoogleFonts.inter(color: AppColors.textPrimary),
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(
                  hintText: 'e.g. workspace@firm.com',
                  hintStyle: GoogleFonts.inter(color: AppColors.textHint, fontSize: 13.5),
                  prefixIcon: Icon(Icons.email_outlined, color: AppColors.textHint, size: 20),
                  border: InputBorder.none,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                ),
                validator: (v) {
                  if (v == null || v.isEmpty) return 'Email is required';
                  if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(v)) {
                    return 'Please enter a valid email';
                  }
                  return null;
                },
              ),
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _sendOtp,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.gold,
                  foregroundColor: AppColors.navy,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  elevation: 0,
                ),
                child: _isLoading
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: AppColors.navy, strokeWidth: 2))
                    : Text('Send OTP', style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 15)),
              ),
            ),
          ],
        ],
      ),
    ).animate().fadeIn(duration: 300.ms);
  }

  // Step 2 Widget: OTP Input Form
  Widget _buildStep2Otp() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          children: [
            IconButton(
              onPressed: () => setState(() => _currentStep = 1),
              icon: Icon(Icons.arrow_back_ios_new_rounded, color: AppColors.textPrimary, size: 18),
            ),
            const SizedBox(width: 8),
            Text(
              'Enter Security Code',
              style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
            ),
          ],
        ),
        const SizedBox(height: 36),
        Text(
          'Security Verification',
          style: GoogleFonts.inter(fontSize: 28, fontWeight: FontWeight.w800, color: AppColors.textPrimary),
        ),
        const SizedBox(height: 8),
        Text(
          'We sent a 6-digit security code to your email. Enter the code to continue.',
          style: GoogleFonts.inter(fontSize: 13, color: AppColors.textSecondary, height: 1.5),
        ),
        const SizedBox(height: 32),
        // 6-digit OTP fields
        _buildOtpInputRow(),
        const SizedBox(height: 28),
        // Timer countdown / Resend button
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              _timerSeconds > 0 ? 'Resend code in ${_timerSeconds}s' : 'Didn\'t receive the code?',
              style: GoogleFonts.inter(fontSize: 13, color: AppColors.textSecondary, fontWeight: FontWeight.w500),
            ),
            TextButton(
              onPressed: _timerSeconds == 0 && !_isLoading ? _sendOtp : null,
              child: Text(
                'Resend OTP',
                style: GoogleFonts.inter(
                  color: _timerSeconds == 0 ? AppColors.gold : AppColors.textHint,
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 32),
        SizedBox(
          width: double.infinity,
          height: 52,
          child: ElevatedButton(
            onPressed: _isLoading ? null : _verifyOtp,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.gold,
              foregroundColor: AppColors.navy,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              elevation: 0,
            ),
            child: _isLoading
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: AppColors.navy, strokeWidth: 2))
                : Text('Verify Code', style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 15)),
          ),
        ),
      ],
    ).animate().fadeIn(duration: 300.ms);
  }

  // Step 3 Widget: New Password Input
  Widget _buildStep3NewPassword() {
    final double strength = _getPasswordStrength(_newPasswordCtrl.text);

    return Form(
      key: _formKey3,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'New Credentials',
            style: GoogleFonts.inter(fontSize: 28, fontWeight: FontWeight.w800, color: AppColors.textPrimary),
          ),
          const SizedBox(height: 8),
          Text(
            'Create a strong password to lock and secure your account statistics and docs.',
            style: GoogleFonts.inter(fontSize: 13, color: AppColors.textSecondary, height: 1.5),
          ),
          const SizedBox(height: 28),

          // New Password Field
          Text(
            'New Password',
            style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
          ),
          const SizedBox(height: 8),
          Container(
            decoration: BoxDecoration(
              color: AppColors.inputBg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: TextFormField(
              controller: _newPasswordCtrl,
              obscureText: _obscureNewPass,
              style: GoogleFonts.inter(color: AppColors.textPrimary),
              onChanged: (_) => setState(() {}),
              decoration: InputDecoration(
                hintText: 'Enter new password',
                hintStyle: GoogleFonts.inter(color: AppColors.textHint, fontSize: 13.5),
                prefixIcon: Icon(Icons.lock_outline_rounded, color: AppColors.textHint, size: 20),
                suffixIcon: IconButton(
                  icon: Icon(_obscureNewPass ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: AppColors.textHint, size: 20),
                  onPressed: () => setState(() => _obscureNewPass = !_obscureNewPass),
                ),
                border: InputBorder.none,
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              ),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Password is required';
                if (v.length < 8) return 'Password must be at least 8 characters';
                return null;
              },
            ),
          ),

          const SizedBox(height: 16),

          // Password Strength Visual Indicator
          if (_newPasswordCtrl.text.isNotEmpty) ...[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Password Strength:',
                  style: GoogleFonts.inter(fontSize: 11.5, color: AppColors.textSecondary, fontWeight: FontWeight.w500),
                ),
                Text(
                  _getStrengthText(strength),
                  style: GoogleFonts.inter(fontSize: 11.5, color: _getStrengthColor(strength), fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: strength,
                minHeight: 6,
                backgroundColor: AppColors.border,
                valueColor: AlwaysStoppedAnimation<Color>(_getStrengthColor(strength)),
              ),
            ),
            const SizedBox(height: 20),
          ],

          // Confirm Password Field
          Text(
            'Confirm Password',
            style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
          ),
          const SizedBox(height: 8),
          Container(
            decoration: BoxDecoration(
              color: AppColors.inputBg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: TextFormField(
              controller: _confirmPasswordCtrl,
              obscureText: _obscureConfPass,
              style: GoogleFonts.inter(color: AppColors.textPrimary),
              decoration: InputDecoration(
                hintText: 'Re-enter your password',
                hintStyle: GoogleFonts.inter(color: AppColors.textHint, fontSize: 13.5),
                prefixIcon: Icon(Icons.lock_outline_rounded, color: AppColors.textHint, size: 20),
                suffixIcon: IconButton(
                  icon: Icon(_obscureConfPass ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: AppColors.textHint, size: 20),
                  onPressed: () => setState(() => _obscureConfPass = !_obscureConfPass),
                ),
                border: InputBorder.none,
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              ),
              validator: (v) {
                if (v != _newPasswordCtrl.text) {
                  return 'Passwords do not match';
                }
                return null;
              },
            ),
          ),

          const SizedBox(height: 36),

          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton(
              onPressed: _isLoading ? null : _resetPassword,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.gold,
                foregroundColor: AppColors.navy,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                elevation: 0,
              ),
              child: _isLoading
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: AppColors.navy, strokeWidth: 2))
                  : Text('Save and Reset', style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 15)),
            ),
          ),
        ],
      ),
    ).animate().fadeIn(duration: 300.ms);
  }

  // Step 4 Widget: Success flow finish
  Widget _buildStep4Success() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.all(24),
          decoration: const BoxDecoration(
            color: AppColors.successBg,
            shape: BoxShape.circle,
          ),
          child: const Icon(
            Icons.check_circle_outline_rounded,
            size: 64,
            color: AppColors.success,
          ),
        ).animate().scale(curve: Curves.elasticOut, duration: 600.ms),
        const SizedBox(height: 32),
        Text(
          'Password Restored',
          style: GoogleFonts.inter(fontSize: 26, fontWeight: FontWeight.w800, color: AppColors.textPrimary),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 10),
        Text(
          'Your account credentials have been successfully updated. You can now use your new password to sign in.',
          style: GoogleFonts.inter(fontSize: 13.5, color: AppColors.textSecondary, height: 1.5),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 40),
        SizedBox(
          width: double.infinity,
          height: 52,
          child: ElevatedButton(
            onPressed: () {
              Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.gold,
              foregroundColor: AppColors.navy,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              elevation: 0,
            ),
            child: Text('Back to Login', style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 15)),
          ),
        ),
      ],
    ).animate().fadeIn(duration: 300.ms);
  }
}
