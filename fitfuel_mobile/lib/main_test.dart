// Test-only entrypoint for Appium's flutter-driver plugin.
//
// This is NOT shipped to production. It is built with:
//   flutter build apk --debug -t lib/main_test.dart
// and installed alongside (or instead of) the normal debug APK so that
// Appium (server >= 2.x with the flutter-driver plugin, or the legacy
// FlutterDriver capability) can attach to the running app and drive it
// through find.byValueKey(...) / find.text(...) / find.byType(...).
//
// enableFlutterDriverExtension() registers a VM-service extension that the
// driver talks to over the Dart VM Service protocol. Nothing about normal
// app behaviour changes — this file just wraps the real app.
//
// See mobile-tests/README.md → "How the app is made testable" for the
// full explanation of why this file exists and how it's wired into CI.
import 'package:flutter_driver/driver_extension.dart';
import 'main.dart' as app;

void main() {
  enableFlutterDriverExtension();
  app.main();
}
