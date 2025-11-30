# Exotrac AI Chatbot

Quick start:

- Install dependencies (recommended in the repo venv):

```powershell
python -m pip install -r .\requirements.txt
```

- Run in production mode (requires `OPENAI_API_KEY` set in your environment):

```powershell
# set the env var for the current PowerShell session
$env:OPENAI_API_KEY = "your_openai_api_key_here"
# run
& "C:/Users/rosha/OneDrive/Desktop/1 python/.venv/Scripts/python.exe" .\main.py
```

- Run in local/mock mode (no OpenAI key required) for development or testing:

```powershell
& "C:/Users/rosha/OneDrive/Desktop/1 python/.venv/Scripts/python.exe" .\main.py --local
```

Notes:
- The dataset has been moved to `training_dataset.json` (previously contained in `new.py`).
- Use `--local` to run without making calls to the OpenAI API; the bot will return simple mock responses.
- To fully use the chatbot in production, set `OPENAI_API_KEY` in your environment.

If you'd like, I can:
- Add a small unit test to validate dataset loading and local-mode behavior.
- Commit these changes to a Git branch and create a changelog.
