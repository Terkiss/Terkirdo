@echo off
setlocal EnableDelayedExpansion

:: ============================================================================
:: Terukirdo v5.6 Harness Updater (Deterministic Mirror & Legacy Purger)
:: - Synchronizes core harness directories (.agents, agents, scripts/harness,
::   scripts/self-evolution, tests/harness, docs/harness, docs/archive,
::   docs/v2_specs, reference) from the master template.
:: - Purges deleted/moved template files and stale root protocols (v5.2~v5.5)
::   that still linger in older target projects.
:: - Preserves target project's .git, source code, README.md, MEMORY.md,
::   docs/specs, docs/Terukirdo_Trajectory.txt, and .agents/state.
:: ============================================================================

set "SOURCE=D:\Project\codex-flutter\newAntigravity"
set "TARGET=%~dp0"
if "%TARGET:~-1%"=="\" set "TARGET=%TARGET:~0,-1%"

set "NO_PAUSE=0"
set "CLI_TARGET="

:parse_args
if "%~1"=="" goto :args_done
if /I "%~1"=="--no-pause" (
    set "NO_PAUSE=1"
) else (
    set "CLI_TARGET=%~1"
)
shift
goto :parse_args
:args_done

if not "!CLI_TARGET!"=="" (
    set "CLI_TARGET=!CLI_TARGET:"=!"
    if "!CLI_TARGET:~-1!"=="\" set "CLI_TARGET=!CLI_TARGET:~0,-1!"
    set "TARGET=!CLI_TARGET!"
)

echo ============================================================================
echo  [Terukirdo v5.6] Harness Updater (Mirror ^& Purge Engine)
echo ============================================================================

if not exist "%SOURCE%\scripts\harness\sync_harness.py" (
    echo [ERROR] Master template synchronizer not found at:
    echo         "%SOURCE%\scripts\harness\sync_harness.py"
    if "!NO_PAUSE!"=="0" pause
    exit /b 1
)

if /I "%TARGET%"=="%SOURCE%" (
    echo [INFO] Running inside the master template directory.
    echo Copy this .bat file into a target project folder and run it there,
    echo OR enter the target project folder path below:
    echo.
    set /p "USER_TARGET=Target Project Path: "
    if "!USER_TARGET!"=="" (
        echo [CANCELED] No target path provided.
        if "!NO_PAUSE!"=="0" pause
        exit /b 1
    )
    set "USER_TARGET=!USER_TARGET:"=!"
    if "!USER_TARGET:~-1!"=="\" set "USER_TARGET=!USER_TARGET:~0,-1!"
    set "TARGET=!USER_TARGET!"
)

if /I "%TARGET%"=="%SOURCE%" (
    echo [SKIP] Source and target are identical. Aborting.
    if "!NO_PAUSE!"=="0" pause
    exit /b 1
)

if not exist "%TARGET%" (
    echo [ERROR] Target directory does not exist: "%TARGET%"
    if "!NO_PAUSE!"=="0" pause
    exit /b 1
)

echo.
echo  * Source Template : "%SOURCE%"
echo  * Target Project  : "%TARGET%"
echo  * Sync Mode       : Mirror ^& Purge (deletes obsolete template files)
echo  * Preserved       : .git, README.md, MEMORY.md, docs/specs, .agents/state
echo.

python -X utf8 "%SOURCE%\scripts\harness\sync_harness.py" --source "%SOURCE%" --target "%TARGET%"
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [WARNING] Harness update/validation reported errors. Please check output above.
    if "!NO_PAUSE!"=="0" pause
    exit /b 1
)

echo.
echo ============================================================================
echo  [SUCCESS] Terukirdo v5.6 harness synchronized, purged, and verified!
echo  Note: Restart any running 'agy' CLI session in the target project.
echo ============================================================================
if "!NO_PAUSE!"=="0" pause
(copy /Y "%SOURCE%\update_harness.bat" "%TARGET%\update_harness.bat" >nul 2>&1) & exit /b 0
