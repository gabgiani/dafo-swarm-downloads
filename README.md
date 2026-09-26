# DAFO Swarm — Downloads, API documentation and examples

**DAFO Swarm** runs large language models across the machines you already own. It splits a model's layers between Macs, NVIDIA workstations and servers on your network. The result is served through an **OpenAI-compatible API** and bundled **Word and Excel copilots**. Prompts, documents and knowledge stay on your hardware.

- Website: <https://swarm.dafonet.com>
- Latest release: <https://github.com/gabgiani/dafo-swarm-downloads/releases/latest>
- Full API reference: [docs/API.md](docs/API.md)
- Runnable examples: [examples/](examples/)

This repository contains the public **installers** and their **checksums**, plus the **API documentation** and **client examples**. The runtime source code is private.

---

## Downloads

| Platform | Package | Acceleration | Install |
|---|---|---|---|
| macOS 26.5+ on Apple Silicon (M1–M4) | `dafo-swarm-<version>-macos-arm64.pkg` | Metal / MLX | Open the package and approve one admin prompt |
| Ubuntu 24.04 x86_64 with an NVIDIA GPU (compute capability 8.6+, driver 525.60+) | `dafo-swarm-cuda_<version>_amd64.deb` | CUDA 12 runtime bundled | `sudo apt install ./dafo-swarm-cuda_<version>_amd64.deb` |
| Windows 11 / Server | coming soon | CUDA / CPU | — |
| Linux x86_64 CPU only | coming soon | CPU | — |

Every release contains the packages and a `.sha256` file for each one. Release tags follow `v0.1.0-YYYYMMDD.N`.

### Always download the latest version

The installed apps check these manifests every 6 hours and offer a one-click update:

```bash
curl -s https://swarm.dafonet.com/downloads/macos-arm64.json
curl -s https://swarm.dafonet.com/downloads/ubuntu24.04-cuda.json
```

Each manifest has these fields:
- `version`
- `artifact`
- `bytes`
- `sha256`
- `minimum_os`
- `download_url`, which points to this repository

To script an install:

```bash
MANIFEST=$(curl -s https://swarm.dafonet.com/downloads/ubuntu24.04-cuda.json)
URL=$(echo "$MANIFEST" | jq -r .download_url)
SHA=$(echo "$MANIFEST" | jq -r .sha256)
curl -L -o dafo-swarm.deb "$URL"
echo "$SHA  dafo-swarm.deb" | sha256sum -c -
sudo apt install ./dafo-swarm.deb
```

### Verify a download

```bash
shasum -a 256 -c dafo-swarm-<version>-macos-arm64.pkg.sha256      # macOS
sha256sum -c dafo-swarm-cuda_<version>_amd64.deb.sha256            # Linux
spctl -a -vv -t install dafo-swarm-<version>-macos-arm64.pkg       # macOS: "Notarized Developer ID"
```

---

## Installation

### macOS

1. Download the `.pkg` from the [latest release](https://github.com/gabgiani/dafo-swarm-downloads/releases/latest) and open it.
2. Approve the administrator prompt. The package is signed with an Apple Developer ID and notarized by Apple.
3. The **DAFO Swarm** icon appears in the menu bar. It runs the node as a background agent. **Open Chat** and **Open Settings** open the dashboard at <http://127.0.0.1:43100>.
4. The menu bar app asks once to trust a local certificate. That lets the Word and Excel add-ins load from `https://localhost`.

**Updates:** the menu bar shows **Update available: vX**. Click it: the app downloads the package from this repository, verifies its SHA-256 and signature, and installs it after a single admin prompt.

### Ubuntu 24.04 with NVIDIA

```bash
sudo apt install ./dafo-swarm-cuda_<version>_amd64.deb
systemctl --user status dafo-swarm.service      # inference node
systemctl --user status dafo-swarm-tray.service # tray icon and automatic updates
```

The package bundles the CUDA 12 runtime libraries it needs. Only the NVIDIA driver must be installed. Logs are in `~/.local/share/dafo-swarm/logs/`.

---

## First steps

1. On the machine that will coordinate, open the dashboard at <http://127.0.0.1:43100>.
2. **Create a room**, or **join** an existing one with its 6-digit code on the other machines.
3. **Model:** download or select a model from the catalogue (Gemma 4 E2B, E4B, 12B or 26B A4B, Qwen and others).
4. **Nodes and Distribution:** choose which machines run which layers, then preview and approve the plan.
5. When every node shows **Ready**, use the chat, the Office add-ins or the API.

Nodes on the same network connect directly. Across networks they first meet through the DAFO relay, and inference traffic then travels directly between the machines.

---

## Word and Excel add-ins (macOS)

The macOS package adds a **DAFO Swarm** button to the Home tab of Word and Excel. Its pane:

- **Word:** writes and edits documents from a request: proposals, letters, reports, cover pages, tables and translations. Every change is shown as a proposal you **Apply** or **Discard**.
- **Excel:** builds spreadsheets: tables, titles, formulas, totals, formats and new worksheets. It reads only the cells it needs.
- **Agents:** uses the agent you choose, so answers follow that agent's instructions and knowledge base.
- **Shared documents:** can **share its document with the swarm**. Other panes can then mention it (for example `@Costos.xlsx`), and the dashboard chat can read it or send it changes. A change that comes from elsewhere is applied only after that document's user approves it.

---

## API in 30 seconds

The coordinator serves an OpenAI-compatible API on port `43100`:

```bash
MODEL=$(curl -s http://127.0.0.1:43100/v1/models | jq -r '.data[0].id')

curl -s http://127.0.0.1:43100/v1/chat/completions \
  -H 'content-type: application/json' \
  -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}" \
  | jq -r '.choices[0].message.content'
```

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:43100/v1", api_key="unused")
model = client.models.list().data[0].id
reply = client.chat.completions.create(model=model, messages=[{"role": "user", "content": "Hello"}])
print(reply.choices[0].message.content)
```

| Endpoint | Purpose |
|---|---|
| `GET /v1/models` | Returns the active model id |
| `GET /v1/agents` | Lists the enabled agents |
| `POST /v1/chat/completions` | Chat, with streaming, images, function tools and an optional `agent` |
| `POST /v1/responses` | Responses API with files and MCP tools, including the built-in `builtin://chat` tools |
| `/api/agents…` | Create, update and delete agents |
| `/api/agents/{id}/knowledge…` | Manage and search an agent's knowledge base |
| `https://localhost:43110/api/swarm/documents…` | Documents shared from the Office add-ins |

Every endpoint is documented with request and response examples in **[docs/API.md](docs/API.md)**.

> **Security:** the node API has no authentication. Keep it on `127.0.0.1` or on a network you control. If you expose it, put a reverse proxy with authentication in front of it.

---

## Examples

| Folder | What it shows |
|---|---|
| [examples/curl](examples/curl) | Every endpoint from the shell: chat, streaming, images, tools, Responses, agents, knowledge and Office documents |
| [examples/python](examples/python) | The official `openai` SDK and `requests`: chat, streaming, tool calling, agents, loading knowledge from a CSV and the built-in MCP tools |
| [examples/javascript](examples/javascript) | Node.js 20+: the `openai` SDK and plain `fetch`, streaming, loading knowledge and Office documents |

All examples read the `SWARM_URL` environment variable (default `http://127.0.0.1:43100`).

---

## Support

For installation or API questions, open an issue in this repository. Include the version (from the menu bar, or from `dpkg -l dafo-swarm-cuda`) and the relevant log lines.
