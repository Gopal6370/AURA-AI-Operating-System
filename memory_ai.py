import json
import re

from .ai import answer


MEMORY_PROMPT = """
You are AURA's memory extraction system.

Analyze the conversation and determine whether there is any
useful long-term information that AURA should remember about
the user.

Only save information that is:
- useful in future conversations
- reasonably stable
- directly stated by the user

Do NOT save:
- passwords
- API keys
- financial credentials
- highly sensitive personal information
- temporary information
- random conversation

Return ONLY valid JSON in this format:

{
    "should_remember": true,
    "memories": [
        "short useful memory"
    ]
}

If there is nothing useful:

{
    "should_remember": false,
    "memories": []
}
"""


def extract_memories(conversation_text: str):

    prompt = f"""
{MEMORY_PROMPT}

Conversation:

{conversation_text}
"""

    try:

        result = answer(
            [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            agent="general",
            web_search=False,
            context=""
        )

        text = result.strip()

        # Remove markdown code fences if the model adds them
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"\s*```$",
            "",
            text
        )

        data = json.loads(text)

        if not isinstance(data, dict):
            return []

        if not data.get("should_remember"):
            return []

        memories = data.get("memories", [])

        if not isinstance(memories, list):
            return []

        return [
            str(memory).strip()
            for memory in memories
            if str(memory).strip()
        ]

    except Exception as exc:

        print(
            "Memory extraction error:",
            type(exc).__name__,
            str(exc)
        )

        return []