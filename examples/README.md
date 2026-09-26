# Examples

Runnable clients for the DAFO Swarm API. Every example reads `SWARM_URL`, which defaults to `http://127.0.0.1:43100`, and discovers the model id from `GET /v1/models`, so nothing is hard-coded.

```bash
export SWARM_URL=http://127.0.0.1:43100   # the coordinator
```

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
