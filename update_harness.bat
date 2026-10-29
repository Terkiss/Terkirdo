@echo off
setlocal EnableDelayedExpansion

:: ============================================================================
:: Terukirdo v5.6 Harness Updater
:: - Updates core harness files (.agents, scripts, docs/harness, reference,
::   AGENTS.md, Terukirdo_Protocol_v5.6.md) from the master template.
:: - Preserves target project's .git, README.md, MEMORY.md, docs/specs, state.
:: ============================================================================

set "SOURCE=D:\Project\codex-flutter\newAntigravity"
set "TARGET=%~dp0"
if "%TARGET:~-1%"=="\" set "TARGET=%TARGET:~0,-1%"

echo ============================================================================
echo  [Terukirdo v5.6] Harness Updater
echo ============================================================================

if not exist "%SOURCE%\.agents\agents\agy-worker\agent.md" (
    echo [ERROR] Master template not found at: "%SOURCE%"
    pause
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
        pause
        exit /b 1
    )
    set "USER_TARGET=!USER_TARGET:"=!"
    if "!USER_TARGET:~-1!"=="\" set "USER_TARGET=!USER_TARGET:~0,-1!"
    set "TARGET=!USER_TARGET!"
)

if /I "%TARGET%"=="%SOURCE%" (
    echo [SKIP] Source and target are identical. Aborting.
    pause
    exit /b 1
)

if not exist "%TARGET%" (
    echo [ERROR] Target directory does not exist: "%TARGET%"
    pause
    exit /b 1
)

echo.
echo  * Source Template : "%SOURCE%"
echo  * Target Project  : "%TARGET%"
echo  * Preserved       : .git, README.md, MEMORY.md, docs/specs, .agents/state
echo.

echo [1/5] Updating .agents (agents, hooks, rules, schemas, skills)...
robocopy "%SOURCE%\.agents" "%TARGET%\.agents" /E /XD state __pycache__ .pytest_cache /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if !ERRORLEVEL! GEQ 8 (
    echo [ERROR] Failed to copy .agents directory.
    pause
    exit /b 1
)
if not exist "%TARGET%\.agents\state" mkdir "%TARGET%\.agents\state"

echo [2/5] Updating scripts (validate_harness.py, hermes_disasm.py, etc.)...
robocopy "%SOURCE%\scripts" "%TARGET%\scripts" /E /XD __pycache__ .pytest_cache /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if !ERRORLEVEL! GEQ 8 (
    echo [ERROR] Failed to copy scripts directory.
    pause
    exit /b 1
)

echo [3/5] Updating docs\harness and reference...
robocopy "%SOURCE%\docs\harness" "%TARGET%\docs\harness" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul
robocopy "%SOURCE%\reference" "%TARGET%\reference" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul

echo [4/5] Updating AGENTS.md and Terukirdo_Protocol_v5.6.md...
copy /Y "%SOURCE%\Terukirdo_Protocol_v5.6.md" "%TARGET%\Terukirdo_Protocol_v5.6.md" >nul
copy /Y "%SOURCE%\AGENTS.md" "%TARGET%\AGENTS.md" >nul

if not exist "%TARGET%\MEMORY.md" (
    echo       - Creating initial MEMORY.md...
    copy /Y "%SOURCE%\MEMORY.md" "%TARGET%\MEMORY.md" >nul
) else (
    echo       - Existing MEMORY.md preserved.
)

if not exist "%TARGET%\docs" mkdir "%TARGET%\docs"
if not exist "%TARGET%\docs\Terukirdo_Trajectory.txt" (
    echo       - Creating initial docs\Terukirdo_Trajectory.txt...
    type nul > "%TARGET%\docs\Terukirdo_Trajectory.txt"
) else (
    echo       - Existing docs\Terukirdo_Trajectory.txt preserved.
)

echo [5/5] Running validate_harness.py --strict...
python "%TARGET%\scripts\harness\validate_harness.py" --strict
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [WARNING] Harness validation reported errors. Please check output above.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo  [SUCCESS] Terukirdo v5.6 harness updated and verified!
echo  Note: Restart any running 'agy' CLI session in the target project.
echo ============================================================================
if "%~1"=="--no-pause" exit /b 0
pause
exit /b 0
