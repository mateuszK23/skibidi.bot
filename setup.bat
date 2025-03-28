@echo off

REM Set up path variables
SET THIRDPARTY_DIR=thirdparty
SET REQ_PATH=src\requirements.txt
SET SETUP_PATH=src\setup.py
SET FFMPEG_PATH=thirdparty\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe
SET FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
SET FFMPEG_ARCHIVE=ffmpeg-release-i686-static.zip

REM Check if Python is installed
where python > nul 2> nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Installing Python...

    REM Download the latest Python installer (this will download the 64-bit version)
    SET PYTHON_INSTALLER=python-installer.exe
    curl -L https://www.python.org/ftp/python/3.9.6/python-3.9.6-amd64.exe -o %PYTHON_INSTALLER%

    REM Install Python silently
    %PYTHON_INSTALLER% /quiet InstallAllUsers=1 PrependPath=1

    REM Clean up installer after installation
    del %PYTHON_INSTALLER%

    REM Check if installation was successful
    where python > nul 2> nul
    IF %ERRORLEVEL% NEQ 0 (
        echo Python installation failed. Please install Python manually.
        pause
        exit /b
    )
    echo Python installed successfully.
) ELSE (
    echo Python is already installed.
)

REM Ensure "py" launcher works (it should automatically work if Python is installed)
where py > nul 2> nul
IF %ERRORLEVEL% NEQ 0 (
    echo "py" launcher is not found. Please ensure that it is installed and available in your PATH.
    pause
    exit /b
)

REM Install ffmpeg if it's not already installed
IF NOT EXIST %FFMPEG_PATH% (
    echo ffmpeg is not installed. Installing ffmpeg...

    REM Download the latest ffmpeg static build in .zip format
    curl -L %FFMPEG_URL% -o %FFMPEG_ARCHIVE%

    REM Verify that the file downloaded correctly
    IF NOT EXIST %FFMPEG_ARCHIVE% (
        echo Download failed. The file was not downloaded correctly.
        pause
        exit /b
    )

    REM Extract the downloaded .zip archive using PowerShell
    powershell -Command "Expand-Archive -Path .\%FFMPEG_ARCHIVE% -DestinationPath %THIRDPARTY_DIR%"

    REM Check if ffmpeg was successfully extracted
    IF EXIST %FFMPEG_PATH% (
        echo ffmpeg installed successfully.
    ) ELSE (
        echo ffmpeg installation failed. The file might be corrupt or invalid.
        pause
        exit /b
    )

    REM Clean up the archive after extraction
    del %FFMPEG_ARCHIVE%

) ELSE (
    echo ffmpeg is already installed.
)

REM Install required packages from requirements.txt
IF EXIST %REQ_PATH% (
    echo Installing packages from %REQ_PATH%...
    pip install -r %REQ_PATH%
) ELSE (
    echo %REQ_PATH% not found. Skipping package installation.
)

REM Run setup.py if it exists
IF EXIST %SETUP_PATH% (
    echo Running setup.py from %SETUP_PATH%...
    py %SETUP_PATH%
) ELSE (
    echo %SETUP_PATH% not found. Skipping setup script execution.
)

echo Installation and setup complete.
pause
