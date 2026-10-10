# DAFO Swarm — Downloads, API documentation and examples

**DAFO Swarm** runs large language models across the machines you already own. It splits a model's layers between Macs, NVIDIA workstations and servers on your network. The result is served through an **OpenAI-compatible API** and bundled **Word and Excel copilots**. Prompts, documents and knowledge stay on your hardware.

- Website: <https://swarm.dafonet.com>
- Latest release: <https://github.com/gabgiani/dafo-swarm-downloads/releases/latest>
- Full API reference: [docs/API.md](docs/API.md)
- Agents that work together (subagents, shared workspace, design advice): [docs/AGENTS.md](docs/AGENTS.md)
- Runnable examples: [examples/](examples/)

This repository contains the public **installers** and their **checksums**, plus the **API documentation** and **client examples**. The runtime source code is private.

---

## Downloads

| Platform | Package | Acceleration | Install |
|---|---|---|---|
| macOS 26.5+ on Apple Silicon (M1–M4) | `dafo-swarm-<version>-macos-arm64.pkg` | Metal / MLX | Open the package and approve one admin prompt |
| Ubuntu 24.04 x86_64 with an NVIDIA GPU (compute capability 8.6+, driver 525.60+) | `dafo-swarm-cuda_<version>_amd64.deb` | CUDA 12 runtime bundled | `sudo apt install ./dafo-swarm-cuda_<version>_amd64.deb` |
| Windows 10 / 11 x64 (NVIDIA GPU optional) | `dafo-swarm-setup_<version>_x64.exe` | CUDA 12 when an NVIDIA GPU is present, otherwise CPU | Run the installer; no administrator rights needed |
| Linux x86_64 CPU only | coming soon | CPU | — |

Releases starting with `v0.1.0-20260926.3` include a `.sha256` file for each package. For every release, the checksum is also in the `sha256` field of the manifests below. Release tags follow `v0.1.0-YYYYMMDD.N`.

### Always download the latest version

The installed apps check these manifests every 6 hours and offer a one-click update:

```bash
curl -s https://swarm.dafonet.com/downloads/macos-arm64.json
curl -s https://swarm.dafonet.com/downloads/ubuntu24.04-cuda.json
curl -s https://swarm.dafonet.com/downloads/windows-x64.json
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

On Windows, in PowerShell:

```powershell
(Get-FileHash .\dafo-swarm-setup_<version>_x64.exe -Algorithm SHA256).Hash   # compare with the .sha256 file
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

### Windows 10 / 11

1. Download `dafo-swarm-setup_<version>_x64.exe` from the [latest release](https://github.com/gabgiani/dafo-swarm-downloads/releases/latest) and run it.
2. The installer is per user: it installs into `%LOCALAPPDATA%\Programs\DAFO Swarm` and needs no administrator rights. It is **not code-signed yet**, so Windows SmartScreen may show a warning: choose **More info → Run anyway**, after checking the SHA-256 above if you want to be sure.
3. The **DAFO Swarm** icon appears in the system tray. It starts the node in the background; **Open Chat** and **Open Settings** open the dashboard at <http://127.0.0.1:43100>.
4. With an NVIDIA GPU and a current driver, the tray runs the CUDA engine. Without one, or if CUDA fails to start, it switches to the CPU engine by itself.

**Updates:** the tray checks for a new version every 6 hours and offers **Install update**; it waits until the node is idle. Logs are in `%LOCALAPPDATA%\DAFO Swarm\logs` (tray menu → **Open Logs**).

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

The coordinator serves an OpenAI-compatible API on port `43100`. Every request carries an API token created in **Settings → API → API Access**:

```bash
export SWARM_API_KEY=<your API token>
MODEL=$(curl -s http://127.0.0.1:43100/v1/models -H "Authorization: Bearer $SWARM_API_KEY" | jq -r '.data[0].id')

curl -s http://127.0.0.1:43100/v1/chat/completions \
  -H "Authorization: Bearer $SWARM_API_KEY" -H 'content-type: application/json' \
  -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}" \
  | jq -r '.choices[0].message.content'
```

```python
import os
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:43100/v1", api_key=os.environ["SWARM_API_KEY"])
model = client.models.list().data[0].id
reply = client.chat.completions.create(model=model, messages=[{"role": "user", "content": "Hello"}])
print(reply.choices[0].message.content)
```

| Endpoint | Purpose |
|---|---|
| `GET /v1/models` | The swarm's own model, plus AI cloud and linked-coordinator models |
| `GET /v1/agents` | Lists the agents you may use |
| `POST /v1/chat/completions` | Chat, with streaming, images, function tools and an optional `agent` |
| `POST /v1/responses` | Responses API with streaming, files and MCP tools, including the built-in `builtin://chat` tools |
| `/v1/files` | Upload files once and reference them by `file_id` |
| `/api/agents…` | Create, update and delete agents |
| `/api/agents/{id}/knowledge…` | Manage and search an agent's knowledge base |
| `https://localhost:43110/api/swarm/documents…` | Documents shared from the Office add-ins |

Every endpoint is documented with request and response examples in **[docs/API.md](docs/API.md)**.

> **Security:** every request needs an API token, and runs as that token's user. Traffic is plain HTTP: keep the node on `127.0.0.1` or a network you control, or put an HTTPS reverse proxy in front of it.

### Agents that work together

Do not load one agent with every MCP server. Create several specialised agents (one per system: SAP, MES, web…) and a principal agent that talks to the user and delegates to them. Subagents fetch data; it lands as SQL tables in the conversation's workspace, and the principal analyses it there. See **[docs/AGENTS.md](docs/AGENTS.md)**.

---

## Examples

| Folder | What it shows |
|---|---|
| [examples/curl](examples/curl) | Every endpoint from the shell: chat, streaming, images, tools, Responses, agents, knowledge and Office documents |
| [examples/python](examples/python) | The official `openai` SDK and `requests`: chat, streaming, tool calling, agents, loading knowledge from a CSV and the built-in MCP tools |
| [examples/javascript](examples/javascript) | Node.js 20+: the `openai` SDK and plain `fetch`, streaming, loading knowledge and Office documents |

All examples read `SWARM_URL` (default `http://127.0.0.1:43100`) and the API token from `SWARM_API_KEY`.

---

## Support

For installation or API questions, open an issue in this repository. Include the version (from the menu bar, or from `dpkg -l dafo-swarm-cuda`) and the relevant log lines.
