import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()
TRACES_DIR = Path(__file__).parent / "traces"
TRACES_DIR.mkdir(exist_ok=True)


class Tracer:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.events = []
        self.trace_file = TRACES_DIR / f"trace_{self.session_id}.json"

    def log(self, event_type: str, data: dict):
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        self.events.append(event)
        self._print_event(event)

    def _print_event(self, event):
        t = event["type"]
        d = event["data"]

        if t == "user_input":
            console.print(Panel(d["text"], title="👤 User", border_style="cyan"))

        elif t == "llm_thinking":
            if d.get("text"):
                console.print(Panel(d["text"], title="🤖 Claude", border_style="green"))

        elif t == "tool_call":
            payload = f"[bold]{d['tool_name']}[/bold]\n{json.dumps(d['input'], indent=2, ensure_ascii=False)}"
            console.print(Panel(payload, title="🔧 Tool Call", border_style="yellow"))

        elif t == "tool_result":
            result_str = json.dumps(d["result"], indent=2, ensure_ascii=False)
            console.print(Panel(
                Syntax(result_str, "json", theme="monokai"),
                title=f"✅ Tool Result: {d['tool_name']}",
                border_style="magenta"
            ))

        elif t == "final_response":
            console.print(Panel(d["text"], title="🎯 Final Response", border_style="bright_blue"))

        elif t == "error":
            console.print(Panel(d["message"], title="❌ Error", border_style="red"))

    def save(self):
        with open(self.trace_file, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": self.session_id,
                "events": self.events
            }, f, indent=2, ensure_ascii=False)
        console.print(f"\n[dim]Trace saved to {self.trace_file}[/dim]")