import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/worker_provider.dart';
import 'screens/application_tracker_screen.dart';
import 'screens/consent_screen.dart';
import 'screens/credit_score_screen.dart';
import 'screens/financial_profile_screen.dart';
import 'screens/home_dashboard.dart';
import 'screens/landing_screen.dart';
import 'screens/loan_simulator_screen.dart';
import 'screens/onboarding_screen.dart';
import 'theme/app_theme.dart';

void main() {
  runApp(const GigCreditWorkerApp());
}

class GigCreditWorkerApp extends StatelessWidget {
  const GigCreditWorkerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => WorkerProvider(),
      child: MaterialApp(
        title: 'GigCredit - Worker App',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        home: const WorkerRootPage(),
      ),
    );
  }
}

class WorkerRootPage extends StatefulWidget {
  const WorkerRootPage({super.key});

  @override
  State<WorkerRootPage> createState() => _WorkerRootPageState();
}

enum AppFlowState {
  landing,
  onboarding,
  mainDashboard,
}

class _WorkerRootPageState extends State<WorkerRootPage> {
  int _currentIndex = 0;
  AppFlowState _flowState = AppFlowState.landing;
  bool _hasCheckedSession = false;

  void _onTabTapped(int index) {
    setState(() {
      _currentIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<WorkerProvider>(context);

    // Auto restore persistent login session on startup
    if (!_hasCheckedSession) {
      _hasCheckedSession = true;
      if (provider.profile.isOnboarded) {
        _flowState = AppFlowState.mainDashboard;
      }
    }

    // Landing Page View
    if (_flowState == AppFlowState.landing && !provider.profile.isOnboarded) {
      return LandingScreen(
        onGetStarted: () {
          setState(() {
            _flowState = provider.profile.isOnboarded
                ? AppFlowState.mainDashboard
                : AppFlowState.onboarding;
          });
        },
      );
    }

    // Onboarding Flow View
    if (_flowState == AppFlowState.onboarding && !provider.profile.isOnboarded) {
      return OnboardingScreen(
        onComplete: () {
          setState(() {
            _flowState = AppFlowState.mainDashboard;
          });
        },
      );
    }

    // Main App Dashboard View
    final List<Widget> pages = [
      HomeDashboardScreen(onNavigateTab: _onTabTapped),
      const ConsentScreen(),
      const FinancialProfileScreen(),
      const CreditScoreScreen(),
      LoanSimulatorScreen(onViewApplications: () => _onTabTapped(5)),
      const ApplicationTrackerScreen(),
    ];

    int barIndex = _currentIndex > 4 ? 4 : _currentIndex;

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: pages,
      ),
      bottomNavigationBar: Container(
        margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        decoration: BoxDecoration(
          color: AppTheme.secondaryAccent,
          borderRadius: BorderRadius.circular(36),
          boxShadow: [
            BoxShadow(
              color: AppTheme.secondaryAccent.withValues(alpha: 0.25),
              blurRadius: 20,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(36),
          child: BottomNavigationBar(
            currentIndex: barIndex,
            backgroundColor: AppTheme.secondaryAccent,
            selectedItemColor: AppTheme.primaryAccent,
            unselectedItemColor: const Color(0xFF869781),
            type: BottomNavigationBarType.fixed,
            elevation: 0,
            onTap: (index) {
              if (index == 4) {
                provider.markNotificationsRead();
              }
              _onTabTapped(index);
            },
            items: const [
              BottomNavigationBarItem(
                icon: Icon(Icons.space_dashboard_outlined),
                activeIcon: Icon(Icons.space_dashboard),
                label: 'Home',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.shield_outlined),
                activeIcon: Icon(Icons.shield),
                label: 'Consents',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.account_balance_wallet_outlined),
                activeIcon: Icon(Icons.account_balance_wallet),
                label: 'Earnings',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.speed_outlined),
                activeIcon: Icon(Icons.speed),
                label: 'Score',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.calculate_outlined),
                activeIcon: Icon(Icons.calculate),
                label: 'Loan Sim',
              ),
            ],
          ),
        ),
      ),
    );
  }
}
