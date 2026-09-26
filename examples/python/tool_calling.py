"""Function calling loop: the model requests tools, this script runs them, the model answers.

    python tool_calling.py "How many units of A-100 and B-200 do we have, and which is lower?"
"""
import json
import sys

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
question = sys.argv[1] if len(sys.argv) > 1 else "How many units of A-100 and B-200 do we have, and which is lower?"
messages = [{"role": "user", "content": question}]

for _ in range(5):
    reply = client.chat.completions.create(model=model, messages=messages, tools=TOOLS, tool_choice="auto")
    message = reply.choices[0].message
    if not message.tool_calls:
        print(message.content)
        break
    messages.append(message.model_dump(exclude_none=True))
    for call in message.tool_calls:
        arguments = json.loads(call.function.arguments)
        result = get_stock(**arguments)
        print(f"-> {call.function.name}({arguments}) = {result}")
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
