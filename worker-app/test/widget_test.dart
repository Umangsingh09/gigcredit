import 'package:flutter_test/flutter_test.dart';
import 'package:worker_app/main.dart';

void main() {
  testWidgets('GigCredit Worker App Smoke Test', (WidgetTester tester) async {
    await tester.pumpWidget(const GigCreditWorkerApp());
    expect(find.byType(GigCreditWorkerApp), findsOneWidget);
  });
}
