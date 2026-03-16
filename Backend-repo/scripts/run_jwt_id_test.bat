@echo off
echo Running JWT ID Assignment Test...
cd %~dp0..
python scripts\test_jwt_id_assignment.py
pause