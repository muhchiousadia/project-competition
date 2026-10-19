# CashFlow Sentinel AI

CashFlow Sentinel AI is a local Streamlit application for SME cash-flow forecasting, payment-delay and network stress scenarios, and evidence-based financial decision support. Bundled transaction and network data are synthetic.

## Technologies

- Python 3.11 or newer
- Streamlit for the web interface
- pandas for transaction processing
- Plotly for visualizations
- SQLite for local accounts and audit records
- pytest for automated tests

## Prerequisites

- Windows 10 or newer with PowerShell
- Python 3.11 or newer, available through the `py` launcher or `python.exe`
- Internet access for the initial dependency installation

Ollama is optional. The application works without it using its built-in Python Rule-Based chat.

## Install dependencies

Open PowerShell in the project folder (the folder containing `app.py`, `requirements.txt`, and `run_windows.bat`). If you opened a terminal in the outer `CashFlow_Sentinel_AI_FINAL_Developer_Build (1)` folder, first enter the actual project folder:

```powershell
Set-Location ".\CashFlow_Sentinel_AI_FINAL_backup_20261018_233300"
```

Then run these commands once:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

If `py -3.11` is unavailable, use an installed Python 3.11+ version, for example `py -3.12`, or create the environment with `python -m venv .venv` if the Python launcher is unavailable.

## Start the project

From the project folder in PowerShell (not the outer folder), run:

```powershell
.\run_windows.bat
```

This is the one-command startup option: the launcher creates `.venv` if it is missing, installs the dependencies from `requirements.txt`, and starts Streamlit. When the app is ready, open **http://localhost:8501**. If that port is busy, Streamlit prints the alternate local URL in the terminal. Stop the app with `Ctrl+C`.

After the dependencies have been installed, you can also start Streamlit directly:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\app.py
```

## Accounts, authentication, and database

No separate backend or database server is required. The app stores local accounts and audit records in SQLite at `data\cfs_security.sqlite3` by default.

- If the database has no accounts, use **Create your owner account** on the first-run screen. Passwords must be at least 12 characters.
- Once an account exists, use **Sign in**. Ask an existing owner to create additional accounts; public registration is not available.
- The existing project database is retained during cleanup. If it already contains accounts, sign in with the existing credentials.

To use a different database location, set `CFS_DB_PATH` in PowerShell before starting the app:

```powershell
$env:CFS_DB_PATH = "C:\CashFlowData\cfs_security.sqlite3"
.\run_windows.bat
```

Keep the database private and backed up; it contains account and audit data. This prototype's authentication is not intended for an internet-facing production deployment.

## Optional local AI

Ollama is only needed if you select **Ollama Local AI** in Finance Chat. Install Ollama, then run the selected model, for example:

```powershell
ollama run qwen2.5:3b
```

Leave Ollama running while using that mode. The built-in Python Rule-Based mode does not require Ollama or an API key. See [LOCAL_AI_SETUP.md](./LOCAL_AI_SETUP.md) for details.

## Tests

Run the automated tests from the project folder:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Safety and limitations

Forecasts and network stress simulations are deterministic scenarios, not calibrated probabilities or guarantees. Financing comparisons are illustrative, not lending offers or financial advice. The app does not connect to banks or execute payments, loans, or external messages. Verify supplied data and assumptions before making real financial decisions.
