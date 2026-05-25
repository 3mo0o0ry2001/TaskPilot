TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_contact",
            "description": "Search for a contact by name. Returns matching contacts with their email addresses. Use this BEFORE sending an email when you only have a person's name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name (or partial name) of the contact to search for"
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to a specific email address. You must have the recipient's email address before calling this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient_email": {"type": "string", "description": "The email address of the recipient"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "The body of the email"}
                },
                "required": ["recipient_email", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task in the user's task list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short description of the task"},
                    "due_date": {"type": "string", "description": "Due date in ISO format (YYYY-MM-DDTHH:MM:SS). Optional."}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List all tasks, optionally filtered by status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "completed"],
                        "description": "Filter tasks by status. Omit to get all tasks."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": "Create a calendar event/reminder at a specific time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS)"},
                    "duration_minutes": {"type": "integer", "description": "Duration in minutes. Defaults to 30."},
                    "description": {"type": "string", "description": "Optional event description"}
                },
                "required": ["title", "start_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Get the current date and time. Use this when the user mentions relative dates like 'tomorrow', 'next week', 'بكرة', etc.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]