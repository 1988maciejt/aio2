SET mypath=%~dp0
SET mydir=%mypath:~0,-1%
SET currpath=%CD%
cd %mydir%
python3 -m ptpython -i --config-file ptpython_config.py aio2.py %currpath%