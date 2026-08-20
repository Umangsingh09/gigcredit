import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/worker_profile.dart';
import '../models/consent_model.dart';
import '../models/credit_score.dart';
import '../models/loan_application.dart';
import '../services/api_service.dart';

class WorkerProvider extends ChangeNotifier {
  final WorkerApiService _apiService = WorkerApiService();

  late WorkerProfile _profile;
  late ConsentSettings _consents;
  GigCreditScore? _score;
  final List<LoanApplication> _applications = [];
  final List<WorkerNotification> _notifications = [];

  bool _isLoading = false;
  bool _isSessionRestored = false;
  String _loanPurpose = 'Vehicle Repair / Maintenance';
  double _simulatedAmount = 25000.0;
  int _simulatedTenure = 6; // months

  WorkerProvider() {
    _initData();
  }

  // Getters
  WorkerProfile get profile => _profile;
  ConsentSettings get consents => _consents;
  GigCreditScore? get score => _score;
  List<LoanApplication> get applications => List.unmodifiable(_applications);
  List<WorkerNotification> get notifications => List.unmodifiable(_notifications);
  bool get isLoading => _isLoading;
  bool get isSessionRestored => _isSessionRestored;
  String get loanPurpose => _loanPurpose;
  double get simulatedAmount => _simulatedAmount;
  int get simulatedTenure => _simulatedTenure;

  int get unreadNotificationsCount =>
      _notifications.where((n) => !n.isRead).length;

  void _initData() {
    _profile = _apiService.getInitialProfile();
    _consents = _apiService.getInitialConsents();

    // Default notifications
    _notifications.addAll([
      WorkerNotification(
        id: '1',
        title: 'GigCredit Score Active ⚡',
        message: 'Your score was refreshed based on Swiggy & Zomato earnings.',
        timestamp: DateTime.now().subtract(const Duration(hours: 2)),
        isRead: false,
        type: 'score',
      ),
      WorkerNotification(
        id: '2',
        title: 'Platform Earnings Synced 💰',
        message: 'Aggregated monthly income: ₹30,900 across linked apps.',
        timestamp: DateTime.now().subtract(const Duration(hours: 5)),
        isRead: false,
        type: 'sync',
      ),
      WorkerNotification(
        id: '3',
        title: 'Pre-Approved Credit Limit Unlocked 🎉',
        message: 'You are eligible for instant loan access up to ₹80,000.',
        timestamp: DateTime.now().subtract(const Duration(days: 1)),
        isRead: true,
        type: 'loan',
      ),
    ]);

    restoreSession();
  }

  // Restore persistent login state from SharedPreferences
  Future<bool> restoreSession() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final isLoggedIn = prefs.getBool('is_logged_in') ?? false;
      if (isLoggedIn) {
        final savedName = prefs.getString('user_name') ?? _profile.name;
        final savedEmail = prefs.getString('user_email') ?? _profile.email;

        _profile = _profile.copyWith(
          name: savedName,
          email: savedEmail,
          isOnboarded: true,
        );
        _isSessionRestored = true;
        recalculateScore();
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('SharedPreferences restoreSession error: $e');
    }
    _isSessionRestored = true;
    notifyListeners();
    return false;
  }

  // Complete Onboarding & Save Session
  void completeOnboarding({
    required String name,
    String? email,
    required String phone,
    required String city,
    required String pan,
    required String upi,
  }) async {
    final updatedEmail = email ?? '${name.toLowerCase().replaceAll(' ', '.')}@gmail.com';
    _profile = _profile.copyWith(
      name: name,
      email: updatedEmail,
      phone: phone,
      city: city,
      panNumber: pan,
      upiId: upi,
      isOnboarded: true,
    );

    // Save to SharedPreferences
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('is_logged_in', true);
      await prefs.setString('user_name', name);
      await prefs.setString('user_email', updatedEmail);
    } catch (e) {
      debugPrint('SharedPreferences save session error: $e');
    }

    recalculateScore();
    notifyListeners();
  }

  // Logout & Clear Session
  Future<void> logout() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.clear();
    } catch (e) {
      debugPrint('SharedPreferences clear error: $e');
    }
    _profile = _apiService.getInitialProfile();
    notifyListeners();
  }

  // Setters for Simulator
  void setSimulatedAmount(double amount) {
    _simulatedAmount = amount;
    notifyListeners();
  }

  void setSimulatedTenure(int months) {
    _simulatedTenure = months;
    notifyListeners();
  }

  void setLoanPurpose(String purpose) {
    _loanPurpose = purpose;
    notifyListeners();
  }

  // Calculate EMI
  double get calculatedMonthlyInterestRate => 0.012; // 1.2% per month
  double get calculatedMonthlyEmi {
    double p = _simulatedAmount;
    double r = calculatedMonthlyInterestRate;
    int n = _simulatedTenure;
    if (n <= 0) return 0;
    double factor = 1.0;
    for (int i = 0; i < n; i++) {
      factor *= (1 + r);
    }
    return (p * r * factor) / (factor - 1);
  }

  double get emiToIncomeRatio {
    if (_profile.totalMonthlyEarnings == 0) return 0.0;
    return (calculatedMonthlyEmi / _profile.totalMonthlyEarnings) * 100;
  }

  // Toggle platform connection
  void togglePlatform(String platformId) {
    final updatedList = _profile.platforms.map((p) {
      if (p.id == platformId) {
        return p.copyWith(isConnected: !p.isConnected);
      }
      return p;
    }).toList();

    _profile = _profile.copyWith(platforms: updatedList);
    _apiService.togglePlatformApi(platformId);
    recalculateScore();
    notifyListeners();
  }

  // Toggle Consent
  void toggleConsent(String consentId) {
    final currentMap = Map<String, ConsentItem>.from(_consents.items);
    if (currentMap.containsKey(consentId)) {
      final item = currentMap[consentId]!;
      currentMap[consentId] = item.copyWith(isGranted: !item.isGranted);
      _consents = ConsentSettings(
        items: currentMap,
        consentGivenAt: DateTime.now(),
      );

      _notifications.insert(
        0,
        WorkerNotification(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          title: 'Consent Setting Updated',
          message: '${item.title} consent was ${currentMap[consentId]!.isGranted ? "granted" : "revoked"}.',
          timestamp: DateTime.now(),
          isRead: false,
          type: 'consent',
        ),
      );

      _apiService.toggleConsentApi(consentId);
      recalculateScore();
      notifyListeners();
    }
  }

  // Recalculate score via Backend API
  Future<void> recalculateScore() async {
    _isLoading = true;
    notifyListeners();

    _score = await _apiService.fetchCreditScore(_profile, _consents);

    _isLoading = false;
    notifyListeners();
  }

  // Submit Loan Application via Backend API
  Future<bool> applyForLoan() async {
    _isLoading = true;
    notifyListeners();

    try {
      final newApp = await _apiService.submitLoanApplication(
        amount: _simulatedAmount,
        tenureMonths: _simulatedTenure,
        interestRateMonthly: calculatedMonthlyInterestRate,
        emi: calculatedMonthlyEmi,
        purpose: _loanPurpose,
      );

      _applications.insert(0, newApp);

      _notifications.insert(
        0,
        WorkerNotification(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          title: 'Loan Application Submitted 🚀',
          message: 'Your loan request for ₹${_simulatedAmount.toStringAsFixed(0)} was sent to backend.',
          timestamp: DateTime.now(),
          isRead: false,
          type: 'loan',
        ),
      );

      // Underwriting step simulation
      Future.delayed(const Duration(seconds: 3), () {
        int idx = _applications.indexWhere((a) => a.id == newApp.id);
        if (idx != -1) {
          _applications[idx] = LoanApplication(
            id: newApp.id,
            requestedAmount: newApp.requestedAmount,
            tenureMonths: newApp.tenureMonths,
            interestRateMonthly: newApp.interestRateMonthly,
            calculatedEmi: newApp.calculatedEmi,
            status: LoanStatus.underwriting,
            purpose: newApp.purpose,
            appliedAt: newApp.appliedAt,
            lenderName: newApp.lenderName,
            referenceId: newApp.referenceId,
          );
          notifyListeners();
        }
      });

      // Pre-Approval step simulation
      Future.delayed(const Duration(seconds: 7), () {
        int idx = _applications.indexWhere((a) => a.id == newApp.id);
        if (idx != -1) {
          _applications[idx] = LoanApplication(
            id: newApp.id,
            requestedAmount: newApp.requestedAmount,
            tenureMonths: newApp.tenureMonths,
            interestRateMonthly: newApp.interestRateMonthly,
            calculatedEmi: newApp.calculatedEmi,
            status: LoanStatus.approved,
            purpose: newApp.purpose,
            appliedAt: newApp.appliedAt,
            lenderName: newApp.lenderName,
            referenceId: newApp.referenceId,
          );
          notifyListeners();
        }
      });

      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  void markNotificationsRead() {
    for (int i = 0; i < _notifications.length; i++) {
      _notifications[i] = _notifications[i].copyWith(isRead: true);
    }
    notifyListeners();
  }
}
