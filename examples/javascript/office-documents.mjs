// Lists documents shared from Word/Excel on this Mac, reads one and optionally sends it an instruction.
//   node office-documents.mjs
//   node office-documents.mjs Informe.docx "Add a closing paragraph with the total cost of 18,450 EUR."
// The add-in certificate is trusted by the macOS Keychain, not by Node, and the host only
// listens on localhost, so certificate checks are relaxed for this script only.
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
const OFFICE_URL = process.env.OFFICE_URL ?? "https://localhost:43110";

async function request(target, kind, args) {
  const response = await fetch(`${OFFICE_URL}/api/swarm/documents/request`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ target, kind, source: "Node.js example", arguments: args }),
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error);
  return body.result;
}

const { data: documents } = await (await fetch(`${OFFICE_URL}/api/swarm/documents`)).json();
for (const document of documents) {
  console.log(document.name.padEnd(40), document.app.padEnd(6), document.online ? "open" : "closed");
}

const target = process.argv[2] ?? documents.find((document) => document.online)?.name;
if (!target) throw new Error("No open shared document. Enable 'Share with swarm' in a Word or Excel pane.");

const content = await request(target, "read", {});
console.log(`\n${target}:`);
console.log(content.app === "word" ? content.text : content.text.map((row) => row.join(" | ")).join("\n"));

if (process.argv[3]) {
  console.log("\nSent:", await request(target, "instruction", { instruction: process.argv[3] }));
}
