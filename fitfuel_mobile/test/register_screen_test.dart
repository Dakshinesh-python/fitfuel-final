import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fitfuel_mobile/screens/register_screen.dart';

void main() {
  testWidgets('RegisterScreen renders key form fields',
      (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: RegisterScreen()));

    expect(find.text('Full Name'), findsOneWidget);
    expect(find.text('Email Address'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('Age'), findsOneWidget);
    expect(find.text('Height (cm)'), findsOneWidget);
    expect(find.text('Weight (kg)'), findsOneWidget);
  });
}
