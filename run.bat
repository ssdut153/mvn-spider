@echo off
set /p num=Input num of process:
for /L %%i in (1,1,%num%) do (
if not exist mvn-spider-%%i (
mkdir mvn-spider-%%i
xcopy mvnrepository-spider mvn-spider-%%i /c /q /e
)
cd mvn-spider-%%i
start python main.py
cd ../
)