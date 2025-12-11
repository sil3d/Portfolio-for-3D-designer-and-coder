@echo off
echo Setting up Flask environment...
set FLASK_ENV=development
set FLASK_APP=run.py

echo Starting Portfolio Server...
python run.py --host=0.0.0.0 --port=5000 --debug
pause
