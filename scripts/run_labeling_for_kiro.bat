@echo off
REM Batch labeling script for Kiro's terminal
REM Run this from: C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp\
REM
REM Usage: run_labeling_for_kiro.bat [batch_number]
REM   batch_number: 1-22 (process 45 paragraphs per batch, ~5h per batch)
REM
REM Example: run_labeling_for_kiro.bat 1
REM   Processes paragraphs 0-44 (first 45)
REM
REM Then wait ~5 hours and run again:
REM   run_labeling_for_kiro.bat 2
REM   Processes paragraphs 45-89 (next 45)

setlocal enabledelayedexpansion

REM Get batch number from argument or default to 1
set BATCH_NUM=%1
if "%BATCH_NUM%"=="" set BATCH_NUM=1

REM Calculate paragraph limit (45 per batch)
set /a LIMIT=!BATCH_NUM! * 45

echo.
echo ============================================================
echo Batch Labeling for Kiro - Batch #%BATCH_NUM% (Limit: %LIMIT% paragraphs)
echo ============================================================
echo.
echo Settings:
echo   - Model: haiku (Kiro's available Claude)
echo   - Batch size: 15 paragraphs per call
echo   - Pause: 300s (5 min) between batches to stay under rate limits
echo   - Resume: Safe - will skip already-completed paragraphs
echo.
echo Starting in 5 seconds (Ctrl+C to cancel)...
timeout /t 5

python scripts/batch_label_via_claude_cli.py ^
  --paragraphs data/corpora/smoke-2k/paragraphs-B.jsonl ^
  --output docs/labeler-eval/cli-haiku-B.jsonl ^
  --model haiku ^
  --batch-size 15 ^
  --batch-pause-seconds 300 ^
  --limit %LIMIT%

echo.
echo ============================================================
if %ERRORLEVEL% equ 0 (
    echo SUCCESS! Batch #%BATCH_NUM% completed.
    echo.
    echo Next steps:
    echo   1. Wait ~5 hours for rate limits to reset
    echo   2. Run: run_labeling_for_kiro.bat %BATCH_NUM%+1
) else (
    echo ERROR! Batch #%BATCH_NUM% failed with code %ERRORLEVEL%
    echo Check the error messages above.
)
echo ============================================================
echo.

endlocal
