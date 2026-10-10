# DAFO Swarm HTTP API reference

This reference covers version `0.1.0-20261010.11` and later.

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

- **Every request needs a user.** Programs send `Authorization: Bearer <token>` with an API token created in **Settings → API → API Access**; the dashboard uses a login session. Without a valid token the node answers `401` with `code: "unauthorized"`. With the OpenAI SDKs, pass the token as the API key.
- A request runs as the token's user: it sees only that user's chats and the agents that user may use. Only administrators manage nodes, models, users, email and linked coordinators.
- A new coordinator starts with the user `admin` / password `admin`, which must be changed at the first login.
- Traffic is plain HTTP. Keep the node on `127.0.0.1` or a private network, or put an HTTPS reverse proxy in front of it.
- The Office document endpoints only listen on `localhost` (ports 43110/43111), so documents cannot be read from other machines.
- Document and knowledge content is passed to the model as **data**, not as instructions. Changes to an Office document always require approval by that document's user.

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
    { "id": "qwen3-vl-4b-instruct-4bit", "object": "model", "created": 1790416000, "owned_by": "dafo-swarm" },
    { "id": "azure/gpt-5", "object": "model", "created": 1790416000, "owned_by": "azure" }
  ]
}
```

`data` is empty (still `200`) when no model is configured.

### `GET /v1/models/{model}`

Returns one entry, or `404` with `code: "model_not_found"`. Ids may contain slashes. `dafo_swarm.input_modalities` is `["text", "image"]` or `["text"]`; for the swarm's own model, `dafo_swarm.image_input` tells how an image becomes visual tokens (`pixels_per_token`, `max_tokens_per_image`, `max_pixels`), so a client can size images. AI cloud models carry a `cloud` object with prices and their node's monthly budget (`monthly_budget`, `spent_this_month`, `over_budget`, `budget_fallback`); while over budget, requests are answered by the fallback model, named in the response's `model`.

### `GET /v1/agents`

Lists the agents the token's user may use. An agent adds its instructions, knowledge base and tools to any request that names it. Agents marked **Subagent only** are not listed: they work only through the agents that delegate to them (see [AGENTS.md](AGENTS.md)).

```bash
curl -s $SWARM_URL/v1/agents -H "$AUTH"
```

```json
{ "object": "list", "data": [ { "id": "agent-4c1f…", "object": "agent", "name": "Oliver" } ] }
```

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
| `tools` | array | no | Function tools (`type: "function"`) |
| `tool_choice` | string or object | no | `"auto"`, `"none"`, `"required"` or `{"type":"function","function":{"name":…}}` |
| `parallel_tool_calls` | boolean | no | `false` limits the model to one call per turn |
| `n` | integer | no | Only `1` |

`content` is a string or an array of parts: `{"type":"text","text":…}` and `{"type":"image_url","image_url":{"url":…,"detail":"auto"|"low"|"high"}}`.

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

The node puts the agent's instructions and the 5 knowledge facts most relevant to the last user message into the system context. An unknown agent returns `400` and a disabled agent returns `409`.

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
| `model` | string | yes | An id from `/v1/models` |
| `input` | string or array | yes | Text, or items `{role, content}` with `input_text`, `input_image` and `input_file` parts |
| `agent` | string | no | Same behaviour as in chat completions; the agent's own tools and subagents are used |
| `max_output_tokens` | integer | no | Greater than 0 |
| `temperature` | number | no | `0`–`2`; same override as in chat completions |
| `tools` | array | no | MCP tools only (`type: "mcp"`) |
| `max_tool_calls` | integer | no | Greater than 0 |
| `stream` | boolean | no | `true` returns Responses Server-Sent Events |

```bash
curl -s $SWARM_URL/v1/responses -H "$AUTH" -H 'content-type: application/json' \
  -d "{\"model\":\"$MODEL\",\"input\":\"Summarise lean manufacturing in one sentence.\"}" \
  | jq -r '.output[] | select(.type=="message") | .content[0].text'
```

#### Streaming

With `stream: true` the reply is `text/event-stream` in the OpenAI Responses format: `response.created`, `response.in_progress`, then per output item `response.output_item.added`, `response.content_part.added`, `response.output_text.delta`…, `response.output_text.done`, `response.content_part.done`, `response.output_item.done`, and finally `response.completed` (or `response.incomplete`) with the full response. Without `tools`, text deltas arrive while the model generates; with tools, each message's text arrives when its turn ends. A failure emits `error` then `response.failed`. Closing the connection cancels the request. The OpenAI SDK's `client.responses.create(..., stream=True)` reads it.

A response that stopped at its output limit has `status: "incomplete"` and `incomplete_details: {"reason": "max_output_tokens"}`; one the swarm stopped because the model kept repeating itself has `{"reason": "repetition"}`.

#### Files

`input_file` takes exactly one of `file_id` (a file uploaded to [`/v1/files`](#v1files)), `file_data` (base64 data URL) or `file_url` (HTTP/HTTPS), up to 20 MiB:

- PDFs are rendered to page images.
- `text/plain`, `text/markdown`, `text/csv` and `application/json` are read as text.

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

An unknown or someone else's `file_id` returns `404` with `code: "file_not_found"`.

#### MCP tools

```json
{
  "type": "mcp",
  "server_label": "erp",
  "server_url": "https://erp.example.com/mcp",
  "authorization": "Bearer <token for that server>",
  "allowed_tools": ["find_order"],
  "require_approval": "never"
}
```

Rules:
- `server_label` must be unique within the request.
- `require_approval` must be `"never"`.
- `authorization` is sent to the MCP server only; it is not a credential for this node.

#### Built-in tools: `builtin://chat`

The node itself provides an MCP server with these tools:

| Tool | Purpose |
|---|---|
| `store_knowledge`, `search_knowledge`, `list_knowledge` | Write and read the agent's knowledge base |
| `list_office_documents`, `read_office_document`, `send_office_document_instruction` | Work with documents shared from Word/Excel on the same machine |
| `read_web_page`, `search_web` | Read a public page or search the web (`?search=duckduckgo` enables search) |
| `render_mermaid`, `render_echarts`, `plot_function` | Diagrams and charts (rendered by the dashboard) |
| `check_emails`, `search_emails`, `read_email`, `send_email`, `reply_email`, `forward_email`, `create_email_folder`, `move_email` | The configured email account |

Add `?agent=<agent id>` to `server_url` to choose which agent's knowledge the tools use.

```bash
curl -s $SWARM_URL/v1/responses -H "$AUTH" -H 'content-type: application/json' -d "{
  \"model\": \"$MODEL\", \"agent\": \"$AGENT\", \"max_tool_calls\": 4,
  \"input\": \"Remember that line 3 maintenance is every Friday at 6am.\",
  \"tools\": [{
    \"type\": \"mcp\", \"server_label\": \"swarm\",
    \"server_url\": \"builtin://chat?agent=$AGENT\",
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
| `POST` | `/api/agents` | `AgentPayload` | The created agent (`id` like `agent-<uuid>`) |
| `PUT` | `/api/agents/{agent_id}` | `AgentPayload` | The updated agent |
| `DELETE` | `/api/agents/{agent_id}` | — | `204`; also deletes the agent's knowledge |
| `POST` | `/api/chat-agent` | `{"chat_id", "agent_id"}` | Assigns an agent to a dashboard chat (omit `agent_id` to clear it) |

`AgentPayload`:

```json
{
  "name": "Oliver",
  "system_prompt": "You are Oliver, the production assistant of ACME. Answer in Spanish, be precise, cite line numbers.",
  "email_system_prompt": "Optional instructions used only when processing incoming email.",
  "enabled": true
}
```

```bash
curl -s -X POST $SWARM_URL/api/agents -H "$AUTH" -H 'content-type: application/json' \
  -d '{"name":"Oliver","system_prompt":"You are Oliver, the production assistant of ACME.","enabled":true}'
```

---

## 6. Knowledge base

Each agent has a knowledge base of **facts**: a subject–predicate–object triple plus a free-text description. It is stored in SQLite on the coordinator.

Facts are used in three ways:
- **Automatically:** every request that names the agent receives the 5 most relevant facts. This covers the chat, the Office add-ins and the API.
- **As tools:** `store_knowledge`, `search_knowledge` and `list_knowledge` through `builtin://chat`.
- **Directly:** through the REST endpoints below. Use these to load data from an ERP, a CRM or a spreadsheet.

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET` | `/api/settings/knowledge-graph` | — | `{enabled, database_path, total_items, embedding_dimension, engine_type}` |
| `POST` | `/api/settings/knowledge-graph` | `{"enabled": true}` | Turns the whole feature on or off (coordinator only) |
| `GET` | `/api/agents/{agent_id}/knowledge` | — | Array of facts, newest first |
| `POST` | `/api/agents/{agent_id}/knowledge` | `KnowledgePayload` | The stored fact (coordinator only) |
| `PUT` | `/api/agents/{agent_id}/knowledge/{item_id}` | `KnowledgePayload` | The updated fact |
| `DELETE` | `/api/agents/{agent_id}/knowledge/{item_id}` | — | `{"deleted": true}` |
| `POST` | `/api/agents/{agent_id}/knowledge/search` | `{"query", "limit"?}` | Ranked results `{item, score, match_type}` |

`KnowledgePayload` and the stored fact:

```json
{ "subject": "Line 3", "predicate": "plc_supplier", "object": "Siemens",
  "content": "Line 3 uses a Siemens S7-1500 PLC; contact Carlos Gómez, carlos@example.com." }
```

```json
{ "id": "kg-…", "agent_id": "agent-…", "subject": "Line 3", "predicate": "plc_supplier", "object": "Siemens",
  "content": "…", "created_at": 1790416000000, "updated_at": 1790416000000 }
```

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

When a user enables **Share with swarm** in the Word or Excel pane, that document is registered on the node. Only the pane can read or write its document with Office.js, so every request is queued for the pane, which answers it. These endpoints exist only on the add-in hosts, and only on `localhost`:

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
- `kind: "instruction"`: `arguments` is `{"instruction": "…"}`. The pane shows the instruction and prepares a proposal. Nothing changes until its user clicks **Apply**. The call returns `{"status": "queued"}` right away.
- The pane has 45 seconds to answer. A pane that has not checked in for 40 seconds is treated as closed (`409`).

```bash
# Read the used area of a shared workbook
curl -sk https://localhost:43111/api/swarm/documents/request -H 'content-type: application/json' \
  -d '{"target":"Costos.xlsx","kind":"read","source":"ERP sync","arguments":{}}'
```

```json
{ "result": { "app": "excel", "name": "Costos.xlsx", "sheets": ["Hoja1"], "sheet": "Hoja1",
              "range": "A1:B5", "rows": 5, "columns": 2,
              "text": [["Concepto","Importe"],["Licencias","8.200"],["Servidores","6.750"],["Soporte","3.500"],["Total","18.450"]] } }
```

```bash
# Ask a shared Word document to add a paragraph (its user approves it)
curl -sk https://localhost:43110/api/swarm/documents/request -H 'content-type: application/json' \
  -d '{"target":"Informe.docx","kind":"instruction","source":"ERP sync",
       "arguments":{"instruction":"Add a closing paragraph stating that total costs are 18,450 EUR."}}'
```

The dashboard chat and `/v1/responses` reach the same documents through the built-in tools `list_office_documents`, `read_office_document` and `send_office_document_instruction`.

---

## 8. Monitoring

| Method | Path | Notes |
|---|---|---|
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

| Status | Meaning |
|---|---|
| `200` | Success |
| `400` | Malformed request, empty messages, invalid image or file, unsupported option, unknown agent |
| `401` | Missing or invalid API token (`code: "unauthorized"`) |
| `403` | The user may not do this (management call by a non-administrator, or on a node that is not the coordinator) |
| `404` | Unknown `model` or `file_id` |
| `409` | Disabled agent; shared document not found or its pane is closed |
| `502` | Invalid tool call generated by the model, or MCP server failure |
| `503` | No model or plan loaded, or a node went offline (check `/api/state`) |
| `504` | The model stopped producing tokens within the configured gap |

The `/api` endpoints return a plain-text or `{"error": "…"}` body with the status.

---

## 10. Limits and behaviour

- **Models.** The swarm serves one distributed model of its own (change it in Settings → Model) plus any AI cloud or linked-coordinator models listed in `/v1/models`.
- **Concurrency.** Requests beyond the coordinator's *maximum active requests* setting wait in a queue. Every token travels through all the nodes that hold layers, so set generous client timeouts (several minutes for long answers).
- **Context.** Long dashboard chats are summarised automatically before they exceed the memory of the nodes. API clients should keep conversations within the model's context.
- **Request size.** 64 MiB per request body; 20 MiB per image or file.
- **Unsupported.** `n > 1`, embeddings and audio endpoints, and streaming `/v1/responses` with an agent linked from another swarm.
- **Knowledge scope.** The knowledge base lives on the coordinator and is not replicated to other nodes.
