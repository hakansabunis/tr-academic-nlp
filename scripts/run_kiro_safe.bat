@echo off
REM Safe single-paragraph mode for Kiro with low quota
REM Spreads 45 paragraphs over time with generous pauses

cd /d C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp

echo.
echo ============================================================
echo Kiro's Safe Labeling (Single-Paragraph Mode)
echo ============================================================
echo.
echo Running 45 paragraphs with 20s pause between each
echo This is much safer for Pro tier with low remaining quota
echo.
echo Expected time: ~12-15 minutes
echo.

python scripts/batch_label_via_claude_cli.py --paragraphs data/corpora/smoke-2k/paragraphs-B.jsonl --output docs/labeler-eval/cli-haiku-B.jsonl --model haiku --batch-size 1 --pause-seconds 20 --limit 45

echo.
echo ============================================================
if %ERRORLEVEL% equ 0 (
    echo SUCCESS! 45 paragraphs labeled.
) else (
    echo FAILED with exit code %ERRORLEVEL%
)
echo ============================================================
echo.

pause
