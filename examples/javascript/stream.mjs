// Streaming with plain fetch (no SDK): parses the Server-Sent Events of /v1/chat/completions.
//   node stream.mjs "Write a short paragraph about predictive maintenance."
const SWARM_URL = (process.env.SWARM_URL ?? "http://127.0.0.1:43100").replace(/\/$/, "");

const models = await (await fetch(`${SWARM_URL}/v1/models`)).json();
const response = await fetch(`${SWARM_URL}/v1/chat/completions`, {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({
    model: models.data[0].id,
    stream: true,
    stream_options: { include_usage: true },
    messages: [{ role: "user", content: process.argv[2] ?? "Write a short paragraph about predictive maintenance." }],
  }),
});
if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);

const decoder = new TextDecoder();
let buffer = "";
for await (const bytes of response.body) {
  buffer += decoder.decode(bytes, { stream: true });
  let newline;
  while ((newline = buffer.indexOf("\n")) >= 0) {
    const line = buffer.slice(0, newline).trim();
    buffer = buffer.slice(newline + 1);
    if (!line.startsWith("data:")) continue;
    const data = line.slice(5).trim();
    if (data === "[DONE]") process.exit(0);
    const chunk = JSON.parse(data);
    if (chunk.error) throw new Error(chunk.error.message);
    const delta = chunk.choices?.[0]?.delta?.content;
    if (delta) process.stdout.write(delta);
    if (chunk.usage) console.log(`\n[${chunk.usage.completion_tokens} tokens]`);
  }
}
