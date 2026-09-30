# Examples

Runnable clients for the DAFO Swarm API. Every example reads `SWARM_URL`, which defaults to `http://127.0.0.1:43100`, and discovers the model id from `GET /v1/models`, so nothing is hard-coded.

```bash
export SWARM_URL=http://127.0.0.1:43100   # the coordinator
```

For the Python examples, run from their folder:

```bash
cd examples/python
python3 -m pip install -r requirements.txt
python3 chat.py "Explain OEE in two sentences."
```

Chat prints `finish: stop` when the model ends normally and `finish: length` when it reaches the output limit. For a longer answer, run `python3 chat.py --max-tokens 512 "Explain OEE in detail."` if the model has enough free context.

The script asks for your API token if `SWARM_API_KEY` or `SWARM_API_TOKEN` is not set. Create it in the dashboard under **Settings > Server > Account > API tokens**. Paste it at the hidden prompt and press Enter; nothing will appear while you type. The script uses the token only for that run. You can also set `SWARM_API_KEY` in your environment to avoid the prompt on each run.

| Folder | Requirements | Contents |
|---|---|---|
| [curl](curl) | `curl`, `jq` | One script per endpoint |
| [python](python) | Python 3.9+, `pip install -r requirements.txt` | OpenAI SDK, tool calling, agents, knowledge loading, built-in tools, Office documents |
| [javascript](javascript) | Node.js 20+, `npm install` | OpenAI SDK, streaming with `fetch`, knowledge, Office documents |

Scripts that **write** data create agents or knowledge facts on the coordinator:
- `curl/08-agents.sh`
- `curl/09-knowledge.sh`
- `python/load_knowledge_csv.py`
- `javascript/knowledge.mjs`

The Office document examples need a Word or Excel pane with **Share with swarm** enabled on the same Mac.

See [../docs/API.md](../docs/API.md) for the full reference.
