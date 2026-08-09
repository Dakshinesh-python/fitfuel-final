import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

/// Handles register/login calls against the backend's /api/auth endpoints
/// and persists the returned JWT in shared_preferences.
class AuthService {
  AuthService._();
  static final AuthService instance = AuthService._();

  static const _tokenKey = 'fitfuel_auth_token';

  Future<String> register({
    required String name,
    required String email,
    required String password,
    int? age,
    String? gender,
    double? heightCm,
    double? weightKg,
  }) async {
    final result = await ApiService.instance.post('/api/auth/register', body: {
      'name': name,
      'email': email,
      'password': password,
      if (age != null) 'age': age,
      if (gender != null) 'gender': gender,
      if (heightCm != null) 'heightCm': heightCm,
      if (weightKg != null) 'weightKg': weightKg,
    });
    final token = result['token'] as String;
    await _storeToken(token);
    return token;
  }

  Future<String> login({
    required String email,
    required String password,
  }) async {
    final result = await ApiService.instance.post('/api/auth/login', body: {
      'email': email,
      'password': password,
    });
    final token = result['token'] as String;
    await _storeToken(token);
    return token;
  }

  Future<void> _storeToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  Future<String?> currentToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  Future<bool> isLoggedIn() async {
    final token = await currentToken();
    return token != null && token.isNotEmpty;
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
  }
}
