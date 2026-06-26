Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Error "Нет .venv. Создайте: py -3.12 -m venv .venv"
    exit 1
}

.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m streamlit run app.py
