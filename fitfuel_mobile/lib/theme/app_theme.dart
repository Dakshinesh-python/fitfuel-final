import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Colors & type scale extracted 1:1 from the Stitch "Vitality Tech-Aesthetic"
/// design system (see stitch export: vitality_tech_aesthetic/DESIGN.md).
class AppColors {
  AppColors._();

  static const surface = Color(0xFFF5FBF5);
  static const surfaceDim = Color(0xFFD6DBD6);
  static const surfaceBright = Color(0xFFF5FBF5);
  static const surfaceContainerLowest = Color(0xFFFFFFFF);
  static const surfaceContainerLow = Color(0xFFEFF5EF);
  static const surfaceContainer = Color(0xFFEAEFEA);
  static const surfaceContainerHigh = Color(0xFFE4EAE4);
  static const surfaceContainerHighest = Color(0xFFDEE4DE);

  static const onSurface = Color(0xFF171D1A);
  static const onSurfaceVariant = Color(0xFF3D4943);
  static const inverseSurface = Color(0xFF2C322E);
  static const inverseOnSurface = Color(0xFFECF2ED);

  static const outline = Color(0xFF6D7A72);
  static const outlineVariant = Color(0xFFBCCAC1);

  static const surfaceTint = Color(0xFF006C4D);
  static const primary = Color(0xFF006C4D);
  static const onPrimary = Color(0xFFFFFFFF);
  static const primaryContainer = Color(0xFF3EB489);
  static const onPrimaryContainer = Color(0xFF00402D);
  static const inversePrimary = Color(0xFF69DBAD);

  static const secondary = Color(0xFF9E4227);
  static const onSecondary = Color(0xFFFFFFFF);
  static const secondaryContainer = Color(0xFFFE8B6A);
  static const onSecondaryContainer = Color(0xFF74240B);

  static const tertiary = Color(0xFF9C413F);
  static const onTertiary = Color(0xFFFFFFFF);
  static const tertiaryContainer = Color(0xFFEF817D);
  static const onTertiaryContainer = Color(0xFF691B1C);

  static const error = Color(0xFFBA1A1A);
  static const onError = Color(0xFFFFFFFF);
  static const errorContainer = Color(0xFFFFDAD6);
  static const onErrorContainer = Color(0xFF93000A);

  static const primaryFixed = Color(0xFF86F8C8);
  static const primaryFixedDim = Color(0xFF69DBAD);
  static const onPrimaryFixed = Color(0xFF002115);
  static const onPrimaryFixedVariant = Color(0xFF005139);

  static const secondaryFixed = Color(0xFFFFDBD1);
  static const secondaryFixedDim = Color(0xFFFFB5A0);
  static const onSecondaryFixed = Color(0xFF3B0900);
  static const onSecondaryFixedVariant = Color(0xFF7E2B12);

  static const tertiaryFixed = Color(0xFFFFDAD7);
  static const tertiaryFixedDim = Color(0xFFFFB3AF);
  static const onTertiaryFixed = Color(0xFF410005);
  static const onTertiaryFixedVariant = Color(0xFF7E2A2A);

  static const background = Color(0xFFF5FBF5);
  static const onBackground = Color(0xFF171D1A);
  static const surfaceVariant = Color(0xFFDEE4DE);

  /// Warm Coral used for Match Score / highlight gradients.
  static const coralStart = Color(0xFFFE8B6A);
  static const coralEnd = Color(0xFFEF817D);
}

class AppRadius {
  AppRadius._();
  static const sm = 4.0;
  static const dflt = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const xl = 24.0;
  static const full = 999.0;
}

class AppSpacing {
  AppSpacing._();
  static const base = 8.0;
  static const gutter = 24.0;
  static const marginMobile = 20.0;
  static const marginDesktop = 40.0;
}

class AppTextStyles {
  AppTextStyles._();

  static TextStyle get displayLg => GoogleFonts.manrope(
        fontSize: 48,
        fontWeight: FontWeight.w800,
        height: 56 / 48,
        letterSpacing: -0.02 * 48,
        color: AppColors.onBackground,
      );

  static TextStyle get headlineLg => GoogleFonts.manrope(
        fontSize: 32,
        fontWeight: FontWeight.w700,
        height: 40 / 32,
        letterSpacing: -0.01 * 32,
        color: AppColors.onBackground,
      );

  static TextStyle get headlineLgMobile => GoogleFonts.manrope(
        fontSize: 28,
        fontWeight: FontWeight.w700,
        height: 34 / 28,
        color: AppColors.onBackground,
      );

  static TextStyle get headlineMd => GoogleFonts.manrope(
        fontSize: 24,
        fontWeight: FontWeight.w600,
        height: 32 / 24,
        color: AppColors.onBackground,
      );

  static TextStyle get bodyLg => GoogleFonts.inter(
        fontSize: 18,
        fontWeight: FontWeight.w400,
        height: 28 / 18,
        color: AppColors.onSurfaceVariant,
      );

  static TextStyle get bodyMd => GoogleFonts.inter(
        fontSize: 16,
        fontWeight: FontWeight.w400,
        height: 24 / 16,
        color: AppColors.onBackground,
      );

  static TextStyle get labelMd => GoogleFonts.inter(
        fontSize: 14,
        fontWeight: FontWeight.w500,
        height: 20 / 14,
        letterSpacing: 0.01 * 14,
        color: AppColors.onSurfaceVariant,
      );

  static TextStyle get labelSm => GoogleFonts.inter(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        height: 16 / 12,
        color: AppColors.onSurfaceVariant,
      );
}

/// Level 1 card shadow: Y:4 Blur:20 Opacity:4% black
const List<BoxShadow> kCardShadowLevel1 = [
  BoxShadow(color: Color(0x0A000000), offset: Offset(0, 4), blurRadius: 20),
];

/// Level 2 floating/interactive shadow: Y:8 Blur:24 Opacity:8% black
const List<BoxShadow> kCardShadowLevel2 = [
  BoxShadow(color: Color(0x14000000), offset: Offset(0, 8), blurRadius: 24),
];

ThemeData buildAppTheme() {
  return ThemeData(
    useMaterial3: true,
    scaffoldBackgroundColor: AppColors.background,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.primary,
      primary: AppColors.primary,
      onPrimary: AppColors.onPrimary,
      secondary: AppColors.secondary,
      onSecondary: AppColors.onSecondary,
      tertiary: AppColors.tertiary,
      error: AppColors.error,
      surface: AppColors.surface,
      onSurface: AppColors.onSurface,
    ),
    textTheme: TextTheme(
      displayLarge: AppTextStyles.displayLg,
      headlineLarge: AppTextStyles.headlineLg,
      headlineMedium: AppTextStyles.headlineMd,
      bodyLarge: AppTextStyles.bodyLg,
      bodyMedium: AppTextStyles.bodyMd,
      labelMedium: AppTextStyles.labelMd,
      labelSmall: AppTextStyles.labelSm,
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: AppColors.surface,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      centerTitle: true,
      iconTheme: const IconThemeData(color: AppColors.onSurface),
      titleTextStyle: GoogleFonts.manrope(
        fontSize: 18,
        fontWeight: FontWeight.w700,
        color: AppColors.onSurface,
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.onPrimary,
        minimumSize: const Size.fromHeight(52),
        textStyle: GoogleFonts.inter(
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.md),
        ),
        elevation: 0,
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.primary,
        minimumSize: const Size.fromHeight(52),
        side: const BorderSide(color: AppColors.primary, width: 1.5),
        textStyle: GoogleFonts.inter(
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.md),
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.surfaceContainerLowest,
      contentPadding:
          const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      hintStyle: const TextStyle(
        fontFamily: 'Inter',
        fontSize: 16,
        color: AppColors.outline,
      ),
      labelStyle: AppTextStyles.labelMd,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadius.md),
        borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadius.md),
        borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadius.md),
        borderSide: const BorderSide(color: AppColors.primary, width: 1.5),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadius.md),
        borderSide: const BorderSide(color: AppColors.error),
      ),
    ),
  );
}
