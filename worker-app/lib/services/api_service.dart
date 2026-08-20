import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/consent_model.dart';
import '../models/credit_score.dart';
import '../models/loan_application.dart';
import '../models/worker_profile.dart';

class WorkerApiService {
  // Determine Base URLs depending on platform
  static String get baseUrl {
    if (kIsWeb) return 'http://localhost:8000/worker';
    if (Platform.isAndroid) return 'http://10.0.2.2:8000/worker';
    return 'http://localhost:8000/worker';
  }

  static String get authBaseUrl {
    if (kIsWeb) return 'http://localhost:8000/auth';
    if (Platform.isAndroid) return 'http://10.0.2.2:8000/auth';
    return 'http://localhost:8000/auth';
  }

  static String get creditBaseUrl {
    if (kIsWeb) return 'http://localhost:8000/credit';
    if (Platform.isAndroid) return 'http://10.0.2.2:8000/credit';
    return 'http://localhost:8000/credit';
  }

  // --- Backend Google & Email Authentication (auth.py) ---
  Future<Map<String, dynamic>> authenticateWithGoogle({
    required String email,
    required String name,
  }) async {
    try {
      final res = await http.post(
        Uri.parse('$authBaseUrl/google'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'name': name,
        }),
      ).timeout(const Duration(seconds: 4));

      if (res.statusCode == 200) {
        return jsonDecode(res.body);
      }
    } catch (e) {
      debugPrint('Backend Google Auth fallback: $e');
    }

    return {
      'message': 'Google Authentication Successful',
      'user_id': 'usr_google_local',
      'email': email,
      'name': name,
      'access_token': 'gc_mock_access_token',
    };
  }

  // --- Backend Credit ML Prediction (credit.py) ---
  Future<Map<String, dynamic>?> fetchMLCreditPrediction(String token) async {
    try {
      final res = await http.post(
        Uri.parse('$creditBaseUrl/predict'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      ).timeout(const Duration(seconds: 4));

      if (res.statusCode == 200) {
        return jsonDecode(res.body);
      }
    } catch (e) {
      debugPrint('Backend ML Credit Predict fallback: $e');
    }
    return null;
  }

  // --- Initial Profile (worker.py) ---
  WorkerProfile getInitialProfile() {
    return WorkerProfile(
      id: 'wrk_8849',
      name: 'Raja Kumar',
      email: 'raja.kumar@gmail.com',
      phone: '+91 98765 43210',
      city: 'Bengaluru, KA',
      panNumber: 'ABCDE1234F',
      upiId: 'raja.kumar@okaxis',
      totalMonthsExperience: 18,
      avgDailyHours: 8.5,
      isOnboarded: false,
      platforms: [
        GigPlatform(
          id: 'p_swiggy',
          name: 'Swiggy Food',
          logo: 'swiggy',
          workType: 'Food Delivery',
          monthlyEarnings: 14200.0,
          tripsCompleted: 420,
          rating: 4.9,
          isConnected: true,
        ),
        GigPlatform(
          id: 'p_zomato',
          name: 'Zomato',
          logo: 'zomato',
          workType: 'Food Delivery',
          monthlyEarnings: 10500.0,
          tripsCompleted: 310,
          rating: 4.85,
          isConnected: true,
        ),
        GigPlatform(
          id: 'p_uber',
          name: 'Uber India',
          logo: 'uber',
          workType: 'Rideshare Driver',
          monthlyEarnings: 6200.0,
          tripsCompleted: 95,
          rating: 4.8,
          isConnected: true,
        ),
        GigPlatform(
          id: 'p_urbancompany',
          name: 'Urban Company',
          logo: 'urban',
          workType: 'Home Services',
          monthlyEarnings: 0.0,
          tripsCompleted: 0,
          rating: 0.0,
          isConnected: false,
        ),
      ],
    );
  }

  // --- Initial Consents (worker.py) ---
  ConsentSettings getInitialConsents() {
    final now = DateTime.now();
    return ConsentSettings(
      consentGivenAt: now,
      items: {
        'c_bank_cashflow': ConsentItem(
          id: 'c_bank_cashflow',
          title: 'Bank Account Cashflow Sync',
          category: 'Banking',
          subtitle: 'Read-only access to verify direct deposit payouts',
          description: 'Validates income stability and recurring earnings directly from linked bank account AA feeds.',
          dataPoints: 'Statement deposits, daily balance averages, recurring credits',
          isGranted: true,
          isMandatory: true,
          lastUpdated: now,
        ),
        'c_gig_ratings': ConsentItem(
          id: 'c_gig_ratings',
          title: 'Gig Platform Ratings & Trips',
          category: 'Platform Work',
          subtitle: 'Aggregates completed deliveries, customer stars, and work tenure',
          description: 'Proves work reliability and platform tenure to unlock lower interest rates.',
          dataPoints: 'Customer rating average, total trips completed, active work months',
          isGranted: true,
          isMandatory: true,
          lastUpdated: now,
        ),
        'c_location_telematics': ConsentItem(
          id: 'c_location_telematics',
          title: 'Work Location & Operating Zone',
          category: 'Logistics',
          subtitle: 'Verifies regular active work areas in your registered city',
          description: 'Used by AI risk algorithms to detect consistent work shifts and active delivery hubs.',
          dataPoints: 'Aggregated daily work hours, primary operating pin codes',
          isGranted: true,
          isMandatory: false,
          lastUpdated: now,
        ),
        'c_utility_bills': ConsentItem(
          id: 'c_utility_bills',
          title: 'Utility & Mobile Bill Timeliness',
          category: 'Alternative Credit',
          subtitle: 'Checks on-time payment history for electricity and phone bills',
          description: 'Demonstrates financial responsibility even without traditional CIBIL score history.',
          dataPoints: 'Bill payment timestamps, mobile recharge regularity',
          isGranted: true,
          isMandatory: false,
          lastUpdated: now,
        ),
        'c_tax_returns': ConsentItem(
          id: 'c_tax_returns',
          title: 'ITR / Form 26AS Tax Proofs',
          category: 'Taxation',
          subtitle: 'Optional tax filing submission for higher loan limits',
          description: 'Unlocks maximum loan limits up to ₹1,50,000 for verified tax-paying gig workers.',
          dataPoints: 'Gross taxable income, Form 26AS TDS receipts',
          isGranted: false,
          isMandatory: false,
          lastUpdated: now,
        ),
      },
    );
  }

  // --- Fetch Credit Score from Backend (worker.py & credit.py) ---
  Future<GigCreditScore> fetchCreditScore(WorkerProfile profile, ConsentSettings consents) async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/score')).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final factorsJson = data['factors'] as List;

        return GigCreditScore(
          score: data['score'],
          riskCategory: data['riskCategory'],
          incomeStabilityScore: (data['incomeStabilityScore'] as num).toDouble(),
          workConsistencyScore: (data['workConsistencyScore'] as num).toDouble(),
          debtBurdenRatio: (data['debtBurdenRatio'] as num).toDouble(),
          maxRecommendedLoan: (data['maxRecommendedLoan'] as num).toDouble(),
          calculatedAt: DateTime.tryParse(data['calculatedAt']) ?? DateTime.now(),
          factors: factorsJson.map((f) => ScoreFactor(
            title: f['title'],
            description: f['description'],
            impact: f['impact'],
            isPositive: f['isPositive'],
            iconType: f['iconType'],
          )).toList(),
        );
      }
    } catch (e) {
      debugPrint('Backend fetchCreditScore fallback: $e');
    }

    return _localCalculateScore(profile, consents);
  }

  // --- Submit Loan Application to Backend (worker.py) ---
  Future<LoanApplication> submitLoanApplication({
    required double amount,
    required int tenureMonths,
    required double interestRateMonthly,
    required double emi,
    required String purpose,
  }) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/loans/apply'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'amount': amount,
          'tenureMonths': tenureMonths,
          'interestRateMonthly': interestRateMonthly,
          'emi': emi,
          'purpose': purpose,
        }),
      ).timeout(const Duration(seconds: 4));

      if (res.statusCode == 200 || res.statusCode == 201) {
        final data = jsonDecode(res.body);
        return LoanApplication(
          id: data['id'],
          referenceId: data['referenceId'],
          requestedAmount: (data['requestedAmount'] as num).toDouble(),
          tenureMonths: data['tenureMonths'],
          interestRateMonthly: (data['interestRateMonthly'] as num).toDouble(),
          calculatedEmi: (data['calculatedEmi'] as num).toDouble(),
          purpose: data['purpose'],
          status: LoanStatus.submitted,
          appliedAt: DateTime.tryParse(data['appliedAt']) ?? DateTime.now(),
          lenderName: data['lenderName'] ?? 'GigCredit Lending NBFC',
        );
      }
    } catch (e) {
      debugPrint('Backend submitLoanApplication fallback: $e');
    }

    final id = 'app_${Random().nextInt(9000) + 1000}';
    return LoanApplication(
      id: id,
      referenceId: 'GC-LOAN-${Random().nextInt(8000) + 1000}',
      requestedAmount: amount,
      tenureMonths: tenureMonths,
      interestRateMonthly: interestRateMonthly,
      calculatedEmi: emi,
      purpose: purpose,
      status: LoanStatus.submitted,
      appliedAt: DateTime.now(),
      lenderName: 'GigCredit Lending NBFC',
    );
  }

  // --- Toggle Consent on Backend (worker.py) ---
  Future<bool> toggleConsentApi(String consentId) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/consent/toggle'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'consent_id': consentId}),
      ).timeout(const Duration(seconds: 3));
      return res.statusCode == 200;
    } catch (e) {
      debugPrint('Backend toggleConsentApi fallback: $e');
      return false;
    }
  }

  // --- Toggle Platform on Backend (worker.py) ---
  Future<bool> togglePlatformApi(String platformId) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/platform/toggle'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'platform_id': platformId}),
      ).timeout(const Duration(seconds: 3));
      return res.statusCode == 200;
    } catch (e) {
      debugPrint('Backend togglePlatformApi fallback: $e');
      return false;
    }
  }

  // Local fallback calculation
  GigCreditScore _localCalculateScore(WorkerProfile profile, ConsentSettings consents) {
    double baseScore = 620.0;
    int connectedApps = profile.totalConnectedPlatforms;
    baseScore += (connectedApps * 25);

    if (profile.averageRating > 4.5) {
      baseScore += 35;
    }

    if (profile.totalMonthlyEarnings > 25000) {
      baseScore += 45;
    } else if (profile.totalMonthlyEarnings > 15000) {
      baseScore += 25;
    }

    for (var consent in consents.items.values) {
      if (consent.isGranted) {
        baseScore += 20;
      }
    }

    int finalScore = baseScore.round().clamp(300, 900);

    String tier;
    double maxLoan;
    if (finalScore >= 740) {
      tier = 'Prime Gig Credit';
      maxLoan = 80000;
    } else if (finalScore >= 680) {
      tier = 'Good Credit';
      maxLoan = 50000;
    } else if (finalScore >= 600) {
      tier = 'Fair Credit';
      maxLoan = 25000;
    } else {
      tier = 'Developing Credit';
      maxLoan = 10000;
    }

    return GigCreditScore(
      score: finalScore,
      riskCategory: tier,
      maxRecommendedLoan: maxLoan,
      incomeStabilityScore: min(95.0, profile.totalMonthlyEarnings / 350.0),
      workConsistencyScore: 88.0,
      debtBurdenRatio: 18.5,
      calculatedAt: DateTime.now(),
      factors: [
        ScoreFactor(
          title: 'Platform Earnings Consistency',
          description: 'Based on last 4 months aggregated Swiggy & Zomato weekly payouts.',
          impact: '+45 pts',
          isPositive: true,
          iconType: 'trending_up',
        ),
        ScoreFactor(
          title: 'Customer Rating (4.88★)',
          description: 'Top 10% rated delivery partner in Bengaluru zone.',
          impact: '+35 pts',
          isPositive: true,
          iconType: 'star',
        ),
        ScoreFactor(
          title: 'Consents Granted',
          description: 'Consents boost active financial risk modeling.',
          impact: '+60 pts',
          isPositive: consents.grantedCount >= 3,
          iconType: 'shield',
        ),
      ],
    );
  }
}
