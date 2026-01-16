@echo off
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║              GITHUB PROFILE VIEW API                      ║
echo ║                                                           ║
echo ║              Created by: dewhush                          ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo Starting API server...
echo.

uvicorn api:app --host 0.0.0.0 --port 8000 --reload

pause
