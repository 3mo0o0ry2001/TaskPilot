import os
import json
from groq import Groq
from dotenv import load_dotenv

from tools import TOOLS
from tool_handlers import TOOL_REGISTRY
from tracer import Tracer
from db import init_db

load_dotenv()

MODEL = "qwen/qwen3-32b"
MAX_ITERATIONS = 10

SYSTEM_PROMPT = """You are TaskPilot, a personal productivity assistant.

You help the user manage their tasks, calendar events, and emails via tools.

TOOLS AVAILABLE:
- find_contact: search contacts by name
- send_email: send email (requires email address, not just name)
- create_task: create a new task
- list_tasks: list tasks filtered by status
- create_event: create a calendar event
- get_current_datetime: get current date/time

STRICT RULES:
1. ALWAYS call find_contact first when user mentions a person by name before sending email.
2. ALWAYS call get_current_datetime FIRST (before any other tool) when the request mentions relative dates, even if the request contains multiple actions. Relative date examples: tomorrow, next week, Monday, بكرة, الأسبوع الجاي.
3. If a contact is not found, say ONLY: "I couldn't find [name] in your contacts. Please provide their email address."
4. Do NOT offer unrequested options or next steps after completing a task.
5. Do NOT expose XML, JSON, or any internal tags in your response.
6. Respond in the same language the user uses.
7. After completing a task, give ONE short confirmation sentence only.

CRITICAL RULES ABOUT ACTIONS:
8. NEVER say you performed an action unless you actually called the tool in this exact turn.
9. NEVER assume an action completed — verify by checking your own tool calls.
10. If you called find_contact but NOT send_email, you did NOT send the email.
11. When user asks to send email: you MUST call send_email. No exceptions.
12. When user provides an email address directly, call send_email immediately — do NOT ask for subject/body, generate reasonable ones from context.
13. For multi-action requests, plan ALL required tools before executing. If ANY action involves a relative date, get_current_datetime must be the very first tool called.
"""

ACTION_INTENTS = [
    "send", "email", "mail",
    "create", "add", "schedule", "remind",
    "بعت", "ابعت", "ضيف", "اعمل", "حدد"
]

RELATIVE_DATE_KEYWORDS = [
    "tomorrow", "next", "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday", "week",
    "بكرة", "الأسبوع", "الجاي", "يوم"
]

CLAIMED_ACTION_PHRASES = [
    "i've sent", "i have sent", "i sent",
    "email has been sent", "sent the email",
    "i've created", "i have created", "i created",
    "task has been created", "event has been created",
    "has been created successfully",      
    "has been successfully created",      
    "i've added", "i have added", "reminder has been set",
    "i've scheduled", "scheduled the",
]

ACTION_TOOLS = {"send_email", "create_task", "create_event"}


class ResponseValidator:
    def validate(self, response_text: str, tools_used: list) -> tuple:
        if not response_text:
            return True, "ok"

        text_lower = response_text.lower()
        claimed = any(phrase in text_lower for phrase in CLAIMED_ACTION_PHRASES)

        if not claimed:
            return True, "ok"

        used_action_tools = any(t in tools_used for t in ACTION_TOOLS)

        if claimed and not used_action_tools:
            return False, f"Hallucination detected: claimed action but used tools: {tools_used}"

        return True, "ok"


class Agent:
    def __init__(self):
     self.client = Groq(
        api_key=os.getenv("GROQ_API_KEY"),
        timeout=120.0,
        max_retries=2
    )
     self.tracer = Tracer()

    def _detect_intent(self, user_message: str) -> str:
        msg = user_message.lower()
        if any(word in msg for word in RELATIVE_DATE_KEYWORDS):
         return "required"
        if any(word in msg for word in ACTION_INTENTS):
            return "required"
        return "auto"


    def _critic_check(self, user_message: str, response: str, tools_used: list) -> tuple:
        critic_prompt = f"""You are a strict QA checker for an AI assistant.

User request: "{user_message}"
Tools actually called: {tools_used}
Assistant response: "{response}"

Answer these questions:
1. Did the assistant claim to perform an action (send email, create task, etc)?
2. If yes, did it actually call the corresponding tool?

If the assistant claimed an action WITHOUT calling the tool, respond with:
FAIL: [brief reason]

If everything is consistent, respond with:
PASS

Only respond with FAIL or PASS and nothing else."""

        try:
            result = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a strict QA checker."},
                    {"role": "user", "content": critic_prompt}
                ],
                max_tokens=100,
                tool_choice="none",
                tools=TOOLS
            )
            verdict = result.choices[0].message.content.strip()
            passed = verdict.upper().startswith("PASS")
            return passed, verdict
        except Exception as e:
            return True, f"Critic check failed (skipped): {e}"

    def run(self, user_message: str) -> str:
        self.tracer.log("user_input", {"text": user_message})
        validator = ResponseValidator()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        for iteration in range(MAX_ITERATIONS):
            tool_choice = self._detect_intent(user_message) if iteration == 0 else "auto"

            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice=tool_choice,
                max_tokens=2048
            )

            message = response.choices[0].message
            tool_calls = message.tool_calls or []

            if message.content and message.content.strip():
                self.tracer.log("llm_thinking", {"text": message.content})

            if response.choices[0].finish_reason == "stop" or not tool_calls:
                final_text = message.content or ""
                tools_used = [
                    e["data"]["tool_name"]
                    for e in self.tracer.events
                    if e["type"] == "tool_call"
                ]

                # طبقة 3: Validation
                is_valid, reason = validator.validate(final_text, tools_used)
                if not is_valid:
                    self.tracer.log("validation_failed", {"reason": reason})
                    messages.append({"role": "assistant", "content": final_text})
                    messages.append({
                        "role": "user",
                        "content": "You claimed to perform an action but I don't see the tool call. Please actually execute the action using the appropriate tool."
                    })
                    continue

                    # طبقة 4: Critic (disabled temporarily due to network latency)
                    # critic_passed, critic_verdict = self._critic_check(user_message, final_text, tools_used)
                    # self.tracer.log("critic_check", {"verdict": critic_verdict, "passed": critic_passed})


                self.tracer.log("final_response", {"text": final_text})
                self.tracer.save()
                return final_text

            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            })

            for tc in tool_calls:
                tool_input = json.loads(tc.function.arguments)
                result = self._execute_tool(tc.function.name, tool_input)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })

        self.tracer.log("error", {"message": f"Max iterations ({MAX_ITERATIONS}) reached"})
        self.tracer.save()
        return "Sorry, I couldn't complete the task within the allowed steps."

    def _execute_tool(self, tool_name: str, tool_input: dict) -> dict:
        self.tracer.log("tool_call", {"tool_name": tool_name, "input": tool_input})

        if tool_name not in TOOL_REGISTRY:
            result = {"error": f"Unknown tool: {tool_name}"}
        else:
            try:
                result = TOOL_REGISTRY[tool_name](**tool_input)
            except Exception as e:
                result = {"error": str(e), "type": type(e).__name__}

        self.tracer.log("tool_result", {"tool_name": tool_name, "result": result})
        return result


def main():
    init_db()
    agent = Agent()

    print("TaskPilot ready. Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input or user_input.lower() in ("exit", "quit"):
            break

        agent.run(user_input)


if __name__ == "__main__":
    main()