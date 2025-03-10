@echo off
REM Enable delayed expansion for loops
setlocal EnableExtensions EnableDelayedExpansion

REM ---------------------------
REM Cleanup Code (Unchanged)
REM ---------------------------
echo Starting build process...

REM Remove the "build" and "dist" directories if they exist
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Remove any directory ending with .egg-info recursively
for /d /r %%d in (*.egg-info) do (
    rmdir /s /q "%%d"
)

REM Remove the OpenVPCal.spec file if it exists
if exist OpenVPCal.spec del /q OpenVPCal.spec

echo Cleanup complete.

REM ---------------------------
REM Remove existing uv environment directory (if applicable)
REM ---------------------------
echo Removing existing uv environment...
if exist .uv rmdir /s /q .uv
echo UV environment removed.

REM ---------------------------
REM Build Environment with uv
REM ---------------------------
echo Building environment with uv...
call uv build

REM ---------------------------
REM Run the compile.py script using uv
REM ---------------------------
echo Running compile.py using uv...
call uv run python compile.py

echo Build process finished successfully.

REM ---------------------------
REM Post Build Cleanup
REM ---------------------------
echo Post build cleanup...
if exist build rmdir /s /q build
for /d /r %%d in (*.egg-info) do (
    rmdir /s /q "%%d"
)
if exist OpenVPCal.spec del /q OpenVPCal.spec

echo Post cleanup complete.

endlocal