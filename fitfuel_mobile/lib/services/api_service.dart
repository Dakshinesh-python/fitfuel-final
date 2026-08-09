import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_config.dart';
import 'auth_service.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);

  @override
  String toString() => 'ApiException($statusCode): $message';
}

/// Thin HTTP client wrapper used by all feature services. Attaches the
/// stored auth token (if present) and throws [ApiException] with the
/// backend's error message on non-2xx responses.
class ApiService {
  ApiService._();
  static final ApiService instance = ApiService._();

  Uri _uri(String path, [Map<String, dynamic>? query]) {
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    return Uri.parse('${ApiConfig.baseUrl}$normalizedPath').replace(
      queryParameters:
          query?.map((k, v) => MapEntry(k, v?.toString())).cast<String, String>(),
    );
  }

  Future<Map<String, String>> _headers({bool json = true}) async {
    final headers = <String, String>{};
    if (json) headers['Content-Type'] = 'application/json';
    final token = await AuthService.instance.currentToken();
    if (token != null) headers['Authorization'] = 'Bearer $token';
    return headers;
  }

  dynamic _decode(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      String message = 'Request failed (${response.statusCode})';
      try {
        final body = jsonDecode(response.body);
        if (body is Map && body['message'] != null) {
          message = body['message'].toString();
        } else if (body is Map && body['error'] != null) {
          message = body['error'].toString();
        }
      } catch (_) {
        // Response body wasn't JSON; keep the generic message.
      }
      throw ApiException(response.statusCode, message);
    }
    if (response.body.isEmpty) return null;
    return jsonDecode(response.body);
  }

  Future<dynamic> get(String path, {Map<String, dynamic>? query}) async {
    final res =
        await http.get(_uri(path, query), headers: await _headers(json: false));
    return _decode(res);
  }

  Future<dynamic> post(String path, {Map<String, dynamic>? body}) async {
    final res = await http.post(
      _uri(path),
      headers: await _headers(),
      body: body != null ? jsonEncode(body) : null,
    );
    return _decode(res);
  }

  Future<dynamic> put(String path, {Map<String, dynamic>? body}) async {
    final res = await http.put(
      _uri(path),
      headers: await _headers(),
      body: body != null ? jsonEncode(body) : null,
    );
    return _decode(res);
  }

  Future<dynamic> delete(String path) async {
    final res = await http.delete(_uri(path), headers: await _headers());
    return _decode(res);
  }
}
