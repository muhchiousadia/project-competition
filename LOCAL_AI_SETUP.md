# CashFlow Sentinel AI v0.9 Final — Local AI + Rule-Based Chat 


- Python Rule-Based Chat: offline, no API key, deterministic supported-topic responses.
- Ollama Local AI: optional local language model for natural-language explanations.
- Financial calculations, forecast and stress tests remain in Python. The LLM cannot execute payments or loans.
- Evidence table and uncertainty note are shown with chat responses.

## 1. Install Ollama (optional)
1. Windows installer: https://ollama.com/download
2. Open a new PowerShell/VS Code terminal and run: `ollama run qwen2.5:3b`
3. Wait for model download and test a prompt. Type `/bye` to exit.
4. Confirm model exists with: `ollama list`
5. Ollama must be running while you use Local AI mode. Default URL: `http://localhost:11434`.

For 8 GB RAM, start with `qwen2.5:3b`. If it is too slow, try `ollama run qwen2.5:1.5b` and enter `qwen2.5:1.5b` in the dashboard model field.

## 2. Install project dependencies
Open the `source_code` folder in VS Code, then run:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Run
```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```

Create the local owner account on first run; use a unique password of at least 12 characters. This local authentication is for prototype/demo use only.

## 4. Use chat
Go to `8. Finance Chat — Python Rules + Free Local AI`. Select either:
- `Python Rule-Based (offline)`: works without Ollama or internet and supports a limited set of finance questions.
- `Ollama Local AI (free)`: requires Ollama running and the selected model downloaded.

Try: `Why is my cash decreasing?`, `Is there a cash shortage risk?`, `Which customer payments matter most?`, or `help`.

## Troubleshooting
- `ollama is not recognized`: restart terminal after installation or check Ollama installation.
- Connection refused: open Ollama desktop app or run `ollama serve` in a separate terminal if needed.
- Model not found: run `ollama pull qwen2.5:3b`, then `ollama list`.
- Slow response: close other apps or use `qwen2.5:1.5b`.
- If local model fails, switch to Python Rule-Based mode.

## Data privacy and limitations
Local Ollama requests are sent to the local Ollama service at the configured URL. The app sends the selected business's compact transaction/forecast context (up to 30 rows each) to that local model. Keep the URL local unless you deliberately configure a trusted server. Model output may hallucinate; verify amounts against the evidence table. No real bank, loan, payment, email, or external action is connected. Bundled data are synthetic. This is a prototype, not production financial software.
