@echo off
echo Running HVAC System Diagnosis...
cd /d "%~dp0"
streamlit run diagnose.py
pause