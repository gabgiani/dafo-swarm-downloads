"""Interactive launcher for the DAFO Swarm Python API examples.

Launch with run.py so dependencies come from the local virtual environment.
The API token is requested once per menu session when SWARM_API_KEY is unset.
"""

import getpass
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
URL = os.environ.get("SWARM_URL", "http://127.0.0.1:43100").rstrip("/")


def ask(label, default=""):
    value = input(f"{label}" + (f" [{default}]" if default else "") + ": ").strip()
    return value or default


def run(script, *args, extra_env=None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    print(f"\nRunning {script} against {URL}\n", flush=True)
    result = subprocess.run([sys.executable, str(HERE / script), *args], cwd=HERE, env=env)
    print(f"\n{script}: exit {result.returncode}\n", flush=True)


def main():
    print(f"DAFO Swarm Python examples | {URL}")
    if not os.environ.get("SWARM_API_KEY"):
        print("Create a token in Settings > Server > Account > API tokens.")
        token = getpass.getpass("SWARM_API_KEY (hidden; once for this menu): ").strip()
        if not token:
            print("No token entered.", file=sys.stderr)
            return 1
        os.environ["SWARM_API_KEY"] = token

    while True:
        print("1  Chat")
        print("2  Streaming chat")
        print("3  Tool calling")
        print("4  Agent chat")
        print("5  Responses with built-in tools (read only)")
        print("6  Knowledge CSV (dry run)")
        print("7  Office documents (list only)")
        print("8  Knowledge CSV (IMPORT: writes facts)")
        print("9  Office document (read)")
        print("0  Exit")
        try:
            choice = ask("Choose")
            if choice == "0":
                return 0
            if choice == "1":
                run("chat.py", ask("Question", "Explain OEE in two sentences."))
            elif choice == "2":
                run("stream.py", ask("Question", "Write a short paragraph about predictive maintenance."))
            elif choice == "3":
                run("tool_calling.py", ask("Question", "Use get_stock for A-100 and B-200, then say which has fewer units."))
            elif choice == "4":
                run("agent_chat.py", ask("Question", "What do you know about line 3?"))
            elif choice == "5":
                run("responses_builtin_tools.py", ask("Question", "What do you know about line 3?"), extra_env={"SWARM_READ_ONLY": "1"})
            elif choice in ("6", "8"):
                csv_path = ask("CSV path", "knowledge.csv")
                if csv_path != "knowledge.csv":
                    csv_path = str(Path(csv_path).expanduser().resolve())
                if choice == "8" and ask("This will write facts to SWARM. Type yes to continue") != "yes":
                    print("Cancelled.\n")
                    continue
                run("load_knowledge_csv.py", csv_path, extra_env={"SWARM_DRY_RUN": "1" if choice == "6" else "0"})
            elif choice == "7":
                run("office_documents.py", "--list-only")
            elif choice == "9":
                document = ask("Document name (blank: first open)")
                run("office_documents.py", *([document] if document else []))
            else:
                print("Unknown option.\n")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
