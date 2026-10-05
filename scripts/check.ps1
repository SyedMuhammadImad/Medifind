$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
function Assert-NativeSuccess {
    if ($LASTEXITCODE -ne 0) { throw 'The preceding verification command failed.' }
}
& .venv/Scripts/ruff.exe check backend scripts
Assert-NativeSuccess
& .venv/Scripts/ruff.exe format --check backend scripts
Assert-NativeSuccess
& .venv/Scripts/python.exe scripts/verify_sample.py
Assert-NativeSuccess
& .venv/Scripts/python.exe scripts/verify_p2.py
Assert-NativeSuccess
& .venv/Scripts/python.exe -m pytest
Assert-NativeSuccess
& npm.cmd --prefix frontend run build
Assert-NativeSuccess
