@echo off
REM Bootstrap script for Windows

REM Activate conda environment - replace YOUR_ENV_NAME with your conda environment name
call conda activate nft-data

REM compile smart contracts
call npx hardhat compile

REM remove any left over assets from watermarking
if exist "src\lsb_watermarking\input\0" (
    for /d %%d in ("src\lsb_watermarking\input\0\*") do rmdir /s /q "%%d"
    del /q "src\lsb_watermarking\input\0\*" 2>nul
)
if exist "src\lsb_watermarking\output\imgs" (
    for /d %%d in ("src\lsb_watermarking\output\imgs\*") do rmdir /s /q "%%d"
    del /q "src\lsb_watermarking\output\imgs\*" 2>nul
)
if exist "images" (
    for /d %%d in ("images\*") do rmdir /s /q "%%d"
    del /q "images\*" 2>nul
)

REM empty contents of contracts list
type nul > contracts.json

REM remove the current database and create new one from schema
if exist "src\db\demo.db" del /q "src\db\demo.db"
type "src\db\schema.sql" | sqlite3 "src\db\demo.db"

REM seed the database with test data
type "src\db\seed.sql" | sqlite3 "src\db\demo.db"

REM start a eth node in background
start "Hardhat Node" cmd /c "npx hardhat node"

REM wait a bit for the node to start
timeout /t 3 /nobreak >nul

REM run main app
streamlit run src/app.py

