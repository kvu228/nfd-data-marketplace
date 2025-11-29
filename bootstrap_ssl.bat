@echo off
REM Bootstrap script for Windows

REM Activate conda environment - replace YOUR_ENV_NAME with your conda environment name
call conda activate nft-data

REM compile smart contracts
call npx hardhat compile

REM remove any left over assets from watermarking
if exist "src\ssl_watermarking\input\0" (
    for /d %%d in ("src\ssl_watermarking\input\0\*") do rmdir /s /q "%%d"
    del /q "src\ssl_watermarking\input\0\*" 2>nul
)
if exist "src\ssl_watermarking\output\imgs" (
    for /d %%d in ("src\ssl_watermarking\output\imgs\*") do rmdir /s /q "%%d"
    del /q "src\ssl_watermarking\output\imgs\*" 2>nul
)
if exist "images" (
    for /d %%d in ("images\*") do rmdir /s /q "%%d"
    del /q "images\*" 2>nul
)

REM empty contents of contracts list
type nul > contracts.json

REM Check and download out2048_yfcc_orig.pth if needed
if not exist "src\ssl_watermarking\normlayers\out2048_yfcc_orig.pth" (
    echo Did not detect out2048_yfcc_orig.pth. Downloading fresh copy to src\ssl_watermarking\normlayers...
    
    if not exist "src\ssl_watermarking\normlayers" mkdir "src\ssl_watermarking\normlayers"
    curl -k -L -o "src\ssl_watermarking\normlayers\out2048_yfcc_orig.pth" https://dl.fbaipublicfiles.com/ssl_watermarking/out2048_yfcc_orig.pth
)

REM Check and download dino_r50_plus.pth if needed
if not exist "src\ssl_watermarking\models\dino_r50_plus.pth" (
    echo Did not detect dino_r50_plus.pth. Downloading fresh copy to src\ssl_watermarking\models...
    
    if not exist "src\ssl_watermarking\models" mkdir "src\ssl_watermarking\models"
    curl -k -L -o "src\ssl_watermarking\models\dino_r50_plus.pth" https://dl.fbaipublicfiles.com/ssl_watermarking/dino_r50_plus.pth
)

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

