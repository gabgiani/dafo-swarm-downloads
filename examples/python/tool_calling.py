"""Function calling loop: the model requests tools, this script runs them, the model answers.

    python tool_calling.py "How many units of A-100 and B-200 do we have, and which is lower?"
"""
import json
import sys

from openai import APIStatusError

from swarm import active_model, client

# Replace with real lookups in your ERP / MES.
STOCK = {"A-100": 42, "B-200": 7}


def get_stock(part: str) -> dict:
    return {"part": part, "stock": STOCK.get(part), "found": part in STOCK}


TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_stock",
        "description": "Current warehouse stock for a part number",
        "parameters": {
            "type": "object",
            "properties": {"part": {"type": "string", "description": "Part number, e.g. A-100"}},
            "required": ["part"],
        },
    },
}]

model = active_model()
question = sys.argv[1] if len(sys.argv) > 1 else "Use get_stock for A-100 and B-200, then say which has fewer units."
print("Question:", question, flush=True)
messages = [
    {"role": "system", "content": "When calling get_stock, supply valid JSON arguments containing only the part string."},
    {"role": "user", "content": question},
]

for _ in range(5):
    for attempt in range(3):
        try:
            reply = client.chat.completions.create(
                model=model, messages=messages, tools=TOOLS, tool_choice="auto",
                temperature=0, max_completion_tokens=160,
            )
            break
        except APIStatusError as error:
            details = error.body if isinstance(error.body, dict) else {}
            code = details.get("code") or details.get("error", {}).get("code")
            invalid_arguments = error.status_code == 502 and code == "invalid_model_output"
            if not invalid_arguments or attempt == 2:
                raise
            print("Model returned invalid tool arguments; retrying.", file=sys.stderr, flush=True)
    message = reply.choices[0].message
    if not message.tool_calls:
        print("Answer:", message.content)
        break
    messages.append(message.model_dump(exclude_none=True))
    for call in message.tool_calls:
        arguments = json.loads(call.function.arguments)
        result = get_stock(**arguments)
        print(f"-> {call.function.name}({arguments}) = {result}")
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
else:
    raise SystemExit("The model did not finish after five tool rounds.")
