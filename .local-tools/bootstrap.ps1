param(
    [string]$Vault = "C:\Users\delib\Desktop\OMNISVERA"
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $Vault

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv não está instalado."
}
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "Ollama não está instalado."
}

uv python install 3.13
uv venv .omnisvera-tools --python 3.13
uv pip install --python .omnisvera-tools\Scripts\python.exe `
    pyyaml ruamel.yaml pymupdf pypdf pillow pytesseract python-frontmatter `
    rapidfuzz jsonschema networkx ollama markdown-it-py beautifulsoup4 lxml `
    chardet rich "mcp[cli]"

ollama pull nomic-embed-text
ollama pull qwen2.5-coder:1.5b
ollama pull qwen2.5-coder:7b
ollama create omnisvera-fast -f .ollama\Modelfile.omnisvera-fast
ollama create omnisvera-local -f .ollama\Modelfile.omnisvera-local

.omnisvera-tools\Scripts\python.exe .local-tools\vault_tools.py index
.omnisvera-tools\Scripts\python.exe .local-tools\vault_tools.py audit

Write-Output "Ambiente local restaurado."
