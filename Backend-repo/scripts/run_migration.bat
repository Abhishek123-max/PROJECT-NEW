@echo off
echo Running Migration to Add Phone Column...
cd %~dp0..
python scripts\run_migration.py
pause