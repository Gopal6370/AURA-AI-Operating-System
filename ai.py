from typing import List, Dict
import os
import numpy as np

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
EMBEDDING_MODEL = "gemini-embedding-001"

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


AGENT_PROMPTS = {
    "general": """
You are AURA, an intelligent personal AI operating system.
Be helpful, accurate, practical and concise.
""",

    "study": """
You are AURA Study Agent.
Teach concepts clearly using simple explanations, examples,
step-by-step reasoning and exam-focused summaries.
""",

    "coding": """
You are AURA Coding Agent.
Help with programming, debugging, architecture and code.
Explain errors clearly and provide practical solutions.
""",

    "research": """
You are AURA Research Agent.
Analyze information carefully, distinguish facts from assumptions,
and provide structured research-style answers.
""",

    "career": """
You are AURA Career Agent.
Help with skills, resumes, internships, projects and career planning.
""",

    "productivity": """
You are AURA Productivity Agent.
Help organize tasks, plans, schedules and priorities.
"""
}


def require_client():
    if client is None:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured in the .env file."
        )


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using Google's Gemini embedding model.
    This replaces the old OpenAI embeddings system.
    """

    require_client()

    if not texts:
        return []

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            output_dimensionality=768
        ),
    )

    return [
        list(embedding.values)
        for embedding in result.embeddings
    ]


def cosine_scores(query_embedding, matrix):
    """
    Calculate cosine similarity between a query embedding
    and stored document embeddings.
    """

    q = np.asarray(query_embedding, dtype=np.float32)
    m = np.asarray(matrix, dtype=np.float32)

    if len(m) == 0:
        return np.array([])

    q_norm = np.linalg.norm(q)

    if q_norm == 0:
        return np.zeros(len(m))

    m_norm = np.linalg.norm(m, axis=1)

    denominator = (m_norm * q_norm) + 1e-8

    return (m @ q) / denominator


def answer(
    messages: List[Dict[str, str]],
    agent: str = "general",
    web_search: bool = False,
    context: str = ""
) -> str:

    require_client()

    system_prompt = AGENT_PROMPTS.get(
        agent,
        AGENT_PROMPTS["general"]
    )

    if context:
        system_prompt += (
            "\n\nRelevant AURA memory / knowledge:\n"
            + context
        )

    prompt_parts = [
        system_prompt,
        "",
        "Conversation:"
    ]

    for message in messages:

        role = message.get("role", "user")
        content = message.get("content", "")

        if role == "assistant":
            role_name = "AURA"
        else:
            role_name = "User"

        prompt_parts.append(
            f"{role_name}: {content}"
        )

    prompt_parts.append("")
    prompt_parts.append("AURA:")

    prompt = "\n".join(prompt_parts)

    config = types.GenerateContentConfig(
        max_output_tokens=2048,
        system_instruction=system_prompt,
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config,
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return response.text