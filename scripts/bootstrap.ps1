$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

function Assert-NativeSuccess {
    if ($LASTEXITCODE -ne 0) { throw 'The preceding setup command failed. Stop before continuing.' }
}

if (-not (Test-Path '.local/tooling/Scripts/uv.exe')) {
    py -3.11 -m venv .local/tooling
    Assert-NativeSuccess
    & .local/tooling/Scripts/python.exe -m pip install --timeout 120 --retries 3 uv==0.12.21
    Assert-NativeSuccess
}
$env:UV_PYTHON_INSTALL_DIR = Join-Path (Get-Location) '.local/python'
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
$env:npm_config_cache = Join-Path (Get-Location) '.cache/npm'
& .local/tooling/Scripts/uv.exe python install 3.12 --no-bin --no-registry
Assert-NativeSuccess
& .local/tooling/Scripts/uv.exe sync --frozen --python 3.12
Assert-NativeSuccess
& .venv/Scripts/python.exe scripts/local_config.py
Assert-NativeSuccess
& .venv/Scripts/python.exe scripts/install_postgres.py
Assert-NativeSuccess
& .venv/Scripts/python.exe scripts/database.py init
Assert-NativeSuccess
& .venv/Scripts/python.exe scripts/database.py start
Assert-NativeSuccess
& .venv/Scripts/python.exe scripts/database.py create
Assert-NativeSuccess
& .venv/Scripts/python.exe scripts/database.py migrate
Assert-NativeSuccess
& npm.cmd --prefix frontend ci --no-audit --no-fund
Assert-NativeSuccess
Write-Output 'Local foundation setup completed. Medicine sources are verified separately.'
