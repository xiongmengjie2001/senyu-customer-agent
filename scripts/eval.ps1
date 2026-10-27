$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
python eval/run_eval.py
exit $LASTEXITCODE
