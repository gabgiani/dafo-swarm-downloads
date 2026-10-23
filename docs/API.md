# DAFO Swarm HTTP API reference

This reference describes version `0.1.0-20261023.2`. The parts on security, agents as models, external agents (Claude Code and Codex) and setting up a server without a desktop were written against that version's source code; the rest was last checked against `0.1.0-20261015.1`. If you are an AI coding assistant, or want a compact implementation guide, read [llms-full.txt](../llms-full.txt) first.

Every DAFO Swarm node serves HTTP on port **43100** (`http://127.0.0.1:43100` by default). Send inference and management requests to the **coordinator**: the node that created the room. It plans the work, runs the layers it owns, and forwards the rest to the other machines.

| Base URL | Served by | Used for |
|---|---|---|
| `http://<coordinator>:43100/v1` | Coordinator | OpenAI-compatible API |
| `http://<coordinator>:43100/api` | Coordinator | Agents, knowledge base, cluster management |
| `https://localhost:43110` (Word), `https://localhost:43111` (Excel) | macOS app | Office add-in panes and shared documents; loopback only |

Examples use `curl` and `jq`, with:

```bash
export SWARM_URL=http://127.0.0.1:43100
export SWARM_API_KEY=<token from Settings → API → API Access>
AUTH="Authorization: Bearer $SWARM_API_KEY"
```

Runnable versions of every example are in [`../examples`](../examples). How agents delegate to each other and share data is explained in [AGENTS.md](AGENTS.md).

---

## Contents

1. [Security](#1-security)
2. [Discovery: `GET /v1/models`, `GET /v1/agents`](#2-discovery)
3. [Chat completions: `POST /v1/chat/completions`](#3-chat-completions)
4. [Responses and MCP tools: `POST /v1/responses`](#4-responses)
5. [Agents](#5-agents)
6. [Knowledge base](#6-knowledge-base)
7. [Shared Office documents](#7-shared-office-documents)
8. [Monitoring](#8-monitoring)
9. [Errors and status codes](#9-errors-and-status-codes)
10. [Limits and behaviour](#10-limits-and-behaviour)

---

## 1. Security

- **Every `/v1` and `/api` request needs a user.** Programs send `Authorization: Bearer <token>` with an API token created in **Settings → API → API Access**; the dashboard uses a login session. Without a valid token the node answers `401` with `code: "unauthorized"`. With the OpenAI SDKs, pass the token as the API key. Only `GET /api/health`, the login endpoints and the web chat widget (which checks its own key and origin) answer without a user.
- A program can also get a token with `POST /api/auth/login` and `{"username", "password", "token": true, "client_name": "My app"}`; the reply carries `token`. API tokens do not expire; revoke them in the dashboard or with `DELETE /api/auth/tokens/{id}`.
- A request runs as the token's user: it sees only that user's chats and files and the agents that user may use. Only administrators manage nodes, models, users, email, databases, MCP servers, functions and linked coordinators.
- **The first administrator.** A new node has no account of its own. Create it in the dashboard on the computer where DAFO Swarm is installed, or with `POST /api/auth/first-account` and `{"username", "password"}` (add `"token": true` to get an API token back instead of a browser session). Until it exists the network can only create it: `POST /api/auth/login` answers `403` (the placeholder administrator cannot sign in from the network) and the setup pages answer `401`.
- **A server without a desktop.** The first time a node starts with no account it makes a **setup code** (`XXXX-XXXX-XXXX`), keeps it beside its identity in an owner-only file, prints it in its output and shows it again with `swarm-node setup-code` (`dafo-swarm setup-code` for the Debian package). From another computer, open `http://<server>:43100`, enter the code and choose the administrator's name and password; over the API, add `"setup_code"` to the `first-account` body. The code is the only thing the network can use before the first account, it works only for creating that account, and it disappears with it. `DAFO_SWARM_SETUP_CODE` sets it from outside for a scripted install.
- Traffic is plain HTTP. New installs listen on every network interface (`0.0.0.0:43100`); a node updated from an older version keeps the address it had. Keep the node behind a firewall or a VPN, or put an HTTPS reverse proxy in front of it, and do not expose port `43100` to the Internet before the first administrator exists.
- The Office document endpoints only listen on `localhost` (ports 43110/43111), so documents cannot be read from other machines.
- Document and knowledge content is passed to the model as **data**, not as instructions. An instruction sent to a shared Office document through the HTTP endpoint becomes a proposal its user must **Apply**; see [section 7](#7-shared-office-documents) for the chat tool.

---

## 2. Discovery

### `GET /v1/models`

Lists the models this swarm can answer with: its own model (`owned_by: "dafo-swarm"`), the models of AI cloud nodes configured by an administrator (ids like `azure/gpt-5`) and those of linked coordinators. Always read ids from here instead of hard-coding them; an unknown `model` returns `404`.

```bash
curl -s $SWARM_URL/v1/models -H "$AUTH"
```

```json
{
  "object": "list",
  "data": [
    { "id": "qwen3-vl-4b-instruct-4bit", "object": "model", "created": 1790416000, "owned_by": "dafo-swarm",
      "dafo_swarm": {
        "coordinator": "Apple M4", "ready": true, "context_limit_tokens": 32768, "visual_tokens": 1120,
        "image_input": { "pixels_per_token": 32, "max_tokens_per_image": 1120, "max_pixels": 1146880 },
        "input_modalities": ["text", "image"],
        "nodes": [ { "name": "Apple M4", "layers": [[0, 36]], "device": "metal", "kv_cache": "bf16" } ] } },
    { "id": "azure/gpt-5", "object": "model", "created": 1790416000, "owned_by": "azure",
      "dafo_swarm": { "coordinator": "Azure", "ready": true, "context_limit_tokens": null, "visual_tokens": null,
                      "image_input": null, "input_modalities": ["text", "image"], "nodes": [] },
      "cloud": { "provider": "azure", "provider_label": "Azure OpenAI", "node": "Azure", "model": "gpt-5", "base_model": "gpt-5",
                 "paid": true, "input_price_per_million": 1.25, "output_price_per_million": 10.0,
                 "monthly_budget": 200.0, "spent_this_month": 12.4, "over_budget": false, "budget_fallback": null } }
  ]
}
```

`data` is empty (still `200`) when no model is configured. Values above are illustrative.

| Field | Meaning |
|---|---|
| `dafo_swarm.ready` | The model can answer now. Send requests only to ready models |
| `dafo_swarm.context_limit_tokens` | Prompt + output tokens one request may use on the current plan (`null` for cloud models) |
| `dafo_swarm.input_modalities` | `["text"]` or `["text", "image"]`. PDF pages reach the model as images, so PDFs need `image` |
| `dafo_swarm.image_input` | How an image becomes visual tokens: `pixels_per_token`, `max_tokens_per_image`, `max_pixels`, and `max_edge_pixels` when the model limits the longest side. `null` when unknown or for cloud models |
| `dafo_swarm.nodes` | Machines holding layers of the swarm's own model: `name`, `layers` (`[start, end)` ranges), `device`, `kv_cache` (`bf16`, `k16_v8` or `int8`) |
| `cloud` | Only for AI cloud models: provider, prices per million tokens, and the node's monthly budget |

#### Agents as models

`/v1/models` also lists the agents the user may use, as `agent/<name>` (`agent/<id>` when two agents share a name), with `owned_by` `agent`, `external-agent` or `linked-agent` and an `agent` object `{id, name, kind}`. A client that can only choose a model reaches an agent by naming it in `model` of `/v1/chat/completions` or `/v1/responses`. A name changes when the agent is renamed: store `agent.id` and send `model: "agent/<id>"`; `GET /v1/models/agent/<id>` checks it. The swarm's own model leaves the list while it has no active plan, so do not take `data[0]` blindly. Every response carries the node's version in `x-dafo-swarm-version`, and `GET /v1/models` repeats it as `dafo_swarm_version`.

### `GET /v1/models/{model}`

Returns one entry, or `404` with `code: "model_not_found"`. Ids may contain slashes (`azure/gpt-5`). A request with images to a model without `image` in `input_modalities` returns `400` with `code: "unsupported_capability"`. The budget in `cloud` covers the whole cloud node, not each model; while `over_budget` is `true`, requests are answered by `budget_fallback` (or the room's model when it is `null`), and the response's `model` names the model that actually answered.

### `GET /v1/agents`

Lists the agents the token's user may use. An agent adds its instructions, knowledge base and tools to any request that names it. Agents marked **Subagent only** are not listed: they work only through the agents that delegate to them (see [AGENTS.md](AGENTS.md)).

```bash
curl -s $SWARM_URL/v1/agents -H "$AUTH"
```

```json
{ "object": "list", "data": [ { "id": "agent-4c1f…", "object": "agent", "name": "Oliver" } ] }
```

Agents shared by a linked coordinator also carry `coordinator`, the name of the swarm that runs them.

---

## 3. Chat completions

### `POST /v1/chat/completions`

This is OpenAI's Chat Completions API. The Word and Excel add-ins use it.

| Field | Type | Required | Notes |
|---|---|---|---|
| `model` | string | no | An id from `/v1/models`. Omitted with an `agent`, the agent's first ready model is used; otherwise the swarm's own model |
| `messages` | array | yes | Non-empty; roles `system`, `user`, `assistant`, `tool` |
| `agent` | string | no | Agent id from `/v1/agents`. Adds its instructions and relevant knowledge |
| `stream` | boolean | no | `true` returns Server-Sent Events |
| `stream_options.include_usage` | boolean | no | Adds a final chunk with `usage` when streaming |
| `max_completion_tokens` | integer | no | Greater than 0 |
| `max_tokens` | integer | no | Legacy alias; if both are sent they must match |
| `temperature` | number | no | `0`–`2`; overrides the configured temperature for this request. `0` gives deterministic output on the swarm's own model |
| `tools` | array | no | Function tools (`type: "function"`). Names must be unique; `parameters` must be a JSON object. `strict: true` validates the model's arguments against `parameters` |
| `tool_choice` | string or object | no | `"auto"` or `"required"` (both need `tools`), `"none"`, or `{"type":"function","function":{"name":…}}` naming a declared tool |
| `parallel_tool_calls` | boolean | no | `false` limits the model to one call per turn |
| `response_format` | object | no | `{"type":"text"}`, `{"type":"json_object"}` or `{"type":"json_schema","json_schema":{"name":…,"schema":{…}}}`. Decoding is constrained to the schema and the final output is validated. Cannot be combined with `tools` |
| `n` | integer | no | Only `1` |

`content` is a string or an array of parts: `{"type":"text","text":…}` and `{"type":"image_url","image_url":{"url":…,"detail":"auto"|"low"|"high"}}`. Other part types (`file`, `input_audio`) are rejected; send files through [`/v1/responses`](#4-responses). Roles are `system`, `user`, `assistant` and `tool`; `developer` is not supported, use `system`.

Unknown fields are **ignored**, not rejected. In particular `top_p`, `stop`, `seed`, `presence_penalty`, `frequency_penalty`, `logprobs` and `user` have no effect: the node's own generation settings apply.

The node always puts its own system context first (identity, the agent's instructions when an `agent` is named, current date and time, language rule). Your leading `system` messages are appended after it, so they still apply.

#### Text

```bash
MODEL=$(curl -s $SWARM_URL/v1/models -H "$AUTH" | jq -r '.data[0].id')

curl -s $SWARM_URL/v1/chat/completions -H "$AUTH" -H 'content-type: application/json' -d "{
  \"model\": \"$MODEL\",
  \"messages\": [
    {\"role\": \"system\", \"content\": \"You are a concise manufacturing assistant.\"},
    {\"role\": \"user\", \"content\": \"Explain OEE in two sentences.\"}
  ],
  \"max_completion_tokens\": 200,
  \"temperature\": 0.2
}"
```

```json
{
  "id": "chatcmpl-…",
  "object": "chat.completion",
  "created": 1790416000,
  "model": "…",
  "choices": [
    { "index": 0,
      "message": { "role": "assistant", "content": "OEE (Overall Equipment Effectiveness) …" },
      "finish_reason": "stop" }
  ],
  "usage": { "prompt_tokens": 38, "completion_tokens": 54, "total_tokens": 92 }
}
```

`finish_reason` is `stop`, `length` (the token limit was reached, or the swarm stopped a model that kept repeating itself) or `tool_calls`.

#### Streaming

```bash
curl -sN $SWARM_URL/v1/chat/completions -H "$AUTH" -H 'content-type: application/json' -d "{
  \"model\": \"$MODEL\", \"stream\": true, \"stream_options\": {\"include_usage\": true},
  \"messages\": [{\"role\": \"user\", \"content\": \"Write a haiku about CNC machines.\"}]
}"
```

```text
data: {"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}
data: {"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"Steel"},"finish_reason":null}]}
…
data: {"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}
data: {"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[],"usage":{"prompt_tokens":20,"completion_tokens":17,"total_tokens":37}}
data: [DONE]
```

If an error happens after streaming starts, it arrives as `data: {"error": {…}}`.

#### With an agent (instructions + knowledge base)

```bash
AGENT=$(curl -s $SWARM_URL/v1/agents -H "$AUTH" | jq -r '.data[0].id')

curl -s $SWARM_URL/v1/chat/completions -H "$AUTH" -H 'content-type: application/json' -d "{
  \"model\": \"$MODEL\", \"agent\": \"$AGENT\",
  \"messages\": [{\"role\": \"user\", \"content\": \"Who supplies the PLC for line 3?\"}]
}"
```

The node puts the agent's instructions into the system context. Knowledge facts are **not** added automatically: an agent reads its knowledge base through the `search_knowledge` tool (available in [`/v1/responses`](#built-in-tools-builtinchat) and the dashboard chat), so chat completions with an agent use its instructions only. An unknown or inaccessible agent returns `400` and a disabled agent `409`, both with `code: "invalid_agent"`. When `model` is omitted, the agent's first ready preferred model answers.

#### Images

Models whose `input_modalities` include `image` (see `/v1/models/{model}`) read images. Pass them as base64 data URLs or HTTP(S) URLs. Supported types are JPEG, PNG and WebP, up to 20 MiB each.

```bash
B64=$(base64 -i part.png | tr -d '\n')
jq -n --arg model "$MODEL" --arg url "data:image/png;base64,$B64" '{
  model: $model,
  messages: [{ role: "user", content: [
    { type: "text", text: "List any visible defects on this part." },
    { type: "image_url", image_url: { url: $url } }
  ]}]
}' | curl -s $SWARM_URL/v1/chat/completions -H "$AUTH" -H 'content-type: application/json' --data-binary @-
```

#### Function tools

```json
{
  "model": "<model id>",
  "messages": [{ "role": "user", "content": "What is the stock of part A-100?" }],
  "tools": [{
    "type": "function",
    "function": {
      "name": "get_stock",
      "description": "Current stock for a part number",
      "parameters": { "type": "object", "properties": { "part": { "type": "string" } }, "required": ["part"] }
    }
  }],
  "tool_choice": "auto"
}
```

When the model calls a tool, `finish_reason` is `tool_calls` and the message contains:

```json
"tool_calls": [{ "id": "call_…", "type": "function", "function": { "name": "get_stock", "arguments": "{\"part\":\"A-100\"}" } }]
```

Run the tool yourself, then send the conversation back with the assistant message and a `{"role":"tool","tool_call_id":"call_…","content":"{\"stock\":42}"}` message. The complete loop is in [`examples/python/tool_calling.py`](../examples/python/tool_calling.py).

---

## 4. Responses

### `POST /v1/responses`

This is OpenAI's Responses API. The dashboard chat uses it. It supports file inputs and **MCP tools**, including the node's built-in tools.

| Field | Type | Required | Notes |
|---|---|---|---|
| `model` | string | no | An id from `/v1/models`. Omitted: the agent's first ready model, otherwise the swarm's own model |
| `input` | string or array | yes | Text, or items `{role, content}` with `input_text`, `input_image` and `input_file` parts |
| `agent` | string | no | Adds the agent's instructions and its **subagents** (as `ask_<name>` tools). It does **not** add the MCP servers or built-in tools configured on the agent in the dashboard: pass the tools you want in `tools` |
| `max_output_tokens` | integer | no | Greater than 0 |
| `temperature` | number | no | `0`–`2`; same override as in chat completions |
| `tools` | array | no | MCP tools only (`type: "mcp"`). Function tools are only in chat completions |
| `max_tool_calls` | integer | no | Greater than 0; default 16 |
| `text.format` | object | no | `{"type":"json_object"}` or `{"type":"json_schema","name":…,"schema":{…}}`, as in OpenAI. Cannot be combined with `tools` |
| `stream` | boolean | no | `true` returns Responses Server-Sent Events |

`instructions`, `previous_response_id`, `store`, `tool_choice` and `metadata` are ignored: send the whole conversation in `input` on every call, and put your instructions in a leading `{"role": "system", "content": "…"}` item.

```bash
curl -s $SWARM_URL/v1/responses -H "$AUTH" -H 'content-type: application/json' \
  -d "{\"model\":\"$MODEL\",\"input\":\"Summarise lean manufacturing in one sentence.\"}" \
  | jq -r '.output[] | select(.type=="message") | .content[0].text'
```

#### Streaming

With `stream: true` the reply is `text/event-stream` in the OpenAI Responses format: `response.created`, `response.in_progress`, then per output item `response.output_item.added`, `response.content_part.added`, `response.output_text.delta`…, `response.output_text.done`, `response.content_part.done`, `response.output_item.done`, and finally `response.completed` (or `response.incomplete`) with the full response. Without `tools`, text deltas arrive while the model generates; with tools, each message's text arrives when its turn ends. A failure emits `error` then `response.failed`. Closing the connection cancels the request. The OpenAI SDK's `client.responses.create(..., stream=True)` reads it.

A response that stopped at its output limit has `status: "incomplete"` and `incomplete_details: {"reason": "max_output_tokens"}`; one the swarm stopped because the model kept repeating itself has `{"reason": "repetition"}`. A response whose MCP server answered with a background task (for example DAFO Agent Bridge) can end with `status: "background_pending"`; the API does not follow such tasks, only the dashboard chat does.

#### Files

`input_file` takes exactly one of `file_id` (a file uploaded to [`/v1/files`](#v1files)), `file_data` (base64 data URL) or `file_url` (HTTP/HTTPS), up to 20 MiB:

- PDFs are rendered to page images, so the model must accept images.
- `text/plain`, `text/markdown`, `text/csv`, `application/csv` and `application/json` are read as UTF-8 text, up to 4 MiB of text per file.
- Other types (Word, Excel, PowerPoint, images as files) are rejected with `unsupported_file`. Send images as `input_image`.

```json
{
  "model": "<model id>",
  "input": [{ "role": "user", "content": [
    { "type": "input_text", "text": "Extract the delivery dates from this order." },
    { "type": "input_file", "filename": "order.pdf", "file_data": "data:application/pdf;base64,…" }
  ]}]
}
```

#### `/v1/files`

Upload a file once and reference it by `file_id`, as with OpenAI. Files are kept on the coordinator, visible only to the user who uploaded them (and administrators), until deleted.

| Request | Result |
|---|---|
| `POST /v1/files` (multipart: `file`, `purpose`) | The file object |
| `GET /v1/files?purpose=&limit=&order=asc\|desc&after=` | `{ "object": "list", "data": [...] }` |
| `GET /v1/files/{file_id}` | The file object |
| `GET /v1/files/{file_id}/content` | The file's bytes |
| `DELETE /v1/files/{file_id}` | `{ "id": "...", "object": "file", "deleted": true }` |

`purpose` is one of `user_data`, `assistants`, `vision`, `batch`, `fine-tune` or `evals`; up to 20 MiB per file.

```bash
curl -s $SWARM_URL/v1/files -H "$AUTH" -F purpose=user_data -F file=@drawing.pdf
```

```json
{ "id": "file-…", "object": "file", "bytes": 48213, "created_at": 1791349200,
  "filename": "drawing.pdf", "purpose": "user_data", "status": "processed", "expires_at": null }
```

The list also carries `first_id`, `last_id` and `has_more`.

An unknown or someone else's `file_id` returns `404` with `code: "file_not_found"`.

#### MCP tools

```json
{
  "type": "mcp",
  "server_label": "erp",
  "server_url": "https://erp.example.com/mcp",
  "authorization": "<token for that server, without the Bearer prefix>",
  "allowed_tools": ["find_order"],
  "require_approval": "never"
}
```

Rules:
- `server_label` must be unique within the request.
- `require_approval` is required and must be `"never"`. There is no approval loop.
- `authorization` is the bare token: the node sends it to the MCP server as `Authorization: Bearer <token>`. It is not a credential for this node, and `builtin://chat` takes none.
- Tool name collisions between servers, connection failures and MCP errors return `502`.

#### Built-in tools: `builtin://chat`

The node itself provides an MCP server with these tools:

| Tool | Purpose | Needs |
|---|---|---|
| `current_datetime` | Current date and time | — |
| `search_knowledge`, `list_knowledge` | Read the agent's knowledge base | `agent` in the request |
| `store_knowledge`, `update_knowledge`, `delete_knowledge` | Change the agent's knowledge base | `agent`, and the right to edit its knowledge |
| `read_web_page`, `search_web` | Read a public page; search the web | `search_web` needs `?search=duckduckgo` in `server_url` |
| `plot_function` | Plot a mathematical function as a chart | — |
| `list_office_documents`, `read_office_document`, `send_office_document_instruction` | Documents the same user shared from Word/Excel on the coordinator's machine | — |
| `check_emails`, `search_emails`, `read_email`, `send_email`, `reply_email`, `forward_email`, `create_email_folder`, `move_email` | The node's configured email account | Sensitive-tool rights |
| `list_databases`, `list_database_tables`, `describe_database_table`, `query_database`, `execute_database_statement` | The database connections assigned to the agent | `agent` with databases, sensitive-tool rights |
| `list_functions` | Published calculation functions | — |
| `create_function`, `delete_function` | Propose or withdraw a draft function (an administrator publishes it) | Sensitive-tool rights |
| `fn_<name>` | One tool per published function: runs its reviewed code | — |

"Sensitive-tool rights" means an administrator, or a user allowed to use the named agent's tools. Tools the token's user may not use are not offered to the model. Mermaid diagrams and ECharts charts are not tools: the model writes fenced `mermaid` or `echarts` code blocks and the dashboard renders them.

The agent whose knowledge and databases the tools use is the request's `agent` field. A `?agent=` parameter in `server_url` is ignored.

The dashboard chat additionally gives agents the conversation workspace tools (`workspace_tables`, `workspace_query`, `workspace_read`, …, see [AGENTS.md](AGENTS.md#4-the-conversation-workspace)) and folder tools; those are not reachable through `/v1/responses`.

```bash
curl -s $SWARM_URL/v1/responses -H "$AUTH" -H 'content-type: application/json' -d "{
  \"model\": \"$MODEL\", \"agent\": \"$AGENT\", \"max_tool_calls\": 4,
  \"input\": \"Remember that line 3 maintenance is every Friday at 6am.\",
  \"tools\": [{
    \"type\": \"mcp\", \"server_label\": \"swarm\",
    \"server_url\": \"builtin://chat\",
    \"allowed_tools\": [\"store_knowledge\", \"search_knowledge\"],
    \"require_approval\": \"never\"
  }]
}"
```

Besides the `message`, `output` contains `mcp_list_tools` and one `mcp_call` item per tool call, with its `arguments`, `output` or `error`:

```json
{
  "id": "resp_…", "object": "response", "status": "completed", "model": "…",
  "output": [
    { "type": "mcp_list_tools", "server_label": "swarm", "tools": [ … ] },
    { "type": "mcp_call", "status": "completed", "server_label": "swarm", "name": "store_knowledge",
      "arguments": "{\"subject\":\"Line 3\",\"predicate\":\"maintenance\",…}", "output": "{\"status\":\"stored\",…}" },
    { "type": "message", "role": "assistant", "status": "completed",
      "content": [{ "type": "output_text", "text": "Saved: line 3 maintenance is every Friday at 6am.", "annotations": [] }] }
  ],
  "usage": { "input_tokens": 812, "output_tokens": 64, "total_tokens": 876 }
}
```

---

## 5. Agents

An agent is a named set of instructions with its own knowledge base, tools (built-in tools, databases, MCP servers), preferred models and, optionally, **subagents**: other agents it delegates to. Agents are stored on the coordinator. Create and edit them in the dashboard (**Settings → Agents**), where tools, MCP servers and subagents are chosen; the endpoints below cover the basic fields. How a team of agents works together, and why several specialised agents beat one agent with many MCP tools, is explained in [AGENTS.md](AGENTS.md).

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET` | `/v1/agents` | — | Agents the user may use (id, name) |
| `POST` | `/api/agents` | `AgentPayload` | The created agent (`id` like `agent-<uuid>`), all fields plus `can_edit` |
| `PUT` | `/api/agents/{agent_id}` | `AgentPayload` | The updated agent |
| `DELETE` | `/api/agents/{agent_id}` | — | `204`; also deletes the agent's knowledge |
| `POST` | `/api/chat-agent` | `{"chat_id", "agent_id"}` | Assigns an agent to a dashboard chat (omit `agent_id` to clear it) |

There is no `GET /api/agents`; `/v1/agents` lists ids and names only. These endpoints work on the coordinator only (`403` elsewhere). Errors here are plain text, with `422` for an invalid payload.

`AgentPayload` (only `name`, `system_prompt` and `enabled` are required):

```json
{
  "name": "Oliver",
  "system_prompt": "You are Oliver, the production assistant of ACME. Answer in Spanish, be precise, cite line numbers.",
  "email_system_prompt": "Optional instructions used only when processing incoming email.",
  "enabled": true,
  "model_preferences": ["qwen3-vl-4b-instruct-4bit", "*"],
  "all_users": false,
  "allowed_group_ids": [],
  "default_knowledge_visibility": "group",
  "tools": {
    "web": true, "mermaid": true, "echarts": true, "email": false, "knowledge": true, "documents": false,
    "functions": [], "function_authoring": false,
    "mcp_servers": [ { "server_id": "<registered MCP server id>", "allowed_tools": ["find_order"] } ]
  },
  "subagent_only": false,
  "subagents": [ { "agent_id": "agent-…", "description": "Fetches SAP orders, stock and purchases", "mode": "data", "enabled": true } ]
}
```

- `model_preferences`: ordered model ids, up to 8. `*` falls back to any ready swarm model, `*:all` to swarm models then cloud models, `*:cloud` to cloud models only.
- `tools` applies in the dashboard chat, Microsoft Teams and when the agent runs as a subagent; `/v1/responses` uses the `tools` of each request instead, and `/v1/chat/completions` only the request's function tools. MCP servers must first be registered by an administrator (**Settings → MCP servers**).
- `subagents[].mode`: `data` (fetches records), `answer` (answers as an expert) or `action` (carries out operations). See [AGENTS.md](AGENTS.md).
- Also accepted: `owner_user_id`, `owner_group_id`, `share_with_federation`, `tools_owner_group_only` (default `true`) and, for administrators, `database_ids`.
- **`PUT` replaces the whole agent.** Omitted fields return to their defaults (for example no tools, no subagents); only `database_ids` is kept when omitted. Send the complete agent you received from `POST`/`PUT`.

```bash
curl -s -X POST $SWARM_URL/api/agents -H "$AUTH" -H 'content-type: application/json' \
  -d '{"name":"Oliver","system_prompt":"You are Oliver, the production assistant of ACME.","enabled":true}'
```

### 5.1 External agents: Claude Code and Codex

An **external** agent has no Swarm model: its answers come from the **Claude Code** or **Codex** command-line program installed on the node's computer, which uses only the agent's tools (its MCP servers, databases, knowledge and built-in tools). Two uses:

- **Outside assistants** (Claude Desktop, VS Code, Claude Code on another machine) use the agent's tools over MCP at `/mcp/agents/<id>` with an API token. Leave the CLI empty for this.
- **With a CLI set**, other Swarm agents add it as a subagent, it appears in the chat's agent selector and in `GET /v1/agents`, and API clients chat with it. It needs no distributed model: a coordinator without a model plan, for example a server without a GPU, still answers.

Create one in the dashboard (**Agents**, type **Claude** or **Codex**) or through the API; only an administrator may set `runner`, because it starts a program on that computer:

```bash
curl -s -X POST $SWARM_URL/api/agents -H "$AUTH" -H 'content-type: application/json' \
  -d '{"name":"Claude","system_prompt":"","enabled":true,"all_users":true,"kind":"external","runner":{"cli":"claude","model":"sonnet"}}'
```

`runner.cli` is `"claude"`, `"codex"` or `null` (only used from outside); `runner.model` is optional (empty uses the CLI's own default).

**Signing the CLI in.** Install the CLI on the node's computer (`GET /api/external-agents/clis` says where each was found: `{"claude": "<path or null>", "codex": "<path or null>"}`). Codex uses the account signed in with `codex login` on that computer. For Claude Code on a server nobody can open a browser on, an administrator runs `claude setup-token` on their own computer and pastes the token in the agent editor (or sends it to the API). The node tries it once with Claude Code and keeps it only if the CLI accepts it; it is stored beside the node identity, given to the CLI on each run and never shown again. An API key (`sk-ant-api…`) works too.

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET` | `/api/external-agents/connections` | — | `{"claude": {"connected": true, "source": "dashboard", "hint": "sk-ant-oat01-…AAAA"}}`; `source` is `dashboard` or `environment`; `{"connected": false}` when there is none |
| `POST` | `/api/external-agents/connections/claude` | `{"token": "…"}` | The same view; `422` with the reason if Claude Code does not accept the token |
| `DELETE` | `/api/external-agents/connections/claude` | — | The same view, now disconnected |

All three are administrator-only.

**Chatting with it.** Name it in `model` (see *Agents as models*), with or without streaming:

```bash
AGENT=$(curl -s $SWARM_URL/v1/models -H "$AUTH" | jq -r '.data[] | select(.agent.name=="Claude") | .id')   # agent/agent-…
curl -s $SWARM_URL/v1/chat/completions -H "$AUTH" -H 'content-type: application/json' \
  -d "{\"model\":\"$AGENT\",\"messages\":[{\"role\":\"user\",\"content\":\"Which orders are late?\"}]}"
```

- **Conversations.** Unlike Swarm models, an external agent keeps a conversation: `/v1/responses` accepts `conversation` (text or `{"id"}`) and `previous_response_id`, and the response `id` names the conversation, so the calls of one job continue the CLI's own session (it remembers earlier images, answers and reasoning). `/v1/chat/completions` takes `conversation_id`. These API chats are not listed in the dashboard.
- **Tools.** `tools` does not define tools here; it **selects** which of the agent's tools the CLI may use in that request, by name (the tool's name, or `server__tool`). Without `tools` it may use all of them; `tool_choice: "none"` none (the CLI does not even connect to the MCP servers); a named function in `tool_choice`, only that one. An unknown name answers `400` with `code: "unknown_tool"` and the list of available tools. Unselected tools cannot be run.
- **Structured output.** `response_format` (chat) and `text.format` (Responses) work: Swarm puts the schema at the end of the user's message, takes the JSON from the answer (whole, in a ```json block or between text), validates it against the schema and, if it does not fit, asks once for a correction.
- **Images and files** sent in the request reach the CLI, and the agent can delegate to other agents with `ask_agent`.

**What it consumed.** The `usage` of the answer is real: `prompt_tokens` (input plus cache reads and writes), `completion_tokens`, `total_tokens`, `prompt_tokens_details.cached_tokens` and `completion_tokens_details.reasoning_tokens`. With `stream: true` it arrives in the last chunk, which has no `choices`, when you send `stream_options.include_usage`. `dafo_swarm.usage` adds the detail:

```json
"dafo_swarm": { "usage": {
  "cli": "claude", "input_tokens": 1200, "cache_read_tokens": 18000, "cache_write_tokens": 0,
  "output_tokens": 340, "reasoning_tokens": 0,
  "cost_usd": 0.042, "cost_is_list_price": true,
  "models": { "claude-opus-4-1": { "input_tokens": 1200, "output_tokens": 340, "cost_usd": 0.042 } },
  "rate_limits": [ { "window": "five_hour", "used_percent": 85.4, "resets_at": 1790420000, "warning": true },
                   { "window": "seven_day", "used_percent": 20.0, "resets_at": 1790900000, "warning": false } ] } }
```

`rate_limits` are the usage windows of the CLI's plan: `five_hour` and `seven_day` for Claude, windows named by their length (`300min`, `10080min`) for Codex. `used_percent` is how full each is, `resets_at` is Unix seconds, and `warning` is true from 80 %, so a caller can switch agent before one runs out. `cost_usd` is at API list prices; with a subscription it is not what is charged. Values above are illustrative. `GET /api/external-agents/usage` (administrator) returns the latest windows of each CLI and the totals of the last 30 days: `{"limits": {"<cli>": {"seen_at", "windows": […]}}, "warning_percent": 80, "agents": [{"cli", "agent_id", "totals"}], "days": [{"day", "totals"}]}`, where `totals` has `requests`, `failed_requests`, the token counts and `cost_usd`. A window that has reset since counts as empty.

---

## 6. Knowledge base

Each agent has a knowledge base of **facts**: a subject–predicate–object triple plus a free-text description. It is stored in SQLite on the coordinator.

Facts are used in two ways:
- **As tools:** the model looks them up with `search_knowledge` and `list_knowledge`, and changes them with `store_knowledge`, `update_knowledge` and `delete_knowledge` (dashboard chat with the agent's **Knowledge** tool enabled, or `builtin://chat` in `/v1/responses`). Facts are not added to prompts automatically.
- **Directly:** through the REST endpoints below. Use these to load data from an ERP, a CRM or a spreadsheet.

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET` | `/api/settings/knowledge-graph` | — | `{enabled, database_path, total_items, embedding_dimension, engine_type}` |
| `POST` | `/api/settings/knowledge-graph` | `{"enabled": true}` | Turns the whole feature on or off (coordinator only) |
| `GET` | `/api/agents/{agent_id}/knowledge` | — | Array of facts, newest first |
| `POST` | `/api/agents/{agent_id}/knowledge` | `KnowledgePayload` | The stored fact (coordinator only) |
| `PUT` | `/api/agents/{agent_id}/knowledge/{item_id}` | `KnowledgePayload` | The updated fact |
| `DELETE` | `/api/agents/{agent_id}/knowledge/{item_id}` | — | `{"deleted": true}` |
| `POST` | `/api/agents/{agent_id}/knowledge/search` | `{"query", "limit"?}` | Ranked results `{item, score, match_type}`; `limit` defaults to 5 |

`KnowledgePayload` and the stored fact:

```json
{ "subject": "Line 3", "predicate": "plc_supplier", "object": "Siemens",
  "content": "Line 3 uses a Siemens S7-1500 PLC; contact Carlos Gómez, carlos@example.com.",
  "visibility": "group" }
```

```json
{ "id": "kg-…", "agent_id": "agent-…", "subject": "Line 3", "predicate": "plc_supplier", "object": "Siemens",
  "content": "…", "created_at": 1790416000000, "updated_at": 1790416000000, "visibility": "group" }
```

`visibility` is `group` (only the agent's owner group) or `public` (every user who may use the agent); omitted, the agent's `default_knowledge_visibility` applies. Facts learned in a Microsoft Teams conversation also carry a `scope` and belong to that conversation only.

Search results combine semantic similarity (60 %) with subject/object/relation matches (40 %):

```bash
curl -s -X POST $SWARM_URL/api/agents/$AGENT/knowledge/search -H "$AUTH" -H 'content-type: application/json' \
  -d '{"query":"who supplies line 3","limit":3}'
```

```json
[ { "item": { "subject": "Line 3", "predicate": "plc_supplier", "object": "Siemens", "content": "…" },
    "score": 0.71, "match_type": "exact_subject+relation+semantic" } ]
```

Bulk-load example from a CSV: [`examples/python/load_knowledge_csv.py`](../examples/python/load_knowledge_csv.py).

---

## 7. Shared Office documents

When a user enables **Share with swarm** in the Word or Excel pane, that document is registered on the node for that user. Only the pane can read or write its document with Office.js, so every request is queued for the pane, which answers it. These endpoints exist only on the add-in hosts, only on `localhost`, and need the same `Authorization: Bearer` token; a user sees only the documents they shared:

- Word: `https://localhost:43110`
- Excel: `https://localhost:43111`

Both hosts share the same registry.

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET` | `/api/swarm/documents` | — | `{"data": [{id, app: "word"|"excel", name, online}]}` |
| `POST` | `/api/swarm/documents/request` | `{"target", "kind", "source", "arguments"}` | `{"result": …}` or `409 {"error": …}` |

- `target`: the document name (case-insensitive) or its id.
- `kind: "read"`:
  - Word arguments: `offset`, `max_chars` (up to 50 000).
  - Excel arguments: `sheet`, `range` (A1 notation, up to 4 000 cells). Without `range`, the used area of the sheet is returned.
- `kind: "instruction"`: `arguments` is `{"instruction": "…"}`. The pane shows the instruction and prepares a proposal. Through this endpoint nothing changes until its user clicks **Apply**. The call returns `{"status": "queued"}` right away.
- The pane has 45 seconds to answer. A pane that has not checked in for 40 seconds is treated as closed (`409`). Without a valid token the answer is `401`.

```bash
# Read the used area of a shared workbook
curl -sk https://localhost:43111/api/swarm/documents/request -H "$AUTH" -H 'content-type: application/json' \
  -d '{"target":"Costos.xlsx","kind":"read","source":"ERP sync","arguments":{}}'
```

```json
{ "result": { "app": "excel", "name": "Costos.xlsx", "sheets": ["Hoja1"], "sheet": "Hoja1",
              "range": "A1:B5", "rows": 5, "columns": 2,
              "text": [["Concepto","Importe"],["Licencias","8.200"],["Servidores","6.750"],["Soporte","3.500"],["Total","18.450"]] } }
```

```bash
# Ask a shared Word document to add a paragraph (its user approves it)
curl -sk https://localhost:43110/api/swarm/documents/request -H "$AUTH" -H 'content-type: application/json' \
  -d '{"target":"Informe.docx","kind":"instruction","source":"ERP sync",
       "arguments":{"instruction":"Add a closing paragraph stating that total costs are 18,450 EUR."}}'
```

The dashboard chat and `/v1/responses` reach the same documents through the built-in tools `list_office_documents`, `read_office_document` and `send_office_document_instruction`. An instruction sent with that tool is **applied automatically by Word** once its pane prepares it; **Excel** still shows it to its user for approval.

---

## 8. Monitoring

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/health` | No token needed. `{mode, node_name, busy, activity}`: use it to check the node is up |
| `GET` | `/api/state?chat_id=<id>` | Room, model, plan, nodes and their readiness; the full chat only for `chat_id` |
| `GET` | `/api/events?chat_id=<id>` | Server-Sent Events with the same snapshot on every change |
| `GET` | `/api/logs?peer=<peer id>&level=warn&limit=200` | Recent logs of this node or of a connected peer |
| `GET` | `/api/office-addins` | Whether the Word/Excel add-ins are installed, registered and listening |

A node is ready when `peers[].status.phase` is `ready` for every node in the active plan.

---

## 9. Errors and status codes

The `/v1` endpoints return OpenAI-style errors:

```json
{ "error": { "message": "model 'x' is not available", "type": "invalid_request_error", "param": "model", "code": "model_not_found" } }
```

| Status | `code` values | Meaning |
|---|---|---|
| `200` | — | Success. With `stream: true`, a later failure arrives inside the stream |
| `400` | `invalid_json`, `invalid_value`, `invalid_messages`, `invalid_input`, `invalid_tools`, `unknown_tool`, `invalid_schema`, `invalid_image`, `invalid_file`, `unsupported_file`, `file_too_large`, `unsupported_capability`, `invalid_agent`, `context_length_exceeded`, `context_length_exceeded_after_tool_calls` | The request is wrong, too long for the model's context, or asks for something the model cannot do |
| `401` | `unauthorized` | Missing or invalid API token |
| `403` | `unauthorized`, `forbidden` | The user may not do this |
| `404` | `model_not_found`, `file_not_found` | Unknown `model` or `file_id` |
| `409` | `invalid_agent` | Disabled agent |
| `413` | `request_too_large` | Body over 64 MiB |
| `500` | `inference_error`, `workspace_error`, `pdf_render_failed`, `file_storage_error` | Internal failure |
| `502` | `invalid_model_output`, `generation_loop`, `invalid_tools`, `mcp_connection_error`, `mcp_error` | The model produced an invalid tool call or structured output, or an MCP server failed |
| `503` | `model_not_ready`, `model_not_available`, `gpu_out_of_memory`, `service_unavailable`, `file_storage_unavailable` | No model or plan loaded, a node went offline, or out of GPU memory (check `/api/state`) |
| `504` | `request_timeout` | The model stopped producing tokens within the configured gap |

Retry `503` and `504` after a pause; do not retry `400`, `401`, `403`, `404` or `409` unchanged. For `context_length_exceeded`, shorten the conversation or the images.

The `/api` endpoints return a plain-text or `{"error": "…"}` body with the status.

---

## 10. Limits and behaviour

- **Models.** The swarm serves one distributed model of its own (change it in Settings → Model) plus any AI cloud or linked-coordinator models listed in `/v1/models`.
- **Concurrency.** Requests beyond the coordinator's *maximum active requests* setting wait in a queue. Every token travels through all the nodes that hold layers, so set generous client timeouts (several minutes for long answers).
- **Context.** Long dashboard chats are summarised automatically before they exceed the memory of the nodes. API clients should keep conversations within the model's context.
- **Request size.** 64 MiB per request body; 20 MiB per image or file; 4 MiB of extracted text per text file.
- **Tool calls.** `/v1/responses` stops after `max_tool_calls` (default 16) tool calls in one request.
- **No server-side conversation state.** Send the whole history on every request; `previous_response_id` and `store` are ignored for Swarm models and agents. External agents (section 5.1) are the exception: their CLI keeps the conversation.
- **Unsupported.** `n > 1`; embeddings, audio, image generation, moderation and batch endpoints; function tools in `/v1/responses`; `file` parts in chat completions; streaming `/v1/responses` with an agent linked from another swarm (`400`, `unsupported_capability`).
- **Knowledge scope.** The knowledge base lives on the coordinator and is not replicated to other nodes.
