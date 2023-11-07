@echo on

REM Check if directories/files exist, and if so, delete them
if exist myenv rmdir /s /q myenv
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist Output rmdir /s /q Output
if exist OpenVPCal.spec del /F OpenVPCal.spec

REM Create Python virtual environment and install dependencies
py -m venv myenv
call myenv\Scripts\activate
pip install -r requirements.txt
pip freeze > requirements.txt
py compile.py
call deactivate

REM Check if directories/files exist, and if so, delete them
if exist build rmdir /s /q build
if exist myenv rmdir /s /q myenv
if exist OpenVPCal.spec del /F OpenVPCal.spec
