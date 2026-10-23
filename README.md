# DAFO Swarm — Downloads, API documentation and examples

**DAFO Swarm** runs large language models across the machines you already own. It splits a model's layers between Macs, NVIDIA workstations and servers on your network. The result is served through an **OpenAI-compatible API** and bundled **Word and Excel copilots**. Prompts, documents and knowledge stay on your hardware.

- Website: <https://swarm.dafonet.com>
- Latest release: <https://github.com/gabgiani/dafo-swarm-downloads/releases/latest>
- Full API reference: [docs/API.md](docs/API.md)
- Agents that work together (subagents, shared workspace, design advice): [docs/AGENTS.md](docs/AGENTS.md)
- Single-file guide for AI coding assistants (what it enables, rules, recipes, SAP Connect integration): [llms-full.txt](llms-full.txt), indexed in [llms.txt](llms.txt)
- Runnable examples: [examples/](examples/)

This repository contains the public **installers** and their **checksums**, plus the **API documentation** and **client examples**. The runtime source code is private.

---

## What's new in 0.1.0-20261023.2

- **Claude Code and Codex as agents.** An agent of type **Claude** or **Codex** answers with that program, using the agent's tools, and works as a subagent, in the chat and through the API (`model: "agent/<id>"`), with conversations that continue, per-request tool selection and real token usage and plan limits in every answer. Details: [docs/API.md](docs/API.md#51-external-agents-claude-code-and-codex).
- **A server without a desktop.** The CPU packages (Ubuntu 22.04 and 24.04) need no GPU. The node makes a **setup code** the first time it starts; open `http://<server>:43100` from another computer, enter it and create the administrator. Claude Code is connected from the same page by pasting the token of `claude setup-token`.
- **Android.** A signed APK joins a room as a chat-only node.
- **Windows installer signed** by DAFO AI LTD; macOS package signed and notarized.
- **Safer first start.** Until the first administrator exists, the node accepts nothing from the network except creating it (with the setup code, or from the same computer).

## Downloads

| Platform | Package | Acceleration | Install |
|---|---|---|---|
| macOS 26.5+ on Apple Silicon (M1–M4) | `dafo-swarm-<version>-macos-arm64.pkg` | Metal / MLX | Open the package and approve one admin prompt |
| Ubuntu 24.04 x86_64 with an NVIDIA GPU (compute capability 8.6+, driver 525.60+) | `dafo-swarm-cuda_<version>_amd64.deb` | CUDA 12 runtime bundled | `sudo apt install ./dafo-swarm-cuda_<version>_amd64.deb` |
| Windows 10 / 11 x64 (NVIDIA GPU optional) | `dafo-swarm-setup_<version>_x64.exe` | CUDA 12 when an NVIDIA GPU is present, otherwise CPU | Run the installer; no administrator rights needed |
| Ubuntu 24.04 x86_64, no GPU needed | `dafo-swarm_<version>_amd64.deb` | CPU | `sudo apt install ./dafo-swarm_<version>_amd64.deb` |
| Ubuntu 22.04 x86_64, no GPU needed | `dafo-swarm_<version>_ubuntu22.04_amd64.deb` | CPU | `sudo apt install ./dafo-swarm_<version>_ubuntu22.04_amd64.deb` |
| Android 9+ (phones and tablets, arm64) | `dafo-swarm-<version>-android.apk` | none: chat-only node | Open the APK and allow installing from this source |

Releases starting with `v0.1.0-20260926.3` include a `.sha256` file for each package. For every release, the checksum is also in the `sha256` field of the manifests below. Release tags follow `v0.1.0-YYYYMMDD.N`.

### Always download the latest version

The installed apps check these manifests every 6 hours and offer a one-click update:

```bash
curl -s https://swarm.dafonet.com/downloads/macos-arm64.json
curl -s https://swarm.dafonet.com/downloads/ubuntu24.04-cuda.json
curl -s https://swarm.dafonet.com/downloads/ubuntu24.04-cpu.json
curl -s https://swarm.dafonet.com/downloads/ubuntu22.04-cpu.json
curl -s https://swarm.dafonet.com/downloads/windows-x64.json
curl -s https://swarm.dafonet.com/downloads/android.json
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
sha256sum -c dafo-swarm-cuda_<version>_amd64.deb.sha256            # Linux (CUDA)
sha256sum -c dafo-swarm_<version>_amd64.deb.sha256                 # Linux (CPU)
shasum -a 256 -c dafo-swarm-<version>-android.apk.sha256           # Android
spctl -a -vv -t install dafo-swarm-<version>-macos-arm64.pkg       # macOS: "Notarized Developer ID"
```

On Windows, in PowerShell:

```powershell
(Get-FileHash .\dafo-swarm-setup_<version>_x64.exe -Algorithm SHA256).Hash   # compare with the .sha256 file
Get-AuthenticodeSignature .\dafo-swarm-setup_<version>_x64.exe                # Status: Valid, signer CN=DAFO AI LTD
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

### Ubuntu without a GPU (a server)

```bash
sudo apt install ./dafo-swarm_<version>_amd64.deb          # Ubuntu 22.04: dafo-swarm_<version>_ubuntu22.04_amd64.deb
```

The CPU package runs no GPU engine. It suits a cloud machine that **coordinates a room** or **serves a Claude Code or Codex agent**, with no desktop. To set up such a server from another computer, install it with `install-linux-coordinator.sh`: it prints an address and a **setup code**. Open the address in a browser, enter the code, create the administrator, then create the room and connect to DafoNet. Until the administrator exists, the network can do nothing else with the node.

For a Claude Code agent, install the `claude` CLI on the server, then in the agent editor choose **Claude** and paste the token printed by `claude setup-token` on your own computer.

### Android

1. Download the `.apk` on the phone and open it; Android asks once to allow installing from that source.
2. Open **DAFO Swarm** and join a room with its six-digit code. The phone only chats: it runs no model.
3. The APK is signed with the DAFO release key; updates must be signed with the same key. The signing certificate's SHA-256 is in `android.json` (`signing_certificate_sha256`).

### Windows 10 / 11

1. Download `dafo-swarm-setup_<version>_x64.exe` from the [latest release](https://github.com/gabgiani/dafo-swarm-downloads/releases/latest) and run it.
2. The installer is per user: it installs into `%LOCALAPPDATA%\Programs\DAFO Swarm` and needs no administrator rights. The installer and its programs are code-signed by **DAFO AI LTD**. SmartScreen may still warn while the certificate builds reputation: choose **More info → Run anyway** after checking the signature and SHA-256 above.
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
- **Shared documents:** can **share its document with the swarm**. Other panes can then mention it (for example `@Costos.xlsx`), and the dashboard chat can read it or send it changes. A change sent from the dashboard chat is applied automatically in Word and waits for its user's approval in Excel; a change sent through the HTTP API always waits for approval.

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
| `GET /v1/models` | The swarm's own model, plus AI cloud and linked-coordinator models, with readiness and context limits. Also lists the agents you may use as `agent/<name>` |
| `GET /v1/agents` | Lists the agents you may use |
| `POST /v1/chat/completions` | Chat, with streaming, images, function tools, JSON schema output and an optional `agent` |
| `POST /v1/responses` | Responses API with streaming, files, JSON schema output, subagents and MCP tools, including the built-in `builtin://chat` tools |
| `/v1/files` | Upload files once and reference them by `file_id` |
| `/api/agents…` | Create, update and delete agents, including Claude Code and Codex agents (`kind: "external"`) |
| `/api/external-agents/…` | Which CLIs are installed, connecting Claude Code with a token, and what the CLIs consumed (administrator) |
| `/api/agents/{id}/knowledge…` | Manage and search an agent's knowledge base |
| `https://localhost:43110/api/swarm/documents…` | Documents shared from the Office add-ins |

Every endpoint is documented with request and response examples in **[docs/API.md](docs/API.md)**. When an AI assistant writes the integration for you, point it to **[llms-full.txt](llms-full.txt)**: one self-contained file with everything it needs.

> **Security:** every request needs an API token, and runs as that token's user. Traffic is plain HTTP: new installs listen on every interface, so keep the node behind a firewall or a VPN, or put an HTTPS reverse proxy in front of it. Until the first administrator exists, the network can only create it, with the setup code.

### Claude Code and Codex as agents

An external agent has no Swarm model: its answers come from the **Claude Code** or **Codex** CLI installed on the node's computer, restricted to the agent's tools (MCP servers, databases, knowledge). Create it in the dashboard (**Agents**, choose **Claude** or **Codex**) or with `POST /api/agents` (`"kind": "external"`, `"runner": {"cli": "claude"}`), and reach it like any model: `"model": "agent/<id>"` in `/v1/chat/completions` or `/v1/responses`, streaming included. Its answers carry the tokens and the plan limits the CLI used (`dafo_swarm.usage.rate_limits`), so a program can switch agent before one runs out. It works on a coordinator without a model plan, for example a CPU-only server. Claude Code on a server: install the CLI, then paste the token from `claude setup-token` (run on your own computer) in the agent editor.

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
