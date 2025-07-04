$scriptPath = $PSScriptRoot
Set-Location -Path $scriptPath

if (Test-Path .\.venv\Scripts\Activate.ps1) {
    .\.venv\Scripts\Activate.ps1
} else {
    Write-Error "Virtual environment activation script not found!"
    exit 1
}

python main.py