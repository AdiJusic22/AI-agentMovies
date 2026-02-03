@echo off
echo ========================================
echo Pokretanje Movie Recommender Agent-a
echo ========================================
echo.
echo Background runner ce raditi autonomno!
echo Server: http://localhost:8001
echo.
python -m uvicorn src.interface.api:app --host 0.0.0.0 --port 8001
