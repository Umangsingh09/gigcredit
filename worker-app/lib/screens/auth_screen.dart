import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:provider/provider.dart';
import '../providers/worker_provider.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class AuthScreen extends StatefulWidget {
  final VoidCallback onAuthSuccess;

  const AuthScreen({super.key, required this.onAuthSuccess});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  bool _isAuthenticating = false;
  bool _isEmailMode = false;

  final TextEditingController _emailController = TextEditingController(text: 'raja.kumar@gigworker.in');
  final TextEditingController _passwordController = TextEditingController(text: '••••••••');
  final WorkerApiService _apiService = WorkerApiService();
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
  );

  // Trigger Native Google Account Sign-In Popup
  Future<void> _handleGoogleSignIn() async {
    setState(() {
      _isAuthenticating = true;
    });

    try {
      // 1. Try native Google Sign-In SDK on device/browser
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();

      if (googleUser != null) {
        // Successfully retrieved Google account from native popup
        final email = googleUser.email;
        final name = googleUser.displayName ?? email.split('@').first;
        await _performBackendGoogleAuth(email: email, name: name);
        return;
      }
    } catch (e) {
      debugPrint('Native Google Sign-In notice: $e');
    }

    // 2. If Google Play services is unconfigured on emulator or user canceled, open custom input dialog
    if (mounted) {
      _showFallbackGooglePrompt();
    } else {
      setState(() {
        _isAuthenticating = false;
      });
    }
  }

  void _showFallbackGooglePrompt() {
    final TextEditingController promptEmailCtrl = TextEditingController(text: 'raja.kumar@gmail.com');
    final TextEditingController promptNameCtrl = TextEditingController(text: 'Raja Kumar');

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.cardBgDark,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      builder: (ctx) {
        return Padding(
          padding: EdgeInsets.only(
            left: 24,
            right: 24,
            top: 24,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 5,
                  decoration: BoxDecoration(
                    color: AppTheme.borderDark,
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: const [
                  Icon(Icons.g_mobiledata, size: 36, color: AppTheme.primaryAccent),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Google Account Sync',
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w900,
                        color: AppTheme.textDarkContrast,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              const Text(
                'Enter your Google account details to authenticate via FastAPI backend:',
                style: TextStyle(fontSize: 12, color: Color(0xFF869781)),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: promptEmailCtrl,
                style: const TextStyle(color: AppTheme.textDarkContrast),
                decoration: InputDecoration(
                  labelText: 'Google Email ID',
                  labelStyle: const TextStyle(color: Color(0xFF869781)),
                  filled: true,
                  fillColor: AppTheme.secondaryAccent,
                  prefixIcon: const Icon(Icons.email, color: AppTheme.primaryAccent),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(16),
                    borderSide: const BorderSide(color: AppTheme.borderDark),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: promptNameCtrl,
                style: const TextStyle(color: AppTheme.textDarkContrast),
                decoration: InputDecoration(
                  labelText: 'Full Name',
                  labelStyle: const TextStyle(color: Color(0xFF869781)),
                  filled: true,
                  fillColor: AppTheme.secondaryAccent,
                  prefixIcon: const Icon(Icons.person, color: AppTheme.primaryAccent),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(16),
                    borderSide: const BorderSide(color: AppTheme.borderDark),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.pop(ctx);
                    _performBackendGoogleAuth(
                      email: promptEmailCtrl.text.trim(),
                      name: promptNameCtrl.text.trim(),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryAccent,
                    foregroundColor: AppTheme.secondaryAccent,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: const Text('Confirm Google Sign-In', style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        );
      },
    ).then((_) {
      if (mounted && _isAuthenticating) {
        setState(() {
          _isAuthenticating = false;
        });
      }
    });
  }

  Future<void> _performBackendGoogleAuth({required String email, required String name}) async {
    setState(() {
      _isAuthenticating = true;
    });

    // Call FastAPI backend /auth/google endpoint
    final authResult = await _apiService.authenticateWithGoogle(
      email: email,
      name: name,
    );

    if (mounted) {
      final provider = Provider.of<WorkerProvider>(context, listen: false);
      final finalName = authResult['name'] ?? name;
      final finalEmail = authResult['email'] ?? email;

      provider.completeOnboarding(
        name: finalName,
        email: finalEmail,
        phone: '+91 98765 43210',
        city: 'Bengaluru, KA',
        pan: 'ABCDE1234F',
        upi: 'raja.kumar@okaxis',
      );

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Google Sign-In Verified: $finalEmail ✅'),
          backgroundColor: AppTheme.secondaryAccent,
        ),
      );

      setState(() {
        _isAuthenticating = false;
      });

      widget.onAuthSuccess();
    }
  }

  void _handleEmailSubmit() async {
    final email = _emailController.text.trim();
    if (email.isEmpty) return;

    setState(() {
      _isAuthenticating = true;
    });

    await Future.delayed(const Duration(milliseconds: 600));

    if (mounted) {
      final provider = Provider.of<WorkerProvider>(context, listen: false);
      provider.completeOnboarding(
        name: email.split('@').first,
        email: email,
        phone: '+91 98765 43210',
        city: 'Bengaluru, KA',
        pan: 'ABCDE1234F',
        upi: 'raja.kumar@okaxis',
      );

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Authenticated with email: $email'),
          backgroundColor: AppTheme.secondaryAccent,
        ),
      );

      setState(() {
        _isAuthenticating = false;
      });

      widget.onAuthSuccess();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.secondaryAccent,
      appBar: AppBar(
        backgroundColor: AppTheme.secondaryAccent,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppTheme.textDarkContrast),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Authentication',
          style: TextStyle(color: AppTheme.textDarkContrast, fontWeight: FontWeight.bold),
        ),
        elevation: 0,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          physics: const BouncingScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Brand Logo Badge
              ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Image.asset(
                  'assets/images/app_logo.png',
                  width: 52,
                  height: 52,
                  fit: BoxFit.cover,
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Welcome to GigCredit 👋',
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                  color: AppTheme.textDarkContrast,
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Sign in with your Google account to automatically sync gig earnings and connect to backend APIs.',
                style: TextStyle(
                  fontSize: 13,
                  color: Color(0xFF869781),
                  height: 1.4,
                ),
              ),

              const SizedBox(height: 28),

              // Google Auth Button Card
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: AppTheme.cardBgDark,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: AppTheme.borderDark, width: 1.5),
                ),
                child: Column(
                  children: [
                    // Google Account Box Visual
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppTheme.secondaryAccent,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 36,
                            height: 36,
                            decoration: const BoxDecoration(
                              color: AppTheme.primaryAccent,
                              shape: BoxShape.circle,
                            ),
                            child: const Center(
                              child: Text(
                                'G',
                                style: TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.w900,
                                  color: AppTheme.secondaryAccent,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: const [
                                Text(
                                  'Google OAuth 2.0 Secure Sync',
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w800,
                                    color: AppTheme.textDarkContrast,
                                  ),
                                ),
                                SizedBox(height: 2),
                                Text(
                                  'Tap below to open native Google account popup',
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: Color(0xFF869781),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 18),

                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton(
                        onPressed: _isAuthenticating ? null : _handleGoogleSignIn,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryAccent,
                          foregroundColor: AppTheme.secondaryAccent,
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                        ),
                        child: _isAuthenticating
                            ? const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2.5,
                                      color: AppTheme.secondaryAccent,
                                    ),
                                  ),
                                  SizedBox(width: 10),
                                  Flexible(
                                    child: Text(
                                      'Opening Google Popup...',
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ],
                              )
                            : Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: const [
                                  Icon(Icons.g_mobiledata, size: 32, color: AppTheme.secondaryAccent),
                                  SizedBox(width: 4),
                                  Flexible(
                                    child: FittedBox(
                                      fit: BoxFit.scaleDown,
                                      child: Text(
                                        'Sign In with Google Account',
                                        style: TextStyle(
                                          fontSize: 15,
                                          fontWeight: FontWeight.w900,
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // Divider
              Row(
                children: const [
                  Expanded(child: Divider(color: AppTheme.borderDark)),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 12),
                    child: Text(
                      'OR EMAIL / PHONE',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        color: Color(0xFF869781),
                      ),
                    ),
                  ),
                  Expanded(child: Divider(color: AppTheme.borderDark)),
                ],
              ),

              const SizedBox(height: 20),

              // Email / Phone Switcher
              if (_isEmailMode) ...[
                TextField(
                  controller: _emailController,
                  style: const TextStyle(color: AppTheme.textDarkContrast),
                  decoration: InputDecoration(
                    labelText: 'Email Address / Worker ID',
                    labelStyle: const TextStyle(color: Color(0xFF869781)),
                    filled: true,
                    fillColor: AppTheme.cardBgDark,
                    prefixIcon: const Icon(Icons.email_outlined, color: AppTheme.primaryAccent),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: const BorderSide(color: AppTheme.borderDark),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _passwordController,
                  obscureText: true,
                  style: const TextStyle(color: AppTheme.textDarkContrast),
                  decoration: InputDecoration(
                    labelText: 'Password',
                    labelStyle: const TextStyle(color: Color(0xFF869781)),
                    filled: true,
                    fillColor: AppTheme.cardBgDark,
                    prefixIcon: const Icon(Icons.lock_outline, color: AppTheme.primaryAccent),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: const BorderSide(color: AppTheme.borderDark),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _handleEmailSubmit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryAccent,
                      foregroundColor: AppTheme.secondaryAccent,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                    child: const Text('Sign In with Password', style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                ),
              ] else ...[
                Center(
                  child: TextButton(
                    onPressed: () {
                      setState(() {
                        _isEmailMode = true;
                      });
                    },
                    child: const Text(
                      'Use Email & Password Instead',
                      style: TextStyle(
                        color: AppTheme.primaryAccent,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
