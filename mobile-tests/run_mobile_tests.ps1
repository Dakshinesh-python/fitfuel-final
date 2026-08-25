# run_mobile_tests.ps1 - One-stop local Appium/Flutter test runner for FitFuel mobile
#
# Usage:
#   .\run_mobile_tests.ps1                                           # run ALL tests
#   .\run_mobile_tests.ps1 -Test test_01_authentication              # run ONE module
#   .\run_mobile_tests.ps1 -Test test_01_authentication,test_02_registration  # multiple
#   .\run_mobile_tests.ps1 -SkipBuild                                # skip APK build
#   .\run_mobile_tests.ps1 -SkipBackend                              # skip backend start
#   .\run_mobile_tests.ps1 -SkipAppium                               # skip Appium start
#   .\run_mobile_tests.ps1 -SkipBuild -SkipBackend -SkipAppium       # just run pytest
#
# Prerequisites (checked automatically):
#   - Python 3.x       python --version
#   - Flutter          flutter --version
#   - Node.js          node --version
#   - Docker Desktop   docker --version  (for local Postgres - no cloud Neon used)
#   - Appium           installed automatically if missing
#   - Android emulator Pixel_6 AVD started automatically if not running

param(
    [string] $Test        = "",
    [switch] $SkipBuild   = $false,
    [switch] $SkipBackend = $false,
    [switch] $SkipAppium  = $false
)

Set-StrictMode -Off
# Do NOT use Stop - PowerShell throws a terminating error whenever any native
# command (like adb) writes to stderr, even daemon startup messages.
$ErrorActionPreference = "Continue"

$Root      = Split-Path $PSScriptRoot -Parent   # project root (one level up from mobile-tests)
$BEDir     = Join-Path $Root "backend"
$AppDir    = Join-Path $Root "fitfuel_mobile"
$TestDir   = $PSScriptRoot                       # mobile-tests\ itself
$APKPath   = Join-Path $AppDir "build\app\outputs\flutter-apk\app-debug.apk"

# Local Postgres config (Docker container, same as CI) - NOT the cloud Neon URL.
$DB_USER   = "fitfuel"
$DB_PASS   = "fitfuel"
$DB_NAME   = "fitfuel_local"
$DB_PORT   = "5432"
$DB_URL    = "postgresql://${DB_USER}:${DB_PASS}@localhost:${DB_PORT}/${DB_NAME}?schema=public"

# Put Android SDK tools on PATH for this session.
$sdkRoot = "C:\Users\$env:USERNAME\AppData\Local\Android\Sdk"
if ($env:ANDROID_HOME -and (Test-Path $env:ANDROID_HOME)) { $sdkRoot = $env:ANDROID_HOME }
$env:ANDROID_HOME     = $sdkRoot
$env:ANDROID_SDK_ROOT = $sdkRoot
$platformTools = Join-Path $sdkRoot "platform-tools"
$emulatorBin   = Join-Path $sdkRoot "emulator"
foreach ($p in @($platformTools, $emulatorBin)) {
    if ((Test-Path $p) -and ($env:PATH -notlike "*$p*")) {
        $env:PATH = "$env:PATH;$p"
        Write-Host "    Added to PATH: $p" -ForegroundColor DarkGray
    }
}

function Write-Step { param($msg) Write-Host "" ; Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "    WARN: $msg" -ForegroundColor Yellow }
function Write-Fail {
    param($msg)
    Write-Host ""
    Write-Host "    FAIL: $msg" -ForegroundColor Red
    exit 1
}

# Run adb silently - suppresses daemon startup stderr that PowerShell
# would otherwise treat as a NativeCommandError even with 2>$null.
function Invoke-Adb {
    $out = & adb @args 2>&1
    return $out | Where-Object { $_ -notmatch "daemon not running|daemon started" }
}

# ---------------------------------------------------------------------------
# 0. Prerequisites
# ---------------------------------------------------------------------------
Write-Step "Checking prerequisites"

foreach ($cmd in @("python", "flutter", "node", "adb", "docker")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Fail "'$cmd' not found on PATH. Install it and open a new terminal."
    }
}
Write-OK "python, flutter, node, adb, docker all found"

# ---------------------------------------------------------------------------
# Check / start emulator
# ---------------------------------------------------------------------------
$deviceList = Invoke-Adb devices
$runningEmu = $deviceList | Where-Object { $_ -match "emulator" -and $_ -match "device" }

if (-not $runningEmu) {
    Write-Warn "No running emulator - auto-starting Pixel_6 AVD"
    $emulatorExe = Join-Path $emulatorBin "emulator.exe"
    if (-not (Test-Path $emulatorExe)) {
        Write-Fail "emulator.exe not found at $emulatorExe"
    }
    Start-Process -FilePath $emulatorExe `
        -ArgumentList "-avd", "Pixel_6", "-no-audio", "-no-boot-anim" `
        -WindowStyle Minimized

    Write-Host "    Waiting for emulator to boot (1-3 min)..." -ForegroundColor DarkGray
    $booted = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep 5
        try {
            $prop = Invoke-Adb shell getprop sys.boot_completed
            if ($prop -match "^1") { $booted = $true; break }
        }
        catch { }
        Write-Host "    ... boot check $i/60" -ForegroundColor DarkGray
    }
    if (-not $booted) {
        Write-Fail "Emulator never fully booted. Start it manually from Android Studio AVD Manager."
    }
    Start-Sleep 5
    $deviceList = Invoke-Adb devices
    $runningEmu = $deviceList | Where-Object { $_ -match "emulator" -and $_ -match "device" }
}
Write-OK "Emulator: $($runningEmu | Select-Object -First 1)"

# ---------------------------------------------------------------------------
# Enable Flutter semantics tree via accessibility service
# ---------------------------------------------------------------------------
# Flutter only populates the UiAutomator2-visible semantics tree when an
# accessibility service is attached. Without this, Flutter-driver element
# lookups return empty results even though the screen renders correctly.
Write-Step "Enabling accessibility service (required for Flutter semantics tree)"
$emuId    = ($runningEmu | Select-Object -First 1) -replace "\s+.*$", ""
$talkback = "com.google.android.marvin.talkback/com.google.android.marvin.talkback.TalkBackService"
Invoke-Adb -s $emuId shell settings put secure enabled_accessibility_services $talkback | Out-Null
Invoke-Adb -s $emuId shell settings put secure accessibility_enabled 1 | Out-Null
Start-Sleep 3
Write-OK "Accessibility service enabled on $emuId"

# ---------------------------------------------------------------------------
# 1. Build APK with local backend URL baked in
# ---------------------------------------------------------------------------
if (-not $SkipBuild) {
    Write-Step "Building flutter-driver-enabled debug APK (--dart-define=API_BASE_URL=http://10.0.2.2:4000)"
    # 10.0.2.2 is the Android emulator alias for the host machine's localhost.
    # The production APK hardcodes the Render URL; this build overrides it.
    Push-Location $AppDir
    try {
        & flutter pub get
        if ($LASTEXITCODE -ne 0) { Write-Fail "flutter pub get failed" }
        & flutter build apk --debug -t lib/main_test.dart --dart-define=API_BASE_URL=http://10.0.2.2:4000
        if ($LASTEXITCODE -ne 0) { Write-Fail "flutter build apk failed" }
    }
    finally {
        Pop-Location
    }
    Write-OK "APK built: $APKPath"
}
else {
    Write-Warn "Skipping build (-SkipBuild). Using: $APKPath"
    if (-not (Test-Path $APKPath)) {
        Write-Fail "APK not found at $APKPath. Remove -SkipBuild or build manually."
    }
}

# ---------------------------------------------------------------------------
# 2. Python deps for the test suite
# ---------------------------------------------------------------------------
Write-Step "Installing mobile-tests Python dependencies"
Push-Location $TestDir
& python -m pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Fail "pip install failed for mobile-tests/requirements.txt" }
Pop-Location
Write-OK "Test dependencies installed"

# ---------------------------------------------------------------------------
# 3. Local Postgres via Docker (NOT the cloud Neon URL)
# ---------------------------------------------------------------------------
New-Item -ItemType Directory -Force -Path (Join-Path $TestDir "reports") | Out-Null
$backendLog = Join-Path $TestDir "reports\backend.log"
$appiumLog  = Join-Path $TestDir "reports\appium.log"

if (-not $SkipBackend) {
    Write-Step "Starting local Postgres via Docker (fitfuel_local_db)"

    # Make sure Docker daemon is running
    $dockerPs = & docker ps 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Docker Desktop not running - starting it now..."
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        Write-Host "    Waiting for Docker daemon..." -ForegroundColor DarkGray
        $dockerUp = $false
        for ($i = 0; $i -lt 30; $i++) {
            Start-Sleep 5
            $test = & docker ps 2>&1
            if ($LASTEXITCODE -eq 0) { $dockerUp = $true; break }
            Write-Host "    ... docker $i/30" -ForegroundColor DarkGray
        }
        if (-not $dockerUp) {
            Write-Fail "Docker never came up. Start Docker Desktop manually and retry."
        }
    }
    Write-OK "Docker daemon is running"

    # Stop + remove any leftover container from a previous run
    & docker rm -f fitfuel_local_db 2>&1 | Out-Null

    # Start a fresh Postgres 16 container - same image and creds as CI
    & docker run -d `
        --name fitfuel_local_db `
        -e POSTGRES_USER=$DB_USER `
        -e POSTGRES_PASSWORD=$DB_PASS `
        -e POSTGRES_DB=$DB_NAME `
        -p "${DB_PORT}:5432" `
        postgres:16 | Out-Null

    if ($LASTEXITCODE -ne 0) { Write-Fail "docker run postgres:16 failed" }

    Write-Host "    Waiting for Postgres to be ready..." -ForegroundColor DarkGray
    $pgUp = $false
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep 3
        $ready = & docker exec fitfuel_local_db pg_isready -U $DB_USER 2>&1
        if ($ready -match "accepting connections") { $pgUp = $true; break }
        Write-Host "    ... postgres $i/20" -ForegroundColor DarkGray
    }
    if (-not $pgUp) { Write-Fail "Postgres container never became ready" }
    Write-OK "Postgres is up at localhost:$DB_PORT/$DB_NAME"

    # Run Prisma migrations
    Write-Step "Running Prisma migrations"
    Push-Location $BEDir
    $env:DATABASE_URL = $DB_URL
    & npx prisma migrate deploy
    if ($LASTEXITCODE -ne 0) { Write-Fail "prisma migrate deploy failed" }
    Pop-Location
    Write-OK "Migrations applied"

    # Seed meal catalog
    Write-Step "Seeding meal catalog"
    Push-Location $BEDir
    & npm run prisma:seed
    if ($LASTEXITCODE -ne 0) { Write-Warn "Seed returned non-zero (may already be seeded - continuing)" }
    Pop-Location
    Write-OK "Seed complete"

    # Build backend
    Write-Step "Building backend"
    Push-Location $BEDir
    & npm run build
    if ($LASTEXITCODE -ne 0) { Write-Fail "npm run build failed" }
    Pop-Location
    Write-OK "Backend built"

    # Start backend as background job
    Write-Step "Starting backend on :4000 (background job)"
    $dbUrl = $DB_URL
    Start-Job -Name "FitFuelBackend" -ScriptBlock {
        param($dir, $db, $log)
        Set-Location $dir
        $env:DATABASE_URL = $db
        $env:PORT         = "4000"
        $env:NODE_ENV     = "development"
        & npm run start *> $log
    } -ArgumentList $BEDir, $dbUrl, $backendLog | Out-Null

    Write-Host "    Waiting for backend /health..." -ForegroundColor DarkGray
    $up = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep 2
        try {
            $r = Invoke-WebRequest "http://127.0.0.1:4000/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            if ($r.StatusCode -eq 200) { $up = $true; break }
        }
        catch { }
        Write-Host "    ... backend $i/30" -ForegroundColor DarkGray
    }
    if (-not $up) {
        Write-Warn "Last backend log:"
        if (Test-Path $backendLog) { Get-Content $backendLog -Tail 30 }
        Write-Fail "Backend never became healthy at http://127.0.0.1:4000"
    }
    Write-OK "Backend is up at http://127.0.0.1:4000"
}
else {
    Write-Warn "Skipping backend (-SkipBackend). Make sure it's running on :4000"
}

# ---------------------------------------------------------------------------
# 4. Appium
# ---------------------------------------------------------------------------
# Always check if Appium is already up first -- reuse it if so.
# Start-Job jobs are session-scoped and die when the script exits, so we
# use Start-Process (truly detached) to keep Appium alive across re-runs.
Write-Step "Checking Appium on :4723"
$appiumAlreadyUp = $false
try {
    $r = Invoke-WebRequest "http://127.0.0.1:4723/status" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    if ($r.StatusCode -eq 200) { $appiumAlreadyUp = $true }
} catch { }

if ($appiumAlreadyUp) {
    Write-OK "Appium already running on :4723 - reusing existing instance"
}
elseif ($SkipAppium) {
    Write-Fail "Appium is NOT running on :4723 but -SkipAppium was set. Start Appium first or remove -SkipAppium."
}
else {
    $appiumCheck = Get-Command appium -ErrorAction SilentlyContinue
    if (-not $appiumCheck) {
        Write-Step "Installing Appium globally"
        & npm install -g appium
        if ($LASTEXITCODE -ne 0) { Write-Fail "npm install appium failed" }
    }
    else {
        Write-OK "Appium found at: $($appiumCheck.Source)"
    }

    # Ensure flutter driver is installed.
    # Check the full driver list (not just --installed) because Appium 3.x
    # sometimes omits already-installed npm-sourced drivers from --installed output.
    $driverListAll = & appium driver list 2>&1
    $driverListInstalled = & appium driver list --installed 2>&1
    $flutterFound = ($driverListAll -match "flutter") -or ($driverListInstalled -match "flutter")
    if (-not $flutterFound) {
        Write-Step "Installing appium-flutter-driver@3.5.0"
        & appium driver install --source=npm appium-flutter-driver@3.5.0
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "appium driver install returned non-zero (may already be installed - continuing)"
        }
    }
    else {
        Write-OK "Flutter driver already installed - skipping"
    }

    # appium-flutter-driver@3.5.0 takes ~16s to load on Node 24.
    # Use Start-Process (detached) so Appium persists after this script exits.
    Write-Step "Starting Appium on :4723 (detached process - persists across runs)"
    $appiumJs = "$env:APPDATA\npm\node_modules\appium\index.js"
    if (-not (Test-Path $appiumJs)) {
        $appiumJs = (& npm root -g 2>$null) + "\appium\index.js"
    }
    $nodeExe = (Get-Command node -ErrorAction SilentlyContinue).Source
    if (-not $nodeExe) { $nodeExe = "node" }

    # Redirect both stdout+stderr to appium.log using cmd /c so the process
    # is fully detached from this PowerShell session.
    $appiumCmd = "`"$nodeExe`" `"$appiumJs`" --base-path / --address 127.0.0.1 --port 4723"
    $env:ANDROID_HOME = $sdkRoot
    Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c `"$appiumCmd`" >> `"$appiumLog`" 2>&1" `
        -WindowStyle Hidden

    Write-Host "    Waiting for Appium /status (flutter driver takes ~16s to load)..." -ForegroundColor DarkGray
    $up = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep 3
        try {
            $r = Invoke-WebRequest "http://127.0.0.1:4723/status" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            if ($r.StatusCode -eq 200) { $up = $true; break }
        }
        catch { }
        Write-Host "    ... appium $i/30" -ForegroundColor DarkGray
    }
    if (-not $up) {
        Write-Warn "Last Appium log:"
        if (Test-Path $appiumLog) { Get-Content $appiumLog -Tail 20 }
        Write-Fail "Appium never came up at http://127.0.0.1:4723"
    }
    Write-OK "Appium is up at http://127.0.0.1:4723"
}

# ---------------------------------------------------------------------------
# 5. Install APK on emulator + pre-warm Flutter GPU shaders
# ---------------------------------------------------------------------------
Write-Step "Installing APK on emulator"
$installOut = Invoke-Adb install -r $APKPath
Write-Host "    $installOut" -ForegroundColor DarkGray

# Pre-warm Flutter Impeller GPU backend so the first Appium session doesn't
# land on a mid-init Dart isolate (causes every waitFor to return Error:{}).
# Mirrors the CI pre-warm step exactly.
Write-Step "Pre-warming Flutter GPU shaders"
Invoke-Adb shell monkey -p com.example.fitfuel_mobile -c android.intent.category.LAUNCHER 1 | Out-Null
Write-Host "    Sleeping 12s for shader compilation..." -ForegroundColor DarkGray
Start-Sleep 12
Invoke-Adb shell am force-stop com.example.fitfuel_mobile | Out-Null
Start-Sleep 2
Write-OK "Pre-warm complete - app stopped cleanly"

# ---------------------------------------------------------------------------
# 6. Run pytest
# ---------------------------------------------------------------------------
# PLATFORM_VERSION defaults to "" in config.py, which tells Appium to
# auto-detect the connected device's Android version (no hardcoded cap sent).
$env:APK_PATH            = $APKPath
$env:APPIUM_SERVER_URL   = "http://127.0.0.1:4723"
$env:BACKEND_BASE_URL    = "http://10.0.2.2:4000"
$env:REPORTS_DIR         = "reports"
$env:CAPTURE_SCREENSHOTS = "1"

$allModules = @(
    "test_00_ui_chrome",
    "test_01_authentication",
    "test_02_registration",
    "test_03_health_assessment",
    "test_04_navigation",
    "test_05_dashboard",
    "test_06_recommendations",
    "test_07_meal_plan",
    "test_08_progress_crud",
    "test_10_profile_settings",
    "test_11_input_validation",
    "test_12_error_handling",
    "test_13_session_management",
    "test_14_accessibility",
    "test_15_responsiveness",
    "test_16_form_field_matrices",
    "test_17_extended_matrices",
    "test_18_integration_regression",
    "test_19_additional_coverage"
)

if ($Test -ne "") {
    $testPaths = ($Test -split ",") | ForEach-Object {
        $name = $_.Trim() -replace "\.py$", ""
        "tests/$name.py"
    }
}
else {
    $testPaths = $allModules | ForEach-Object { "tests/$_.py" }
}

Write-Step "Running tests: $($testPaths -join ', ')"
Write-Host "    Paths: $($testPaths -join ' | ')" -ForegroundColor DarkGray

Push-Location $TestDir
[string[]]$pathArray = @($testPaths)
# Override pytest.ini's --timeout-method=signal (Linux-only, uses SIGALRM)
# with 'thread' which works on Windows. Also set reruns=0 locally for fast
# feedback -- reruns just double wait time when you're actively debugging.
$pytestArgs = @("-v", "-s", "--tb=short", "-p", "no:cacheprovider",
                "--timeout-method=thread", "--override-ini=addopts=-v --timeout=150 --timeout-method=thread --tb=short") + $pathArray
Write-Host "    CMD: python -m pytest $pytestArgs" -ForegroundColor DarkGray
& python -m pytest @pytestArgs
$pytestExit = $LASTEXITCODE
Pop-Location

# ---------------------------------------------------------------------------
# 7. Reports
# ---------------------------------------------------------------------------
Write-Step "Generating HTML and Excel reports"
Push-Location $TestDir
& python generate_reports.py
Pop-Location

$html = Join-Path $TestDir "reports\execution-report.html"
if (Test-Path $html) {
    Start-Process $html
}

Write-Host ""
if ($pytestExit -eq 0) {
    Write-Host "ALL TESTS PASSED" -ForegroundColor Green
}
else {
    Write-Host "SOME TESTS FAILED (exit $pytestExit) - see reports\execution-report.html" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Logs:" -ForegroundColor DarkGray
Write-Host "  Appium  -> $appiumLog"  -ForegroundColor DarkGray
Write-Host "  Backend -> $backendLog" -ForegroundColor DarkGray
Write-Host "  Report  -> $html"       -ForegroundColor DarkGray
Write-Host ""
Write-Host "Cleanup (when done):" -ForegroundColor DarkGray
Write-Host "  Stop jobs : Get-Job | Stop-Job ; Get-Job | Remove-Job" -ForegroundColor DarkGray
Write-Host "  Stop DB   : docker rm -f fitfuel_local_db"             -ForegroundColor DarkGray
