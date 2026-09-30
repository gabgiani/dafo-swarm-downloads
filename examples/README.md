# Examples

Runnable clients for the DAFO Swarm API. Every example reads `SWARM_URL`, which defaults to `http://127.0.0.1:43100`, and discovers the model id from `GET /v1/models`, so nothing is hard-coded.

```bash
export SWARM_URL=http://127.0.0.1:43100   # the coordinator
```

For the Python examples, run one command from the repository root:

```bash
# macOS / Linux
python3 examples/python/run.py
```

```powershell
# Windows PowerShell
py examples\python\run.py
```

`run.py` creates `examples/python/.venv`, installs the example dependencies there, then starts the menu using that environment. On later runs it reuses the environment and only installs again if `requirements.txt` changed. Use `python3 examples/python/run.py --install-only` when preparing a machine without opening the menu.

The first run asks for `SWARM_API_KEY` once, validates it and saves it as `examples/python/.env`. Later menu and individual-script runs reuse it automatically. The file is ignored by Git and is private to the current user on macOS/Linux. It marks the knowledge import that writes facts and asks for confirmation. The built-in tools option uses read-only mode, and the Office option lists documents by default.

Create a token in the dashboard under **Settings > API > API Access**. To run individual scripts without another prompt, set `SWARM_API_KEY` once in your terminal session:

```bash
# macOS / Linux (input is hidden)
read -rs SWARM_API_KEY; export SWARM_API_KEY; echo
examples/python/.venv/bin/python examples/python/chat.py "Explain OEE in two sentences."
```

```powershell
# Windows PowerShell
$env:SWARM_API_KEY = Read-Host "API token"
examples/python/.venv/Scripts/python.exe examples/python/menu.py
```

The environment variable takes priority over the saved key and lasts for that terminal session. To rotate a locally saved key, delete `examples/python/.env` and run the menu again. Chat prints `finish: stop` when the model ends normally and `finish: length` when it reaches the output limit. For a longer answer, run `python3 examples/python/chat.py --max-tokens 512 "Explain OEE in detail."` if the model has enough free context.

| Folder | Requirements | Contents |
|---|---|---|
| [curl](curl) | `curl`, `jq` | One script per endpoint |
| [python](python) | Python 3.9+, `python run.py` | OpenAI SDK, tool calling, agents, knowledge loading, built-in tools, Office documents |
| [javascript](javascript) | Node.js 20+, `npm install` | OpenAI SDK, streaming with `fetch`, knowledge, Office documents |

Scripts that **write** data create agents or knowledge facts on the coordinator:
- `curl/08-agents.sh`
- `curl/09-knowledge.sh`
- `python/load_knowledge_csv.py`
- `javascript/knowledge.mjs`

The Office document examples need a Word or Excel pane with **Share with swarm** enabled on the same Mac.

See [../docs/API.md](../docs/API.md) for the full reference.
