# CashFlow Sentinel AI — Final Developer Build

## Included
- Streamlit SME cash-flow dashboard and forecasting engine
- CSV validation and data-quality checks
- Payment-delay scenario simulation
- Network shock propagation
- Explainable financial risk radar and counterparty exposure views
- Illustrative financing comparison and scenario tools
- Role-aware local demo authentication and SQLite review audit trail
- Finance Chat: Python rule-based mode and optional Ollama local model mode
- Automated tests, evidence scripts, setup guides, architecture/security docs
- Synthetic small and larger stress-test datasets

## Run (Windows PowerShell, from this folder)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```
If Python 3.12 is not installed, install it from python.org. Python 3.11 or 3.12 is recommended for dependency compatibility.

## Local AI
Install Ollama, then run `ollama run qwen2.5:3b`. In Finance Chat choose Ollama Local AI and use model `qwen2.5:3b`, URL `http://localhost:11434`. Python Rule-Based mode needs no model or API key.

## Important limits
Bundled data is synthetic. Forecasts and network propagation are deterministic simulations, not calibrated probability predictions. Financing choices are illustrative, not live lender offers. No real payment, loan approval, bank transaction, or external message is executed. Local authentication and audit logs are prototype-grade; do not expose the demo publicly or upload sensitive real financial data. Ollama live behavior depends on the user's local installation and model download.
