class ApiConfig {
  ApiConfig._();

  /// 10.0.2.2 is the Android emulator's alias for the host machine's
  /// localhost. iOS simulator should instead be run with:
  ///   flutter run --dart-define=API_BASE_URL=http://localhost:4000
  /// Production builds should override this with the deployed backend URL, e.g.:
  ///   flutter build apk --dart-define=API_BASE_URL=https://your-app.onrender.com
  ///
  /// IMPORTANT: this must actually read the dart-define at compile time.
  /// A previous version of this file had a hardcoded literal here instead
  /// of String.fromEnvironment, which silently ignored
  /// --dart-define=API_BASE_URL=... entirely -- every build (including
  /// CI/Appium builds passing http://10.0.2.2:4000) still hit the live
  /// production backend. That caused CI test runs to depend on
  /// production network latency/availability and production data instead
  /// of the freshly-seeded CI database, which is why registration/login
  /// flows failed almost universally and every test ran far slower than
  /// expected (waiting on real network round-trips to onrender.com,
  /// including its cold-start delay, instead of localhost).
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://fitfuel-final.onrender.com',
  );
}
