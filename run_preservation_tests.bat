@echo off
echo Running Preservation Property Tests (Task 2)...
echo Current TIMEOUT_SECS should be 120 (unfixed code)
echo These tests should PASS on unfixed code (baseline behavior)
echo.
python -m pytest test_lesson_timeout_bugfix.py::TestPreservation -v
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Trying alternative test runner...
    python -m unittest test_lesson_timeout_bugfix.TestPreservation
)
pause
