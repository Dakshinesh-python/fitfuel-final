import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fitfuel_mobile/screens/login_screen.dart';

void main() {
  testWidgets('LoginScreen renders email and password fields',
      (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: LoginScreen()));

    expect(find.byType(TextFormField), findsNWidgets(2));
    expect(find.text('Welcome back'), findsOneWidget);
    expect(find.widgetWithText(ElevatedButton, 'Sign in'), findsOneWidget);
  });
}
