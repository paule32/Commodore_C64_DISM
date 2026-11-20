@echo off
rem Kompatibilitaet: Stage 652 darf keinen separaten Help-Host mehr bauen.
call "%~dp0build_and_deploy_dbase_editor_stage653.bat" %*
exit /b %errorlevel%
