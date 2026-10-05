import re
from typing import Dict, Any


AGENTS = {
    "study": {
        "name": "Study Agent",
        "description": "Handles education, exams, concepts, assignments and learning."
    },

    "coding": {
        "name": "Coding Agent",
        "description": "Handles programming, debugging, software development and code."
    },

    "research": {
        "name": "Research Agent",
        "description": "Handles research, current information, comparisons and web research."
    },

    "career": {
        "name": "Career Agent",
        "description": "Handles resumes, internships, jobs, skills and career planning."
    },

    "productivity": {
        "name": "Productivity Agent",
        "description": "Handles tasks, planning, schedules and organization."
    },

    "general": {
        "name": "General Agent",
        "description": "Handles general conversation and questions."
    }
}


def detect_agent(message: str) -> str:
    """
    Simple local intent router.

    This version does not call an AI model.
    It is fast, free and works without a GPU.
    """

    text = message.lower().strip()

    # Coding
    coding_keywords = [
        "python",
        "java",
        "javascript",
        "c programming",
        "c++",
        "code",
        "coding",
        "program",
        "bug",
        "error",
        "debug",
        "function",
        "class",
        "api",
        "sql",
        "html",
        "css",
        "react",
        "fastapi"
    ]

    if any(word in text for word in coding_keywords):
        return "coding" # Productivity
    
    productivity_keywords = [
        "task",
        "todo",
        "to-do",
        "schedule",
        "plan",
        "planner",
        "remind",
        "deadline",
        "organize",
        "productivity"
    ]

    if any(word in text for word in productivity_keywords):
        return "productivity"

    

    # Study
    study_keywords = [
        "explain",
        "study",
        "exam",
        "assignment",
        "question",
        "definition",
        "what is",
        "difference between",
        "automata",
        "dbms",
        "algorithm",
        "mathematics",
        "formula",
        "theorem",
        "learn"
    ]

    if any(word in text for word in study_keywords):
        return "study"

    # Career
    career_keywords = [
        "resume",
        "cv",
        "internship",
        "job",
        "career",
        "linkedin",
        "interview",
        "skill",
        "placement",
        "salary"
    ]

    if any(word in text for word in career_keywords):
        return "career"

   

    # Research
    research_keywords = [
        "latest",
        "recent",
        "research",
        "news",
        "compare",
        "comparison",
        "current",
        "today",
        "search",
        "information about"
    ]

    if any(word in text for word in research_keywords):
        return "research"

    return "general"


def route_message(message: str) -> Dict[str, Any]:
    """
    Route a user message to the best AURA agent.
    """

    agent_id = detect_agent(message)

    agent = AGENTS[agent_id]

    return {
        "agent": agent_id,
        "agent_name": agent["name"],
        "description": agent["description"]
    }