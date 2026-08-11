class ApiConfig {
  ApiConfig._();

  /// 10.0.2.2 is the Android emulator's alias for the host machine's
  /// localhost. iOS simulator should instead be run with:
  ///   flutter run --dart-define=API_BASE_URL=http://localhost:4000
  /// Production builds should override this with the deployed backend URL, e.g.:
  ///   flutter build apk --dart-define=API_BASE_URL=https://your-app.onrender.com
  static const String baseUrl = 'https://fitfuel-final.onrender.com';
}
